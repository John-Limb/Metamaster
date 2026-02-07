# Comprehensive Deployment Guide

## Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Environment Setup](#environment-setup)
5. [Configuration Management](#configuration-management)
6. [Deployment Procedures](#deployment-procedures)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Rollback Procedures](#rollback-procedures)
9. [Monitoring and Alerting](#monitoring-and-alerting)
10. [Troubleshooting](#troubleshooting)

## Deployment Overview

This guide provides comprehensive instructions for deploying the Metamaster application across multiple environments including local development, Docker, Kubernetes, and cloud platforms (AWS/GCP/Azure).

### Supported Deployment Environments
- **Local Development**: Docker Compose with local services
- **Docker**: Containerized deployment with Docker Compose
- **Kubernetes**: Orchestrated container deployment with Helm
- **Cloud Platforms**: AWS, GCP, Azure with managed services

### Key Components
- **Backend API**: FastAPI application
- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis for caching and task queues
- **Task Queue**: Celery with Redis broker
- **Task Scheduler**: Celery Beat for scheduled tasks

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer / Ingress                 │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼───┐        ┌───▼───┐       ┌───▼───┐
    │ API 1 │        │ API 2 │       │ API N │
    └───┬───┘        └───┬───┘       └───┬───┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼────────┐  ┌────▼────┐  ┌──────▼──┐
    │ PostgreSQL │  │  Redis   │  │ Celery  │
    │ (Primary)  │  │ (Cache)  │  │ Workers │
    └────────────┘  └──────────┘  └─────────┘
```

### Component Responsibilities

| Component | Purpose | Scaling |
|-----------|---------|---------|
| API Servers | Handle HTTP requests | Horizontal (multiple instances) |
| PostgreSQL | Data persistence | Vertical (read replicas) |
| Redis | Caching & task queue | Vertical (cluster mode) |
| Celery Workers | Async task processing | Horizontal (multiple workers) |
| Celery Beat | Scheduled tasks | Single instance (with failover) |

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 20 GB SSD
- **OS**: Linux, macOS, or Windows with WSL2

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk**: 50+ GB SSD
- **OS**: Linux (Ubuntu 20.04 LTS or later)

### Software Requirements

#### Required
- Docker 20.10+
- Docker Compose 1.29+
- Python 3.9+
- PostgreSQL 12+ (or managed service)
- Redis 6.0+ (or managed service)

#### Optional
- Kubernetes 1.20+ (for K8s deployment)
- Helm 3.0+ (for Helm charts)
- Terraform 1.0+ (for IaC)
- kubectl 1.20+ (for K8s management)

### Access Requirements
- Git repository access
- Container registry access (Docker Hub, ECR, GCR, etc.)
- Cloud provider credentials (if deploying to cloud)
- SSH access to deployment servers

### Network Requirements
- Outbound HTTPS access (for external APIs)
- Inbound HTTP/HTTPS (ports 80, 443)
- Internal communication between services
- Database connectivity (port 5432)
- Redis connectivity (port 6379)

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/metamaster.git
cd metamaster
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Application
APP_NAME=Metamaster
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/metamaster
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_DB=1

# API Keys
OMDB_API_KEY=your_omdb_key
TVDB_API_KEY=your_tvdb_key

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_ENABLED=true
```

### 4. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Seed initial data (if applicable)
python -m app.init_db
```

### 5. Verify Installation

```bash
# Check Python version
python --version

# Check Docker
docker --version
docker-compose --version

# Test database connection
python -c "from app.database import engine; engine.connect()"

# Test Redis connection
redis-cli ping
```

## Configuration Management

### Environment-Specific Configuration

#### Development Configuration
```env
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_ECHO=true
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

#### Staging Configuration
```env
APP_ENV=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_ECHO=false
CORS_ORIGINS=["https://staging.example.com"]
```

#### Production Configuration
```env
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_ECHO=false
CORS_ORIGINS=["https://example.com"]
```

### Configuration Hierarchy

1. **Environment Variables** (highest priority)
2. **.env file**
3. **config.py defaults** (lowest priority)

### Secrets Management

#### Using Environment Variables
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export SECRET_KEY="your-secret-key"
```

#### Using .env File
```bash
# .env (never commit to version control)
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=your-secret-key
```

#### Using Docker Secrets (Production)
```bash
# Create secrets
echo "your-secret-key" | docker secret create app_secret_key -

# Reference in docker-compose.yml
secrets:
  app_secret_key:
    external: true
```

#### Using Kubernetes Secrets (K8s)
```bash
# Create secret
kubectl create secret generic app-secrets \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=SECRET_KEY=...

# Reference in deployment
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: DATABASE_URL
```

## Deployment Procedures

### Local Development Deployment

See [`docs/DEPLOYMENT_LOCAL.md`](DEPLOYMENT_LOCAL.md) for detailed local deployment instructions.

**Quick Start:**
```bash
docker-compose up -d
docker-compose exec api alembic upgrade head
docker-compose exec api python -m app.init_db
```

### Docker Deployment

See [`docs/DEPLOYMENT_DOCKER.md`](DEPLOYMENT_DOCKER.md) for detailed Docker deployment instructions.

**Quick Start:**
```bash
docker build -t metamaster:latest .
docker-compose -f docker-compose.yml up -d
```

### Kubernetes Deployment

See [`docs/DEPLOYMENT_KUBERNETES.md`](DEPLOYMENT_KUBERNETES.md) for detailed Kubernetes deployment instructions.

**Quick Start:**
```bash
helm install metamaster ./helm/metamaster \
  -f helm/values-prod.yaml \
  -n production
```

### Cloud Deployment

See [`docs/DEPLOYMENT_CLOUD.md`](DEPLOYMENT_CLOUD.md) for detailed cloud deployment instructions.

**Quick Start (AWS):**
```bash
# Deploy using CloudFormation or Terraform
terraform apply -var-file=prod.tfvars
```

## Post-Deployment Verification

### 1. Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-15T10:30:00Z",
#   "version": "1.0.0"
# }
```

### 2. Database Connectivity

```bash
# Test database connection
curl http://localhost:8000/health/db

# Expected response:
# {
#   "database": "connected",
#   "response_time_ms": 5
# }
```

### 3. Redis Connectivity

```bash
# Test Redis connection
curl http://localhost:8000/health/cache

# Expected response:
# {
#   "cache": "connected",
#   "response_time_ms": 2
# }
```

### 4. API Functionality

```bash
# Test API endpoint
curl -X GET http://localhost:8000/api/v1/movies \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected response: 200 OK with movie data
```

### 5. Celery Tasks

```bash
# Check Celery worker status
celery -A app.celery_app inspect active

# Expected response: List of active tasks
```

### 6. Logs Review

```bash
# Check application logs
docker-compose logs -f api

# Check for errors or warnings
grep -i "error\|warning" logs/app.log
```

### 7. Performance Baseline

```bash
# Run performance tests
pytest tests/test_performance_database.py -v

# Check response times
# Expected: API response time < 200ms
```

## Rollback Procedures

### Database Rollback

```bash
# List available migrations
alembic history

# Rollback to previous version
alembic downgrade -1

# Rollback to specific version
alembic downgrade 001_add_task_error_model
```

### Application Rollback

#### Docker Rollback
```bash
# Stop current version
docker-compose down

# Start previous version
docker-compose -f docker-compose.v1.0.0.yml up -d
```

#### Kubernetes Rollback
```bash
# Check rollout history
kubectl rollout history deployment/metamaster-api

# Rollback to previous version
kubectl rollout undo deployment/metamaster-api

# Rollback to specific revision
kubectl rollout undo deployment/metamaster-api --to-revision=2
```

### Data Recovery

See [`docs/DEPLOYMENT_BACKUP_RECOVERY.md`](DEPLOYMENT_BACKUP_RECOVERY.md) for detailed recovery procedures.

```bash
# Restore from backup
pg_restore -d metamaster backup.sql

# Verify data integrity
psql -d metamaster -c "SELECT COUNT(*) FROM movies;"
```

## Monitoring and Alerting

### Metrics Collection

#### Prometheus Metrics
```bash
# Access Prometheus metrics
curl http://localhost:8000/metrics

# Key metrics:
# - http_requests_total
# - http_request_duration_seconds
# - database_query_duration_seconds
# - celery_task_duration_seconds
```

#### Application Logs
```bash
# View logs
docker-compose logs -f api

# Filter by level
docker-compose logs -f api | grep ERROR
```

### Alerting Setup

#### Alert Rules (Prometheus)
```yaml
groups:
  - name: metamaster
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "Database is down"
      
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / 1024 / 1024 > 1024
        for: 5m
        annotations:
          summary: "High memory usage detected"
```

### Monitoring Dashboards

#### Grafana Dashboard
- Request rate and latency
- Error rates by endpoint
- Database query performance
- Celery task metrics
- Resource utilization (CPU, memory, disk)
- Cache hit rates

## Troubleshooting

### Common Issues

#### Database Connection Errors
```
Error: could not connect to server: Connection refused
```

**Solution:**
1. Verify PostgreSQL is running: `docker-compose ps`
2. Check DATABASE_URL in .env
3. Verify network connectivity: `telnet localhost 5432`
4. Check database logs: `docker-compose logs postgres`

#### Redis Connection Errors
```
Error: Connection refused
```

**Solution:**
1. Verify Redis is running: `docker-compose ps`
2. Check REDIS_URL in .env
3. Test connection: `redis-cli ping`
4. Check Redis logs: `docker-compose logs redis`

#### API Not Responding
```
Error: Connection refused on port 8000
```

**Solution:**
1. Check if API container is running: `docker-compose ps`
2. View API logs: `docker-compose logs api`
3. Verify port mapping: `docker-compose config`
4. Check for startup errors: `docker-compose logs api | tail -50`

#### Celery Tasks Not Processing
```
Error: No workers available
```

**Solution:**
1. Verify Celery worker is running: `docker-compose ps`
2. Check worker logs: `docker-compose logs celery`
3. Verify Redis connection: `redis-cli ping`
4. Check task queue: `celery -A app.celery_app inspect active`

### Debug Mode

Enable debug logging:
```bash
# In .env
LOG_LEVEL=DEBUG
DEBUG=true

# Restart services
docker-compose restart api
```

### Performance Troubleshooting

See [`docs/DEPLOYMENT_TROUBLESHOOTING.md`](DEPLOYMENT_TROUBLESHOOTING.md) for detailed troubleshooting procedures.

## Next Steps

1. Choose your deployment environment:
   - [Local Development](DEPLOYMENT_LOCAL.md)
   - [Docker](DEPLOYMENT_DOCKER.md)
   - [Kubernetes](DEPLOYMENT_KUBERNETES.md)
   - [Cloud Platforms](DEPLOYMENT_CLOUD.md)

2. Configure your environment:
   - [Environment Setup](#environment-setup)
   - [Configuration Management](#configuration-management)

3. Deploy and verify:
   - [Deployment Procedures](#deployment-procedures)
   - [Post-Deployment Verification](#post-deployment-verification)

4. Monitor and maintain:
   - [Monitoring and Alerting](#monitoring-and-alerting)
   - [Troubleshooting](#troubleshooting)

## Support

For additional help:
- Check [Troubleshooting Guide](DEPLOYMENT_TROUBLESHOOTING.md)
- Review [Security Guide](DEPLOYMENT_SECURITY.md)
- See [Database Guide](DEPLOYMENT_DATABASE.md)
- Consult [Backup & Recovery Guide](DEPLOYMENT_BACKUP_RECOVERY.md)
