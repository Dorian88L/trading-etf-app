"""
Endpoints pour la gestion de portfolio personnalisé
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.user_preferences import Portfolio, PortfolioPosition, PortfolioTransaction
from app.services.etf_catalog import get_etf_catalog_service
from app.services.portfolio_service import get_portfolio_calculation_service

router = APIRouter()

@router.get(
    "/portfolios",
    tags=["portfolio"],
    summary="Liste des portfolios de l'utilisateur"
)
async def get_user_portfolios(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère tous les portfolios de l'utilisateur"""
    try:
        portfolios = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id,
            Portfolio.is_active == True
        ).all()
        
        portfolio_data = []
        for portfolio in portfolios:
            # Calculer les métriques du portfolio
            total_value = sum(pos.current_value or 0 for pos in portfolio.positions)
            total_invested = sum(pos.total_invested for pos in portfolio.positions)
            unrealized_pnl = total_value - total_invested
            unrealized_pnl_percent = (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0
            
            portfolio_data.append({
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'is_default': portfolio.is_default,
                'total_value': round(total_value, 2),
                'total_invested': round(total_invested, 2),
                'unrealized_pnl': round(unrealized_pnl, 2),
                'unrealized_pnl_percent': round(unrealized_pnl_percent, 2),
                'positions_count': len(portfolio.positions),
                'created_at': portfolio.created_at.isoformat(),
                'updated_at': portfolio.updated_at.isoformat()
            })
        
        return {
            'status': 'success',
            'count': len(portfolio_data),
            'data': portfolio_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération portfolios: {str(e)}")

@router.post(
    "/portfolios",
    tags=["portfolio"],
    summary="Créer un nouveau portfolio"
)
async def create_portfolio(
    name: str,
    description: str = None,
    is_default: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crée un nouveau portfolio pour l'utilisateur"""
    try:
        # Si c'est le portfolio par défaut, désactiver les autres
        if is_default:
            db.query(Portfolio).filter(
                Portfolio.user_id == current_user.id,
                Portfolio.is_default == True
            ).update({'is_default': False})
        
        # Créer le nouveau portfolio
        portfolio = Portfolio(
            user_id=current_user.id,
            name=name,
            description=description,
            is_default=is_default
        )
        
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        
        return {
            'status': 'success',
            'message': f'Portfolio "{name}" créé avec succès',
            'data': {
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'is_default': portfolio.is_default,
                'created_at': portfolio.created_at.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur création portfolio: {str(e)}")

@router.get(
    "/portfolios/{portfolio_id}",
    tags=["portfolio"],
    summary="Détails d'un portfolio"
)
async def get_portfolio_details(
    portfolio_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les détails complets d'un portfolio"""
    try:
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio non trouvé")
        
        catalog_service = get_etf_catalog_service()
        
        # Préparer les données des positions
        positions_data = []
        total_value = 0
        total_invested = 0
        
        for position in portfolio.positions:
            etf_info = catalog_service.get_etf_by_isin(position.etf_isin)
            
            current_value = position.current_value or (position.quantity * position.average_price)
            unrealized_pnl = current_value - position.total_invested
            unrealized_pnl_percent = (unrealized_pnl / position.total_invested * 100) if position.total_invested > 0 else 0
            
            total_value += current_value
            total_invested += position.total_invested
            
            positions_data.append({
                'id': position.id,
                'etf_isin': position.etf_isin,
                'etf_symbol': position.etf_symbol,
                'etf_name': etf_info.name if etf_info else position.etf_symbol,
                'sector': etf_info.sector if etf_info else 'Unknown',
                'quantity': float(position.quantity),
                'average_price': float(position.average_price),
                'current_price': float(position.current_price) if position.current_price else float(position.average_price),
                'total_invested': float(position.total_invested),
                'current_value': float(current_value),
                'unrealized_pnl': float(unrealized_pnl),
                'unrealized_pnl_percent': round(unrealized_pnl_percent, 2),
                'weight_percent': 0,  # Calculé après
                'stop_loss_price': float(position.stop_loss_price) if position.stop_loss_price else None,
                'target_price': float(position.target_price) if position.target_price else None,
                'opened_at': position.opened_at.isoformat(),
                'updated_at': position.updated_at.isoformat()
            })
        
        # Calculer les poids dans le portfolio
        for position in positions_data:
            position['weight_percent'] = round((position['current_value'] / total_value * 100) if total_value > 0 else 0, 2)
        
        # Métriques globales du portfolio
        portfolio_pnl = total_value - total_invested
        portfolio_pnl_percent = (portfolio_pnl / total_invested * 100) if total_invested > 0 else 0
        
        # Analyse sectorielle
        sector_allocation = {}
        for position in positions_data:
            sector = position['sector']
            if sector in sector_allocation:
                sector_allocation[sector] += position['current_value']
            else:
                sector_allocation[sector] = position['current_value']
        
        # Convertir en pourcentages
        sector_percentages = {
            sector: round((value / total_value * 100), 2) if total_value > 0 else 0
            for sector, value in sector_allocation.items()
        }
        
        return {
            'status': 'success',
            'data': {
                'portfolio': {
                    'id': portfolio.id,
                    'name': portfolio.name,
                    'description': portfolio.description,
                    'is_default': portfolio.is_default,
                    'created_at': portfolio.created_at.isoformat(),
                    'updated_at': portfolio.updated_at.isoformat()
                },
                'metrics': {
                    'total_value': round(total_value, 2),
                    'total_invested': round(total_invested, 2),
                    'unrealized_pnl': round(portfolio_pnl, 2),
                    'unrealized_pnl_percent': round(portfolio_pnl_percent, 2),
                    'positions_count': len(positions_data),
                    'best_performer': max(positions_data, key=lambda x: x['unrealized_pnl_percent']) if positions_data else None,
                    'worst_performer': min(positions_data, key=lambda x: x['unrealized_pnl_percent']) if positions_data else None
                },
                'positions': positions_data,
                'sector_allocation': sector_percentages,
                'risk_metrics': {
                    'diversification_score': len(set(p['sector'] for p in positions_data)),
                    'largest_position_weight': max([p['weight_percent'] for p in positions_data]) if positions_data else 0,
                    'concentration_risk': 'High' if any(p['weight_percent'] > 20 for p in positions_data) else 'Medium' if any(p['weight_percent'] > 10 for p in positions_data) else 'Low'
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération détails portfolio: {str(e)}")

@router.post(
    "/portfolios/{portfolio_id}/positions",
    tags=["portfolio"],
    summary="Ajouter une position au portfolio"
)
async def add_position_to_portfolio(
    portfolio_id: int,
    etf_isin: str,
    etf_symbol: str,
    quantity: float,
    price: float,
    fees: float = 0.0,
    notes: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Ajoute une nouvelle position au portfolio"""
    try:
        # Vérifier que le portfolio appartient à l'utilisateur
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio non trouvé")
        
        # Vérifier que l'ETF existe
        catalog_service = get_etf_catalog_service()
        etf_info = catalog_service.get_etf_by_isin(etf_isin)
        
        if not etf_info:
            raise HTTPException(status_code=404, detail="ETF non trouvé dans le catalogue")
        
        total_amount = quantity * price
        
        # Vérifier si une position existe déjà pour cet ETF
        existing_position = db.query(PortfolioPosition).filter(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.etf_isin == etf_isin
        ).first()
        
        if existing_position:
            # Mettre à jour la position existante (moyenne pondérée)
            new_total_quantity = existing_position.quantity + quantity
            new_total_invested = existing_position.total_invested + total_amount
            new_average_price = new_total_invested / new_total_quantity
            
            existing_position.quantity = new_total_quantity
            existing_position.average_price = new_average_price
            existing_position.total_invested = new_total_invested
            existing_position.current_value = new_total_quantity * price  # Approximation
            existing_position.updated_at = datetime.now()
            
            position = existing_position
        else:
            # Créer nouvelle position
            position = PortfolioPosition(
                portfolio_id=portfolio_id,
                etf_isin=etf_isin,
                etf_symbol=etf_symbol,
                quantity=quantity,
                average_price=price,
                total_invested=total_amount,
                current_value=total_amount,
                current_price=price
            )
            db.add(position)
        
        # Créer la transaction
        transaction = PortfolioTransaction(
            portfolio_id=portfolio_id,
            position_id=position.id if existing_position else None,
            etf_isin=etf_isin,
            etf_symbol=etf_symbol,
            transaction_type='BUY',
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            fees=fees,
            notes=notes
        )
        db.add(transaction)
        
        db.commit()
        
        if not existing_position:
            db.refresh(position)
            transaction.position_id = position.id
            db.commit()
        
        return {
            'status': 'success',
            'message': f'Position {etf_symbol} ajoutée au portfolio',
            'data': {
                'position_id': position.id,
                'etf_symbol': etf_symbol,
                'quantity': float(position.quantity),
                'average_price': float(position.average_price),
                'total_invested': float(position.total_invested),
                'transaction_id': transaction.id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur ajout position: {str(e)}")

@router.post(
    "/portfolios/{portfolio_id}/positions/{position_id}/sell",
    tags=["portfolio"],
    summary="Vendre une partie ou la totalité d'une position"
)
async def sell_position(
    portfolio_id: int,
    position_id: int,
    quantity: float,
    price: float,
    fees: float = 0.0,
    notes: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Vend une partie ou la totalité d'une position"""
    try:
        # Vérifier la position
        position = db.query(PortfolioPosition).join(Portfolio).filter(
            PortfolioPosition.id == position_id,
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id
        ).first()
        
        if not position:
            raise HTTPException(status_code=404, detail="Position non trouvée")
        
        if quantity > position.quantity:
            raise HTTPException(status_code=400, detail="Quantité à vendre supérieure à la position")
        
        total_amount = quantity * price
        
        # Créer la transaction de vente
        transaction = PortfolioTransaction(
            portfolio_id=portfolio_id,
            position_id=position_id,
            etf_isin=position.etf_isin,
            etf_symbol=position.etf_symbol,
            transaction_type='SELL',
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            fees=fees,
            notes=notes
        )
        db.add(transaction)
        
        # Mettre à jour la position
        if quantity == position.quantity:
            # Vente complète - supprimer la position
            db.delete(position)
        else:
            # Vente partielle - ajuster la position
            remaining_quantity = position.quantity - quantity
            # Réduire le total investi proportionnellement
            position.total_invested = (position.total_invested / position.quantity) * remaining_quantity
            position.quantity = remaining_quantity
            position.current_value = remaining_quantity * position.current_price if position.current_price else remaining_quantity * position.average_price
            position.updated_at = datetime.now()
        
        db.commit()
        
        # Calculer le P&L réalisé
        cost_basis = (position.total_invested / (position.quantity + quantity)) * quantity if position else position.average_price * quantity
        realized_pnl = total_amount - cost_basis - fees
        
        return {
            'status': 'success',
            'message': f'Vente de {quantity} parts de {position.etf_symbol} effectuée',
            'data': {
                'transaction_id': transaction.id,
                'quantity_sold': quantity,
                'sale_price': price,
                'total_amount': total_amount,
                'realized_pnl': round(realized_pnl, 2),
                'remaining_quantity': float(position.quantity) if position.quantity else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur vente position: {str(e)}")

@router.get(
    "/portfolios/{portfolio_id}/performance",
    tags=["portfolio"],
    summary="Performance historique du portfolio"
)
async def get_portfolio_performance(
    portfolio_id: int,
    period: str = Query("1M", description="Période: 1W, 1M, 3M, 6M, 1Y"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère la performance historique du portfolio"""
    try:
        # Vérifier le portfolio
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio non trouvé")
        
        # Calculer la période de temps
        period_map = {
            '1W': 7,
            '1M': 30,
            '3M': 90,
            '6M': 180,
            '1Y': 365
        }
        
        days_back = period_map.get(period, 30)
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Récupérer les transactions de la période
        transactions = db.query(PortfolioTransaction).filter(
            PortfolioTransaction.portfolio_id == portfolio_id,
            PortfolioTransaction.executed_at >= start_date
        ).order_by(PortfolioTransaction.executed_at).all()
        
        # Calculer les métriques de performance
        total_invested = 0
        total_sold = 0
        realized_pnl = 0
        
        for transaction in transactions:
            if transaction.transaction_type == 'BUY':
                total_invested += transaction.total_amount + transaction.fees
            elif transaction.transaction_type == 'SELL':
                total_sold += transaction.total_amount - transaction.fees
        
        # Performance simulée (en production, utiliser les vraies valeurs historiques)
        current_positions = portfolio.positions
        current_value = sum(pos.current_value or 0 for pos in current_positions)
        unrealized_pnl = current_value - sum(pos.total_invested for pos in current_positions)
        
        total_return = realized_pnl + unrealized_pnl
        total_return_percent = (total_return / total_invested * 100) if total_invested > 0 else 0
        
        # Générer des points de performance pour le graphique
        performance_points = []
        for i in range(days_back):
            date = start_date + timedelta(days=i)
            # Simulation d'une courbe de performance
            daily_return = total_return_percent * (i / days_back) + (i * 0.1 * ((-1) ** (i % 3)))
            performance_points.append({
                'date': date.isoformat(),
                'value': round(10000 * (1 + daily_return / 100), 2),  # Base 10000€
                'return_percent': round(daily_return, 2)
            })
        
        return {
            'status': 'success',
            'data': {
                'portfolio_id': portfolio_id,
                'period': period,
                'summary': {
                    'total_invested': round(total_invested, 2),
                    'current_value': round(current_value, 2),
                    'total_return': round(total_return, 2),
                    'total_return_percent': round(total_return_percent, 2),
                    'realized_pnl': round(realized_pnl, 2),
                    'unrealized_pnl': round(unrealized_pnl, 2),
                    'best_day': max(performance_points, key=lambda x: x['return_percent']) if performance_points else None,
                    'worst_day': min(performance_points, key=lambda x: x['return_percent']) if performance_points else None
                },
                'performance_history': performance_points,
                'transactions_count': len(transactions)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération performance: {str(e)}")

@router.get(
    "/portfolios/{portfolio_id}/transactions",
    tags=["portfolio"],
    summary="Historique des transactions du portfolio"
)
async def get_portfolio_transactions(
    portfolio_id: int,
    limit: int = Query(50, description="Nombre maximum de transactions"),
    offset: int = Query(0, description="Décalage pour la pagination"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère l'historique des transactions du portfolio"""
    try:
        # Vérifier le portfolio
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio non trouvé")
        
        # Récupérer les transactions
        transactions = db.query(PortfolioTransaction).filter(
            PortfolioTransaction.portfolio_id == portfolio_id
        ).order_by(PortfolioTransaction.executed_at.desc()).offset(offset).limit(limit).all()
        
        total_count = db.query(PortfolioTransaction).filter(
            PortfolioTransaction.portfolio_id == portfolio_id
        ).count()
        
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'id': transaction.id,
                'type': transaction.transaction_type,
                'etf_symbol': transaction.etf_symbol,
                'etf_isin': transaction.etf_isin,
                'quantity': float(transaction.quantity),
                'price': float(transaction.price),
                'total_amount': float(transaction.total_amount),
                'fees': float(transaction.fees),
                'notes': transaction.notes,
                'executed_at': transaction.executed_at.isoformat(),
                'signal_based': transaction.signal_id is not None
            })
        
        return {
            'status': 'success',
            'data': transaction_data,
            'pagination': {
                'total': total_count,
                'count': len(transaction_data),
                'offset': offset,
                'limit': limit,
                'has_more': (offset + limit) < total_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération transactions: {str(e)}")