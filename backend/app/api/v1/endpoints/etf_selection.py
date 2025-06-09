"""
Endpoints pour la sélection d'ETFs et gestion des watchlists
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.user_preferences import UserWatchlist, UserPreferences, UserSignalSubscription
from app.services.etf_catalog import get_etf_catalog_service, ETFInfo
from app.services.signal_generator import get_signal_generator_service
from app.services.technical_indicators import get_technical_analysis_service

router = APIRouter()

@router.get(
    "/catalog",
    tags=["etf-selection"],
    summary="Catalogue complet d'ETFs disponibles",
    description="""
    Récupère le catalogue complet des ETFs européens disponibles pour sélection.
    
    **Filtres disponibles :**
    - Secteur (technology, healthcare, etc.)
    - Région (Europe, USA, World, etc.)
    - TER maximum
    - AUM minimum
    - Devise
    
    **Tri disponible :**
    - Par popularité (AUM)
    - Par coût (TER)
    - Par nom
    """
)
async def get_etf_catalog(
    sector: Optional[str] = Query(None, description="Filtrer par secteur"),
    region: Optional[str] = Query(None, description="Filtrer par région"),
    max_ter: Optional[float] = Query(None, description="TER maximum (ex: 0.20 pour 0.20%)"),
    min_aum: Optional[float] = Query(None, description="AUM minimum en euros"),
    currency: Optional[str] = Query(None, description="Devise (EUR, USD)"),
    sort_by: str = Query("popularity", description="Tri: popularity, cost, name"),
    limit: int = Query(50, description="Nombre maximum d'ETFs à retourner")
):
    """Récupère le catalogue d'ETFs avec filtres"""
    try:
        catalog_service = get_etf_catalog_service()
        
        # Appliquer les filtres
        sectors_filter = [sector] if sector else None
        regions_filter = [region] if region else None
        currencies_filter = [currency] if currency else None
        
        etfs = catalog_service.filter_etfs(
            sectors=sectors_filter,
            regions=regions_filter,
            max_ter=max_ter,
            min_aum=min_aum,
            currencies=currencies_filter
        )
        
        # Trier
        if sort_by == "popularity":
            etfs.sort(key=lambda x: x.aum, reverse=True)
        elif sort_by == "cost":
            etfs.sort(key=lambda x: x.ter)
        elif sort_by == "name":
            etfs.sort(key=lambda x: x.name)
        
        # Limiter les résultats
        etfs = etfs[:limit]
        
        # Convertir en format API
        etf_data = []
        for etf in etfs:
            etf_data.append({
                'isin': etf.isin,
                'symbol': etf.symbol,
                'name': etf.name,
                'sector': etf.sector,
                'region': etf.region,
                'currency': etf.currency,
                'ter': etf.ter,
                'aum': etf.aum,
                'exchange': etf.exchange,
                'description': etf.description,
                'benchmark': etf.benchmark,
                'inception_date': etf.inception_date,
                'dividend_frequency': etf.dividend_frequency,
                'replication_method': etf.replication_method
            })
        
        return {
            'status': 'success',
            'count': len(etf_data),
            'data': etf_data,
            'filters_applied': {
                'sector': sector,
                'region': region,
                'max_ter': max_ter,
                'min_aum': min_aum,
                'currency': currency
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération catalogue: {str(e)}")

@router.get(
    "/sectors",
    tags=["etf-selection"],
    summary="Liste des secteurs disponibles"
)
async def get_available_sectors():
    """Récupère la liste des secteurs d'ETFs disponibles"""
    try:
        catalog_service = get_etf_catalog_service()
        sectors = catalog_service.get_sectors()
        
        return {
            'status': 'success',
            'data': sectors,
            'count': len(sectors)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération secteurs: {str(e)}")

@router.get(
    "/regions",
    tags=["etf-selection"],
    summary="Liste des régions disponibles"
)
async def get_available_regions():
    """Récupère la liste des régions d'ETFs disponibles"""
    try:
        catalog_service = get_etf_catalog_service()
        regions = catalog_service.get_regions()
        
        return {
            'status': 'success',
            'data': regions,
            'count': len(regions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération régions: {str(e)}")

@router.get(
    "/search",
    tags=["etf-selection"],
    summary="Recherche d'ETFs"
)
async def search_etfs(
    q: str = Query(..., description="Terme de recherche (nom, secteur, symbole)"),
    limit: int = Query(20, description="Nombre maximum de résultats")
):
    """Recherche d'ETFs par nom, secteur ou symbole"""
    try:
        catalog_service = get_etf_catalog_service()
        results = catalog_service.search_etfs(q)[:limit]
        
        etf_data = []
        for etf in results:
            etf_data.append({
                'isin': etf.isin,
                'symbol': etf.symbol,
                'name': etf.name,
                'sector': etf.sector,
                'region': etf.region,
                'currency': etf.currency,
                'ter': etf.ter,
                'aum': etf.aum,
                'description': etf.description
            })
        
        return {
            'status': 'success',
            'query': q,
            'count': len(etf_data),
            'data': etf_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recherche: {str(e)}")

@router.get(
    "/popular",
    tags=["etf-selection"],
    summary="ETFs les plus populaires"
)
async def get_popular_etfs(limit: int = Query(10, description="Nombre d'ETFs à retourner")):
    """Récupère les ETFs les plus populaires (par AUM)"""
    try:
        catalog_service = get_etf_catalog_service()
        popular_etfs = catalog_service.get_popular_etfs(limit)
        
        etf_data = []
        for etf in popular_etfs:
            etf_data.append({
                'isin': etf.isin,
                'symbol': etf.symbol,
                'name': etf.name,
                'sector': etf.sector,
                'aum': etf.aum,
                'ter': etf.ter,
                'description': etf.description
            })
        
        return {
            'status': 'success',
            'count': len(etf_data),
            'data': etf_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération ETFs populaires: {str(e)}")

@router.get(
    "/low-cost",
    tags=["etf-selection"],
    summary="ETFs à faibles coûts"
)
async def get_low_cost_etfs(
    max_ter: float = Query(0.20, description="TER maximum"),
    limit: int = Query(20, description="Nombre d'ETFs à retourner")
):
    """Récupère les ETFs avec des frais faibles"""
    try:
        catalog_service = get_etf_catalog_service()
        low_cost_etfs = catalog_service.get_low_cost_etfs(max_ter)[:limit]
        
        etf_data = []
        for etf in low_cost_etfs:
            etf_data.append({
                'isin': etf.isin,
                'symbol': etf.symbol,
                'name': etf.name,
                'sector': etf.sector,
                'ter': etf.ter,
                'aum': etf.aum,
                'description': etf.description
            })
        
        return {
            'status': 'success',
            'max_ter_filter': max_ter,
            'count': len(etf_data),
            'data': etf_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération ETFs faible coût: {str(e)}")

@router.get(
    "/watchlist",
    tags=["watchlist"],
    summary="Watchlist de l'utilisateur"
)
async def get_user_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère la watchlist de l'utilisateur connecté"""
    try:
        watchlist = db.query(UserWatchlist).filter(
            UserWatchlist.user_id == current_user.id,
            UserWatchlist.is_active == True
        ).all()
        
        watchlist_data = []
        catalog_service = get_etf_catalog_service()
        
        for item in watchlist:
            etf_info = catalog_service.get_etf_by_isin(item.etf_isin)
            watchlist_data.append({
                'id': item.id,
                'etf_isin': item.etf_isin,
                'etf_symbol': item.etf_symbol,
                'etf_name': etf_info.name if etf_info else "Unknown",
                'sector': etf_info.sector if etf_info else "Unknown",
                'added_date': item.added_date.isoformat(),
                'notes': item.notes,
                'target_price': item.target_price,
                'stop_loss': item.stop_loss
            })
        
        return {
            'status': 'success',
            'count': len(watchlist_data),
            'data': watchlist_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération watchlist: {str(e)}")

@router.post(
    "/watchlist",
    tags=["watchlist"],
    summary="Ajouter un ETF à la watchlist"
)
async def add_to_watchlist(
    etf_isin: str,
    etf_symbol: str,
    notes: Optional[str] = None,
    target_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Ajoute un ETF à la watchlist de l'utilisateur"""
    try:
        # Vérifier si l'ETF existe dans le catalogue
        catalog_service = get_etf_catalog_service()
        etf_info = catalog_service.get_etf_by_isin(etf_isin)
        
        if not etf_info:
            raise HTTPException(status_code=404, detail="ETF non trouvé dans le catalogue")
        
        # Vérifier si l'ETF n'est pas déjà dans la watchlist
        existing = db.query(UserWatchlist).filter(
            UserWatchlist.user_id == current_user.id,
            UserWatchlist.etf_isin == etf_isin,
            UserWatchlist.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="ETF déjà dans la watchlist")
        
        # Créer l'entrée watchlist
        watchlist_item = UserWatchlist(
            user_id=current_user.id,
            etf_isin=etf_isin,
            etf_symbol=etf_symbol,
            notes=notes,
            target_price=target_price,
            stop_loss=stop_loss
        )
        
        db.add(watchlist_item)
        db.commit()
        db.refresh(watchlist_item)
        
        return {
            'status': 'success',
            'message': f'ETF {etf_symbol} ajouté à la watchlist',
            'data': {
                'id': watchlist_item.id,
                'etf_isin': watchlist_item.etf_isin,
                'etf_symbol': watchlist_item.etf_symbol,
                'added_date': watchlist_item.added_date.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur ajout watchlist: {str(e)}")

@router.delete(
    "/watchlist/{watchlist_id}",
    tags=["watchlist"],
    summary="Supprimer un ETF de la watchlist"
)
async def remove_from_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Supprime un ETF de la watchlist de l'utilisateur"""
    try:
        watchlist_item = db.query(UserWatchlist).filter(
            UserWatchlist.id == watchlist_id,
            UserWatchlist.user_id == current_user.id
        ).first()
        
        if not watchlist_item:
            raise HTTPException(status_code=404, detail="Élément de watchlist non trouvé")
        
        # Marquer comme inactif plutôt que supprimer
        watchlist_item.is_active = False
        db.commit()
        
        return {
            'status': 'success',
            'message': 'ETF retiré de la watchlist'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur suppression watchlist: {str(e)}")

@router.put(
    "/watchlist/{watchlist_id}",
    tags=["watchlist"],
    summary="Mettre à jour un élément de la watchlist"
)
async def update_watchlist_item(
    watchlist_id: int,
    notes: Optional[str] = None,
    target_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Met à jour un élément de la watchlist"""
    try:
        watchlist_item = db.query(UserWatchlist).filter(
            UserWatchlist.id == watchlist_id,
            UserWatchlist.user_id == current_user.id
        ).first()
        
        if not watchlist_item:
            raise HTTPException(status_code=404, detail="Élément de watchlist non trouvé")
        
        # Mettre à jour les champs fournis
        if notes is not None:
            watchlist_item.notes = notes
        if target_price is not None:
            watchlist_item.target_price = target_price
        if stop_loss is not None:
            watchlist_item.stop_loss = stop_loss
        
        db.commit()
        db.refresh(watchlist_item)
        
        return {
            'status': 'success',
            'message': 'Watchlist mise à jour',
            'data': {
                'id': watchlist_item.id,
                'notes': watchlist_item.notes,
                'target_price': watchlist_item.target_price,
                'stop_loss': watchlist_item.stop_loss
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur mise à jour watchlist: {str(e)}")

@router.post(
    "/signal-subscription",
    tags=["signals"],
    summary="S'abonner aux signaux d'un ETF"
)
async def subscribe_to_etf_signals(
    etf_isin: str,
    etf_symbol: str,
    min_confidence: float = 60.0,
    max_risk_score: float = 70.0,
    signal_types: List[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """S'abonne aux signaux de trading pour un ETF"""
    try:
        # Vérifier si l'ETF existe
        catalog_service = get_etf_catalog_service()
        etf_info = catalog_service.get_etf_by_isin(etf_isin)
        
        if not etf_info:
            raise HTTPException(status_code=404, detail="ETF non trouvé")
        
        # Vérifier si l'abonnement existe déjà
        existing = db.query(UserSignalSubscription).filter(
            UserSignalSubscription.user_id == current_user.id,
            UserSignalSubscription.etf_isin == etf_isin
        ).first()
        
        if existing:
            # Mettre à jour l'abonnement existant
            existing.min_confidence = min_confidence
            existing.max_risk_score = max_risk_score
            existing.signal_types = signal_types or ['BUY', 'SELL']
            existing.is_active = True
            subscription = existing
        else:
            # Créer nouvel abonnement
            subscription = UserSignalSubscription(
                user_id=current_user.id,
                etf_isin=etf_isin,
                etf_symbol=etf_symbol,
                min_confidence=min_confidence,
                max_risk_score=max_risk_score,
                signal_types=signal_types or ['BUY', 'SELL']
            )
            db.add(subscription)
        
        db.commit()
        db.refresh(subscription)
        
        return {
            'status': 'success',
            'message': f'Abonnement aux signaux {etf_symbol} configuré',
            'data': {
                'etf_isin': subscription.etf_isin,
                'etf_symbol': subscription.etf_symbol,
                'min_confidence': subscription.min_confidence,
                'max_risk_score': subscription.max_risk_score,
                'signal_types': subscription.signal_types
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur abonnement signaux: {str(e)}")

@router.get(
    "/recommendations",
    tags=["etf-selection"],
    summary="Recommandations d'ETFs personnalisées"
)
async def get_personalized_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Nombre de recommandations")
):
    """Récupère des recommandations d'ETFs personnalisées basées sur les préférences utilisateur"""
    try:
        # Récupérer les préférences utilisateur
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        catalog_service = get_etf_catalog_service()
        
        # Filtrer selon les préférences
        filters = {}
        if preferences:
            if preferences.preferred_sectors:
                filters['sectors'] = preferences.preferred_sectors
            if preferences.preferred_regions:
                filters['regions'] = preferences.preferred_regions
            if preferences.max_ter:
                filters['max_ter'] = preferences.max_ter
            if preferences.min_aum:
                filters['min_aum'] = preferences.min_aum
        
        # Récupérer les ETFs filtrés
        if filters:
            recommended_etfs = catalog_service.filter_etfs(**filters)
        else:
            recommended_etfs = catalog_service.get_popular_etfs(limit * 2)
        
        # Trier par AUM et limiter
        recommended_etfs.sort(key=lambda x: x.aum, reverse=True)
        recommended_etfs = recommended_etfs[:limit]
        
        etf_data = []
        for etf in recommended_etfs:
            etf_data.append({
                'isin': etf.isin,
                'symbol': etf.symbol,
                'name': etf.name,
                'sector': etf.sector,
                'region': etf.region,
                'ter': etf.ter,
                'aum': etf.aum,
                'description': etf.description,
                'recommendation_reason': 'Based on your preferences'
            })
        
        return {
            'status': 'success',
            'count': len(etf_data),
            'data': etf_data,
            'filters_applied': filters
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recommandations: {str(e)}")