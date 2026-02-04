# Media Management Web Tool - Deployment Guide

## Overview

This guide provides detailed instructions for deploying the media management web tool in various environments.

---

## Prerequisites

### System Requirements
- Docker and Docker Compose installed
- 2GB minimum RAM
- 10GB minimum disk space (for media files)
- Network connectivity for API calls

### Required API Keys
- OMDB API key (free tier available at omdbapi.com)
- TVDB API key and PIN (free tier available at thetvdb.com)

---

## Local Development Deployment

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd media-management-tool

# Create .env file from example
cp config/.env.example config/.env

# Edit .env with your API keys
nano config/.env
```

### 2. Environment Variables

```env
# Database
DATABASE_URL=sqlite:///./data/media.db

# API Keys
OMDB_API_KEY=your_omdb_key_here
TVDB_API_KEY=your_tvdb_key_here
TVDB_PIN=your_tvdb_pin_here

# File Monitoring
MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
WATCH_PATTERNS=["*.mp4", "*.mkv", "*.avi", "*.mov", "*.flv", "*.wmv"]

# Celery & Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
REDIS_URL=redis://redis:6379/2

# Logging
LOG_LEVEL=INFO
```

### 3. Start Services

```bash
# Start all services (app, Redis, Celery worker)
docker-compose up -d

# Verify services are running
docker-compose ps

# Check application logs
docker-compose logs -f app

# Check Celery worker logs
docker-compose logs -f celery-worker
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec app python -m alembic upgrade head

# Verify database is initialized
docker-compose exec app sqlite3 data/media.db ".tables"
```

### 5. Access Application

- **Web API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### 6. Verify Setup

```bash
# Test health endpoint
curl http://localhost:8000/health

# List movies (should be empty initially)
curl http://localhost:8000/api/movies

# Check Celery worker status
docker-compose exec celery-worker celery -A app.tasks.celery_app inspect active
```

---

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] API keys obtained and validated
- [ ] Media directories created and accessible
- [ ] Firewall rules configured
- [ ] SSL/TLS certificates obtained
- [ ] Backup strategy defined
- [ ] Monitoring configured
- [ ] Logging aggregation set up

### 2. Environment Configuration

**Production .env:**
```env
# Database - Use persistent volume
DATABASE_URL=sqlite:///./data/media.db

# API Keys - Use secrets management in production
OMDB_API_KEY=${OMDB_API_KEY}
TVDB_API_KEY=${TVDB_API_KEY}
TVDB_PIN=${TVDB_PIN}

# File Monitoring
MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
WATCH_PATTERNS=["*.mp4", "*.mkv", "*.avi", "*.mov", "*.flv", "*.wmv"]

# Celery & Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
REDIS_URL=redis://redis:6379/2

# Logging
LOG_LEVEL=WARNING

# Security
CORS_ORIGINS=["https://yourdomain.com"]
```

### 3. Docker Compose for Production

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: media-management-app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/media.db
      - OMDB_API_KEY=${OMDB_API_KEY}
      - TVDB_API_KEY=${TVDB_API_KEY}
      - TVDB_PIN=${TVDB_PIN}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - REDIS_URL=redis://redis:6379/2
      - MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
      - LOG_LEVEL=WARNING
    volumes:
      - ./data:/app/data
      - /media/movies:/media/movies:ro
      - /media/tv_shows:/media/tv_shows:ro
    depends_on:
      - redis
    networks:
      - media-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: media-management-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - media-network
    restart: always
    command: redis-server --appendonly yes

  celery-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: media-management-celery
    command: celery -A app.tasks.celery_app worker --loglevel=warning --concurrency=4
    environment:
      - DATABASE_URL=sqlite:///./data/media.db
      - OMDB_API_KEY=${OMDB_API_KEY}
      - TVDB_API_KEY=${TVDB_API_KEY}
      - TVDB_PIN=${TVDB_PIN}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - REDIS_URL=redis://redis:6379/2
      - MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
      - LOG_LEVEL=WARNING
    volumes:
      - ./data:/app/data
      - /media/movies:/media/movies:ro
      - /media/tv_shows:/media/tv_shows:ro
    depends_on:
      - redis
      - app
    networks:
      - media-network
    restart: always

volumes:
  redis-data:

networks:
  media-network:
    driver: bridge
```

### 4. Reverse Proxy Configuration (Nginx)

**nginx.conf:**
```nginx
upstream media_app {
    server app:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy settings
    location / {
        proxy_pass http://media_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://media_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5. Deployment Steps

```bash
# 1. SSH into production server
ssh user@production-server

# 2. Clone repository
git clone <repository-url>
cd media-management-tool

# 3. Create production .env
nano config/.env
# Add production API keys and configuration

# 4. Create data directories
mkdir -p data
chmod 755 data

# 5. Start services
docker-compose -f docker-compose.prod.yml up -d

# 6. Verify deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs app

# 7. Test health endpoint
curl https://yourdomain.com/health
```

---

## Kubernetes Deployment

### 1. Kubernetes Manifests

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: media-management-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: media-management
  template:
    metadata:
      labels:
        app: media-management
    spec:
      containers:
      - name: app
        image: media-management:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "sqlite:///./data/media.db"
        - name: OMDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: omdb
        - name: TVDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: tvdb
        - name: TVDB_PIN
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: tvdb-pin
        - name: CELERY_BROKER_URL
          value: "redis://redis:6379/0"
        - name: CELERY_RESULT_BACKEND
          value: "redis://redis:6379/1"
        - name: REDIS_URL
          value: "redis://redis:6379/2"
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: media-movies
          mountPath: /media/movies
          readOnly: true
        - name: media-tv
          mountPath: /media/tv_shows
          readOnly: true
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: media-data-pvc
      - name: media-movies
        hostPath:
          path: /media/movies
      - name: media-tv
        hostPath:
          path: /media/tv_shows
```

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: media-management-service
spec:
  selector:
    app: media-management
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace media-management

# Create secrets
kubectl create secret generic api-keys \
  --from-literal=omdb=$OMDB_API_KEY \
  --from-literal=tvdb=$TVDB_API_KEY \
  --from-literal=tvdb-pin=$TVDB_PIN \
  -n media-management

# Create PVC for data
kubectl apply -f pvc.yaml -n media-management

# Deploy application
kubectl apply -f deployment.yaml -n media-management
kubectl apply -f service.yaml -n media-management

# Verify deployment
kubectl get pods -n media-management
kubectl get svc -n media-management
```

---

## Backup & Recovery

### 1. Database Backup

```bash
# Backup SQLite database
docker-compose exec app sqlite3 data/media.db ".backup data/media.db.backup"

# Restore from backup
docker-compose exec app sqlite3 data/media.db ".restore data/media.db.backup"

# Automated daily backup
0 2 * * * docker-compose -f /path/to/docker-compose.yml exec app sqlite3 data/media.db ".backup data/media.db.$(date +\%Y\%m\%d).backup"
```

### 2. Redis Backup

```bash
# Redis automatically saves with appendonly yes
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Copy backup file
docker cp media-management-redis:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb
```

### 3. Full System Backup

```bash
# Backup entire data directory
tar -czf media-management-backup-$(date +%Y%m%d).tar.gz \
  data/ \
  config/.env

# Store backup securely
scp media-management-backup-*.tar.gz backup-server:/backups/
```

---

## Monitoring & Logging

### 1. Container Logs

```bash
# View application logs
docker-compose logs -f app

# View Celery worker logs
docker-compose logs -f celery-worker

# View Redis logs
docker-compose logs -f redis

# View logs from specific time
docker-compose logs --since 2024-01-01 app
```

### 2. Health Monitoring

```bash
# Check application health
curl http://localhost:8000/health

# Monitor container status
docker-compose ps

# Check resource usage
docker stats
```

### 3. Log Aggregation (ELK Stack)

**filebeat.yml:**
```yaml
filebeat.inputs:
- type: container
  enabled: true
  paths:
    - '/var/lib/docker/containers/*/*.log'

