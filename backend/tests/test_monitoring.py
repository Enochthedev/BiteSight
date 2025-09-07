"""Tests for monitoring and alerting system."""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.core.monitoring import (
    MonitoringService, AlertManager, Alert, PerformanceMonitor,
    monitoring_service, performance_monitor
)
from app.core.health_checks import HealthCheckResult, HealthStatus
from app.core.metrics import metrics


class TestAlertManager:
    """Test alert management functionality."""

    def test_create_alert(self):
        """Test alert creation."""
        alert_manager = AlertManager()

        alert = alert_manager.create_alert(
            "test_alert",
            "warning",
            "Test Alert",
            "This is a test alert"
        )

        assert alert.id == "test_alert"
        assert alert.severity == "warning"
        assert alert.title == "Test Alert"
        assert alert.description == "This is a test alert"
        assert not alert.resolved
        assert "test_alert" in alert_manager.active_alerts

    def test_resolve_alert(self):
        """Test alert resolution."""
        alert_manager = AlertManager()

        # Create alert
        alert_manager.create_alert(
            "test_alert",
            "warning",
            "Test Alert",
            "This is a test alert"
        )

        # Resolve alert
        resolved_alert = alert_manager.resolve_alert("test_alert")

        assert resolved_alert is not None
        assert resolved_alert.resolved
        assert resolved_alert.resolved_at is not None
        assert "test_alert" not in alert_manager.active_alerts

    def test_get_active_alerts(self):
        """Test getting active alerts."""
        alert_manager = AlertManager()

        # Create multiple alerts
        alert_manager.create_alert(
            "alert1", "critical", "Alert 1", "Description 1")
        alert_manager.create_alert(
            "alert2", "warning", "Alert 2", "Description 2")

        active_alerts = alert_manager.get_active_alerts()

        assert len(active_alerts) == 2
        assert any(alert.id == "alert1" for alert in active_alerts)
        assert any(alert.id == "alert2" for alert in active_alerts)

    def test_get_alert_history(self):
        """Test getting alert history."""
        alert_manager = AlertManager()

        # Create and resolve an alert
        alert_manager.create_alert(
            "old_alert", "info", "Old Alert", "Old description")
        alert_manager.resolve_alert("old_alert")

        # Create a new alert
        alert_manager.create_alert(
            "new_alert", "warning", "New Alert", "New description")

        history = alert_manager.get_alert_history(hours=24)

        assert len(history) == 2
        assert any(alert.id == "old_alert" for alert in history)
        assert any(alert.id == "new_alert" for alert in history)


