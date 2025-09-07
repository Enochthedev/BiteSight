#!/bin/bash

# Kubernetes deployment script for Nutrition Feedback System

set -e

# Configuration
NAMESPACE="nutrition-feedback"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace..."
    
    kubectl apply -f "$SCRIPT_DIR/namespace.yaml"
    
    log_success "Namespace created"
}

# Deploy configuration
deploy_config() {
    log_info "Deploying configuration..."
    
    kubectl apply -f "$SCRIPT_DIR/configmap.yaml"
    
    log_success "Configuration deployed"
}

# Deploy database
deploy_database() {
    log_info "Deploying PostgreSQL database..."
    
    kubectl apply -f "$SCRIPT_DIR/postgres.yaml"
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/nutrition-postgres -n $NAMESPACE
    
    log_success "Database deployed"
}

# Deploy Redis
deploy_redis() {
    log_info "Deploying Redis cache..."
    
    kubectl apply -f "$SCRIPT_DIR/redis.yaml"
    
    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/nutrition-redis -n $NAMESPACE
    
    log_success "Redis deployed"
}

# Deploy backend
deploy_backend() {
    log_info "Deploying backend services..."
    
    kubectl apply -f "$SCRIPT_DIR/backend.yaml"
    
    # Wait for backend to be ready
    log_info "Waiting for backend to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/nutrition-backend -n $NAMESPACE
    
    log_success "Backend deployed"
}

# Deploy nginx
deploy_nginx() {
    log_info "Deploying Nginx load balancer..."
    
    kubectl apply -f "$SCRIPT_DIR/nginx.yaml"
    
    # Wait for nginx to be ready
    log_info "Waiting for Nginx to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/nutrition-nginx -n $NAMESPACE
    
    log_success "Nginx deployed"
}

# Deploy monitoring
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    kubectl apply -f "$SCRIPT_DIR/monitoring.yaml"
    
    # Wait for monitoring to be ready
    log_info "Waiting for monitoring to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/nutrition-prometheus -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/nutrition-grafana -n $NAMESPACE
    
    log_success "Monitoring deployed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Get a backend pod
    BACKEND_POD=$(kubectl get pods -n $NAMESPACE -l app=nutrition-backend -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "$BACKEND_POD" ]]; then
        kubectl exec -n $NAMESPACE $BACKEND_POD -- alembic upgrade head
        log_success "Database migrations completed"
    else
        log_error "No backend pod found for migrations"
        return 1
    fi
}

# Check deployment status
check_status() {
    log_info "Checking deployment status..."
    
    echo "Pods:"
    kubectl get pods -n $NAMESPACE
    
    echo -e "\nServices:"
    kubectl get services -n $NAMESPACE
    
    echo -e "\nIngress/LoadBalancer IPs:"
    kubectl get services -n $NAMESPACE -o wide | grep LoadBalancer
}

# Get service URLs
get_urls() {
    log_info "Getting service URLs..."
    
    # Get Nginx LoadBalancer IP
    NGINX_IP=$(kubectl get service nutrition-nginx -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [[ -n "$NGINX_IP" ]]; then
        log_success "Application URL: http://$NGINX_IP"
    else
        log_warning "Nginx LoadBalancer IP not yet assigned"
    fi
    
    # Get Grafana LoadBalancer IP
    GRAFANA_IP=$(kubectl get service nutrition-grafana -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [[ -n "$GRAFANA_IP" ]]; then
        log_success "Grafana URL: http://$GRAFANA_IP:3000"
    else
        log_warning "Grafana LoadBalancer IP not yet assigned"
    fi
}

# Cleanup deployment
cleanup() {
    log_info "Cleaning up deployment..."
    
    kubectl delete namespace $NAMESPACE --ignore-not-found=true
    
    log_success "Cleanup completed"
}

# Main deployment function
deploy_all() {
    log_info "Starting full deployment..."
    
    check_prerequisites
    create_namespace
    deploy_config
    deploy_database
    deploy_redis
    deploy_backend
    deploy_nginx
    deploy_monitoring
    
    # Wait a bit for services to stabilize
    sleep 30
    
    run_migrations
    check_status
    get_urls
    
    log_success "Deployment completed successfully!"
}

# Main execution
case "${1:-deploy}" in
    deploy)
        deploy_all
        ;;
    status)
        check_status
        ;;
    urls)
        get_urls
        ;;
    migrate)
        run_migrations
        ;;
    cleanup)
        cleanup
        ;;
    *)
        log_error "Invalid action: $1"
        log_info "Valid actions: deploy, status, urls, migrate, cleanup"
        exit 1
        ;;
esac