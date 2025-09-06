"""Health check and monitoring system."""

import asyncio
import logging
import time
import psutil
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class HealthChecker:
    """Comprehensive health checking system."""

    def __init__(self):
        self.checks: Dict[str, callable] = {
            "database": self._check_database,
            "disk_space": self._check_disk_space,
            "memory": self._check_memory,
            "cpu": self._check_cpu,
            "file_system": self._check_file_system,
            "model_files": self._check_model_files,
            "async_tasks": self._check_async_tasks
        }

    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks."""
        results = {}

        for check_name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = await check_func()
                result.response_time = time.time() - start_time
                results[check_name] = result
            except Exception as e:
                logger.error(
                    f"Health check '{check_name}' failed: {e}", exc_info=True)
                results[check_name] = HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(e)}",
                    response_time=time.time() - start_time if 'start_time' in locals() else None
                )

        return results

    async def run_check(self, check_name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check."""
        if check_name not in self.checks:
            return None

        try:
            start_time = time.time()
            result = await self.checks[check_name]()
            result.response_time = time.time() - start_time
            return result
        except Exception as e:
            logger.error(
                f"Health check '{check_name}' failed: {e}", exc_info=True)
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                response_time=time.time() - start_time if 'start_time' in locals() else None
            )

    async def _check_database(self) -> HealthCheckResult:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()

            # Test basic connectivity
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            connection_time = time.time() - start_time

            # Test a more complex query
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM students"))
                student_count = result.scalar()

            total_time = time.time() - start_time

            # Determine status based on response time
            if total_time < 0.1:
                status = HealthStatus.HEALTHY
                message = "Database is responding quickly"
            elif total_time < 0.5:
                status = HealthStatus.DEGRADED
                message = "Database is responding slowly"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Database is responding very slowly"

            return HealthCheckResult(
                name="database",
                status=status,
                message=message,
                details={
                    "connection_time": connection_time,
                    "query_time": total_time,
                    "student_count": student_count,
                    "database_url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "hidden"
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}"
            )

    async def _check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        try:
            # Check disk space for uploads directory
            upload_path = settings.UPLOAD_DIR
            if not os.path.exists(upload_path):
                os.makedirs(upload_path, exist_ok=True)

            disk_usage = psutil.disk_usage(upload_path)
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            used_percent = (disk_usage.used / disk_usage.total) * 100

            # Determine status based on available space
            if free_gb > 5.0 and used_percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Sufficient disk space available: {free_gb:.1f}GB free"
            elif free_gb > 1.0 and used_percent < 90:
                status = HealthStatus.DEGRADED
                message = f"Low disk space: {free_gb:.1f}GB free ({used_percent:.1f}% used)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical disk space: {free_gb:.1f}GB free ({used_percent:.1f}% used)"

            return HealthCheckResult(
                name="disk_space",
                status=status,
                message=message,
                details={
                    "free_gb": free_gb,
                    "total_gb": total_gb,
                    "used_percent": used_percent,
                    "path": upload_path
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk space check failed: {str(e)}"
            )

    async def _check_memory(self) -> HealthCheckResult:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            total_gb = memory.total / (1024**3)
            used_percent = memory.percent

            # Determine status based on memory usage
            if used_percent < 70:
                status = HealthStatus.HEALTHY
                message = f"Memory usage is normal: {used_percent:.1f}% used"
            elif used_percent < 85:
                status = HealthStatus.DEGRADED
                message = f"High memory usage: {used_percent:.1f}% used"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical memory usage: {used_percent:.1f}% used"

            return HealthCheckResult(
                name="memory",
                status=status,
                message=message,
                details={
                    "available_gb": available_gb,
                    "total_gb": total_gb,
                    "used_percent": used_percent
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}"
            )

    async def _check_cpu(self) -> HealthCheckResult:
        """Check CPU usage."""
        try:
            # Get CPU usage over a short interval
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

            # Determine status based on CPU usage
            if cpu_percent < 70:
                status = HealthStatus.HEALTHY
                message = f"CPU usage is normal: {cpu_percent:.1f}%"
            elif cpu_percent < 85:
                status = HealthStatus.DEGRADED
                message = f"High CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical CPU usage: {cpu_percent:.1f}%"

            return HealthCheckResult(
                name="cpu",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "load_avg_1min": load_avg[0],
                    "load_avg_5min": load_avg[1],
                    "load_avg_15min": load_avg[2]
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name="cpu",
                status=HealthStatus.UNHEALTHY,
                message=f"CPU check failed: {str(e)}"
            )

    async def _check_file_system(self) -> HealthCheckResult:
        """Check file system access and permissions."""
        try:
            # Check upload directory
            upload_dir = settings.UPLOAD_DIR

            # Test directory creation and file operations
            test_dir = os.path.join(upload_dir, "health_check")
            test_file = os.path.join(test_dir, "test.txt")

            # Create test directory
            os.makedirs(test_dir, exist_ok=True)

            # Write test file
            with open(test_file, 'w') as f:
                f.write("health check test")

            # Read test file
            with open(test_file, 'r') as f:
                content = f.read()

            # Clean up
            os.remove(test_file)
            os.rmdir(test_dir)

            if content == "health check test":
                return HealthCheckResult(
                    name="file_system",
                    status=HealthStatus.HEALTHY,
                    message="File system operations are working correctly",
                    details={"upload_dir": upload_dir}
                )
            else:
                return HealthCheckResult(
                    name="file_system",
                    status=HealthStatus.UNHEALTHY,
                    message="File system read/write test failed"
                )

        except Exception as e:
            return HealthCheckResult(
                name="file_system",
                status=HealthStatus.UNHEALTHY,
                message=f"File system check failed: {str(e)}"
            )

    async def _check_model_files(self) -> HealthCheckResult:
        """Check ML model files availability."""
        try:
            model_path = settings.MODEL_PATH
            food_mapping_path = settings.FOOD_MAPPING_PATH

            issues = []

            # Check model file
            if not os.path.exists(model_path):
                issues.append(f"Model file not found: {model_path}")
            else:
                model_size = os.path.getsize(model_path) / (1024**2)  # MB
                if model_size < 1:  # Less than 1MB seems too small
                    issues.append(
                        f"Model file seems too small: {model_size:.1f}MB")

            # Check food mapping file
            if not os.path.exists(food_mapping_path):
                issues.append(
                    f"Food mapping file not found: {food_mapping_path}")

            if not issues:
                return HealthCheckResult(
                    name="model_files",
                    status=HealthStatus.HEALTHY,
                    message="All model files are available",
                    details={
                        "model_path": model_path,
                        "food_mapping_path": food_mapping_path,
                        "model_size_mb": os.path.getsize(model_path) / (1024**2) if os.path.exists(model_path) else 0
                    }
                )
            else:
                return HealthCheckResult(
                    name="model_files",
                    status=HealthStatus.DEGRADED,
                    message=f"Model file issues: {'; '.join(issues)}",
                    details={"issues": issues}
                )

        except Exception as e:
            return HealthCheckResult(
                name="model_files",
                status=HealthStatus.UNHEALTHY,
                message=f"Model files check failed: {str(e)}"
            )

    async def _check_async_tasks(self) -> HealthCheckResult:
        """Check async task processor status."""
        try:
            from app.core.async_tasks import get_task_processor

            processor = await get_task_processor()
            stats = await processor.get_queue_stats()

            # Determine status based on queue size and active tasks
            queue_size = stats["queue_size"]
            active_tasks = stats["active_tasks"]

            if queue_size < 10 and active_tasks < processor.max_workers:
                status = HealthStatus.HEALTHY
                message = "Async task processor is running normally"
            elif queue_size < 50:
                status = HealthStatus.DEGRADED
                message = f"Async task queue is getting full: {queue_size} tasks queued"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Async task queue is overloaded: {queue_size} tasks queued"

            return HealthCheckResult(
                name="async_tasks",
                status=status,
                message=message,
                details=stats
            )

        except Exception as e:
            return HealthCheckResult(
                name="async_tasks",
                status=HealthStatus.UNHEALTHY,
                message=f"Async tasks check failed: {str(e)}"
            )

    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Determine overall system health status."""
        if not results:
            return HealthStatus.UNHEALTHY

        statuses = [result.status for result in results.values()]

        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED


# Global health checker instance
_health_checker = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
