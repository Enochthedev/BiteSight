"""Caching service with different strategies for various data types."""

import hashlib
import logging
from datetime import timedelta
from typing import Any, Callable, Optional, Union
from functools import wraps

from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing different types of cache operations."""

    def __init__(self):
        """Initialize cache service."""
        self.redis_client = get_redis_client()

        # Cache TTL configurations
        self.ttl_config = {
            # Model results cache for 24 hours
            'model_inference': timedelta(hours=24),
            # User sessions cache for 8 hours
            'user_session': timedelta(hours=8),
            # API responses cache for 15 minutes
            'api_response': timedelta(minutes=15),
            # Food metadata cache for 12 hours
            'food_metadata': timedelta(hours=12),
            # Weekly insights cache for 6 hours
            'weekly_insights': timedelta(hours=6),
            # User history cache for 2 hours
            'user_history': timedelta(hours=2),
        }

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from arguments."""
        # Create a string representation of all arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)

        # Hash the key if it's too long
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"

        return f"{prefix}:{key_string}"

    def cache_model_inference(
        self,
        image_hash: str,
        model_version: str,
        results: dict
    ) -> bool:
        """Cache ML model inference results."""
        cache_key = self._generate_cache_key(
            "model_inference",
            image_hash,
            model_version
        )

        return self.redis_client.set(
            cache_key,
            results,
            expire=self.ttl_config['model_inference']
        )

    def get_cached_inference(
        self,
        image_hash: str,
        model_version: str
    ) -> Optional[dict]:
        """Retrieve cached ML model inference results."""
        cache_key = self._generate_cache_key(
            "model_inference",
            image_hash,
            model_version
        )

        return self.redis_client.get(cache_key)

    def cache_user_session(self, user_id: str, session_data: dict) -> bool:
        """Cache user session data."""
        cache_key = self._generate_cache_key("user_session", user_id)

        return self.redis_client.set(
            cache_key,
            session_data,
            expire=self.ttl_config['user_session']
        )

    def get_user_session(self, user_id: str) -> Optional[dict]:
        """Retrieve cached user session data."""
        cache_key = self._generate_cache_key("user_session", user_id)
        return self.redis_client.get(cache_key)

    def invalidate_user_session(self, user_id: str) -> bool:
        """Invalidate user session cache."""
        cache_key = self._generate_cache_key("user_session", user_id)
        return bool(self.redis_client.delete(cache_key))

    def cache_api_response(
        self,
        endpoint: str,
        params: dict,
        response_data: Any
    ) -> bool:
        """Cache API response data."""
        cache_key = self._generate_cache_key(
            "api_response", endpoint, **params)

        return self.redis_client.set(
            cache_key,
            response_data,
            expire=self.ttl_config['api_response']
        )

    def get_cached_api_response(
        self,
        endpoint: str,
        params: dict
    ) -> Optional[Any]:
        """Retrieve cached API response."""
        cache_key = self._generate_cache_key(
            "api_response", endpoint, **params)
        return self.redis_client.get(cache_key)

    def cache_food_metadata(self, food_id: str, metadata: dict) -> bool:
        """Cache food metadata."""
        cache_key = self._generate_cache_key("food_metadata", food_id)

        return self.redis_client.set(
            cache_key,
            metadata,
            expire=self.ttl_config['food_metadata']
        )

    def get_cached_food_metadata(self, food_id: str) -> Optional[dict]:
        """Retrieve cached food metadata."""
        cache_key = self._generate_cache_key("food_metadata", food_id)
        return self.redis_client.get(cache_key)

    def cache_weekly_insights(
        self,
        user_id: str,
        week_start: str,
        insights: dict
    ) -> bool:
        """Cache weekly insights data."""
        cache_key = self._generate_cache_key(
            "weekly_insights",
            user_id,
            week_start
        )

        return self.redis_client.set(
            cache_key,
            insights,
            expire=self.ttl_config['weekly_insights']
        )

    def get_cached_weekly_insights(
        self,
        user_id: str,
        week_start: str
    ) -> Optional[dict]:
        """Retrieve cached weekly insights."""
        cache_key = self._generate_cache_key(
            "weekly_insights",
            user_id,
            week_start
        )
        return self.redis_client.get(cache_key)

    def cache_user_history(
        self,
        user_id: str,
        date_range: str,
        history_data: list
    ) -> bool:
        """Cache user meal history."""
        cache_key = self._generate_cache_key(
            "user_history",
            user_id,
            date_range
        )

        return self.redis_client.set(
            cache_key,
            history_data,
            expire=self.ttl_config['user_history']
        )

    def get_cached_user_history(
        self,
        user_id: str,
        date_range: str
    ) -> Optional[list]:
        """Retrieve cached user meal history."""
        cache_key = self._generate_cache_key(
            "user_history",
            user_id,
            date_range
        )
        return self.redis_client.get(cache_key)

    def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a specific user."""
        patterns = [
            f"user_session:{user_id}",
            f"weekly_insights:{user_id}:*",
            f"user_history:{user_id}:*"
        ]

        deleted_count = 0
        for pattern in patterns:
            if "*" in pattern:
                # Use scan for pattern matching
                keys = []
                for key in self.redis_client.client.scan_iter(match=pattern):
                    keys.append(key.decode('utf-8'))
                if keys:
                    deleted_count += self.redis_client.delete(*keys)
            else:
                deleted_count += self.redis_client.delete(pattern)

        return deleted_count

    def get_cache_stats(self) -> dict:
        """Get cache statistics and performance metrics."""
        try:
            info = self.redis_client.get_info()

            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

    def cleanup_expired_keys(self) -> int:
        """Manually cleanup expired keys (Redis handles this automatically)."""
        # This is mainly for monitoring purposes
        try:
            info = self.redis_client.get_info()
            return info.get('expired_keys', 0)
        except Exception as e:
            logger.error(f"Failed to get expired keys count: {e}")
            return 0


def cache_result(
    cache_type: str,
    ttl: Optional[Union[int, timedelta]] = None,
    key_generator: Optional[Callable] = None
):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_service = CacheService()

            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = cache_service._generate_cache_key(
                    f"{cache_type}:{func.__name__}",
                    *args,
                    **kwargs
                )

            # Try to get from cache
            cached_result = cache_service.redis_client.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)

            # Cache the result
            cache_ttl = ttl or cache_service.ttl_config.get(
                cache_type, timedelta(minutes=15))
            cache_service.redis_client.set(cache_key, result, expire=cache_ttl)

            logger.debug(f"Cached result for key: {cache_key}")
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_service = CacheService()

            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = cache_service._generate_cache_key(
                    f"{cache_type}:{func.__name__}",
                    *args,
                    **kwargs
                )

            # Try to get from cache
            cached_result = cache_service.redis_client.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)

            # Cache the result
            cache_ttl = ttl or cache_service.ttl_config.get(
                cache_type, timedelta(minutes=15))
            cache_service.redis_client.set(cache_key, result, expire=cache_ttl)

            logger.debug(f"Cached result for key: {cache_key}")
            return result

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Global cache service instance
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """Get cache service instance."""
    return cache_service
