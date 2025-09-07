#!/bin/bash

# Nutrition Feedback System Deployment Script
# Usage: ./scripts/deploy.sh [environment] [action]
# Environment: development, staging, production
# Action: build, start, stop, restart, logs, status

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-development}
ACTION=${2:-start}

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

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            log_info "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_info "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    ENV_FILE="$PROJECT_DIR/.env.$ENVIRONMENT"
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "Environment file not found: $ENV_FILE"
        log_info "Creating from template..."
        cp "$PROJECT_DIR/.env.$ENVIRONMENT" "$PROJECT_DIR/.env"
    else
        cp "$ENV_FILE" "$PROJECT_DIR/.env"
    fi
    
    log_success "Prerequisites check completed"
}

# Build containers
build_containers() {
    log_info "Building containers for $ENVIRONMENT..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.prod.yml build --no-cache
    else
        docker-compose build --no-cache
    fi
    
    log_success "Containers built successfully"
}

# Start services
start_services() {
    log_info "Starting services for $ENVIRONMENT..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.prod.yml up -d
    else
        docker-compose up -d
    fi
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log_success "Services started successfully"
}

# Stop services
stop_services() {
    log_info "Stopping services for $ENVIRONMENT..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.prod.yml down
    else
        docker-compose down
    fi
    
    log_success "Services stopped successfully"
}

# Restart services
restart_services() {
    log_info "Restarting services for $ENVIRONMENT..."
    stop_services
    start_services
}

# Show logs
show_logs() {
    log_info "Showing logs for $ENVIRONMENT..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.prod.yml logs -f
    else
        docker-compose logs -f
    fi
}

# Check service status
check_status() {
    log_info "Checking service status for $ENVIRONMENT..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.prod.yml ps
    else
        docker-compose ps
    fi
}

# Check service health
check_service_health() {
    log_info "Checking service health..."
    
    # Check backend health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend service is healthy"
            break
        fi
        
        if [[ $i -eq 30 ]]; then
            log_error "Backend service health check failed"
            return 1
        fi
        
        sleep 2
    done
    
    # Check nginx health (if not development)
    if [[ "$ENVIRONMENT" != "development" ]]; then
        for i in {1..30}; do
            if curl -f http://localhost/health &> /dev/null; then
                log_success "Nginx service is healthy"
                break
            fi
            
            if [[ $i -eq 30 ]]; then
                log_error "Nginx service health check failed"
                return 1
            fi
            
            sleep 2
        done
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
    else
        docker-compose exec backend alembic upgrade head
    fi
    
    log_success "Database migrations completed"
}

# Backup database
backup_database() {
    log_info "Creating database backup..."
    
    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/nutrition_db_$(date +%Y%m%d_%H%M%S).sql"
    
    cd "$PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U nutrition_user nutrition_feedback > "$BACKUP_FILE"
    else
        docker-compose exec postgres pg_dump -U nutrition_user nutrition_feedback > "$BACKUP_FILE"
    fi
    
    log_success "Database backup created: $BACKUP_FILE"
}

# Main execution
main() {
    validate_environment
    check_prerequisites
    
    case $ACTION in
        build)
            build_containers
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        status)
            check_status
            ;;
        migrate)
            run_migrations
            ;;
        backup)
            backup_database
            ;;
        deploy)
            build_containers
            stop_services
            start_services
            run_migrations
            ;;
        *)
            log_error "Invalid action: $ACTION"
            log_info "Valid actions: build, start, stop, restart, logs, status, migrate, backup, deploy"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"