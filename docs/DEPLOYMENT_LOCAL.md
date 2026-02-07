# Local Development Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Docker Compose Setup](#docker-compose-setup)
5. [Database Initialization](#database-initialization)
6. [Redis Setup](#redis-setup)
7. [Celery Worker Setup](#celery-worker-setup)
8. [Testing the Deployment](#testing-the-deployment)
9. [Development Workflow](#development-workflow)
10. [Troubleshooting](#troubleshooting)

## Overview

This guide provides step-by-step instructions for setting up the Metamaster application for local development using Docker Compose. This setup includes all necessary services: API, PostgreSQL, Redis, and Celery workers.

### What You'll Get
- FastAPI application running on `http://localhost:8000`
- PostgreSQL database on `localhost:5432`
- Redis cache on `localhost:6379`
- Celery worker for async tasks
- Celery Beat for scheduled tasks
- Hot-reload enabled for development

## Prerequisites

### System Requirements
- Docker 20.10+
- Docker Compose 1.29+
- Python 3.9+ (for local development)
- 4 GB RAM minimum
- 10 GB disk space

### Verify Installation

```bash
# Check Docker
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 1.29.0 or higher

# Check Python
python3 --version
# Expected: Python 3.9 or higher
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/metamaster.git
cd metamaster
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` for local development:

```env
# Application
APP_NAME=Metamaster
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://metamaster:metamaster@postgres:5432/metamaster
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_DB=1

# API Keys (use test keys)
OMDB_API_KEY=test_key_omdb
TVDB_API_KEY=test_key_tvdb

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Monitoring
SENTRY_DSN=
PROMETHEUS_ENABLED=true
```

### 3. Start Services

```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Wait for services to be ready (30-60 seconds)
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Seed initial data
docker-compose exec api python -m app.init_db
```

### 5. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

## Docker Compose Setup

### docker-compose.yml Structure

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    container_name: metamaster-postgres
    environment:
      POSTGRES_USER: metamaster
      POSTGRES_PASSWORD: metamaster
      POSTGRES_DB: metamaster
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U metamaster"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: metamaster-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: metamaster-api
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DATABASE_URL=postgresql://metamaster:metamaster@postgres:5432/metamaster
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - APP_ENV=development
      - DEBUG=true
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Celery Worker
  celery:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: metamaster-celery
    command: celery -A app.celery_app worker -l info
    environment:
      - DATABASE_URL=postgresql://metamaster:metamaster@postgres:5432/metamaster
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - APP_ENV=development
    volumes:
      - .:/app
    depends_on:
      - postgres
      - redis
      - api

  # Celery Beat (Scheduler)
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: metamaster-celery-beat
    command: celery -A app.celery_app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DATABASE_URL=postgresql://metamaster:metamaster@postgres:5432/metamaster
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - APP_ENV=development
    volumes:
      - .:/app
    depends_on:
      - postgres
      - redis
      - api

volumes:
  postgres_data:
  redis_data:
```

### Service Management

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres

# Stop all services
docker-compose down

# Stop specific service
docker-compose stop api

# View service logs
docker-compose logs -f api

# View logs for multiple services
docker-compose logs -f api postgres redis

# Restart services
docker-compose restart api

# Remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Database Initialization

### 1. Create Database

```bash
# Database is created automatically by docker-compose
# Verify connection
docker-compose exec postgres psql -U metamaster -d metamaster -c "SELECT 1;"
```

### 2. Run Migrations

```bash
# Apply all pending migrations
docker-compose exec api alembic upgrade head

# View migration history
docker-compose exec api alembic history

# Rollback one migration
docker-compose exec api alembic downgrade -1
```

### 3. Seed Initial Data

```bash
# Run initialization script
docker-compose exec api python -m app.init_db

# Verify data
docker-compose exec postgres psql -U metamaster -d metamaster -c "SELECT COUNT(*) FROM movies;"
```

### 4. Database Access

```bash
# Connect to PostgreSQL directly
docker-compose exec postgres psql -U metamaster -d metamaster

# Common queries
# List tables
\dt

# Describe table
\d movies

# Exit
\q
```

### 5. Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U metamaster metamaster > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U metamaster metamaster < backup.sql
```

## Redis Setup

### 1. Verify Redis Connection

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping
# Expected: PONG

# Check Redis info
docker-compose exec redis redis-cli info
```

### 2. Redis CLI Access

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Common commands
# Get all keys
KEYS *

# Get specific key
GET cache:movies:1

# Delete key
DEL cache:movies:1

# Flush all data
FLUSHALL

# Exit
EXIT
```

### 3. Monitor Redis

```bash
# Monitor Redis commands in real-time
docker-compose exec redis redis-cli monitor

# Check memory usage
docker-compose exec redis redis-cli info memory

# Check connected clients
docker-compose exec redis redis-cli info clients
```

## Celery Worker Setup

### 1. Start Celery Worker

```bash
# Start worker (already running in docker-compose)
docker-compose up -d celery

# View worker logs
docker-compose logs -f celery
```

### 2. Monitor Celery Tasks

```bash
# Check active tasks
docker-compose exec celery celery -A app.celery_app inspect active

# Check registered tasks
docker-compose exec celery celery -A app.celery_app inspect registered

# Check worker stats
docker-compose exec celery celery -A app.celery_app inspect stats
```

### 3. Test Celery Task

```bash
# Create a test task
curl -X POST http://localhost:8000/api/v1/tasks/test \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Check task status
curl http://localhost:8000/api/v1/tasks/{task_id}
```

### 4. Celery Beat Scheduler

```bash
# View scheduled tasks
docker-compose exec celery-beat celery -A app.celery_app inspect scheduled

# Check beat logs
docker-compose logs -f celery-beat
```

## Testing the Deployment

### 1. Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Cache health
curl http://localhost:8000/health/cache

# Expected: All return 200 OK
```

### 2. API Endpoints

```bash
# Get movies
curl http://localhost:8000/api/v1/movies

# Get TV shows
curl http://localhost:8000/api/v1/tv-shows

# Get cache stats
curl http://localhost:8000/api/v1/cache/stats

# Expected: All return 200 OK with data
```

### 3. Database Operations

```bash
# Test database query
docker-compose exec api python -c "
from app.database import SessionLocal
from app.models import Movie
db = SessionLocal()
count = db.query(Movie).count()
print(f'Total movies: {count}')
"
```

### 4. Redis Operations

```bash
# Test cache operations
docker-compose exec api python -c "
from app.services.redis_cache import RedisCache
cache = RedisCache()
cache.set('test_key', 'test_value')
value = cache.get('test_key')
print(f'Cache value: {value}')
"
```

### 5. Celery Tasks

```bash
# Test async task
curl -X POST http://localhost:8000/api/v1/tasks/process-movie \
  -H "Content-Type: application/json" \
  -d '{"movie_id": 1}'

# Check task status
curl http://localhost:8000/api/v1/tasks/{task_id}
```

### 6. Run Test Suite

```bash
# Run all tests
docker-compose exec api pytest tests/ -v

# Run specific test file
docker-compose exec api pytest tests/test_api_endpoints_integration.py -v

# Run with coverage
docker-compose exec api pytest tests/ --cov=app --cov-report=html
```

## Development Workflow

### 1. Code Changes

```bash
# Make code changes (files are mounted as volumes)
# Changes are automatically reloaded in the API container

# View logs to verify changes
docker-compose logs -f api
```

### 2. Database Changes

```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "Add new column"

# Review migration file
cat alembic/versions/004_add_new_column.py

# Apply migration
docker-compose exec api alembic upgrade head
```

### 3. Dependency Changes

```bash
# Update requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Rebuild Docker image
docker-compose build api

# Restart service
docker-compose up -d api
```

### 4. Environment Changes

```bash
# Edit .env file
nano .env

# Restart services to apply changes
docker-compose restart api celery
```

### 5. Debugging

```bash
# View detailed logs
docker-compose logs -f api --tail=100

# Execute command in container
docker-compose exec api python -c "print('debug')"

# Interactive shell
docker-compose exec api bash

# Debug with pdb
# Add breakpoint in code: breakpoint()
# Run with: docker-compose up api (not -d)
```

## Troubleshooting

### Services Won't Start

```bash
# Check service status
docker-compose ps

# View error logs
docker-compose logs api

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose down -v
docker-compose up -d
```

### Database Connection Error

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U metamaster -d metamaster -c "SELECT 1;"

# Restart database
docker-compose restart postgres
```

### Redis Connection Error

```bash
# Verify Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### API Not Responding

```bash
# Check if API container is running
docker-compose ps api

# View API logs
docker-compose logs -f api

# Check port binding
docker ps | grep metamaster-api

# Restart API
docker-compose restart api
```

### Celery Tasks Not Processing

```bash
# Check if Celery worker is running
docker-compose ps celery

# View Celery logs
docker-compose logs -f celery

# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart Celery
docker-compose restart celery
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
# ports:
#   - "8001:8000"
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a

# Remove volumes
docker-compose down -v

# Check disk usage
du -sh .

# Remove old backups
rm -f backup_*.sql
```

## Performance Optimization

### 1. Database Connection Pooling

```env
# In .env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

### 2. Redis Optimization

```bash
# Monitor Redis memory
docker-compose exec redis redis-cli info memory

# Set max memory policy
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 3. Celery Optimization

```bash
# Increase worker concurrency
docker-compose exec celery celery -A app.celery_app worker -c 4

# Use prefork pool
docker-compose exec celery celery -A app.celery_app worker --pool=prefork
```

## Next Steps

1. **Start Development**: Begin making code changes
2. **Run Tests**: Execute test suite regularly
3. **Monitor Logs**: Watch logs for issues
4. **Commit Changes**: Push to version control
5. **Deploy to Staging**: Follow [Docker Deployment Guide](DEPLOYMENT_DOCKER.md)

## Additional Resources

- [Main Deployment Guide](DEPLOYMENT.md)
- [Docker Deployment Guide](DEPLOYMENT_DOCKER.md)
- [Database Guide](DEPLOYMENT_DATABASE.md)
- [Troubleshooting Guide](DEPLOYMENT_TROUBLESHOOTING.md)
