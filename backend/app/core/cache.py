"""
Cache middleware avec Redis pour optimiser les performances
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class InMemoryCache:
    """Cache en mémoire simple pour le développement"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        if key not in self._cache:
            return None
            
        item = self._cache[key]
        if datetime.now() > item['expires']:
            del self._cache[key]
            return None
            
        return item['data']
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Stocke une valeur dans le cache"""
        expires = datetime.now() + timedelta(seconds=ttl_seconds)
        self._cache[key] = {
            'data': value,
            'expires': expires,
            'created': datetime.now()
        }
    
    def delete(self, key: str) -> None:
        """Supprime une clé du cache"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Vide tout le cache"""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        now = datetime.now()
        valid_entries = 0
        expired_entries = 0
        
        for item in self._cache.values():
            if now > item['expires']:
                expired_entries += 1
            else:
                valid_entries += 1
                
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'memory_usage_mb': len(str(self._cache)) / 1024 / 1024
        }

# Instance globale
cache = InMemoryCache()

def generate_cache_key(*args, **kwargs) -> str:
    """Génère une clé de cache unique basée sur les arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def cache_response(ttl_seconds: int = 300, key_prefix: str = ""):
    """Décorateur pour mettre en cache les réponses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Générer une clé de cache
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Vérifier le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit pour {cache_key}")
                return cached_result
            
            # Exécuter la fonction
            result = await func(*args, **kwargs)
            
            # Mettre en cache le résultat
            cache.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cache mis à jour pour {cache_key}")
            
            return result
            
        return wrapper
    return decorator

class CacheManager:
    """Gestionnaire de cache pour différents types de données"""
    
    @staticmethod
    def get_market_data_key(symbol: str) -> str:
        return f"market_data:{symbol}"
    
    @staticmethod
    def get_etf_list_key() -> str:
        return "etf_list:all"
    
    @staticmethod
    def get_signals_key(filters: Optional[str] = None) -> str:
        if filters:
            return f"signals:{generate_cache_key(filters)}"
        return "signals:all"
    
    @staticmethod
    def invalidate_market_data(symbol: Optional[str] = None):
        """Invalide le cache des données de marché"""
        if symbol:
            cache.delete(CacheManager.get_market_data_key(symbol))
        else:
            # Invalider tout le cache marché
            keys_to_delete = [k for k in cache._cache.keys() if k.startswith("market_data:")]
            for key in keys_to_delete:
                cache.delete(key)
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Retourne les statistiques détaillées du cache"""
        stats = cache.get_stats()
        
        # Ajouter des statistiques par type
        type_stats = {}
        for key in cache._cache.keys():
            cache_type = key.split(':')[0] if ':' in key else 'unknown'
            type_stats[cache_type] = type_stats.get(cache_type, 0) + 1
        
        stats['entries_by_type'] = type_stats
        return stats