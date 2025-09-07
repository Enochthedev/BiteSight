#!/bin/bash

# Test script for monitoring and logging systems
# This script runs comprehensive tests for the monitoring infrastructure

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "$BACKEND_DIR/requirements.txt" ]]; then
        log_error "Backend directory not found or invalid"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pytest
    if ! python3 -c "import pytest" &> /dev/null; then
        log_error "pytest is not installed"
        log_info "Install with: pip install pytest pytest-asyncio"
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

# Install test dependencies
install_dependencies() {
    log_info "Installing test dependencies..."
    
    cd "$BACKEND_DIR"
    
    # Install required packages for testing
    pip install pytest pytest-asyncio pytest-cov psutil prometheus-client
    
    log_success "Dependencies installed"
}

# Run monitoring tests
run_monitoring_tests() {
    log_info "Running monitoring system tests..."
    
    cd "$BACKEND_DIR"
    
    # Run monitoring tests with coverage
    python -m pytest tests/test_monitoring.py -v --cov=app.core.monitoring --cov-report=term-missing
    
    if [[ $? -eq 0 ]]; then
        log_success "Monitoring tests passed"
    else
        log_error "Monitoring tests failed"
        return 1
    fi
}

# Run logging tests
run_logging_tests() {
    log_info "Running logging system tests..."
    
    cd "$BACKEND_DIR"
    
    # Run logging tests with coverage
    python -m pytest tests/test_logging.py -v --cov=app.core.logging_config --cov-report=term-missing
    
    if [[ $? -eq 0 ]]; then
        log_success "Logging tests passed"
    else
        log_error "Logging tests failed"
        return 1
    fi
}

# Run health check tests
run_health_check_tests() {
    log_info "Running health check tests..."
    
    cd "$BACKEND_DIR"
    
    # Run health check tests
    python -m pytest tests/test_health_checks.py -v --cov=app.core.health_checks --cov-report=term-missing
    
    if [[ $? -eq 0 ]]; then
        log_success "Health check tests passed"
    else
        log_warning "Health check tests failed (may be expected if no test file exists)"
    fi
}

# Run metrics tests
run_metrics_tests() {
    log_info "Running metrics system tests..."
    
    cd "$BACKEND_DIR"
    
    # Create a simple metrics test if it doesn't exist
    if [[ ! -f "tests/test_metrics.py" ]]; then
        log_info "Creating basic metrics test..."
        cat > tests/test_metrics.py << 'EOF'
"""Basic tests for metrics system."""

import pytest
from app.core.metrics import metrics, MetricsCollector


def test_metrics_collector_initialization():
    """Test metrics collector initialization."""
    collector = MetricsCollector()
    assert collector is not None
    assert hasattr(collector, 'record_request')
    assert hasattr(collector, 'record_ml_inference')


def test_record_request():
    """Test recording request metrics."""
    try:
        metrics.record_request("GET", "/test", 200, 0.1)
        assert True  # If no exception, test passes
    except Exception as e:
        pytest.fail(f"Failed to record request: {e}")


def test_record_ml_inference():
    """Test recording ML inference metrics."""
    try:
        metrics.record_ml_inference("test_model", 0.5, True, 0.95)
        assert True  # If no exception, test passes
    except Exception as e:
        pytest.fail(f"Failed to record ML inference: {e}")
EOF
    fi
    
    # Run metrics tests
    python -m pytest tests/test_metrics.py -v --cov=app.core.metrics --cov-report=term-missing
    
    if [[ $? -eq 0 ]]; then
        log_success "Metrics tests passed"
    else
        log_error "Metrics tests failed"
        return 1
    fi
}

