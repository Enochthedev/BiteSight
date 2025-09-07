"""Tests for caching functionality."""

import pytest
import time
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock

from app.core.redis_client import RedisClient
from app.core.cache_service import CacheService, cache_result
from app.core.cache_monitoring import CacheMonitor


class TestRedisClient:
    """Test Redis client functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection."""
        with patch('redis.Redis') as mock_redis:
            mock_instance = Mock()
            mock_redis.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def redis_client(self, mock_redis):
        """Create Redis client with mocked connection."""
        client = RedisClient()
        client._client = mock_redis
        return client

    def test_redis_client_initialization(self):
        """Test Redis client initialization."""
        client = RedisClient()
        assert client._client is None
        assert client._connection_pool is None

    def test_set_and_get_string(self, redis_client, mock_redis):
        """Test setting and getting string values."""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = b'test_value'

        # Test set
        result = redis_client.set('test_key', 'test_value')
        assert result is True
        mock_redis.set.assert_called_once_with(
            'test_key', 'test_value', ex=None)

        # Test get
        value = redis_client.get('test_key', deserialize=False)
        assert value == 'test_value'
        mock_redis.get.assert_called_once_with('test_key')

    def test_set_and_get_json(self, redis_client, mock_redis):
        """Test setting and getting JSON values."""
        test_data = {'key': 'value', 'number': 42}
        mock_redis.set.return_value = True
        mock_redis.get.return_value = b'{"key": "value", "number": 42}'

        # Test set with serialization
        result = redis_client.set('test_key', test_data)
        assert result is True

        # Test get with deserialization
        value = redis_client.get('test_key')
        assert value == test_data

    def test_set_with_expiration(self, redis_client, mock_redis):
        """Test setting values with expiration."""
        mock_redis.set.return_value = True

        redis_client.set('test_key', 'test_value', expire=timedelta(minutes=5))
        mock_redis.set.assert_called_once_with(
            'test_key', 'test_value', ex=timedelta(minutes=5))

    def test_delete_keys(self, redis_client, mock_redis):
        """Test deleting keys."""
        mock_redis.delete.return_value = 2

        result = redis_client.delete('key1', 'key2')
        assert result == 2
        mock_redis.delete.assert_called_once_with('key1', 'key2')

    def test_exists_key(self, redis_client, mock_redis):
        """Test checking key existence."""
        mock_redis.exists.return_value = 1

        result = redis_client.exists('test_key')
        assert result is True
        mock_redis.exists.assert_called_once_with('test_key')

    def test_connection_error_handling(self, redis_client, mock_redis):
        """Test handling of connection errors."""
        from redis.exceptions import ConnectionError

        mock_redis.get.side_effect = ConnectionError("Connection failed")

        result = redis_client.get('test_key')
        assert result is None

    def test_is_connected(self, redis_client, mock_redis):
        """Test connection status check."""
        mock_redis.ping.return_value = True

        result = redis_client.is_connected()
        assert result is True

        mock_redis.ping.side_effect = Exception("Connection failed")
        result = redis_client.is_connected()
        assert result is False


