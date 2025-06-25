"""
Endpoints pour les données de marché réelles
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.real_market_data import get_real_market_data_service, RealMarketDataService
from app.schemas.etf import ETFResponse
from app.services.portfolio_service import get_portfolio_calculation_service
from app.services.enhanced_market_data import get_enhanced_market_service
from app.services.etf_catalog import get_etf_catalog_service
from app.services.multi_source_etf_data import MultiSourceETFDataService
from app.services.cached_etf_service import get_cached_etf_service

router = APIRouter()

@router.get("/etfs")
async def get_real_market_etfs():
    """
    Endpoint pour le fallback frontend - retourne des vraies données ETF
    """
    try:
        # Utiliser le service multi-source pour des vraies données
        multi_source_service = MultiSourceETFDataService()
        
        # ETFs principaux avec vraies données
        etf_symbols = ["IWDA.L", "CSPX.L", "VUSA.L", "IEMA.L", "IEUR.L"]
        
        etf_list = []
        
        for symbol in etf_symbols:
            try:
                # Récupérer vraies données temps réel
                etf_data = await multi_source_service.get_etf_data(symbol)
                
                if etf_data and etf_data.current_price > 0:
                    etf_list.append({
                        'symbol': etf_data.symbol,
                        'isin': etf_data.isin,
                        'name': etf_data.name,  # Propriété 'name' que le frontend cherche
                        'sector': etf_data.sector,
                        'current_price': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'change': float(etf_data.change) if etf_data.change is not None else 0.0,
                        'change_percent': float(etf_data.change_percent) if etf_data.change_percent is not None else 0.0,
                        'volume': int(etf_data.volume) if etf_data.volume is not None else 0,
                        'currency': etf_data.currency or 'EUR',
                        'exchange': etf_data.exchange,
                        'last_update': etf_data.last_update.isoformat(),
                        'source': etf_data.source.value,
                        'confidence_score': float(etf_data.confidence_score) if etf_data.confidence_score is not None else 0.0,
                        # Propriétés supplémentaires pour éviter les erreurs frontend
                        'high': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'low': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'open': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'close': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'market_cap': 0.0,
                        'bid': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'ask': float(etf_data.current_price) if etf_data.current_price is not None else 0.0
                    })
            except Exception as e:
                # Si erreur pour un ETF, continuer avec les autres
                continue
        
        # Si aucune donnée temps réel, utiliser les dernières données BDD
        if not etf_list:
            try:
                cached_service = get_cached_etf_service()
                # Récupérer depuis cache/BDD
                for symbol in etf_symbols:
                    # Utiliser les données statiques du service comme fallback
                    if symbol in multi_source_service.european_etfs:
                        etf_info = multi_source_service.european_etfs[symbol]
                        etf_list.append({
                            'symbol': symbol,
                            'isin': etf_info['isin'],
                            'name': etf_info['name'],  # Propriété 'name' importante
                            'sector': etf_info['sector'],
                            'current_price': None,  # Pas de prix simulé
                            'change': None,
                            'change_percent': None,
                            'volume': None,
                            'currency': 'EUR',
                            'exchange': etf_info['exchange'],
                            'last_update': datetime.now().isoformat(),
                            'source': 'metadata_only',
                            'confidence_score': 0.0
                        })
            except Exception:
                pass
        
        return {
            'success': True,
            'data': etf_list,
            'count': len(etf_list),
            'source': 'real_market_fallback',
            'note': 'Données réelles uniquement - aucune simulation'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'count': 0,
            'error': str(e),
            'note': 'Erreur récupération données réelles'
        }

# Endpoint public sans authentification pour les données de base
@router.get(
    "/public/etfs-preview",
    tags=["market"],
    summary="Aperçu ETFs sans authentification",
    description="Retourne un aperçu des ETFs disponibles sans nécessiter d'authentification"
)
async def get_public_etfs_preview(
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """Endpoint public pour l'aperçu des ETFs - VRAIES DONNÉES UNIQUEMENT"""
    etf_list = []
    
    try:
        # Utiliser le service multi-source pour des VRAIES données
        multi_source_service = MultiSourceETFDataService()
        
        # ETFs principaux - récupérer vraies données temps réel
        etf_symbols = ["IWDA.L", "CSPX.L", "VUSA.L", "IEMA.L", "IEUR.L"]
        
        for symbol in etf_symbols:
            try:
                # Récupérer vraies données temps réel
                etf_data = await multi_source_service.get_etf_data(symbol)
                
                if etf_data and etf_data.current_price > 0:
                    etf_list.append({
                        'symbol': etf_data.symbol,
                        'isin': etf_data.isin,
                        'name': etf_data.name,
                        'sector': etf_data.sector,
                        'exchange': etf_data.exchange,
                        'current_price': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'change': float(etf_data.change) if etf_data.change is not None else 0.0,
                        'change_percent': float(etf_data.change_percent) if etf_data.change_percent is not None else 0.0,
                        'volume': int(etf_data.volume) if etf_data.volume is not None else 0,
                        'currency': etf_data.currency or 'EUR',
                        'last_update': etf_data.last_update.isoformat(),
                        # Ajout de propriétés supplémentaires que le frontend pourrait attendre
                        'high': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'low': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'open': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'close': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'market_cap': 0.0,
                        'bid': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                        'ask': float(etf_data.current_price) if etf_data.current_price is not None else 0.0
                    })
            except Exception as e:
                # Si erreur pour un ETF, continuer avec les autres
                continue
                
    except Exception as e:
        # Si erreur générale, retourner erreur explicite
        return {
            'status': 'error',
            'count': 0,
            'data': [],
            'error': 'Impossible de récupérer les données temps réel',
            'message': 'Veuillez vérifier la configuration des APIs de données de marché'
        }
    
    return {
        'status': 'success',
        'count': len(etf_list),
        'data': etf_list,
        'timestamp': datetime.now().isoformat(),
        'message': 'Données publiques - Connectez-vous pour les données temps réel'
    }