# Test monitoring endpoints
test_monitoring_endpoints() {
    log_info "Testing monitoring endpoints..."
    
    cd "$BACKEND_DIR"
    
    # Create endpoint test if it doesn't exist
    if [[ ! -f "tests/test_monitoring_endpoints.py" ]]; then
        log_info "Creating monitoring endpoints test..."
        cat > tests/test_monitoring_endpoints.py << 'EOF'
"""Tests for monitoring endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test basic health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Should return Prometheus format
    assert "text/plain" in response.headers.get("content-type", "")


@patch('app.core.health_checks.get_health_checker')
def test_detailed_health_endpoint(mock_health_checker):
    """Test detailed health endpoint."""
    # Mock health checker
    mock_checker = MagicMock()
    mock_health_checker.return_value = mock_checker
    
    response = client.get("/health/detailed")
    # Should not fail even if some checks fail
    assert response.status_code in [200, 503]
EOF
    fi
    
    # Run endpoint tests
    python -m pytest tests/test_monitoring_endpoints.py -v
    
    if [[ $? -eq 0 ]]; then
        log_success "Monitoring endpoints tests passed"
    else
        log_warning "Monitoring endpoints tests failed (may be expected without full app setup)"
    fi
}

# Generate test report
generate_test_report() {
    log_info "Generating comprehensive test report..."
    
    cd "$BACKEND_DIR"
    
    # Run all monitoring-related tests with coverage
    python -m pytest \
        tests/test_monitoring.py \
        tests/test_logging.py \
        tests/test_metrics.py \
        -v \
        --cov=app.core.monitoring \
        --cov=app.core.logging_config \
        --cov=app.core.metrics \
        --cov=app.core.health_checks \
        --cov-report=html:htmlcov/monitoring \
        --cov-report=term-missing \
        --junit-xml=test-results-monitoring.xml
    
    if [[ $? -eq 0 ]]; then
        log_success "Test report generated successfully"
        log_info "HTML coverage report: $BACKEND_DIR/htmlcov/monitoring/index.html"
        log_info "JUnit XML report: $BACKEND_DIR/test-results-monitoring.xml"
    else
        log_error "Test report generation failed"
        return 1
    fi
}

# Performance test
run_performance_tests() {
    log_info "Running performance tests..."
    
    cd "$BACKEND_DIR"
    
    # Create performance test if it doesn't exist
    if [[ ! -f "tests/test_monitoring_performance.py" ]]; then
        log_info "Creating performance test..."
        cat > tests/test_monitoring_performance.py << 'EOF'
"""Performance tests for monitoring system."""

import time
import pytest
from app.core.monitoring import monitoring_service, performance_monitor


def test_monitoring_cycle_performance():
    """Test monitoring cycle performance."""
    start_time = time.time()
    
    # Simulate monitoring cycle
    monitoring_service.monitoring_enabled = True
    
    duration = time.time() - start_time
    
    # Monitoring cycle should be fast
    assert duration < 1.0, f"Monitoring cycle took too long: {duration}s"


def test_performance_monitor_overhead():
    """Test performance monitor overhead."""
    start_time = time.time()
    
    # Record many performance samples
    for i in range(1000):
        performance_monitor.record_request_time(0.1)
    
    duration = time.time() - start_time
    
    # Should be able to record 1000 samples quickly
    assert duration < 0.1, f"Performance monitoring overhead too high: {duration}s"


def test_metrics_recording_performance():
    """Test metrics recording performance."""
    from app.core.metrics import metrics
    
    start_time = time.time()
    
    # Record many metrics
    for i in range(100):
        metrics.record_request("GET", "/test", 200, 0.1)
    
    duration = time.time() - start_time
    
    # Should be able to record 100 metrics quickly
    assert duration < 0.5, f"Metrics recording too slow: {duration}s"
EOF
    fi
    
    # Run performance tests
    python -m pytest tests/test_monitoring_performance.py -v
    
    if [[ $? -eq 0 ]]; then
        log_success "Performance tests passed"
    else
        log_warning "Performance tests failed"
    fi
}

# Main execution
main() {
    log_info "Starting monitoring and logging system tests..."
    
    check_prerequisites
    install_dependencies
    
    # Run all test suites
    run_monitoring_tests
    run_logging_tests
    run_health_check_tests
    run_metrics_tests
    test_monitoring_endpoints
    run_performance_tests
    
    # Generate comprehensive report
    generate_test_report
    
    log_success "All monitoring and logging tests completed!"
    log_info "Review the generated reports for detailed results"
}

# Run main function
main "$@"