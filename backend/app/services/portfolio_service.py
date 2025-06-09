"""
Service pour calculer les valeurs réelles du portfolio
"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.portfolio import Portfolio, Position, Transaction, TransactionType
from app.models.etf import ETF
from app.services.real_market_data import RealMarketDataService, get_real_market_data_service
import logging

logger = logging.getLogger(__name__)

class PortfolioCalculationService:
    """Service pour calculer les valeurs réelles du portfolio"""
    
    # Mapping ISIN -> Symbol (basé sur les ETFs configurés)
    ISIN_TO_SYMBOL = {
        'IE00B4L5Y983': 'IWDA.AS',
        'IE00BK5BQT80': 'VWCE.DE', 
        'IE00B5BMR087': 'CSPX.L',
        'IE00B4L5YC18': 'IUSQ.DE',
        'IE00BKM4GZ66': 'EIMI.DE',
        'IE00B3XXRP09': 'VUAA.DE'  # Note: VUSA.AS a le même ISIN
    }
    
    def __init__(self, market_service: RealMarketDataService = None):
        self.market_service = market_service or get_real_market_data_service()
    
    def calculate_portfolio_value(self, db: Session, portfolio_id: str) -> Dict:
        """Calcule la valeur totale réelle du portfolio"""
        try:
            # Récupérer toutes les positions du portfolio
            positions = db.query(Position).filter(
                Position.portfolio_id == portfolio_id
            ).all()
            
            if not positions:
                return {
                    'total_value': 0,
                    'total_cost': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0,
                    'positions_count': 0,
                    'positions_detail': []
                }
            
            total_value = Decimal('0')
            total_cost = Decimal('0')
            positions_detail = []
            
            for position in positions:
                # Récupérer le symbole à partir de l'ISIN
                symbol = self.ISIN_TO_SYMBOL.get(position.etf_isin)
                if not symbol:
                    logger.warning(f"Aucun symbole trouvé pour ISIN {position.etf_isin}")
                    continue
                
                # Récupérer le prix actuel de l'ETF
                etf_data = self.market_service.get_real_etf_data(symbol)
                
                if etf_data:
                    current_price = Decimal(str(etf_data.current_price))
                    position_value = position.quantity * current_price
                    position_cost = position.quantity * position.average_price
                    position_pnl = position_value - position_cost
                    position_pnl_percent = (position_pnl / position_cost * 100) if position_cost > 0 else 0
                    
                    total_value += position_value
                    total_cost += position_cost
                    
                    positions_detail.append({
                        'etf_symbol': symbol,
                        'etf_name': position.etf.name,
                        'quantity': float(position.quantity),
                        'average_price': float(position.average_price),
                        'current_price': float(current_price),
                        'position_value': float(position_value),
                        'position_cost': float(position_cost),
                        'pnl': float(position_pnl),
                        'pnl_percent': float(position_pnl_percent),
                        'currency': etf_data.currency
                    })
                else:
                    logger.warning(f"Impossible de récupérer le prix pour {symbol}")
            
            total_pnl = total_value - total_cost
            total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            
            return {
                'total_value': float(total_value),
                'total_cost': float(total_cost),
                'total_pnl': float(total_pnl),
                'total_pnl_percent': float(total_pnl_percent),
                'positions_count': len(positions),
                'positions_detail': positions_detail
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du portfolio {portfolio_id}: {e}")
            return {
                'error': str(e),
                'total_value': 0,
                'total_cost': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'positions_count': 0,
                'positions_detail': []
            }
    
    def calculate_today_pnl(self, db: Session, portfolio_id: str) -> Dict:
        """Calcule le P&L du jour basé sur les variations des ETFs"""
        try:
            positions = db.query(Position).filter(
                Position.portfolio_id == portfolio_id
            ).all()
            
            if not positions:
                return {'today_pnl': 0, 'today_pnl_percent': 0}
            
            today_pnl = Decimal('0')
            total_previous_value = Decimal('0')
            
            for position in positions:
                # Récupérer le symbole à partir de l'ISIN
                symbol = self.ISIN_TO_SYMBOL.get(position.etf_isin)
                if not symbol:
                    continue
                    
                etf_data = self.market_service.get_real_etf_data(symbol)
                
                if etf_data:
                    current_price = Decimal(str(etf_data.current_price))
                    previous_price = current_price - Decimal(str(etf_data.change))
                    
                    current_position_value = position.quantity * current_price
                    previous_position_value = position.quantity * previous_price
                    
                    position_today_pnl = current_position_value - previous_position_value
                    today_pnl += position_today_pnl
                    total_previous_value += previous_position_value
            
            today_pnl_percent = (today_pnl / total_previous_value * 100) if total_previous_value > 0 else 0
            
            return {
                'today_pnl': float(today_pnl),
                'today_pnl_percent': float(today_pnl_percent)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du P&L du jour pour {portfolio_id}: {e}")
            return {'today_pnl': 0, 'today_pnl_percent': 0}
    
    def calculate_portfolio_analytics(self, db: Session, portfolio_id: str) -> Dict:
        """Calcule des métriques avancées du portfolio"""
        try:
            positions = db.query(Position).filter(
                Position.portfolio_id == portfolio_id
            ).all()
            
            if not positions:
                return self._empty_analytics()
            
            # Récupérer les transactions pour calculs historiques
            transactions = db.query(Transaction).filter(
                Transaction.portfolio_id == portfolio_id
            ).order_by(Transaction.transaction_date).all()
            
            # Calculs de base
            portfolio_value = self.calculate_portfolio_value(db, portfolio_id)
            today_pnl = self.calculate_today_pnl(db, portfolio_id)
            
            # Calculs avancés
            sector_allocation = self._calculate_sector_allocation(positions)
            region_allocation = self._calculate_region_allocation(positions)
            risk_metrics = self._calculate_risk_metrics(positions)
            performance_metrics = self._calculate_performance_metrics(transactions, portfolio_value)
            
            return {
                **portfolio_value,
                **today_pnl,
                'sector_allocation': sector_allocation,
                'region_allocation': region_allocation,
                'risk_metrics': risk_metrics,
                'performance_metrics': performance_metrics,
                'diversification_score': self._calculate_diversification_score(sector_allocation),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul analytics portfolio {portfolio_id}: {e}")
            return self._empty_analytics()
    
    def _calculate_sector_allocation(self, positions: List[Position]) -> Dict:
        """Calcule la répartition par secteur"""
        from app.services.etf_catalog import get_etf_catalog_service
        
        catalog_service = get_etf_catalog_service()
        sector_values = {}
        total_value = Decimal('0')
        
        for position in positions:
            symbol = self.ISIN_TO_SYMBOL.get(position.etf_isin)
            if symbol:
                etf_info = catalog_service.get_etf_by_symbol(symbol)
                if etf_info:
                    etf_data = self.market_service.get_real_etf_data(symbol)
                    if etf_data:
                        current_price = Decimal(str(etf_data.current_price))
                        position_value = position.quantity * current_price
                        
                        sector = etf_info.sector
                        sector_values[sector] = sector_values.get(sector, Decimal('0')) + position_value
                        total_value += position_value
        
        # Convertir en pourcentages
        sector_allocation = {}
        for sector, value in sector_values.items():
            percentage = (value / total_value * 100) if total_value > 0 else 0
            sector_allocation[sector] = {
                'value': float(value),
                'percentage': float(percentage)
            }
        
        return sector_allocation
    
    def _calculate_region_allocation(self, positions: List[Position]) -> Dict:
        """Calcule la répartition par région"""
        from app.services.etf_catalog import get_etf_catalog_service
        
        catalog_service = get_etf_catalog_service()
        region_values = {}
        total_value = Decimal('0')
        
        for position in positions:
            symbol = self.ISIN_TO_SYMBOL.get(position.etf_isin)
            if symbol:
                etf_info = catalog_service.get_etf_by_symbol(symbol)
                if etf_info:
                    etf_data = self.market_service.get_real_etf_data(symbol)
                    if etf_data:
                        current_price = Decimal(str(etf_data.current_price))
                        position_value = position.quantity * current_price
                        
                        region = etf_info.region
                        region_values[region] = region_values.get(region, Decimal('0')) + position_value
                        total_value += position_value
        
        # Convertir en pourcentages
        region_allocation = {}
        for region, value in region_values.items():
            percentage = (value / total_value * 100) if total_value > 0 else 0
            region_allocation[region] = {
                'value': float(value),
                'percentage': float(percentage)
            }
        
        return region_allocation
    
    def _calculate_risk_metrics(self, positions: List[Position]) -> Dict:
        """Calcule les métriques de risque du portfolio"""
        try:
            if not positions:
                return {'average_ter': 0, 'concentration_risk': 0, 'volatility_score': 0}
            
            from app.services.etf_catalog import get_etf_catalog_service
            catalog_service = get_etf_catalog_service()
            
            total_value = Decimal('0')
            weighted_ter = Decimal('0')
            position_weights = []
            
            for position in positions:
                symbol = self.ISIN_TO_SYMBOL.get(position.etf_isin)
                if symbol:
                    etf_info = catalog_service.get_etf_by_symbol(symbol)
                    etf_data = self.market_service.get_real_etf_data(symbol)
                    
                    if etf_info and etf_data:
                        current_price = Decimal(str(etf_data.current_price))
                        position_value = position.quantity * current_price
                        total_value += position_value
                        
                        # TER pondéré
                        weighted_ter += position_value * Decimal(str(etf_info.ter))
                        
                        # Poids de position pour concentration
                        position_weights.append(float(position_value))
            
            # TER moyen pondéré
            average_ter = float(weighted_ter / total_value) if total_value > 0 else 0
            
            # Risque de concentration (Herfindahl Index)
            if position_weights and total_value > 0:
                normalized_weights = [w / float(total_value) for w in position_weights]
                concentration_risk = sum(w**2 for w in normalized_weights)
            else:
                concentration_risk = 0
            
            # Score de volatilité (simplifié)
            volatility_score = average_ter * 10 + concentration_risk * 50
            
            return {
                'average_ter': average_ter,
                'concentration_risk': concentration_risk,
                'volatility_score': min(100, volatility_score)  # Cap à 100
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques de risque: {e}")
            return {'average_ter': 0, 'concentration_risk': 0, 'volatility_score': 0}
    
    def _calculate_performance_metrics(self, transactions: List[Transaction], portfolio_value: Dict) -> Dict:
        """Calcule les métriques de performance historique"""
        try:
            if not transactions:
                return {'total_invested': 0, 'total_withdrawals': 0, 'realized_pnl': 0, 'unrealized_pnl': 0}
            
            total_invested = Decimal('0')
            total_withdrawals = Decimal('0')
            realized_pnl = Decimal('0')
            
            for transaction in transactions:
                if transaction.transaction_type == TransactionType.BUY:
                    total_invested += transaction.quantity * transaction.price
                elif transaction.transaction_type == TransactionType.SELL:
                    total_withdrawals += transaction.quantity * transaction.price
                    # Calcul simplifié du PnL réalisé
                    # En pratique, il faudrait tracker le coût moyen par position
            
            # PnL non réalisé = valeur actuelle - (investi - retiré)
            net_invested = total_invested - total_withdrawals
            unrealized_pnl = Decimal(str(portfolio_value.get('total_value', 0))) - net_invested
            
            return {
                'total_invested': float(total_invested),
                'total_withdrawals': float(total_withdrawals),
                'net_invested': float(net_invested),
                'realized_pnl': float(realized_pnl),
                'unrealized_pnl': float(unrealized_pnl)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques de performance: {e}")
            return {'total_invested': 0, 'total_withdrawals': 0, 'realized_pnl': 0, 'unrealized_pnl': 0}
    
    def _calculate_diversification_score(self, sector_allocation: Dict) -> float:
        """Calcule un score de diversification (0-100)"""
        try:
            if not sector_allocation:
                return 0
            
            # Plus le nombre de secteurs est élevé et plus les poids sont équilibrés,
            # plus le score est élevé
            num_sectors = len(sector_allocation)
            
            if num_sectors <= 1:
                return 20  # Très peu diversifié
            
            # Calculer l'indice de Simpson inversé
            percentages = [sector['percentage'] / 100 for sector in sector_allocation.values()]
            simpson_index = sum(p**2 for p in percentages)
            
            # Score basé sur le nombre de secteurs et l'équilibre
            balance_score = (1 - simpson_index) * 100
            diversity_bonus = min(num_sectors * 10, 40)  # Bonus jusqu'à 4 secteurs
            
            total_score = balance_score + diversity_bonus
            return min(100, max(0, total_score))
            
        except Exception as e:
            logger.error(f"Erreur calcul score de diversification: {e}")
            return 0
    
    def _empty_analytics(self) -> Dict:
        """Retourne des analytics vides en cas d'erreur"""
        return {
            'total_value': 0,
            'total_cost': 0,
            'total_pnl': 0,
            'total_pnl_percent': 0,
            'today_pnl': 0,
            'today_pnl_percent': 0,
            'positions_count': 0,
            'sector_allocation': {},
            'region_allocation': {},
            'risk_metrics': {'average_ter': 0, 'concentration_risk': 0, 'volatility_score': 0},
            'performance_metrics': {'total_invested': 0, 'total_withdrawals': 0, 'realized_pnl': 0, 'unrealized_pnl': 0},
            'diversification_score': 0
        }

def get_portfolio_calculation_service() -> PortfolioCalculationService:
    """Dependency injection pour le service de calcul de portfolio"""
    return PortfolioCalculationService()