class TestMonitoringService:
    """Test monitoring service functionality."""

    @pytest.fixture
    def monitoring_service(self):
        """Create a monitoring service for testing."""
        return MonitoringService()

    @pytest.mark.asyncio
    async def test_process_health_results_unhealthy(self, monitoring_service):
        """Test processing unhealthy health check results."""
        # Mock unhealthy result
        results = {
            "database": HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message="Database connection failed"
            )
        }

        await monitoring_service._process_health_results(results)

        # Check that alert was created
        active_alerts = monitoring_service.alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].severity == "critical"
        assert "database" in active_alerts[0].title

    @pytest.mark.asyncio
    async def test_process_health_results_degraded(self, monitoring_service):
        """Test processing degraded health check results."""
        # Mock degraded result
        results = {
            "memory": HealthCheckResult(
                name="memory",
                status=HealthStatus.DEGRADED,
                message="High memory usage detected"
            )
        }

        await monitoring_service._process_health_results(results)

        # Check that warning alert was created
        active_alerts = monitoring_service.alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].severity == "warning"
        assert "memory" in active_alerts[0].title

    @pytest.mark.asyncio
    async def test_process_health_results_healthy_resolves_alerts(self, monitoring_service):
        """Test that healthy results resolve existing alerts."""
        # Create an existing alert
        monitoring_service.alert_manager.create_alert(
            "health_database",
            "critical",
            "Database Issue",
            "Database is down"
        )

        # Mock healthy result
        results = {
            "database": HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database is working fine"
            )
        }

        await monitoring_service._process_health_results(results)

        # Check that alert was resolved
        active_alerts = monitoring_service.alert_manager.get_active_alerts()
        assert len(active_alerts) == 0

    def test_get_monitoring_status(self, monitoring_service):
        """Test getting monitoring status."""
        status = monitoring_service.get_monitoring_status()

        assert "enabled" in status
        assert "check_interval" in status
        assert "active_alerts" in status
        assert "thresholds" in status
        assert isinstance(status["enabled"], bool)
        assert isinstance(status["check_interval"], int)

    def test_get_system_overview(self, monitoring_service):
        """Test getting system overview."""
        # Create some test alerts
        monitoring_service.alert_manager.create_alert(
            "critical_alert",
            "critical",
            "Critical Issue",
            "Something is critically wrong"
        )
        monitoring_service.alert_manager.create_alert(
            "warning_alert",
            "warning",
            "Warning Issue",
            "Something needs attention"
        )

        overview = monitoring_service.get_system_overview()

        assert "timestamp" in overview
        assert "overall_status" in overview
        assert "alerts" in overview
        assert "monitoring" in overview

        # Due to critical alert
        assert overview["overall_status"] == "critical"
        assert overview["alerts"]["active"]["total"] == 2
        assert overview["alerts"]["active"]["critical"] == 1
        assert overview["alerts"]["active"]["warning"] == 1


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""

    def test_record_request_time(self):
        """Test recording request times."""
        perf_monitor = PerformanceMonitor()

        perf_monitor.record_request_time(0.1)
        perf_monitor.record_request_time(0.2)
        perf_monitor.record_request_time(0.15)

        assert len(perf_monitor.request_times) == 3
        assert 0.1 in perf_monitor.request_times
        assert 0.2 in perf_monitor.request_times
        assert 0.15 in perf_monitor.request_times

    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        perf_monitor = PerformanceMonitor()

        # Add some test data
        times = [0.1, 0.2, 0.15, 0.3, 0.25, 0.18, 0.22, 0.12, 0.28, 0.16]
        for t in times:
            perf_monitor.record_request_time(t)

        stats = perf_monitor.get_performance_stats()

        assert "request_count" in stats
        assert "avg_response_time" in stats
        assert "min_response_time" in stats
        assert "max_response_time" in stats
        assert "p50_response_time" in stats
        assert "p95_response_time" in stats
        assert "p99_response_time" in stats

        assert stats["request_count"] == 10
        assert stats["min_response_time"] == 0.1
        assert stats["max_response_time"] == 0.3
        assert 0.15 <= stats["avg_response_time"] <= 0.25

    def test_get_performance_stats_no_data(self):
        """Test getting performance stats with no data."""
        perf_monitor = PerformanceMonitor()

        stats = perf_monitor.get_performance_stats()

        assert "message" in stats
        assert "No performance data available" in stats["message"]

    def test_max_samples_limit(self):
        """Test that performance monitor respects max samples limit."""
        perf_monitor = PerformanceMonitor()
        perf_monitor.max_samples = 5

        # Add more samples than the limit
        for i in range(10):
            perf_monitor.record_request_time(i * 0.1)

        assert len(perf_monitor.request_times) == 5
        # Should keep the most recent samples
        assert perf_monitor.request_times == [0.5, 0.6, 0.7, 0.8, 0.9]


class TestMetricsIntegration:
    """Test integration with metrics system."""

    def test_metrics_collector_initialization(self):
        """Test that metrics collector is properly initialized."""
        assert metrics is not None
        assert hasattr(metrics, 'record_request')
        assert hasattr(metrics, 'record_ml_inference')
        assert hasattr(metrics, 'record_database_query')

    def test_record_request_metrics(self):
        """Test recording request metrics."""
        # This would test the actual metrics recording
        # For now, we just ensure the method exists and can be called
        try:
            metrics.record_request("GET", "/health", 200, 0.1)
            assert True  # If no exception, test passes
        except Exception as e:
            pytest.fail(f"Failed to record request metrics: {e}")

    def test_record_ml_inference_metrics(self):
        """Test recording ML inference metrics."""
        try:
            metrics.record_ml_inference("mobilenet", 0.5, True, 0.95)
            assert True  # If no exception, test passes
        except Exception as e:
            pytest.fail(f"Failed to record ML inference metrics: {e}")


@pytest.mark.asyncio
async def test_monitoring_loop_integration():
    """Test the monitoring loop integration."""
    # Mock the health checker
    with patch('app.core.monitoring.monitoring_service.health_checker') as mock_health_checker:
        mock_health_checker.run_all_checks = AsyncMock(return_value={
            "database": HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database is healthy"
            )
        })

        # Run one monitoring cycle
        monitoring_service.monitoring_enabled = True
        monitoring_service.last_check_time = 0  # Force check

        await monitoring_service.run_monitoring_cycle()

        # Verify health check was called
        mock_health_checker.run_all_checks.assert_called_once()


@pytest.mark.asyncio
async def test_monitoring_error_handling():
    """Test monitoring error handling."""
    # Mock the health checker to raise an exception
    with patch('app.core.monitoring.monitoring_service.health_checker') as mock_health_checker:
        mock_health_checker.run_all_checks = AsyncMock(
            side_effect=Exception("Test error"))

        # Run monitoring cycle
        monitoring_service.monitoring_enabled = True
        monitoring_service.last_check_time = 0  # Force check

        await monitoring_service.run_monitoring_cycle()

        # Check that an alert was created for the monitoring failure
        active_alerts = monitoring_service.alert_manager.get_active_alerts()
        monitoring_failure_alerts = [
            alert for alert in active_alerts
            if alert.id == "monitoring_failure"
        ]

        assert len(monitoring_failure_alerts) == 1
        assert monitoring_failure_alerts[0].severity == "critical"