class TestCacheService:
    """Test cache service functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock_client = Mock()
        mock_client.set.return_value = True
        mock_client.get.return_value = None
        mock_client.delete.return_value = 1
        return mock_client

    @pytest.fixture
    def cache_service(self, mock_redis_client):
        """Create cache service with mocked Redis client."""
        with patch('app.core.cache_service.get_redis_client') as mock_get_client:
            mock_get_client.return_value = mock_redis_client
            service = CacheService()
            return service

    def test_cache_model_inference(self, cache_service, mock_redis_client):
        """Test caching model inference results."""
        image_hash = "abc123"
        model_version = "v1.0"
        results = {"class": "rice", "confidence": 0.95}

        result = cache_service.cache_model_inference(
            image_hash, model_version, results)
        assert result is True

        # Verify Redis was called with correct parameters
        mock_redis_client.set.assert_called_once()
        call_args = mock_redis_client.set.call_args
        assert "model_inference:abc123:v1.0" in call_args[0][0]

    def test_get_cached_inference(self, cache_service, mock_redis_client):
        """Test retrieving cached inference results."""
        image_hash = "abc123"
        model_version = "v1.0"
        expected_result = {"class": "rice", "confidence": 0.95}

        mock_redis_client.get.return_value = expected_result

        result = cache_service.get_cached_inference(image_hash, model_version)
        assert result == expected_result

    def test_cache_user_session(self, cache_service, mock_redis_client):
        """Test caching user session data."""
        user_id = "user123"
        session_data = {"logged_in": True, "preferences": {"theme": "dark"}}

        result = cache_service.cache_user_session(user_id, session_data)
        assert result is True

    def test_invalidate_user_cache(self, cache_service, mock_redis_client):
        """Test invalidating user cache."""
        user_id = "user123"

        # Mock scan_iter to return some keys
        mock_redis_client.client.scan_iter.return_value = [
            b'user_session:user123',
            b'weekly_insights:user123:2024-01',
            b'user_history:user123:recent'
        ]
        mock_redis_client.delete.return_value = 3

        deleted_count = cache_service.invalidate_user_cache(user_id)
        assert deleted_count >= 1  # At least one deletion call should be made

    def test_generate_cache_key(self, cache_service):
        """Test cache key generation."""
        key = cache_service._generate_cache_key(
            "test_prefix", "arg1", "arg2", param1="value1")
        assert key.startswith("test_prefix:")
        assert "arg1" in key
        assert "arg2" in key
        assert "param1:value1" in key

    def test_cache_key_hashing_for_long_keys(self, cache_service):
        """Test that long cache keys are hashed."""
        long_args = ["very_long_argument_" + str(i) for i in range(50)]
        key = cache_service._generate_cache_key("test_prefix", *long_args)

        # Should be hashed if too long
        assert len(key) < 250  # Should be shortened


class TestCacheDecorator:
    """Test cache decorator functionality."""

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        with patch('app.core.cache_service.CacheService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.redis_client.get.return_value = None
            mock_service.redis_client.set.return_value = True
            mock_service.ttl_config = {'test_cache': timedelta(minutes=15)}
            yield mock_service

    def test_cache_decorator_sync_function(self, mock_cache_service):
        """Test cache decorator with synchronous function."""
        @cache_result('test_cache')
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"

        # First call - should execute function
        result1 = test_function("a", "b")
        assert result1 == "result_a_b"

        # Verify cache was checked and set
        mock_cache_service.redis_client.get.assert_called()
        mock_cache_service.redis_client.set.assert_called()

    def test_cache_decorator_async_function(self, mock_cache_service):
        """Test cache decorator with asynchronous function."""
        @cache_result('test_cache')
        async def async_test_function(arg1, arg2):
            return f"async_result_{arg1}_{arg2}"

        # Test async function
        import asyncio
        result = asyncio.run(async_test_function("x", "y"))
        assert result == "async_result_x_y"

    def test_cache_decorator_hit(self, mock_cache_service):
        """Test cache decorator with cache hit."""
        cached_value = "cached_result"
        mock_cache_service.redis_client.get.return_value = cached_value

        @cache_result('test_cache')
        def test_function(arg1):
            return f"fresh_result_{arg1}"

        result = test_function("test")
        assert result == cached_value

        # Function should not be called due to cache hit
        mock_cache_service.redis_client.get.assert_called()


class TestCacheMonitor:
    """Test cache monitoring functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for monitoring."""
        mock_client = Mock()
        mock_client.get_info.return_value = {
            'keyspace_hits': 100,
            'keyspace_misses': 20,
            'used_memory_human': '1.5MB',
            'connected_clients': 5,
            'instantaneous_ops_per_sec': 50,
            'uptime_in_seconds': 3600
        }
        mock_client.is_connected.return_value = True
        return mock_client

    @pytest.fixture
    def cache_monitor(self, mock_redis_client):
        """Create cache monitor with mocked Redis client."""
        with patch('app.core.cache_monitoring.get_redis_client') as mock_get_client:
            mock_get_client.return_value = mock_redis_client
            monitor = CacheMonitor()
            return monitor

    def test_collect_metrics(self, cache_monitor, mock_redis_client):
        """Test collecting cache metrics."""
        metrics = cache_monitor.collect_metrics()

        assert metrics.hit_rate == 83.33  # 100/(100+20) * 100
        assert metrics.miss_rate == 16.67  # 20/(100+20) * 100
        assert metrics.total_requests == 120
        assert metrics.memory_usage == '1.5MB'
        assert metrics.connected_clients == 5
        assert metrics.operations_per_second == 50

    def test_cache_health_check_healthy(self, cache_monitor, mock_redis_client):
        """Test cache health check when healthy."""
        health = cache_monitor.check_cache_health()

        assert health['status'] == 'healthy'
        assert len(health['issues']) == 0
        assert len(health['recommendations']) == 0

    def test_cache_health_check_low_hit_rate(self, cache_monitor, mock_redis_client):
        """Test cache health check with low hit rate."""
        # Mock low hit rate
        mock_redis_client.get_info.return_value = {
            'keyspace_hits': 10,
            'keyspace_misses': 90,
            'used_memory_human': '1.5MB',
            'connected_clients': 5,
            'instantaneous_ops_per_sec': 50
        }

        health = cache_monitor.check_cache_health()

        assert health['status'] == 'degraded'
        assert any('Low cache hit rate' in issue for issue in health['issues'])
        assert len(health['recommendations']) > 0

    def test_cache_health_check_connection_failed(self, cache_monitor, mock_redis_client):
        """Test cache health check when connection fails."""
        mock_redis_client.is_connected.return_value = False

        health = cache_monitor.check_cache_health()

        assert health['status'] == 'unhealthy'
        assert any(
            'Redis connection failed' in issue for issue in health['issues'])


class TestCacheIntegration:
    """Integration tests for caching system."""

    @pytest.fixture
    def cache_service(self):
        """Create real cache service for integration tests."""
        # Note: These tests would require a real Redis instance
        # In a real test environment, you'd use a test Redis instance
        return CacheService()

    @pytest.mark.integration
    def test_end_to_end_caching_flow(self, cache_service):
        """Test complete caching flow."""
        # This test would require a real Redis instance
        # Skip if Redis is not available
        pytest.skip("Integration test requires Redis instance")

        # Test data
        image_hash = "test_hash_123"
        model_version = "test_model_v1"
        test_results = {
            "predictions": [
                {"class": "rice", "confidence": 0.95},
                {"class": "beans", "confidence": 0.85}
            ]
        }

        # Cache the results
        cache_success = cache_service.cache_model_inference(
            image_hash, model_version, test_results
        )
        assert cache_success

        # Retrieve the results
        cached_results = cache_service.get_cached_inference(
            image_hash, model_version
        )
        assert cached_results == test_results

        # Test cache expiration (would need to wait or mock time)
        # This is typically tested with time mocking in unit tests


@pytest.mark.asyncio
async def test_cache_performance():
    """Test cache performance characteristics."""
    # Mock performance test
    cache_service = CacheService()

    # Test multiple cache operations
    start_time = time.time()

    for i in range(100):
        cache_service._generate_cache_key(
            "perf_test", f"key_{i}", param=f"value_{i}")

    end_time = time.time()
    duration = end_time - start_time

    # Should be very fast
    assert duration < 1.0  # Less than 1 second for 100 key generations


def test_cache_error_handling():
    """Test cache error handling."""
    with patch('app.core.cache_service.get_redis_client') as mock_get_client:
        # Mock Redis client that raises exceptions
        mock_client = Mock()
        mock_client.set.side_effect = Exception("Redis error")
        mock_client.get.side_effect = Exception("Redis error")
        mock_get_client.return_value = mock_client

        cache_service = CacheService()

        # Should handle errors gracefully
        result = cache_service.cache_model_inference(
            "hash", "version", {"data": "test"})
        assert result is False

        cached_data = cache_service.get_cached_inference("hash", "version")
        assert cached_data is None
