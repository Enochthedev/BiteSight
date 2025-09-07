"""Redis client configuration and utilities."""

import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

import redis
from redis.exceptions import ConnectionError, TimeoutError

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisClient:
    """Redis client wrapper with connection management and utilities."""

    def __init__(self):
        """Initialize Redis client."""
        self._client: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None

    def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            self._client = redis.Redis(connection_pool=self._connection_pool)

            # Test connection
            self._client.ping()
            logger.info("Redis connection established successfully")

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None
            raise

    def disconnect(self) -> None:
        """Close Redis connection."""
        if self._connection_pool:
            self._connection_pool.disconnect()
            logger.info("Redis connection closed")

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self._client:
            self.connect()
        return self._client

    def is_connected(self) -> bool:
        """Check if Redis is connected and responsive."""
        try:
            if self._client:
                self._client.ping()
                return True
        except (ConnectionError, TimeoutError):
            pass
        return False

    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None,
        serialize: bool = True
    ) -> bool:
        """Set a key-value pair in Redis."""
        try:
            if serialize and not isinstance(value, (str, bytes, int, float)):
                value = json.dumps(value, default=str)

            result = self.client.set(key, value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set Redis key {key}: {e}")
            return False

    def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Get a value from Redis by key."""
        try:
            value = self.client.get(key)
            if value is None:
                return None

            if deserialize:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value.decode('utf-8') if isinstance(value, bytes) else value

            return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"Failed to get Redis key {key}: {e}")
            return None

    def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis."""
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete Redis keys {keys}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check Redis key existence {key}: {e}")
            return False

    def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """Set expiration time for a key."""
        try:
            return bool(self.client.expire(key, time))
        except Exception as e:
            logger.error(f"Failed to set expiration for Redis key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for Redis key {key}: {e}")
            return -1

    def flush_db(self) -> bool:
        """Flush current database (use with caution)."""
        try:
            return bool(self.client.flushdb())
        except Exception as e:
            logger.error(f"Failed to flush Redis database: {e}")
            return False

    def get_info(self) -> dict:
        """Get Redis server information."""
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}


# Global Redis client instance
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """Get Redis client instance."""
    return redis_client
