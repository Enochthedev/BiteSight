#!/bin/bash

# Production Setup Script for Nutrition Feedback System
# This script sets up the production environment with security hardening

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

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

# Generate secure passwords
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Setup SSL certificates (self-signed for development)
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    SSL_DIR="$PROJECT_DIR/nginx/ssl"
    mkdir -p "$SSL_DIR"
    
    if [[ ! -f "$SSL_DIR/cert.pem" ]]; then
        log_info "Generating self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/key.pem" \
            -out "$SSL_DIR/cert.pem" \
            -subj "/C=NG/ST=Lagos/L=Lagos/O=Nutrition Feedback System/CN=localhost"
        
        chmod 600 "$SSL_DIR/key.pem"
        chmod 644 "$SSL_DIR/cert.pem"
        
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

# Setup environment configuration
setup_environment() {
    log_info "Setting up production environment configuration..."
    
    ENV_FILE="$PROJECT_DIR/.env"
    
    if [[ -f "$ENV_FILE" ]]; then
        log_warning "Environment file already exists. Creating backup..."
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Generate secure passwords
    DB_PASSWORD=$(generate_password)
    JWT_SECRET=$(generate_password)
    GRAFANA_PASSWORD=$(generate_password)
    
    # Create production environment file
    cat > "$ENV_FILE" << EOF
# Production Environment Configuration
# Generated on $(date)

# Database Configuration
POSTGRES_DB=nutrition_feedback
POSTGRES_USER=nutrition_user
POSTGRES_PASSWORD=$DB_PASSWORD

# Application Configuration
JWT_SECRET_KEY=$JWT_SECRET
ENVIRONMENT=production
LOG_LEVEL=INFO

# Redis Configuration
REDIS_URL=redis://redis:6379

# Monitoring Configuration
GRAFANA_PASSWORD=$GRAFANA_PASSWORD

# Performance Configuration
MAX_WORKERS=4
WORKER_MEMORY_LIMIT=512M
REDIS_MAX_MEMORY=256mb

# Backup Configuration
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
EOF
    
    chmod 600 "$ENV_FILE"
    
    log_success "Environment configuration created"
    log_warning "IMPORTANT: Save these credentials securely!"
    log_warning "Database Password: $DB_PASSWORD"
    log_warning "JWT Secret: $JWT_SECRET"
    log_warning "Grafana Password: $GRAFANA_PASSWORD"
}

# Setup monitoring configuration
setup_monitoring() {
    log_info "Setting up monitoring configuration..."
    
    MONITORING_DIR="$PROJECT_DIR/monitoring"
    mkdir -p "$MONITORING_DIR/grafana/dashboards" "$MONITORING_DIR/grafana/datasources"
    
    # Prometheus configuration
    cat > "$MONITORING_DIR/prometheus.yml" << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'nutrition-backend'
    static_configs:
      - targets: ['backend:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: '/nginx_status'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
EOF

    # Grafana datasource configuration
    cat > "$MONITORING_DIR/grafana/datasources/prometheus.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Basic Grafana dashboard configuration
    cat > "$MONITORING_DIR/grafana/dashboards/dashboard.yml" << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    log_success "Monitoring configuration created"
}

# Setup backup directories
setup_backup() {
    log_info "Setting up backup directories..."
    
    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR/database" "$BACKUP_DIR/uploads" "$BACKUP_DIR/logs"
    
    # Create backup script
    cat > "$PROJECT_DIR/scripts/backup.sh" << 'EOF'
#!/bin/bash

# Backup script for Nutrition Feedback System

BACKUP_DIR="/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U nutrition_user nutrition_feedback > "$BACKUP_DIR/database/nutrition_db_$DATE.sql"

# Uploads backup
tar -czf "$BACKUP_DIR/uploads/uploads_$DATE.tar.gz" -C /var/lib/docker/volumes/nutrition-feedback-system_uploaded_images/_data .

# Logs backup
tar -czf "$BACKUP_DIR/logs/logs_$DATE.tar.gz" -C /var/lib/docker/volumes/nutrition-feedback-system_app_logs/_data .

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x "$PROJECT_DIR/scripts/backup.sh"
    
    log_success "Backup configuration created"
}

# Setup log rotation
setup_logging() {
    log_info "Setting up log rotation configuration..."
    
    LOGS_DIR="$PROJECT_DIR/logs"
    mkdir -p "$LOGS_DIR"
    
    # Create logrotate configuration
    cat > "$PROJECT_DIR/logrotate.conf" << EOF
/var/lib/docker/volumes/nutrition-feedback-system_app_logs/_data/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose -f docker-compose.prod.yml restart backend
    endscript
}

/var/lib/docker/volumes/nutrition-feedback-system_nginx_logs/_data/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
    endscript
}
EOF
    
    log_success "Log rotation configuration created"
}

# Setup systemd service (optional)
setup_systemd() {
    log_info "Setting up systemd service..."
    
    cat > "$PROJECT_DIR/nutrition-feedback.service" << EOF
[Unit]
Description=Nutrition Feedback System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/scripts/deploy.sh production start
ExecStop=$PROJECT_DIR/scripts/deploy.sh production stop
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    log_info "Systemd service file created at: $PROJECT_DIR/nutrition-feedback.service"
    log_info "To install: sudo cp nutrition-feedback.service /etc/systemd/system/"
    log_info "To enable: sudo systemctl enable nutrition-feedback"
}

# Main setup function
main() {
    log_info "Starting production setup for Nutrition Feedback System..."
    
    # Check if running as root for some operations
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. Some operations will be skipped for security."
    fi
    
    setup_ssl
    setup_environment
    setup_monitoring
    setup_backup
    setup_logging
    setup_systemd
    
    log_success "Production setup completed!"
    log_info "Next steps:"
    log_info "1. Review and update the .env file with your specific configuration"
    log_info "2. Update SSL certificates for your domain (if using HTTPS)"
    log_info "3. Configure your firewall to allow ports 80, 443, 3000, 9090"
    log_info "4. Run: ./scripts/deploy.sh production deploy"
    log_info "5. Set up automated backups with cron"
    log_warning "Remember to secure your environment file and SSL certificates!"
}

# Run main function
main "$@"