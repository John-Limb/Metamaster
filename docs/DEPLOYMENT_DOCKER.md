# Docker Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Docker Image Building](#docker-image-building)
3. [Docker Compose Configuration](#docker-compose-configuration)
4. [Multi-Container Orchestration](#multi-container-orchestration)
5. [Volume Management](#volume-management)
6. [Network Configuration](#network-configuration)
7. [Environment Variables](#environment-variables)
8. [Production Deployment](#production-deployment)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Troubleshooting](#troubleshooting)

## Overview

This guide covers Docker deployment of the Metamaster application, including image building, container orchestration, and production-ready configurations.

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host / Server                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Docker Network (bridge)                 │   │
│  │                                                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │   API    │  │ Postgres │  │  Redis   │           │   │
│  │  │Container │  │Container │  │Container │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘           │   │
│  │       │              │              │                │   │
│  │  ┌──────────┐  ┌──────────┐                          │   │
│  │  │  Celery  │  │Celery    │                          │   │
│  │  │ Worker   │  │Beat      │                          │   │
│  │  └──────────┘  └──────────┘                          │   │
│  │                                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Volumes (Persistent Storage)            │   │
│  │  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ postgres_data│  │ redis_data   │                 │   │
│  │  └──────────────┘  └──────────────┘                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Docker Image Building

### 1. Dockerfile Structure

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Build Docker Image

```bash
# Build image with tag
docker build -t metamaster:latest .

# Build with specific version
docker build -t metamaster:1.0.0 .

# Build with build arguments
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t metamaster:latest .

# View build output
docker build -t metamaster:latest . --progress=plain

# Build without cache
docker build --no-cache -t metamaster:latest .
```

### 3. Multi-Stage Build (Optimized)

```dockerfile
# Dockerfile.prod
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Push to Registry

```bash
# Tag image for registry
docker tag metamaster:latest myregistry.azurecr.io/metamaster:latest

# Login to registry
docker login myregistry.azurecr.io

# Push image
docker push myregistry.azurecr.io/metamaster:latest

# Pull image
docker pull myregistry.azurecr.io/metamaster:latest
```

## Docker Compose Configuration

### 1. Production docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    container_name: metamaster-postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER:-metamaster}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-metamaster}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-metamaster}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - metamaster-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: metamaster-redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - metamaster-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: metamaster-api
    restart: always
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-metamaster}:${DB_PASSWORD}@postgres:5432/${DB_NAME:-metamaster}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
      - APP_ENV=production
      - DEBUG=false
      - LOG_LEVEL=INFO
      - SECRET_KEY=${SECRET_KEY}
      - OMDB_API_KEY=${OMDB_API_KEY}
      - TVDB_API_KEY=${TVDB_API_KEY}
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - metamaster-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Celery Worker
  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: metamaster-celery
    restart: always
    command: celery -A app.celery_app worker -l info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-metamaster}:${DB_PASSWORD}@postgres:5432/${DB_NAME:-metamaster}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
      - APP_ENV=production
      - DEBUG=false
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
      - api
    networks:
      - metamaster-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Celery Beat (Scheduler)
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: metamaster-celery-beat
    restart: always
    command: celery -A app.celery_app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-metamaster}:${DB_PASSWORD}@postgres:5432/${DB_NAME:-metamaster}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
      - APP_ENV=production
      - DEBUG=false
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
      - api
    networks:
      - metamaster-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  metamaster-network:
    driver: bridge
```

### 2. Deploy with Docker Compose

```bash
# Create .env file
cp .env.example .env
# Edit .env with production values

# Build images
docker-compose -f docker-compose.yml build

# Start services
docker-compose -f docker-compose.yml up -d

# Initialize database
docker-compose exec api alembic upgrade head
docker-compose exec api python -m app.init_db

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Multi-Container Orchestration

### 1. Service Dependencies

```yaml
# Ensure services start in correct order
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
```

### 2. Health Checks

```yaml
# API health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# Database health check
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U metamaster"]
  interval: 10s
  timeout: 5s
  retries: 5

# Redis health check
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### 3. Scaling Services

```bash
# Scale Celery workers
docker-compose up -d --scale celery=3

# Scale API instances (requires load balancer)
docker-compose up -d --scale api=2

# View running containers
docker-compose ps
```

## Volume Management

### 1. Volume Types

```yaml
# Named volume (managed by Docker)
volumes:
  postgres_data:
    driver: local

# Bind mount (host directory)
volumes:
  - /data/postgres:/var/lib/postgresql/data

# Volume mount
volumes:
  - postgres_data:/var/lib/postgresql/data
```

### 2. Backup Volumes

```bash
# Backup PostgreSQL volume
docker run --rm \
  -v metamaster_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore PostgreSQL volume
docker run --rm \
  -v metamaster_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /data

# Backup Redis volume
docker run --rm \
  -v metamaster_redis_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/redis_backup.tar.gz -C /data .
```

### 3. Volume Inspection

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect metamaster_postgres_data

# Remove unused volumes
docker volume prune

# Remove specific volume
docker volume rm metamaster_postgres_data
```

## Network Configuration

### 1. Docker Networks

```yaml
# Define custom network
networks:
  metamaster-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

# Connect services to network
services:
  api:
    networks:
      - metamaster-network
```

### 2. Service Discovery

```bash
# Services communicate by name
# Example: postgres:5432 (not localhost:5432)

# Test connectivity
docker-compose exec api ping postgres
docker-compose exec api redis-cli -h redis ping
```

### 3. Port Mapping

```yaml
# Map container port to host port
ports:
  - "8000:8000"      # host:container
  - "5432:5432"
  - "6379:6379"

# Expose only to other containers
expose:
  - "8000"
```

## Environment Variables

### 1. .env File

```env
# Database
DB_USER=metamaster
DB_PASSWORD=secure_password_here
DB_NAME=metamaster
DB_PORT=5432

# Redis
REDIS_PASSWORD=redis_password_here
REDIS_PORT=6379

# API
API_PORT=8000
SECRET_KEY=your-secret-key-here
DEBUG=false
LOG_LEVEL=INFO

# External APIs
OMDB_API_KEY=your_omdb_key
TVDB_API_KEY=your_tvdb_key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_ENABLED=true
```

### 2. Environment Variable Precedence

```bash
# 1. Command line
docker-compose -e VAR=value up

# 2. .env file
# VAR=value in .env

# 3. docker-compose.yml
environment:
  VAR: value

# 4. Container defaults
```

### 3. Secrets Management

```bash
# Using Docker secrets (Swarm mode)
echo "secret_value" | docker secret create app_secret -

# Reference in compose file
secrets:
  app_secret:
    external: true

# Use in service
environment:
  SECRET_KEY_FILE: /run/secrets/app_secret
```

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database backups created
- [ ] SSL/TLS certificates ready
- [ ] Monitoring and logging configured
- [ ] Health checks verified
- [ ] Resource limits set
- [ ] Security scanning completed
- [ ] Load balancer configured

### 2. Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  postgres:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G

  redis:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 3. Restart Policies

```yaml
# Always restart
restart_policy:
  condition: any
  delay: 5s
  max_attempts: 5
  window: 120s

# Or use restart: always
restart: always
```

### 4. Logging Configuration

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service=metamaster"

# Or use syslog
logging:
  driver: "syslog"
  options:
    syslog-address: "udp://127.0.0.1:514"
    tag: "metamaster"
```

## Monitoring and Logging

### 1. View Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs api

# Follow logs
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Timestamps
docker-compose logs -t api
```

### 2. Container Metrics

```bash
# View resource usage
docker stats

# Specific container
docker stats metamaster-api

# Format output
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### 3. Prometheus Metrics

```bash
# Access metrics endpoint
curl http://localhost:8000/metrics

# Key metrics:
# - http_requests_total
# - http_request_duration_seconds
# - database_query_duration_seconds
# - celery_task_duration_seconds
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Inspect container
docker inspect metamaster-api

# Check resource limits
docker stats metamaster-api

# Rebuild image
docker-compose build --no-cache api
```

### Network Issues

```bash
# Check network
docker network ls
docker network inspect metamaster_metamaster-network

# Test connectivity
docker-compose exec api ping postgres
docker-compose exec api curl http://redis:6379

# Check DNS
docker-compose exec api nslookup postgres
```

### Volume Issues

```bash
# Check volume
docker volume inspect metamaster_postgres_data

# Check permissions
docker-compose exec postgres ls -la /var/lib/postgresql/data

# Backup and recreate
docker-compose down -v
docker-compose up -d
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check logs for errors
docker-compose logs api | grep ERROR

# Monitor database
docker-compose exec postgres psql -U metamaster -d metamaster -c "SELECT * FROM pg_stat_statements;"

# Monitor Redis
docker-compose exec redis redis-cli info stats
```

## Next Steps

1. [Local Development](DEPLOYMENT_LOCAL.md)
2. [Kubernetes Deployment](DEPLOYMENT_KUBERNETES.md)
3. [Cloud Deployment](DEPLOYMENT_CLOUD.md)
4. [Database Management](DEPLOYMENT_DATABASE.md)
5. [Security Configuration](DEPLOYMENT_SECURITY.md)
