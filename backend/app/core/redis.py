import redis.asyncio as redis
import json
from typing import Any, Optional
from app.core.config import settings

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


class RedisCache:
    """Redis cache manager"""
    
    def __init__(self):
        self.client = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        try:
            json_value = json.dumps(value, default=str)
            if ttl:
                await self.client.setex(key, ttl, json_value)
            else:
                await self.client.set(key, json_value)
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.client.delete(key)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(await self.client.exists(key))
        except Exception:
            return False
    
    async def set_hash(self, name: str, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set hash in cache"""
        try:
            await self.client.hset(name, mapping=mapping)
            if ttl:
                await self.client.expire(name, ttl)
            return True
        except Exception:
            return False
    
    async def get_hash(self, name: str, key: str) -> Optional[str]:
        """Get hash field from cache"""
        try:
            return await self.client.hget(name, key)
        except Exception:
            return None
    
    async def get_all_hash(self, name: str) -> Optional[dict]:
        """Get all hash fields from cache"""
        try:
            return await self.client.hgetall(name)
        except Exception:
            return None


# Global cache instance
cache = RedisCache()