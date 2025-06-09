"""
Endpoints pour le monitoring et les diagnostics
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime

from app.core.cache import CacheManager
from app.services.real_market_data import get_real_market_data_service, RealMarketDataService

router = APIRouter()

@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Retourne les statistiques du cache"""
    stats = CacheManager.get_cache_stats()
    stats['timestamp'] = datetime.now().isoformat()
    return {
        'status': 'success',
        'data': stats
    }

@router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """Vide tout le cache"""
    from app.core.cache import cache
    cache.clear()
    
    return {
        'status': 'success',
        'message': 'Cache vidé avec succès',
        'timestamp': datetime.now().isoformat()
    }

@router.delete("/cache/market-data/{symbol}")
async def invalidate_market_data(symbol: str) -> Dict[str, Any]:
    """Invalide le cache pour un ETF spécifique"""
    CacheManager.invalidate_market_data(symbol)
    
    return {
        'status': 'success',
        'message': f'Cache invalidé pour {symbol}',
        'timestamp': datetime.now().isoformat()
    }

@router.get("/health")
async def health_check(
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
) -> Dict[str, Any]:
    """Vérification de santé de l'application"""
    try:
        # Test avec un ETF populaire
        test_data = market_service.get_single_etf_data('IWDA.AS')
        api_status = 'healthy' if test_data else 'degraded'
    except Exception as e:
        api_status = 'error'
        
    cache_stats = CacheManager.get_cache_stats()
    
    return {
        'status': 'success',
        'data': {
            'api_status': api_status,
            'cache_status': 'healthy',
            'cache_entries': cache_stats['total_entries'],
            'memory_usage_mb': cache_stats.get('memory_usage_mb', 0),
            'timestamp': datetime.now().isoformat(),
            'uptime_check': 'ok'
        }
    }

@router.get("/performance/test")
async def performance_test(
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
) -> Dict[str, Any]:
    """Test de performance des APIs"""
    import time
    
    symbols_to_test = ['IWDA.AS', 'VWCE.DE', 'CSPX.L']
    results = []
    
    for symbol in symbols_to_test:
        start_time = time.time()
        try:
            data = market_service.get_single_etf_data(symbol)
            end_time = time.time()
            
            results.append({
                'symbol': symbol,
                'response_time_ms': round((end_time - start_time) * 1000, 2),
                'status': 'success' if data else 'no_data',
                'cached': False  # Premier appel
            })
            
            # Test avec cache
            start_time = time.time()
            data = market_service.get_single_etf_data(symbol)
            end_time = time.time()
            
            results.append({
                'symbol': symbol,
                'response_time_ms': round((end_time - start_time) * 1000, 2),
                'status': 'success' if data else 'no_data',
                'cached': True  # Deuxième appel (cache)
            })
            
        except Exception as e:
            results.append({
                'symbol': symbol,
                'response_time_ms': 0,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'status': 'success',
        'data': {
            'test_results': results,
            'timestamp': datetime.now().isoformat()
        }
    }