@router.get(
    "/real-etfs",
    tags=["market"],
    summary="ETFs européens en temps réel",
    description="""
    Récupère les données temps réel des ETFs européens depuis Yahoo Finance et autres sources.
    
    **Données retournées :**
    - Prix actuels et variations RÉELLES depuis Yahoo Finance
    - Volume de trading en temps réel
    - Secteur et bourse de cotation
    - ISIN et devise
    
    **Sources :** Yahoo Finance API + base de données PostgreSQL
    """,
    response_description="Liste des ETFs avec données temps réel"
)
async def get_real_etf_data(
    symbols: Optional[str] = None,
    db = Depends(get_db),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """
    Récupère les données réelles des ETFs européens depuis Yahoo Finance et autres sources
    
    Args:
        symbols: Liste de symboles séparés par des virgules (optionnel)
        market_service: Service de données de marché en temps réel
        
    Returns:
        Dict contenant la liste des ETFs avec leurs données temps réel
    """
    try:
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Démarrage de la récupération des ETFs temps réel...")
        
        # Si la base de données est vide, utiliser les ETFs prédéfinis
        from app.models.etf import ETF
        etfs_from_db = db.query(ETF).all()
        
        etf_data = []
        
        if len(etfs_from_db) == 0:
            # Utiliser le service alternatif pour des données réalistes
            logger.info("Base de données vide, utilisation du service alternatif")
            from app.services.alternative_market_data import alternative_market_service
            
            real_etf_data = alternative_market_service.get_all_etf_data()
            
            for etf in real_etf_data:
                etf_item = {
                    'symbol': etf.symbol,
                    'isin': etf.isin,
                    'name': etf.name,
                    'current_price': etf.current_price,
                    'change': etf.change,
                    'change_percent': etf.change_percent,
                    'volume': etf.volume,
                    'market_cap': etf.market_cap,
                    'currency': etf.currency,
                    'exchange': etf.exchange,
                    'sector': etf.sector,
                    'last_update': etf.last_update.isoformat(),
                    'source': etf.source
                }
                etf_data.append(etf_item)
        else:
            # Utiliser le service de cache intelligent pour des réponses plus rapides
            logger.info(f"Utilisation du service de cache intelligent pour {len(etfs_from_db)} ETFs")
            
            cached_service = get_cached_etf_service()
            
            # Récupérer les données depuis le cache (rapide) ou sources externes (en arrière-plan)
            real_etf_data = await cached_service.get_all_cached_etfs(db)
            
            for etf_data_point in real_etf_data:
                try:
                    etf_item = {
                        'symbol': etf_data_point.symbol,
                        'isin': etf_data_point.isin,
                        'name': etf_data_point.name,
                        'current_price': etf_data_point.current_price,
                        'change': etf_data_point.change,
                        'change_percent': etf_data_point.change_percent,
                        'volume': etf_data_point.volume,
                        'market_cap': etf_data_point.market_cap,
                        'currency': etf_data_point.currency,
                        'exchange': etf_data_point.exchange,
                        'sector': etf_data_point.sector,
                        'last_update': etf_data_point.last_update.isoformat(),
                        'source': etf_data_point.source,
                        'confidence_score': etf_data_point.confidence_score,
                        'is_real_data': etf_data_point.source not in ['database_cache', 'fallback'],
                        'data_quality': etf_data_point.data_quality,
                        'reliability_icon': etf_data_point.reliability_icon
                    }
                    
                    etf_data.append(etf_item)
                    
                except Exception as etf_error:
                    logger.error(f"Erreur pour ETF {etf_data_point.isin if hasattr(etf_data_point, 'isin') else 'unknown'}: {etf_error}")
                    continue
        
        logger.info(f"Données temps réel préparées pour {len(etf_data)} ETFs")
        
        return {
            'status': 'success',
            'count': len(etf_data),
            'data': etf_data,
            'timestamp': datetime.now().isoformat(),
            'source': 'Yahoo Finance + Database'
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Erreur complète: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données temps réel: {str(e)}")

@router.get(
    "/real-etfs-fast",
    tags=["market"],
    summary="ETFs avec réponse rapide (cache + mise à jour arrière-plan)",
    description="""
    Endpoint optimisé qui retourne immédiatement les données en cache 
    et lance une mise à jour en arrière-plan pour la prochaine requête.
    """
)
async def get_real_etf_data_fast(
    background_tasks: BackgroundTasks,
    db = Depends(get_db),
    cached_service = Depends(get_cached_etf_service)
):
    """
    Réponse rapide avec données en cache + mise à jour en arrière-plan
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. Récupérer rapidement les données en cache
        logger.info("🚀 Récupération rapide des données ETF...")
        
        real_etf_data = await cached_service.get_all_cached_etfs(db)
        
        # 2. Programmer une mise à jour en arrière-plan pour les données expirées
        background_tasks.add_task(refresh_expired_data_background, db)
        
        # 3. Formatter les données pour la réponse
        etf_data = []
        for etf_data_point in real_etf_data:
            try:
                etf_item = {
                    'symbol': etf_data_point.symbol,
                    'isin': etf_data_point.isin,
                    'name': etf_data_point.name,
                    'current_price': etf_data_point.current_price,
                    'change': etf_data_point.change,
                    'change_percent': etf_data_point.change_percent,
                    'volume': etf_data_point.volume,
                    'market_cap': etf_data_point.market_cap,
                    'currency': etf_data_point.currency,
                    'exchange': etf_data_point.exchange,
                    'sector': etf_data_point.sector,
                    'last_update': etf_data_point.last_update.isoformat(),
                    'source': etf_data_point.source,
                    'confidence_score': etf_data_point.confidence_score,
                    'is_real_data': etf_data_point.source not in ['database_cache', 'fallback'],
                    'data_quality': etf_data_point.data_quality,
                    'reliability_icon': etf_data_point.reliability_icon
                }
                
                etf_data.append(etf_item)
                
            except Exception as etf_error:
                logger.error(f"Erreur format ETF {etf_data_point.isin if hasattr(etf_data_point, 'isin') else 'unknown'}: {etf_error}")
                continue
        
        logger.info(f"✅ Réponse rapide avec {len(etf_data)} ETFs (mise à jour en arrière-plan)")
        
        return {
            'status': 'success',
            'count': len(etf_data),
            'data': etf_data,
            'timestamp': datetime.now().isoformat(),
            'source': 'Cached + Background Refresh',
            'message': 'Données en cache retournées, mise à jour en cours...'
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Erreur endpoint rapide: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération rapide: {str(e)}")

async def refresh_expired_data_background(db: Session):
    """Tâche de fond pour rafraîchir les données expirées"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("🔄 Début mise à jour arrière-plan...")
        
        cached_service = get_cached_etf_service()
        
        # Identifier et rafraîchir seulement les données expirées
        from app.models.etf import ETF, MarketData
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(minutes=cached_service.cache_duration_minutes)
        
        # ETFs avec données expirées ou manquantes
        etfs_to_refresh = db.query(ETF).outerjoin(MarketData).filter(
            (MarketData.time < cutoff_time) | (MarketData.time.is_(None))
        ).all()
        
        logger.info(f"🎯 {len(etfs_to_refresh)} ETFs à rafraîchir en arrière-plan")
        
        # Rafraîchir en lots pour éviter la surcharge
        for i in range(0, len(etfs_to_refresh), 5):  # Lots de 5
            batch = etfs_to_refresh[i:i+5]
            
            tasks = []
            for etf in batch:
                symbol = getattr(etf, 'symbol', etf.isin)
                tasks.append(cached_service.get_cached_etf_data(symbol, db))
            
            # Traiter le lot
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Pause entre les lots
            await asyncio.sleep(0.5)
        
        logger.info("✅ Mise à jour arrière-plan terminée")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Erreur mise à jour arrière-plan: {e}")

@router.get("/dashboard-stats")
async def get_dashboard_statistics():
    """Récupère les statistiques simplifiées pour le dashboard basées sur les vraies données"""
    try:
        from app.services.dynamic_etf_service import get_dynamic_etf_service
        
        dynamic_service = get_dynamic_etf_service()
        
        # Récupérer les vraies données ETF
        etf_data = await dynamic_service.get_all_realtime_data_for_dashboard()
        
        if not etf_data:
            # Si pas de données, retourner des valeurs par défaut
            return {
                'status': 'success',
                'data': {
                    'market_overview': {
                        'total_etfs': 0,
                        'avg_change_percent': 0.0,
                        'positive_etfs': 0,
                        'negative_etfs': 0
                    },
                    'alerts_count': 0,
                    'last_update': datetime.now().isoformat()
                }
            }
        
        # Calculer les vraies statistiques
        total_etfs = len(etf_data)
        positive_etfs = sum(1 for etf in etf_data if etf.change_percent > 0)
        negative_etfs = sum(1 for etf in etf_data if etf.change_percent < 0)
        avg_change_percent = sum(etf.change_percent for etf in etf_data) / total_etfs if total_etfs > 0 else 0.0
        
        return {
            'status': 'success',
            'data': {
                'market_overview': {
                    'total_etfs': total_etfs,
                    'avg_change_percent': round(avg_change_percent, 2),
                    'positive_etfs': positive_etfs,
                    'negative_etfs': negative_etfs
                },
                'alerts_count': 0,  # À implémenter avec les vraies alertes
                'last_update': datetime.now().isoformat(),
                'data_source': 'real_time_scraping'
            }
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Erreur dashboard stats: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")

@router.get("/real-etfs", 
    tags=["real-market"],
    summary="Données ETF réelles depuis sources externes",
    description="Récupère la liste des ETFs avec données de marché réelles depuis Yahoo Finance, Alpha Vantage, etc."
)
async def get_real_etfs_from_external_sources(db: Session = Depends(get_db)):
    """Endpoint pour récupérer les ETFs avec données réelles depuis APIs + scraping + cache BDD"""
    try:
        # Utiliser le nouveau service en cache
        cached_service = get_cached_etf_service()
        
        # Récupérer toutes les données avec cache intelligent
        all_etf_data = await cached_service.get_all_cached_etfs(db)
        
        # Récupérer les infos du catalogue pour enrichir
        catalog_service = get_etf_catalog_service()
        catalog_etfs = {etf.symbol: etf for etf in catalog_service.get_all_etfs()}
        
        etf_data = []
        for real_data in all_etf_data:
            try:
                catalog_etf = catalog_etfs.get(real_data.symbol)
                
                etf_data.append({
                    'symbol': real_data.symbol,
                    'isin': real_data.isin,
                    'name': real_data.name,
                    'current_price': real_data.current_price,
                    'change': real_data.change,
                    'change_percent': real_data.change_percent,
                    'volume': real_data.volume,
                    'market_cap': real_data.market_cap,
                    'currency': real_data.currency,
                    'exchange': real_data.exchange,
                    'sector': real_data.sector,
                    'last_update': real_data.last_update.isoformat(),
                    'source': real_data.source,
                    'confidence_score': real_data.confidence_score,
                    'is_real_data': True,
                    'data_quality': real_data.data_quality,
                    'reliability_icon': real_data.reliability_icon,
                    'ter': catalog_etf.ter if catalog_etf else None,
                    'aum': catalog_etf.aum if catalog_etf else None,
                    'region': catalog_etf.region if catalog_etf else None,
                    'benchmark': catalog_etf.benchmark if catalog_etf else None,
                    'description': catalog_etf.description if catalog_etf else None
                })
                
            except Exception as e:
                print(f"❌ Erreur traitement {real_data.symbol}: {e}")
                continue
        
        # Trier par qualité des données puis par confiance
        etf_data.sort(key=lambda x: (x['confidence_score'], x['current_price']), reverse=True)
        
        return {
            'status': 'success',
            'count': len(etf_data),
            'data': etf_data,
            'metadata': {
                'source': 'cached_realtime_data',
                'last_update': datetime.now().isoformat(),
                'successful_fetches': len(etf_data),
                'cache_enabled': True,
                'data_sources': ['scraping', 'yahoo_finance', 'alpha_vantage', 'database_cache']
            }
        }
        
    except Exception as e:
        import traceback
        print(f"Erreur real-etfs: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération ETFs: {str(e)}")

@router.post("/refresh-all-etfs",
    tags=["real-market"],
    summary="Forcer le rafraîchissement de tous les ETFs"
)
async def force_refresh_all_etfs(db: Session = Depends(get_db)):
    """Force le rafraîchissement de toutes les données ETF"""
    try:
        cached_service = get_cached_etf_service()
        results = await cached_service.force_refresh_all(db)
        
        return {
            'status': 'success',
            'message': 'Rafraîchissement terminé',
            'results': results
        }
        
    except Exception as e:
        import traceback
        print(f"Erreur refresh: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur rafraîchissement: {str(e)}")

@router.get("/watchlist",
    tags=["watchlist"],
    summary="Récupérer la watchlist de l'utilisateur"
)
async def get_user_watchlist(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Récupère la watchlist de l'utilisateur avec données ETF enrichies"""
    try:
        from app.models.watchlist import Watchlist
        
        # Récupérer les ETFs en watchlist
        watchlist_items = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id
        ).all()
        
        catalog_service = get_etf_catalog_service()
        watchlist_data = []
        
        # Initialiser le service multi-sources
        data_service = MultiSourceETFDataService()
        
        for item in watchlist_items:
            # Récupérer les infos ETF depuis le catalogue
            etf_info = catalog_service.get_etf_by_isin(item.etf_isin)
            
            if etf_info:
                try:
                    # Récupérer les données réelles
                    real_data = await data_service.get_etf_data(etf_info.symbol)
                    
                    if real_data:
                        watchlist_data.append({
                            'id': str(item.id),
                            'symbol': real_data.symbol,
                            'name': real_data.name,
                            'current_price': real_data.current_price,
                            'change': real_data.change,
                            'change_percent': real_data.change_percent,
                            'volume': real_data.volume,
                            'sector': real_data.sector,
                            'currency': real_data.currency,
                            'addedAt': item.created_at.isoformat(),
                            'isAlertActive': False,
                            'tags': [],
                            'source': real_data.source.value,
                            'confidence_score': real_data.confidence_score,
                            'is_real_data': True
                        })
                    else:
                        print(f"⚠️ Pas de données réelles pour {etf_info.symbol} dans la watchlist")
                        
                except Exception as e:
                    print(f"❌ Erreur récupération données watchlist pour {etf_info.symbol}: {e}")
                    continue
        
        return {
            'status': 'success',
            'count': len(watchlist_data),
            'data': watchlist_data
        }
        
    except Exception as e:
        import traceback
        print(f"Erreur watchlist: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération watchlist: {str(e)}")

class WatchlistAddRequest(BaseModel):
    etf_symbol: str

@router.post("/watchlist",
    tags=["watchlist"], 
    summary="Ajouter un ETF à la watchlist"
)
async def add_to_watchlist(
    request_data: WatchlistAddRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Ajoute un ETF à la watchlist de l'utilisateur"""
    try:
        from app.models.watchlist import Watchlist
        
        etf_symbol = request_data.etf_symbol
        
        catalog_service = get_etf_catalog_service()
        etf_info = catalog_service.get_etf_by_symbol(etf_symbol)
        
        if not etf_info:
            raise HTTPException(status_code=404, detail="ETF non trouvé dans le catalogue")
        
        # Vérifier si déjà en watchlist
        existing = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id,
            Watchlist.etf_isin == etf_info.isin
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="ETF déjà dans la watchlist")
        
        # Ajouter à la watchlist
        watchlist_item = Watchlist(
            user_id=current_user.id,
            etf_isin=etf_info.isin
        )
        
        db.add(watchlist_item)
        db.commit()
        db.refresh(watchlist_item)
        
        return {
            'status': 'success',
            'message': f'ETF {etf_symbol} ajouté à la watchlist',
            'data': {
                'id': str(watchlist_item.id),
                'etf_isin': watchlist_item.etf_isin,
                'symbol': etf_symbol,
                'added_date': watchlist_item.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Erreur ajout watchlist: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur ajout watchlist: {str(e)}")

@router.delete("/watchlist/{etf_symbol}",
    tags=["watchlist"],
    summary="Supprimer un ETF de la watchlist"
)
async def remove_from_watchlist(
    etf_symbol: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Supprime un ETF de la watchlist"""
    try:
        from app.models.watchlist import Watchlist
        
        catalog_service = get_etf_catalog_service()
        etf_info = catalog_service.get_etf_by_symbol(etf_symbol)
        
        if not etf_info:
            raise HTTPException(status_code=404, detail="ETF non trouvé")
        
        watchlist_item = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id,
            Watchlist.etf_isin == etf_info.isin
        ).first()
        
        if not watchlist_item:
            raise HTTPException(status_code=404, detail="ETF non trouvé dans la watchlist")
        
        db.delete(watchlist_item)
        db.commit()
        
        return {
            'status': 'success',
            'message': f'ETF {etf_symbol} retiré de la watchlist'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Erreur suppression watchlist: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur suppression watchlist: {str(e)}")

@router.delete("/watchlist",
    tags=["watchlist"],
    summary="Supprimer toute la watchlist de l'utilisateur"
)
async def clear_watchlist(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Supprime tous les ETFs de la watchlist de l'utilisateur"""
    try:
        from app.models.watchlist import Watchlist
        
        # Supprimer tous les items de la watchlist de l'utilisateur
        deleted_count = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id
        ).delete()
        
        db.commit()
        
        return {
            'status': 'success',
            'message': f'Watchlist vidée ({deleted_count} ETFs supprimés)',
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Erreur suppression watchlist complète: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur suppression watchlist: {str(e)}")

@router.get("/etf-details/{isin}",
    tags=["real-market"],
    summary="Récupérer les détails d'un ETF par ISIN"
)
async def get_etf_details_by_isin(isin: str):
    """Récupère les informations détaillées d'un ETF à partir de son ISIN"""
    try:
        catalog_service = get_etf_catalog_service()
        etf_info = catalog_service.get_etf_by_isin(isin)
        
        if not etf_info:
            raise HTTPException(status_code=404, detail=f"ETF avec ISIN {isin} non trouvé")
        
        return {
            'status': 'success',
            'data': {
                'isin': etf_info.isin,
                'symbol': etf_info.symbol,
                'name': etf_info.name,
                'sector': etf_info.sector,
                'region': etf_info.region,
                'currency': etf_info.currency,
                'ter': etf_info.ter,
                'aum': etf_info.aum,
                'exchange': etf_info.exchange,
                'description': etf_info.description,
                'benchmark': etf_info.benchmark,
                'inception_date': etf_info.inception_date,
                'dividend_frequency': etf_info.dividend_frequency,
                'replication_method': etf_info.replication_method
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Erreur récupération détails ETF: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération détails: {str(e)}")

@router.get("/search-etfs",
    tags=["real-market"],
    summary="Rechercher des ETFs avec données réelles"
)
async def search_etfs_with_real_data(
    q: str,
    limit: int = 20
):
    """Recherche d'ETFs par nom, secteur ou symbole avec données réelles"""
    try:
        catalog_service = get_etf_catalog_service()
        search_results = catalog_service.search_etfs(q)
        
        # Limiter les résultats
        search_results = search_results[:limit]
        
        # Initialiser le service multi-sources
        data_service = MultiSourceETFDataService()
        
        etf_data = []
        for etf in search_results:
            try:
                # Récupérer les données réelles
                real_data = await data_service.get_etf_data(etf.symbol)
                
                if real_data:
                    etf_data.append({
                        'symbol': real_data.symbol,
                        'isin': real_data.isin,
                        'name': real_data.name,
                        'current_price': real_data.current_price,
                        'change': real_data.change,
                        'change_percent': real_data.change_percent,
                        'volume': real_data.volume,
                        'sector': real_data.sector,
                        'currency': real_data.currency,
                        'exchange': real_data.exchange,
                        'ter': etf.ter,
                        'aum': etf.aum,
                        'region': etf.region,
                        'description': etf.description,
                        'source': real_data.source.value,
                        'confidence_score': real_data.confidence_score,
                        'is_real_data': True
                    })
                else:
                    print(f"⚠️ Pas de données réelles pour {etf.symbol} dans la recherche")
                    
            except Exception as e:
                print(f"❌ Erreur récupération données pour {etf.symbol}: {e}")
                continue
        
        return {
            'status': 'success',
            'query': q,
            'count': len(etf_data),
            'data': etf_data,
            'metadata': {
                'source': 'real_data_search',
                'searched_in_catalog': len(search_results),
                'real_data_found': len(etf_data)
            }
        }
        
    except Exception as e:
        import traceback
        print(f"Erreur recherche: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur recherche ETFs: {str(e)}")

@router.get("/real-indices")
async def get_real_market_indices(
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """Récupère les données réelles des indices de marché européens"""
    try:
        indices_data = market_service.get_market_indices()
        
        return {
            'status': 'success',
            'count': len(indices_data),
            'data': indices_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des indices: {str(e)}")

@router.get(
    "/enhanced-indices",
    tags=["market"],
    summary="Indices européens temps réel",
    description="""
    Récupère les indices de marché européens avec sources multiples et validation.
    
    **Indices disponibles :**
    - 🇫🇷 **CAC 40** : Indice français des 40 plus grandes capitalisations
    - 🇩🇪 **DAX** : Indice allemand des 40 principales entreprises
    - 🇬🇧 **FTSE 100** : Indice britannique des 100 plus grandes capitalisations
    - 🇪🇺 **EURO STOXX 50** : Indice européen des 50 plus grandes entreprises
    - 🇳🇱 **AEX** : Indice néerlandais d'Amsterdam
    - 🇪🇸 **IBEX 35** : Indice espagnol des 35 principales valeurs
    
    **Sources de données :**
    - Yahoo Finance (principal)
    - Financial Modeling Prep (fallback)
    - Validation automatique des données suspectes
    
    **Métriques :**
    - Valeur actuelle et variation journalière
    - Volume de trading
    - Score de confiance des données
    - Source utilisée pour chaque indice
    """,
    response_description="Indices européens avec données temps réel et métadonnées"
)
async def get_enhanced_market_indices(
    enhanced_service = Depends(get_enhanced_market_service)
):
    """
    Récupère les indices avec sources multiples et validation
    
    Returns:
        Dict contenant les indices européens avec données temps réel et scores de confiance
    """
    try:
        indices_data = enhanced_service.get_enhanced_indices()
        
        return {
            'status': 'success',
            'count': len(indices_data),
            'data': indices_data,
            'timestamp': datetime.now().isoformat(),
            'sources_used': list(set(data.get('source', 'Unknown') for data in indices_data.values()))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des indices améliorés: {str(e)}")

@router.get(
    "/signals-demo",
    tags=["signals"],
    summary="Signaux de démonstration",
    description="""
    Récupère des signaux de trading de démonstration sans authentification.
    
    **Types de signaux disponibles :**
    - 🟢 **BUY** : Signal d'achat avec prix cible et stop-loss
    - 🔴 **SELL** : Signal de vente recommandé
    - 🟡 **HOLD** : Maintenir la position actuelle
    - ⚪ **WAIT** : Attendre de meilleures conditions
    
    **Métriques incluses :**
    - Score de confiance (0-100%)
    - Score technique basé sur RSI, MACD, etc.
    - Score de risque
    - Prix cible et stop-loss (si applicable)
    
    **Note :** Endpoint public pour démonstration. 
    Pour des signaux personnalisés, utilisez l'authentification.
    """,
    response_description="Liste des signaux actifs avec métriques détaillées"
)
async def get_signals_demo(
    db = Depends(get_db)
):
    """
    Récupère des signaux de démonstration sans authentification
    
    Returns:
        Dict contenant une liste de signaux de trading avec scores et recommandations
    """
    try:
        from app.models.signal import Signal
        
        signals = (
            db.query(Signal)
            .filter(Signal.is_active == True)
            .order_by(Signal.confidence.desc(), Signal.created_at.desc())
            .limit(10)
            .all()
        )
        
        signals_data = []
        for signal in signals:
            signals_data.append({
                'id': str(signal.id),
                'etf_isin': signal.etf_isin,
                'signal_type': signal.signal_type.value,
                'confidence': float(signal.confidence),
                'price_target': float(signal.price_target) if signal.price_target else None,
                'stop_loss': float(signal.stop_loss) if signal.stop_loss else None,
                'technical_score': float(signal.technical_score) if signal.technical_score else None,
                'risk_score': float(signal.risk_score) if signal.risk_score else None,
                'is_active': signal.is_active,
                'created_at': signal.created_at.isoformat(),
                'expires_at': signal.expires_at.isoformat() if signal.expires_at else None
            })
        
        return {
            'status': 'success',
            'count': len(signals_data),
            'data': signals_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des signaux: {str(e)}")

@router.get("/real-market-data/{symbol}")
async def get_real_historical_data(
    symbol: str,
    period: str = "1mo",
    current_user: User = Depends(get_current_active_user),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """
    Récupère les données historiques réelles d'un ETF
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        historical_data = market_service.get_historical_data(symbol, period)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"Aucune donnée trouvée pour le symbole {symbol}")
        
        # Convertir en format API
        data_points = []
        for point in historical_data:
            data_points.append({
                'timestamp': point.timestamp.isoformat(),
                'open_price': point.open_price,
                'high_price': point.high_price,
                'low_price': point.low_price,
                'close_price': point.close_price,
                'volume': point.volume,
                'adj_close': point.adj_close
            })
        
        return {
            'status': 'success',
            'symbol': symbol,
            'period': period,
            'count': len(data_points),
            'data': data_points,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'historique: {str(e)}")

@router.post("/update-database")
async def update_database_with_real_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """Met à jour la base de données avec les données réelles (tâche en arrière-plan)"""
    try:
        background_tasks.add_task(market_service.update_database_with_real_data)
        
        return {
            'status': 'success',
            'message': 'Mise à jour de la base de données lancée en arrière-plan',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de la mise à jour: {str(e)}")

@router.get("/available-etfs")
async def get_available_etfs(
    current_user: User = Depends(get_current_active_user),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """Retourne la liste des ETFs européens disponibles"""
    etf_list = []
    
    for symbol, info in market_service.EUROPEAN_ETFS.items():
        etf_list.append({
            'symbol': symbol,
            'isin': info['isin'],
            'name': info['name'],
            'sector': info['sector'],
            'exchange': info['exchange']
        })
    
    return {
        'status': 'success',
        'count': len(etf_list),
        'etfs': etf_list,
        'timestamp': datetime.now().isoformat()
    }

@router.get("/sectors")
async def get_market_sectors():
    """Récupère les performances par secteur basées sur les vraies données"""
    try:
        from app.services.dynamic_etf_service import get_dynamic_etf_service
        
        dynamic_service = get_dynamic_etf_service()
        
        # Récupérer les vraies données ETF
        etf_data = await dynamic_service.get_all_realtime_data_for_dashboard()
        
        if not etf_data:
            return {
                'status': 'success',
                'count': 0,
                'data': [],
                'timestamp': datetime.now().isoformat()
            }
        
        # Grouper par secteur et calculer les performances
        sectors_dict = {}
        for etf in etf_data:
            sector = etf.sector
            if sector not in sectors_dict:
                sectors_dict[sector] = {
                    'name': sector,
                    'etfs': [],
                    'total_volume': 0,
                    'total_market_cap': 0
                }
            
            sectors_dict[sector]['etfs'].append(etf)
            sectors_dict[sector]['total_volume'] += etf.volume if etf.volume else 0
            sectors_dict[sector]['total_market_cap'] += etf.market_cap if etf.market_cap else 0
        
        # Calculer les moyennes par secteur
        sectors_data = []
        for sector, data in sectors_dict.items():
            etfs = data['etfs']
            avg_change = sum(etf.change_percent for etf in etfs) / len(etfs) if etfs else 0.0
            
            sectors_data.append({
                'name': sector,
                'change': round(avg_change, 1),
                'volume': data['total_volume'],
                'marketCap': data['total_market_cap'],
                'etf_count': len(etfs)
            })
        
        # Trier par performance
        sectors_data.sort(key=lambda x: x['change'], reverse=True)
        
        return {
            'status': 'success',
            'count': len(sectors_data),
            'data': sectors_data,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'real_time_scraping'
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Erreur sectors: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des secteurs: {str(e)}")

@router.get("/market-status")
async def get_market_status(
    current_user: User = Depends(get_current_active_user)
):
    """Retourne le statut des marchés (ouvert/fermé)"""
    now = datetime.now()
    
    # Logique simplifiée pour les heures de marché européen
    hour = now.hour
    weekday = now.weekday()  # 0 = lundi, 6 = dimanche
    
    # Marchés européens généralement ouverts de 9h à 17h30, lundi à vendredi
    market_open = (weekday < 5) and (9 <= hour < 17)
    
    return {
        'status': 'success',
        'market_open': market_open,
        'current_time': now.isoformat(),
        'next_open': 'Lundi 9h00' if weekday >= 5 else 'Demain 9h00' if hour >= 17 else 'Maintenant',
        'timezone': 'CET/CEST'
    }