# Health Check Endpoints Documentation

## Overview

The Health Check API provides endpoints for monitoring the health and status of the application and its dependencies. These endpoints are essential for load balancers, monitoring systems, and deployment orchestration.

**Base URL:** `/health`

---

## Table of Contents

1. [Basic Health Check](#basic-health-check)
2. [Database Health Check](#database-health-check)

---

## Basic Health Check

Retrieve the basic health status of the application.

### Endpoint

```
GET /health
```

### Query Parameters

None

### Request Example

```bash
curl -X GET "http://localhost:8000/health"
```

### Response (200 OK)

```json
{
  "status": "healthy",
  "message": "Application is running"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Health status (healthy, unhealthy) |
| `message` | string | Status message |

### Status Values

| Status | Description | HTTP Code |
|--------|-------------|-----------|
| `healthy` | Application is running normally | 200 |
| `unhealthy` | Application has issues | 503 |

### Use Cases

- **Load Balancer Health Checks**: Verify application is running
- **Kubernetes Liveness Probe**: Detect if pod should be restarted
- **Monitoring Systems**: Track application availability
- **Deployment Verification**: Confirm successful deployment

### Example: Kubernetes Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Example: Kubernetes Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

---

## Database Health Check

Retrieve the health status of the database connection.

### Endpoint

```
GET /health/db
```

### Query Parameters

None

### Request Example

```bash
curl -X GET "http://localhost:8000/health/db"
```

### Response (200 OK) - Healthy

```json
{
  "status": "healthy",
  "message": "Database connection is working"
}
```

### Response (503 Service Unavailable) - Unhealthy

```json
{
  "status": "unhealthy",
  "message": "Database connection failed: Connection refused"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Health status (healthy, unhealthy) |
| `message` | string | Status message or error details |

### Status Values

| Status | Description | HTTP Code |
|--------|-------------|-----------|
| `healthy` | Database connection is working | 200 |
| `unhealthy` | Database connection failed | 503 |

### Common Error Messages

| Message | Cause | Solution |
|---------|-------|----------|
| Connection refused | Database server not running | Start database server |
| Connection timeout | Database unreachable | Check network connectivity |
| Authentication failed | Invalid credentials | Verify database credentials |
| Database does not exist | Database not created | Create database |
| Connection pool exhausted | Too many connections | Increase pool size or reduce load |

### Use Cases

- **Dependency Health Checks**: Verify database availability
- **Kubernetes Startup Probe**: Wait for database before starting
- **Monitoring Systems**: Track database connectivity
- **Troubleshooting**: Diagnose connection issues

### Example: Kubernetes Startup Probe

```yaml
startupProbe:
  httpGet:
    path: /health/db
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 30
```

---

## Health Check Patterns

### Pattern 1: Simple Availability Check

```bash
#!/bin/bash

# Check if application is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
  echo "Application is healthy"
  exit 0
else
  echo "Application is unhealthy"
  exit 1
fi
```

### Pattern 2: Comprehensive Health Check

```bash
#!/bin/bash

# Check application health
APP_HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status')
if [ "$APP_HEALTH" != "healthy" ]; then
  echo "Application is unhealthy"
  exit 1
fi

# Check database health
DB_HEALTH=$(curl -s http://localhost:8000/health/db | jq -r '.status')
if [ "$DB_HEALTH" != "healthy" ]; then
  echo "Database is unhealthy"
  exit 1
fi

echo "All systems healthy"
exit 0
```

### Pattern 3: Monitoring with Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'media-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/health'
```

### Pattern 4: Docker Health Check

```dockerfile
FROM python:3.11

# ... application setup ...

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

---

## Monitoring Integration

### Prometheus Metrics

While the health endpoints don't directly expose Prometheus metrics, they can be used with monitoring systems:

```bash
# Example: Monitor health check response time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### Grafana Dashboard

Create a Grafana dashboard to monitor health checks:

```json
{
  "dashboard": {
    "title": "API Health Status",
    "panels": [
      {
        "title": "Application Health",
        "targets": [
          {
            "expr": "up{job='media-api'}"
          }
        ]
      },
      {
        "title": "Database Health",
        "targets": [
          {
            "expr": "up{job='media-api-db'}"
          }
        ]
      }
    ]
  }
}
```

### Alert Rules

Set up alerting for health check failures:

```yaml
# alert-rules.yml
groups:
  - name: api-health
    rules:
      - alert: APIUnhealthy
        expr: up{job='media-api'} == 0
        for: 5m
        annotations:
          summary: "API is unhealthy"
          
      - alert: DatabaseUnhealthy
        expr: up{job='media-api-db'} == 0
        for: 5m
        annotations:
          summary: "Database is unhealthy"
```

---

## Load Balancer Configuration

### Nginx

```nginx
upstream api_backend {
  server localhost:8000;
  server localhost:8001;
  server localhost:8002;
}

server {
  listen 80;
  server_name api.example.com;

  location / {
    proxy_pass http://api_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}

# Health check configuration
upstream api_health {
  server localhost:8000;
  check interval=3000 rise=2 fall=5 timeout=1000 type=http;
  check_http_send "GET /health HTTP/1.0\r\n\r\n";
  check_http_expect_alive http_2xx;
}
```

### HAProxy

```haproxy
global
  log stdout local0
  log stdout local1 notice

defaults
  log     global
  mode    http
  option  httplog
  option  dontlognull
  timeout connect 5000
  timeout client  50000
  timeout server  50000

frontend api_frontend
  bind *:80
  default_backend api_backend

backend api_backend
  balance roundrobin
  option httpchk GET /health
  server api1 localhost:8000 check
  server api2 localhost:8001 check
  server api3 localhost:8002 check
```

---

## Deployment Orchestration

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    image: media-api:latest
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: media_db
      POSTGRES_PASSWORD: password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: media-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: media-api
  template:
    metadata:
      labels:
        app: media-api
    spec:
      containers:
      - name: api
        image: media-api:latest
        ports:
        - containerPort: 8000
        
        # Liveness probe - restart if unhealthy
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Readiness probe - remove from load balancer if not ready
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        # Startup probe - wait for startup before other probes
        startupProbe:
          httpGet:
            path: /health/db
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30
```

---

## Monitoring Best Practices

### 1. Check Frequency

- **Liveness Probe**: Every 10-30 seconds
- **Readiness Probe**: Every 5-10 seconds
- **Startup Probe**: Every 10 seconds until success

### 2. Timeout Configuration

- **Liveness Probe**: 5-10 seconds
- **Readiness Probe**: 3-5 seconds
- **Startup Probe**: 5 seconds

### 3. Failure Thresholds

- **Liveness Probe**: 3 failures
- **Readiness Probe**: 2 failures
- **Startup Probe**: 30 failures

### 4. Alerting

- Alert on 3+ consecutive health check failures
- Alert on database connectivity issues
- Alert on response time degradation

### 5. Logging

- Log all health check requests
- Log failures with error details
- Monitor health check response times

---

## Troubleshooting

### Application Health Check Fails

**Symptoms**: `/health` returns 503 or connection refused

**Solutions**:
1. Verify application is running: `ps aux | grep python`
2. Check application logs: `docker logs <container_id>`
3. Verify port is listening: `netstat -tlnp | grep 8000`
4. Check firewall rules: `sudo ufw status`

### Database Health Check Fails

**Symptoms**: `/health/db` returns 503

**Solutions**:
1. Verify database is running: `docker ps | grep postgres`
2. Check database logs: `docker logs <db_container_id>`
3. Verify connection string: Check `DATABASE_URL` environment variable
4. Test connection manually: `psql -U user -d database -h localhost`
5. Check database credentials: Verify username and password

### Intermittent Health Check Failures

**Symptoms**: Health checks occasionally fail

**Solutions**:
1. Increase timeout values
2. Reduce check frequency
3. Increase failure threshold
4. Check system resources (CPU, memory)
5. Review application logs for errors

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [Deployment Guide](../plans/DEPLOYMENT_GUIDE.md)
- [Docker Setup](../DOCKER_SETUP.md)
- [Architecture](../plans/ARCHITECTURE.md)
