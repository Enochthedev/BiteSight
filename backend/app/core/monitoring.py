"""Monitoring and alerting system integration."""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from app.core.health_checks import get_health_checker, HealthStatus, HealthCheckResult
from app.core.metrics import metrics
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    severity: str  # critical, warning, info
    title: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertManager:
    """Manages system alerts and notifications."""

    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 1000

    def create_alert(self, alert_id: str, severity: str, title: str,
                     description: str, metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """Create a new alert."""
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Trim history if needed
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]

        logger.warning(f"Alert created: {title} - {description}")
        return alert

    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()

            del self.active_alerts[alert_id]

            logger.info(f"Alert resolved: {alert.title}")
            return alert

        return None

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the specified time period."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff]


class MonitoringService:
    """Main monitoring service that coordinates health checks and alerting."""

    def __init__(self):
        self.health_checker = get_health_checker()
        self.alert_manager = AlertManager()
        self.monitoring_enabled = True
        self.check_interval = 60  # seconds
        self.last_check_time = 0

        # Thresholds for alerting
        self.thresholds = {
            'cpu_critical': 90,
            'cpu_warning': 80,
            'memory_critical': 90,
            'memory_warning': 80,
            'disk_critical': 95,
            'disk_warning': 85,
            'response_time_critical': 5.0,
            'response_time_warning': 2.0,
            'error_rate_critical': 0.1,
            'error_rate_warning': 0.05
        }

    async def run_monitoring_cycle(self):
        """Run a complete monitoring cycle."""
        if not self.monitoring_enabled:
            return

        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return

        self.last_check_time = current_time

        try:
            # Run health checks
            health_results = await self.health_checker.run_all_checks()

            # Process health check results for alerting
            await self._process_health_results(health_results)

            # Check application metrics
            await self._check_application_metrics()

            logger.info("Monitoring cycle completed successfully")

        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}", exc_info=True)
            self.alert_manager.create_alert(
                "monitoring_failure",
                "critical",
                "Monitoring System Failure",
                f"Monitoring cycle failed: {str(e)}"
            )

    async def _process_health_results(self, results: Dict[str, HealthCheckResult]):
        """Process health check results and create alerts if needed."""
        for check_name, result in results.items():
            alert_id = f"health_{check_name}"

            if result.status == HealthStatus.UNHEALTHY:
                # Create or update critical alert
                if alert_id not in self.alert_manager.active_alerts:
                    self.alert_manager.create_alert(
                        alert_id,
                        "critical",
                        f"Health Check Failed: {check_name}",
                        result.message,
                        result.details
                    )

            elif result.status == HealthStatus.DEGRADED:
                # Create or update warning alert
                warning_id = f"{alert_id}_warning"
                if warning_id not in self.alert_manager.active_alerts:
                    self.alert_manager.create_alert(
                        warning_id,
                        "warning",
                        f"Health Check Degraded: {check_name}",
                        result.message,
                        result.details
                    )

            else:  # HEALTHY
                # Resolve any existing alerts for this check
                self.alert_manager.resolve_alert(alert_id)
                self.alert_manager.resolve_alert(f"{alert_id}_warning")

    async def _check_application_metrics(self):
        """Check application-specific metrics and create alerts."""
        # This would integrate with your metrics collection system
        # For now, we'll create placeholder checks

        # Check error rates (this would come from your metrics system)
        # error_rate = get_current_error_rate()
        # if error_rate > self.thresholds['error_rate_critical']:
        #     self.alert_manager.create_alert(
        #         "high_error_rate",
        #         "critical",
        #         "High Error Rate Detected",
        #         f"Error rate is {error_rate:.2%}"
        #     )

        pass

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status."""
        return {
            "enabled": self.monitoring_enabled,
            "last_check": datetime.fromtimestamp(self.last_check_time).isoformat() if self.last_check_time else None,
            "check_interval": self.check_interval,
            "active_alerts": len(self.alert_manager.active_alerts),
            "thresholds": self.thresholds
        }

    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview."""
        active_alerts = self.alert_manager.get_active_alerts()
        recent_alerts = self.alert_manager.get_alert_history(hours=24)

        # Categorize alerts by severity
        critical_alerts = [
            a for a in active_alerts if a.severity == "critical"]
        warning_alerts = [a for a in active_alerts if a.severity == "warning"]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "critical" if critical_alerts else "warning" if warning_alerts else "healthy",
            "alerts": {
                "active": {
                    "total": len(active_alerts),
                    "critical": len(critical_alerts),
                    "warning": len(warning_alerts)
                },
                "recent_24h": len(recent_alerts)
            },
            "monitoring": self.get_monitoring_status()
        }


class PerformanceMonitor:
    """Monitors application performance metrics."""

    def __init__(self):
        self.request_times = []
        self.max_samples = 1000

    def record_request_time(self, duration: float):
        """Record a request duration."""
        self.request_times.append(duration)
        if len(self.request_times) > self.max_samples:
            self.request_times = self.request_times[-self.max_samples:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.request_times:
            return {"message": "No performance data available"}

        times = sorted(self.request_times)
        count = len(times)

        return {
            "request_count": count,
            "avg_response_time": sum(times) / count,
            "min_response_time": min(times),
            "max_response_time": max(times),
            "p50_response_time": times[int(count * 0.5)],
            "p95_response_time": times[int(count * 0.95)],
            "p99_response_time": times[int(count * 0.99)]
        }


# Global monitoring instances
monitoring_service = MonitoringService()
performance_monitor = PerformanceMonitor()


async def start_monitoring():
    """Start the monitoring service."""
    logger.info("Starting monitoring service...")
    monitoring_service.monitoring_enabled = True

    # Start monitoring loop
    asyncio.create_task(monitoring_loop())


async def stop_monitoring():
    """Stop the monitoring service."""
    logger.info("Stopping monitoring service...")
    monitoring_service.monitoring_enabled = False


async def monitoring_loop():
    """Main monitoring loop."""
    while monitoring_service.monitoring_enabled:
        try:
            await monitoring_service.run_monitoring_cycle()
            await asyncio.sleep(monitoring_service.check_interval)
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}", exc_info=True)
            await asyncio.sleep(30)  # Wait before retrying


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    return monitoring_service


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor
