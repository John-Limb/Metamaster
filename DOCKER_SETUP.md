# Docker Setup Guide

## Overview

This document provides instructions for building and running the Media Management Web Tool using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 1.29+)
- At least 2GB of available disk space
- Ports 6379, 8000 available (or modify docker-compose.yml)

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t media-tool:latest .
```

### 2. Run with Docker Compose (Production)

```bash
docker-compose up -d
```

This will start:
- **Redis** on port 6379
- **FastAPI Application** on port 8000
- **Celery Worker** (background tasks)
- **Celery Beat** (scheduled tasks)

### 3. Verify Services

Check service health:
```bash
docker-compose ps
```

Check application logs:
```bash
docker-compose logs -f app
```

Access the application:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Testing Setup

### Run Test Environment

```bash
docker-compose -f docker-compose.test.yml up -d
```

This creates an isolated test environment on:
- **Redis** on port 6380
- **FastAPI Application** on port 8001
- **Database** at `media_test.db`

### Stop Test Environment

```bash
docker-compose -f docker-compose.test.yml down
```

## Development Workflow

### 1. Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python -m app.main
```

### 2. Docker Development

```bash
# Build image
docker build -t media-tool:dev .

# Run with volume mounts for live reload
docker-compose up -d
```

Changes to files in `./app` will automatically reload the application.

## Environment Configuration

### Production Environment (.env)

```env
DATABASE_URL=sqlite:///./media.db
REDIS_URL=redis://redis:6379/0
DEBUG=False
LOG_LEVEL=INFO
```

### Test Environment

The test compose file uses:
- `DATABASE_URL=sqlite:///./media_test.db`
- `DEBUG=True`
- `LOG_LEVEL=DEBUG`

## Common Commands

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs app
docker-compose logs celery_worker

# Follow logs
docker-compose logs -f app
```

### Execute Commands in Container

```bash
# Run command in app container
docker-compose exec app python -m app.init_db

# Access shell
docker-compose exec app /bin/bash
```

### Database Operations

```bash
# Initialize database
docker-compose exec app python -m app.init_db

# Reset database
docker-compose exec app python -m app.init_db reset

# Drop database
docker-compose exec app python -m app.init_db drop
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Change port in docker-compose.yml
# Change: "8000:8000" to "8001:8000"
docker-compose up -d
```

### Redis Connection Issues

```bash
# Check Redis health
docker-compose exec redis redis-cli ping

# View Redis logs
docker-compose logs redis
```

### Database Locked

```bash
# Remove database and reinitialize
docker-compose exec app rm media.db
docker-compose exec app python -m app.init_db
```

### Container Won't Start

```bash
# View detailed logs
docker-compose logs app

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

## Performance Optimization

### Resource Limits

Edit `docker-compose.yml` to add resource limits:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Volume Performance

For better performance on macOS/Windows, use named volumes:

```yaml
volumes:
  app_data:
  redis_data:

services:
  app:
    volumes:
      - app_data:/app/data
```

## Security Considerations

### Production Deployment

1. **Change CORS settings** in `app/main.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

2. **Set DEBUG=False** in environment

3. **Use strong Redis password**:
   ```yaml
   command: redis-server --requirepass your_strong_password
   ```

4. **Use environment variables** for sensitive data:
   ```bash
   docker-compose up -d --env-file .env.production
   ```

## Monitoring

### Health Checks

The application includes health check endpoints:

```bash
# Basic health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db
```

### Logs

Logs are structured and include:
- Request IDs for tracing
- Processing times
- Error details with stack traces

View logs:
```bash
docker-compose logs -f app | grep ERROR
```

## Cleanup

### Remove All Containers and Volumes

```bash
docker-compose down -v
```

### Remove Docker Image

```bash
docker rmi media-tool:latest
```

### Clean Up Unused Resources

```bash
docker system prune -a
```

## Next Steps

1. Configure environment variables in `.env`
2. Set up media directory: `mkdir -p ./media`
3. Run `docker-compose up -d`
4. Access API at http://localhost:8000/docs
5. Monitor logs: `docker-compose logs -f`
