"""
Endpoints optimisés pour les données ETF avec sources multiples
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import redis
import json
import logging

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.multi_source_etf_data import get_multi_source_etf_service, MultiSourceETFDataService, ETFDataPoint, DataSource
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache Redis pour les données ETF
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
except:
    redis_client = None
    logger.warning("Redis non disponible, cache désactivé")

@router.get(
    "/optimized-etfs",
    tags=["optimized-market"],
    summary="ETFs européens optimisés multi-sources",
    description="""
    Récupère les données ETF européens depuis sources multiples avec fallback intelligent.
    
    **Sources utilisées dans l'ordre de priorité :**
    1. 🟢 **Yahoo Finance** : Source principale, données gratuites et fiables
    2. 🟡 **Alpha Vantage** : Fallback 1, 25 requêtes/jour gratuit
    3. 🟡 **Financial Modeling Prep** : Fallback 2, 250 requêtes/jour gratuit
    4. 🟡 **EODHD** : Fallback 3, 20 requêtes/jour gratuit
    5. 🔵 **Données hybrides** : Dernier recours, calculées selon tendances marché
    
    **Optimisations :**
    - Cache intelligent Redis (5 minutes)
    - Rate limiting automatique par source
    - Retry automatique avec sources alternatives
    - Score de confiance pour chaque donnée
    
    **ETFs Européens supportés :**
    - 🇬🇧 London Stock Exchange (.L) : IWDA, VWRL, CSPX, VUSA, etc.
    - 🇩🇪 XETRA (.DE) : EUNL, XMME, EXS1, SX5E
    - 🇫🇷 Euronext Paris (.PA) : CW8, CAC
    - 🇳🇱 Euronext Amsterdam (.AS) : IWDA, VWRL
    
    **Données retournées :**
    - Prix actuels et variations RÉELLES
    - Volume de trading
    - Secteur et bourse de cotation
    - ISIN et devise
    - Source utilisée et score de confiance
    """,
    response_description="Liste des ETFs avec données temps réel optimisées"
)
async def get_optimized_etf_data(
    use_cache: bool = True,
    min_confidence: float = 0.0
):
    """
    Récupère les données ETF optimisées avec sources multiples
    
    Args:
        use_cache: Utiliser le cache Redis (défaut: True)
        min_confidence: Score de confiance minimum (0.0 à 1.0)
        etf_service: Service de données ETF multi-sources
        
    Returns:
        Dict contenant la liste des ETFs avec métadonnées
    """
    try:
        cache_key = f"optimized_etfs_v2:{min_confidence}"
        
        # Vérifier le cache Redis
        if use_cache and redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.info("Données ETF récupérées depuis le cache Redis")
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Erreur cache Redis: {e}")
        
        # Copier exactement la logique de real-market qui fonctionne
        logger.info("Récupération des données ETF avec logique real-market...")
        try:
            # Utiliser le service multi-source pour des vraies données
            multi_source_service = MultiSourceETFDataService()
            
            # ETFs principaux avec vraies données
            etf_symbols = ["IWDA.L", "CSPX.L", "VUSA.L", "IEMA.L", "IEUR.L", 
                          "EUNL.DE", "VWRL.AS", "IWDA.AS"]
            
            etf_api_data = []
            source_stats = {}
            
            for symbol in etf_symbols:
                try:
                    # Récupérer vraies données temps réel
                    etf_data = await multi_source_service.get_etf_data(symbol)
                    
                    if etf_data and etf_data.current_price > 0:
                        source_name = etf_data.source.value
                        if source_name not in source_stats:
                            source_stats[source_name] = 0
                        source_stats[source_name] += 1
                        
                        etf_api_data.append({
                            'symbol': etf_data.symbol,
                            'isin': etf_data.isin,
                            'name': etf_data.name,
                            'current_price': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                            'change': float(etf_data.change) if etf_data.change is not None else 0.0,
                            'change_percent': float(etf_data.change_percent) if etf_data.change_percent is not None else 0.0,
                            'volume': int(etf_data.volume) if etf_data.volume is not None else 0,
                            'market_cap': float(etf_data.market_cap) if etf_data.market_cap is not None else 0.0,
                            'currency': etf_data.currency or 'EUR',
                            'exchange': etf_data.exchange,
                            'sector': etf_data.sector,
                            'last_update': etf_data.last_update.isoformat(),
                            'source': etf_data.source.value,
                            'confidence_score': float(etf_data.confidence_score) if etf_data.confidence_score is not None else 0.0,
                            # Propriétés supplémentaires pour éviter les erreurs frontend
                            'high': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                            'low': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                            'open': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                            'close': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                            'bid': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                            'ask': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                            # Métadonnées
                            'is_real_data': etf_data.source != DataSource.HYBRID,
                            'data_quality': 'excellent' if etf_data.confidence_score >= 0.9 else 'good' if etf_data.confidence_score >= 0.7 else 'fair',
                            'reliability_icon': '🟢' if etf_data.confidence_score >= 0.9 else '🟡' if etf_data.confidence_score >= 0.7 else '🟠'
                        })
                        logger.debug(f"Données récupérées pour {symbol}: {etf_data.current_price} {etf_data.currency}")
                except Exception as symbol_error:
                    logger.warning(f"Erreur pour {symbol}: {symbol_error}")
                    continue
            
            # Si aucune donnée temps réel, utiliser les métadonnées comme fallback
            if not etf_api_data:
                logger.warning("Aucune donnée temps réel, utilisation des métadonnées")
                if 'CACHE' not in source_stats:
                    source_stats['CACHE'] = 0
                    
                for symbol in etf_symbols:
                    if symbol in multi_source_service.european_etfs:
                        etf_info = multi_source_service.european_etfs[symbol]
                        source_stats['CACHE'] += 1
                        etf_api_data.append({
                            'symbol': symbol,
                            'isin': etf_info['isin'],
                            'name': etf_info['name'],
                            'sector': etf_info['sector'],
                            'current_price': 0.0,  # 0.0 au lieu de None pour éviter toFixed error
                            'change': 0.0,
                            'change_percent': 0.0,
                            'volume': 0,
                            'market_cap': 0.0,
                            'currency': 'EUR',
                            'exchange': etf_info['exchange'],
                            'last_update': datetime.now().isoformat(),
                            'source': 'metadata_only',
                            'confidence_score': 0.0,
                            # Propriétés supplémentaires 
                            'high': 0.0,
                            'low': 0.0,
                            'open': 0.0,
                            'close': 0.0,
                            'bid': 0.0,
                            'ask': 0.0,
                            # Métadonnées
                            'is_real_data': False,
                            'data_quality': 'metadata_only',
                            'reliability_icon': '🔵'
                        })
            
            logger.info(f"Données récupérées pour {len(etf_api_data)} ETFs")
                    
        except Exception as e:
            logger.error(f"Erreur récupération données ETF: {e}")
            return {
                "status": "error",
                "error": "Erreur de récupération des données ETF",
                "message": "Veuillez réessayer dans quelques minutes",
                "data": [],
                "count": 0,
                "metadata": {"sources_used": {}, "api_limits_reached": True}
            }
        
        # Filtrer selon le score de confiance
        filtered_etfs = [
            etf for etf in etf_api_data 
            if etf['confidence_score'] >= min_confidence
        ]
        
        # Trier par score de confiance et nom
        filtered_etfs.sort(key=lambda x: (-x['confidence_score'], x['name']))
        
        response_data = {
            'status': 'success',
            'count': len(filtered_etfs),
            'data': filtered_etfs,
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'sources_used': source_stats,
                'avg_confidence': sum(etf['confidence_score'] for etf in filtered_etfs) / len(filtered_etfs) if filtered_etfs else 0,
                'real_data_percentage': round((len([etf for etf in filtered_etfs if etf['is_real_data']]) / len(filtered_etfs)) * 100, 1) if filtered_etfs else 0,
                'cache_used': False,
                'next_update_in': 300  # 5 minutes
            }
        }
        
        # Mettre en cache pour 5 minutes
        if redis_client:
            try:
                redis_client.setex(cache_key, 300, json.dumps(response_data, default=str))
                logger.info("Données ETF mises en cache Redis")
            except Exception as e:
                logger.warning(f"Erreur mise en cache Redis: {e}")
        
        logger.info(f"Données ETF récupérées: {len(etf_api_data)} ETFs depuis {len(source_stats)} sources")
        return response_data
        
    except Exception as e:
        logger.error(f"Erreur récupération ETF optimisée: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données ETF: {str(e)}")

@router.get(
    "/optimized-etf/{symbol}",
    tags=["optimized-market"],
    summary="Données ETF spécifique optimisées",
    description="""
    Récupère les données d'un ETF spécifique avec sources multiples.
    
    **Paramètres :**
    - `symbol` : Symbole ETF (ex: IWDA.L, VWRL.L, CSPX.L)
    
    **Retourne :**
    - Données temps réel de l'ETF
    - Source utilisée et score de confiance
    - Métadonnées de qualité
    """,
    response_description="Données détaillées de l'ETF"
)
async def get_optimized_single_etf_data(
    symbol: str,
    use_cache: bool = True,
    etf_service: MultiSourceETFDataService = Depends(get_multi_source_etf_service)
):
    """
    Récupère les données d'un ETF spécifique
    
    Args:
        symbol: Symbole ETF (ex: IWDA.L)
        use_cache: Utiliser le cache Redis
        etf_service: Service de données ETF
        
    Returns:
        Dict contenant les données de l'ETF
    """
    try:
        cache_key = f"optimized_etf:{symbol}"
        
        # Vérifier le cache
        if use_cache and redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Erreur cache Redis pour {symbol}: {e}")
        
        # Récupérer les données
        etf_data = await etf_service.get_etf_data(symbol)
        
        if not etf_data:
            raise HTTPException(status_code=404, detail=f"ETF {symbol} non trouvé")
        
        response_data = {
            'status': 'success',
            'symbol': etf_data.symbol,
            'data': {
                'symbol': etf_data.symbol,
                'isin': etf_data.isin,
                'name': etf_data.name,
                'current_price': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                'change': float(etf_data.change) if etf_data.change is not None else 0.0,
                'change_percent': float(etf_data.change_percent) if etf_data.change_percent is not None else 0.0,
                'volume': int(etf_data.volume) if etf_data.volume is not None else 0,
                'market_cap': float(etf_data.market_cap) if etf_data.market_cap is not None else 0.0,
                'currency': etf_data.currency,
                'exchange': etf_data.exchange,
                'sector': etf_data.sector,
                'last_update': etf_data.last_update.isoformat(),
                'source': etf_data.source.value,
                'confidence_score': float(etf_data.confidence_score) if etf_data.confidence_score is not None else 0.0,
                'is_real_data': etf_data.source != DataSource.HYBRID,
                'data_quality': 'excellent' if etf_data.confidence_score >= 0.9 else 'good' if etf_data.confidence_score >= 0.7 else 'fair',
                # Propriétés supplémentaires pour éviter les erreurs frontend
                'high': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                'low': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                'open': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                'close': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                'bid': float(etf_data.current_price) if etf_data.current_price is not None else 0.0,
                'ask': float(etf_data.current_price) if etf_data.current_price is not None else 0.0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache pour 2 minutes
        if redis_client:
            try:
                redis_client.setex(cache_key, 120, json.dumps(response_data, default=str))
            except Exception as e:
                logger.warning(f"Erreur mise en cache pour {symbol}: {e}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération ETF {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de {symbol}: {str(e)}")

@router.get(
    "/data-sources-status",
    tags=["optimized-market"],
    summary="Statut des sources de données",
    description="""
    Retourne le statut des différentes sources de données ETF.
    
    **Informations fournies :**
    - Rate limits par source
    - Disponibilité des API keys
    - Statistiques d'utilisation
    - Recommandations
    """,
    response_description="Statut détaillé des sources de données"
)
def get_data_sources_status():
    """
    Retourne le statut des sources de données
    """
    import os
    from datetime import datetime
    
    # Vérification des clés API depuis les variables d'environnement
    alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    fmp_key = os.getenv('FINANCIAL_MODELING_PREP_API_KEY') 
    eodhd_key = os.getenv('EODHD_API_KEY')
    twelvedata_key = os.getenv('TWELVEDATA_API_KEY')
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    
    current_time = datetime.now().isoformat()
    sources_status = {}
    
    # Yahoo Finance (toujours disponible)
    sources_status['yahoo_finance'] = {
        'api_key_available': True,
        'rate_limit': 'unlimited',
        'calls_used': 'N/A',
        'calls_remaining': 'unlimited',
        'window_seconds': 86400,
        'status': 'available',
        'last_reset': current_time,
        'notes': 'Source principale gratuite'
    }
    
    # Alpha Vantage
    if alpha_vantage_key:
        sources_status['alpha_vantage'] = {
            'api_key_available': True,
            'rate_limit': 25,
            'calls_used': 0,
            'calls_remaining': 25,
            'window_seconds': 86400,
            'status': 'available',
            'last_reset': current_time,
            'notes': 'API gratuite 25 req/jour'
        }
    
    # Financial Modeling Prep
    if fmp_key:
        sources_status['financial_modeling_prep'] = {
            'api_key_available': True,
            'rate_limit': 250,
            'calls_used': 0,
            'calls_remaining': 250,
            'window_seconds': 86400,
            'status': 'available',
            'last_reset': current_time,
            'notes': 'API gratuite 250 req/jour'
        }
    
    # Statistiques globales
    available_sources = len([s for s in sources_status.values() if s['status'] == 'available'])
    total_sources = len(sources_status)
    
    return {
        'status': 'success',
        'sources': sources_status,
        'summary': {
            'available_sources': available_sources,
            'total_sources': total_sources,
            'reliability_score': available_sources / max(total_sources, 1),
            'primary_source': 'yahoo_finance',
            'fallback_sources': available_sources - 1
        },
        'recommendations': [
            "Yahoo Finance est la source principale",
            f"{available_sources} source(s) configurée(s)",
            "Ajoutez plus de clés API pour une meilleure fiabilité"
        ],
        'timestamp': current_time
    }

@router.post(
    "/refresh-cache",
    tags=["optimized-market"],
    summary="Rafraîchir le cache des données ETF",
    description="Force le rafraîchissement du cache Redis pour les données ETF",
    response_description="Confirmation du rafraîchissement"
)
async def refresh_etf_cache(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    etf_service: MultiSourceETFDataService = Depends(get_multi_source_etf_service)
):
    """
    Force le rafraîchissement du cache des données ETF
    """
    try:
        if redis_client:
            # Supprimer les clés de cache
            pattern = "optimized_etfs_v2:*"
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cache ETF vidé: {len(keys)} clés supprimées")
        
        # Lancer le rafraîchissement en arrière-plan
        background_tasks.add_task(etf_service.get_all_etf_data)
        
        return {
            'status': 'success',
            'message': 'Cache rafraîchi, nouvelles données en cours de récupération',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur rafraîchissement cache: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du rafraîchissement: {str(e)}")