processors:
  - add_docker_metadata: ~

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

---

## Troubleshooting

### Common Issues

**1. Application won't start**
```bash
# Check logs
docker-compose logs app

# Verify database
docker-compose exec app sqlite3 data/media.db ".tables"

# Check environment variables
docker-compose exec app env | grep -E "OMDB|TVDB"
```

**2. File monitoring not working**
```bash
# Check file permissions
ls -la /media/movies /media/tv_shows

# Verify watch paths in config
docker-compose exec app cat config/.env | grep MEDIA_WATCH

# Check Celery worker status
docker-compose exec celery-worker celery -A app.tasks.celery_app inspect active
```

**3. API calls failing**
```bash
# Check API keys
docker-compose exec app env | grep -E "OMDB|TVDB"

# Test API connectivity
docker-compose exec app curl -I https://www.omdbapi.com/

# Check rate limiting
docker-compose logs app | grep "rate"
```

**4. Database errors**
```bash
# Check database integrity
docker-compose exec app sqlite3 data/media.db "PRAGMA integrity_check;"

# Rebuild database
docker-compose exec app rm data/media.db
docker-compose exec app python -m alembic upgrade head
```

---

## Performance Tuning

### 1. Celery Worker Optimization

```bash
# Increase worker concurrency
docker-compose exec celery-worker celery -A app.tasks.celery_app worker --concurrency=8

# Use prefork pool for CPU-bound tasks
docker-compose exec celery-worker celery -A app.tasks.celery_app worker --pool=prefork
```

### 2. Redis Optimization

```bash
# Monitor Redis memory
docker-compose exec redis redis-cli INFO memory

# Configure Redis persistence
docker-compose exec redis redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### 3. Database Optimization

```bash
# Analyze query performance
docker-compose exec app sqlite3 data/media.db "EXPLAIN QUERY PLAN SELECT * FROM movies WHERE title LIKE '%test%';"

# Rebuild indexes
docker-compose exec app sqlite3 data/media.db "REINDEX;"
```

---

## Security Hardening

### 1. Network Security

- Use firewall to restrict access to ports
- Enable SSL/TLS for all connections
- Use VPN for remote access
- Implement rate limiting on API endpoints

### 2. API Key Management

- Rotate API keys regularly
- Use environment variables (never hardcode)
- Monitor API usage for anomalies
- Implement API key expiration

### 3. Database Security

- Restrict database file permissions (600)
- Enable database encryption (if using PostgreSQL)
- Regular backups with encryption
- Test restore procedures

### 4. Container Security

- Use minimal base images
- Scan images for vulnerabilities
- Run containers as non-root user
- Implement resource limits

---

## Scaling Considerations

### 1. Horizontal Scaling

- Deploy multiple app instances behind load balancer
- Use shared Redis for caching
- Migrate to PostgreSQL for multi-instance database
- Implement distributed file locking

### 2. Vertical Scaling

- Increase Celery worker concurrency
- Increase Redis memory
- Optimize database indexes
- Implement query caching

### 3. Monitoring at Scale

- Implement distributed tracing
- Set up centralized logging
- Create performance dashboards
- Implement alerting for anomalies

---

## Maintenance

### 1. Regular Tasks

- **Daily:** Check logs for errors, verify backups
- **Weekly:** Review performance metrics, update dependencies
- **Monthly:** Rotate API keys, review security logs
- **Quarterly:** Full system audit, capacity planning

### 2. Updates

```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Update Python dependencies
docker-compose exec app pip install --upgrade -r requirements.txt

# Restart services
docker-compose restart
```

### 3. Cleanup

```bash
# Remove old backups
find ./backups -name "*.tar.gz" -mtime +30 -delete

# Clean Docker system
docker system prune -a

# Cleanup expired cache
docker-compose exec app python -m app.tasks.cleanup.cleanup_expired_cache
```

---

## Support & Documentation

- **API Documentation:** http://yourdomain.com/docs
- **GitHub Issues:** Report bugs and feature requests
- **Email Support:** support@yourdomain.com
- **Documentation:** https://docs.yourdomain.com
