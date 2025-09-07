# Deployment Guide

This guide covers deployment options for the Nutrition Feedback System, including Docker Compose for local development and Kubernetes for production environments.

## Prerequisites

### For Docker Deployment
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ disk space

### For Kubernetes Deployment
- Kubernetes cluster 1.20+
- kubectl configured
- 8GB+ RAM across nodes
- 50GB+ storage

## Quick Start (Development)

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd nutrition-feedback-system
   ```

2. **Start development environment:**
   ```bash
   ./scripts/deploy.sh development deploy
   ```

3. **Access the application:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Database: localhost:5432
   - Redis: localhost:6379

## Production Deployment

### Option 1: Docker Compose (Recommended for single server)

1. **Setup production environment:**
   ```bash
   ./scripts/setup-production.sh
   ```

2. **Review and update configuration:**
   ```bash
   # Edit the generated .env file with your production values
   nano .env
   ```

3. **Deploy to production:**
   ```bash
   ./scripts/deploy.sh production deploy
   ```

4. **Verify deployment:**
   ```bash
   ./scripts/deploy.sh production status
   ```

### Option 2: Kubernetes (Recommended for scalable deployment)

1. **Update Kubernetes secrets:**
   ```bash
   # Edit k8s/configmap.yaml with your values
   nano k8s/configmap.yaml
   ```

2. **Deploy to Kubernetes:**
   ```bash
   cd k8s
   ./deploy.sh deploy
   ```

3. **Check deployment status:**
   ```bash
   ./deploy.sh status
   ```

4. **Get service URLs:**
   ```bash
   ./deploy.sh urls
   ```

## Environment Configuration

### Development Environment
- Uses `.env.development`
- Debug logging enabled
- Hot reload enabled
- Single worker process
- No SSL/TLS

### Production Environment
- Uses `.env.production`
- Info-level logging
- Multiple worker processes
- SSL/TLS enabled
- Performance optimizations
- Health checks
- Resource limits

## Key Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Database password | Generated |
| `JWT_SECRET_KEY` | JWT signing key | Generated |
| `ENVIRONMENT` | Environment name | production |
| `LOG_LEVEL` | Logging level | INFO |
| `MAX_WORKERS` | API worker processes | 4 |
| `REDIS_MAX_MEMORY` | Redis memory limit | 256mb |

## Monitoring and Observability

### Included Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Application logs**: Structured logging
- **Health checks**: Service health monitoring

### Access Monitoring
- Grafana: http://your-domain:3000 (admin/admin)
- Prometheus: http://your-domain:9090

### Key Metrics
- API response times
- Database connection pool
- Redis cache hit rates
- Memory and CPU usage
- Error rates and types

## Security Considerations

### Production Security Checklist
- [ ] Change default passwords
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Configure backup encryption
- [ ] Review file permissions
- [ ] Update container images regularly

### Network Security
- API rate limiting enabled
- File upload size limits
- CORS configuration
- Security headers
- Input validation

## Backup and Recovery

### Automated Backups
```bash
# Setup automated backups
crontab -e
# Add: 0 2 * * * /path/to/nutrition-feedback-system/scripts/backup.sh
```

### Manual Backup
```bash
./scripts/deploy.sh production backup
```

### Restore from Backup
```bash
# Stop services
./scripts/deploy.sh production stop

# Restore database
docker-compose exec postgres psql -U nutrition_user -d nutrition_feedback < backup.sql

# Start services
./scripts/deploy.sh production start
```

## Scaling

### Horizontal Scaling (Kubernetes)
```bash
# Scale backend pods
kubectl scale deployment nutrition-backend --replicas=5 -n nutrition-feedback

# Scale nginx pods
kubectl scale deployment nutrition-nginx --replicas=3 -n nutrition-feedback
```

### Vertical Scaling (Docker Compose)
```yaml
# Update docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## Troubleshooting

### Common Issues

1. **Database connection failed**
   ```bash
   # Check database status
   docker-compose logs postgres
   
   # Verify credentials
   docker-compose exec postgres psql -U nutrition_user -d nutrition_feedback
   ```

2. **High memory usage**
   ```bash
   # Check container stats
   docker stats
   
   # Adjust Redis memory limit
   # Edit .env: REDIS_MAX_MEMORY=512mb
   ```

3. **Slow API responses**
   ```bash
   # Check backend logs
   docker-compose logs backend
   
   # Monitor metrics in Grafana
   # Scale backend if needed
   ```

### Log Locations
- Application logs: `/var/lib/docker/volumes/nutrition-feedback-system_app_logs/_data/`
- Nginx logs: `/var/lib/docker/volumes/nutrition-feedback-system_nginx_logs/_data/`
- Database logs: `docker-compose logs postgres`

### Health Check Endpoints
- Backend: `GET /health`
- Database: `docker-compose exec postgres pg_isready`
- Redis: `docker-compose exec redis redis-cli ping`

## Performance Tuning

### Database Optimization
```sql
-- Monitor slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### Redis Optimization
```bash
# Monitor Redis performance
docker-compose exec redis redis-cli info stats
```

### Application Optimization
- Enable response compression
- Optimize image processing
- Use connection pooling
- Cache frequently accessed data

## Maintenance

### Regular Maintenance Tasks
- [ ] Update container images monthly
- [ ] Review and rotate logs weekly
- [ ] Monitor disk usage daily
- [ ] Test backup restoration monthly
- [ ] Review security updates weekly

### Update Procedure
1. Backup current deployment
2. Test updates in staging
3. Schedule maintenance window
4. Deploy updates
5. Verify functionality
6. Monitor for issues

## Support

### Getting Help
- Check logs for error messages
- Review monitoring dashboards
- Consult troubleshooting section
- Check GitHub issues

### Reporting Issues
Include the following information:
- Environment (development/production)
- Deployment method (Docker/Kubernetes)
- Error messages and logs
- Steps to reproduce
- System specifications