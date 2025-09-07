"""Cache monitoring and performance metrics utilities."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics data class."""
    timestamp: datetime
    hit_rate: float
    miss_rate: float
    total_requests: int
    memory_usage: str
    connected_clients: int
    operations_per_second: float
    average_response_time: float


class CacheMonitor:
    """Monitor cache performance and provide metrics."""

    def __init__(self):
        """Initialize cache monitor."""
        self.redis_client = get_redis_client()
        self.metrics_history: List[CacheMetrics] = []
        self.max_history_size = 1000

    def collect_metrics(self) -> CacheMetrics:
        """Collect current cache metrics."""
        try:
            start_time = time.time()
            info = self.redis_client.get_info()
            response_time = (time.time() - start_time) * \
                1000  # Convert to milliseconds

            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total_requests = hits + misses

            hit_rate = (hits / total_requests *
                        100) if total_requests > 0 else 0
            miss_rate = (misses / total_requests *
                         100) if total_requests > 0 else 0

            ops_per_second = info.get('instantaneous_ops_per_sec', 0)

            metrics = CacheMetrics(
                timestamp=datetime.utcnow(),
                hit_rate=round(hit_rate, 2),
                miss_rate=round(miss_rate, 2),
                total_requests=total_requests,
                memory_usage=info.get('used_memory_human', '0B'),
                connected_clients=info.get('connected_clients', 0),
                operations_per_second=ops_per_second,
                average_response_time=round(response_time, 2)
            )

            # Store metrics in history
            self._store_metrics(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect cache metrics: {e}")
            return CacheMetrics(
                timestamp=datetime.utcnow(),
                hit_rate=0.0,
                miss_rate=0.0,
                total_requests=0,
                memory_usage="0B",
                connected_clients=0,
                operations_per_second=0.0,
                average_response_time=0.0
            )

    def _store_metrics(self, metrics: CacheMetrics) -> None:
        """Store metrics in history with size limit."""
        self.metrics_history.append(metrics)

        # Keep only recent metrics
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]

    def check_cache_health(self) -> Dict:
        """Perform cache health check."""
        health_status = {
            'status': 'healthy',
            'issues': [],
            'recommendations': []
        }

        try:
            # Test basic connectivity
            if not self.redis_client.is_connected():
                health_status['status'] = 'unhealthy'
                health_status['issues'].append('Redis connection failed')
                return health_status

            # Collect current metrics
            metrics = self.collect_metrics()

            # Check hit rate
            if metrics.hit_rate < 50:
                health_status['issues'].append(
                    f'Low cache hit rate: {metrics.hit_rate}%')
                health_status['recommendations'].append(
                    'Consider adjusting cache TTL or improving cache key strategies')

            # Check response time
            if metrics.average_response_time > 100:  # 100ms threshold
                health_status['issues'].append(
                    f'High response time: {metrics.average_response_time}ms')
                health_status['recommendations'].append(
                    'Check Redis server performance and network latency')

            # Set overall status
            if health_status['issues']:
                health_status['status'] = 'degraded' if len(
                    health_status['issues']) <= 2 else 'unhealthy'

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health_status['status'] = 'unhealthy'
            health_status['issues'].append(f'Health check error: {str(e)}')

        return health_status


# Global cache monitor instance
cache_monitor = CacheMonitor()


def get_cache_monitor() -> CacheMonitor:
    """Get cache monitor instance."""
    return cache_monitor
