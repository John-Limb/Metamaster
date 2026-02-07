# Deployment Troubleshooting Guide

## Table of Contents
1. [Overview](#overview)
2. [Common Deployment Issues](#common-deployment-issues)
3. [Debugging Procedures](#debugging-procedures)
4. [Log Analysis](#log-analysis)
5. [Performance Troubleshooting](#performance-troubleshooting)
6. [Health Check Procedures](#health-check-procedures)
7. [Recovery Procedures](#recovery-procedures)
8. [Monitoring and Diagnostics](#monitoring-and-diagnostics)
9. [Issue Resolution Flowchart](#issue-resolution-flowchart)
10. [Support Resources](#support-resources)

## Overview

This guide provides systematic troubleshooting procedures for common deployment issues in the Metamaster application.

### Troubleshooting Methodology

```
1. Identify the Problem
   ├─ Gather symptoms
   ├─ Check error messages
   └─ Review recent changes

2. Isolate the Issue
   ├─ Check service status
   ├─ Verify connectivity
   └─ Review logs

3. Diagnose Root Cause
   ├─ Analyze error logs
   ├─ Check resource usage
   └─ Test components

4. Implement Solution
   ├─ Apply fix
   ├─ Verify resolution
   └─ Document changes

5. Prevent Recurrence
   ├─ Update monitoring
   ├─ Add safeguards
   └─ Document lessons learned
```

## Common Deployment Issues

### 1. Service Won't Start

**Symptoms:**
- Container exits immediately
- Service fails to start
- Port already in use

**Diagnosis:**

```bash
# Check service status
systemctl status metamaster-api

# View service logs
journalctl -u metamaster-api -n 50

# Check if port is in use
lsof -i :8000
netstat -tlnp | grep 8000

# Check Docker container logs
docker logs metamaster-api
docker logs --tail=100 metamaster-api

# Check for errors
docker logs metamaster-api 2>&1 | grep -i error
```

**Solutions:**

```bash
# Solution 1: Port already in use
# Kill process using port
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or change port in configuration
# Edit .env or docker-compose.yml
API_PORT=8001

# Solution 2: Permission denied
# Fix file permissions
sudo chown -R app:app /app
sudo chmod -R 755 /app

# Solution 3: Out of memory
# Check available memory
free -h

# Increase memory limit
# In docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G

# Solution 4: Missing dependencies
# Rebuild Docker image
docker build --no-cache -t metamaster:latest .

# Or reinstall Python packages
pip install -r requirements.txt --force-reinstall
```

### 2. Database Connection Errors

**Symptoms:**
- "Connection refused" error
- "Authentication failed" error
- "Database does not exist" error

**Diagnosis:**

```bash
# Check database service status
docker-compose ps postgres
systemctl status postgresql

# Test database connectivity
psql -U metamaster -h localhost -d metamaster -c "SELECT 1;"

# Check database logs
docker logs metamaster-postgres
tail -f /var/log/postgresql/postgresql.log

# Verify connection string
echo $DATABASE_URL

# Check network connectivity
telnet localhost 5432
nc -zv localhost 5432
```

**Solutions:**

```bash
# Solution 1: Database not running
docker-compose up -d postgres
systemctl start postgresql

# Solution 2: Wrong credentials
# Verify DATABASE_URL in .env
# Format: postgresql://user:password@host:port/database

# Solution 3: Database doesn't exist
psql -U postgres -c "CREATE DATABASE metamaster;"

# Solution 4: Connection pool exhausted
# Check active connections
psql -U metamaster -d metamaster -c "SELECT COUNT(*) FROM pg_stat_activity;"

# Kill idle connections
psql -U metamaster -d metamaster -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND query_start < now() - interval '10 minutes';
"

# Solution 5: Network issue
# Check firewall
sudo ufw status
sudo iptables -L

# Allow database port
sudo ufw allow 5432/tcp
```

### 3. Redis Connection Errors

**Symptoms:**
- "Connection refused" error
- Cache operations failing
- Celery tasks not processing

**Diagnosis:**

```bash
# Check Redis service status
docker-compose ps redis
systemctl status redis-server

# Test Redis connectivity
redis-cli ping
redis-cli -h localhost -p 6379 ping

# Check Redis logs
docker logs metamaster-redis
tail -f /var/log/redis/redis-server.log

# Check Redis memory
redis-cli info memory

# Check connected clients
redis-cli info clients
```

**Solutions:**

```bash
# Solution 1: Redis not running
docker-compose up -d redis
systemctl start redis-server

# Solution 2: Wrong connection string
# Verify REDIS_URL in .env
# Format: redis://[:password]@host:port/db

# Solution 3: Out of memory
# Check memory usage
redis-cli info memory

# Increase max memory
redis-cli CONFIG SET maxmemory 1gb

# Set eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Solution 4: Authentication failed
# Check Redis password
redis-cli -a password ping

# Update connection string with password
REDIS_URL=redis://:password@localhost:6379/0

# Solution 5: Network issue
# Test connectivity
telnet localhost 6379
nc -zv localhost 6379
```

### 4. API Not Responding

**Symptoms:**
- HTTP 502 Bad Gateway
- HTTP 503 Service Unavailable
- Connection timeout

**Diagnosis:**

```bash
# Check API service status
docker-compose ps api
systemctl status metamaster-api

# Test API endpoint
curl -v http://localhost:8000/health

# Check API logs
docker logs -f metamaster-api
tail -f /var/log/metamaster/api.log

# Check resource usage
docker stats metamaster-api
top -p $(pgrep -f uvicorn)

# Check network connectivity
netstat -tlnp | grep 8000
ss -tlnp | grep 8000
```

**Solutions:**

```bash
# Solution 1: API container crashed
# Restart API
docker-compose restart api
systemctl restart metamaster-api

# Check for startup errors
docker logs metamaster-api | tail -50

# Solution 2: Out of memory
# Check memory usage
docker stats metamaster-api

# Increase memory limit
# In docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G

# Solution 3: High CPU usage
# Check for infinite loops or blocking operations
docker stats --no-stream metamaster-api

# Profile application
python -m cProfile -o profile.stats app/main.py

# Solution 4: Too many connections
# Check connection count
netstat -an | grep ESTABLISHED | wc -l

# Increase connection limits
# In /etc/security/limits.conf:
# * soft nofile 65536
# * hard nofile 65536

# Solution 5: Dependency issue
# Verify all dependencies are running
docker-compose ps

# Restart all services
docker-compose restart
```

### 5. Celery Tasks Not Processing

**Symptoms:**
- Tasks stuck in queue
- No worker logs
- Tasks timing out

**Diagnosis:**

```bash
# Check Celery worker status
docker-compose ps celery
celery -A app.celery_app inspect active

# Check task queue
redis-cli LLEN celery

# Check worker logs
docker logs -f metamaster-celery

# Check Redis connection
redis-cli ping

# Check task status
celery -A app.celery_app inspect active_queues
```

**Solutions:**

```bash
# Solution 1: Worker not running
docker-compose up -d celery
systemctl start celery

# Solution 2: Redis connection issue
# Verify Redis is running
redis-cli ping

# Check connection string
echo $CELERY_BROKER_URL

# Solution 3: Task queue full
# Check queue size
redis-cli LLEN celery

# Purge queue (WARNING: deletes tasks)
celery -A app.celery_app purge

# Solution 4: Worker crashed
# Check worker logs
docker logs metamaster-celery

# Restart worker
docker-compose restart celery

# Solution 5: Task timeout
# Increase task timeout
# In app/celery_app.py:
# app.conf.task_soft_time_limit = 600
# app.conf.task_time_limit = 900
```

## Debugging Procedures

### 1. Enable Debug Logging

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# In .env
LOG_LEVEL=DEBUG
DEBUG=true

# Restart services
docker-compose restart api

# View debug logs
docker logs -f metamaster-api | grep DEBUG
```

### 2. Add Logging to Code

```python
# In app/main.py
import logging

logger = logging.getLogger(__name__)

@app.get("/api/v1/movies")
async def get_movies():
    logger.debug("Fetching movies from database")
    try:
        movies = db.query(Movie).all()
        logger.debug(f"Found {len(movies)} movies")
        return movies
    except Exception as e:
        logger.error(f"Error fetching movies: {str(e)}", exc_info=True)
        raise
```

### 3. Interactive Debugging

```bash
# Add breakpoint in code
# In app/api/movies.py:
# breakpoint()

# Run with debugger
docker-compose up api  # Not -d

# When breakpoint is hit, use pdb commands:
# n - next line
# s - step into
# c - continue
# l - list code
# p variable - print variable
# h - help
```

### 4. Remote Debugging

```python
# In app/main.py
import pdb
import sys

@app.get("/api/v1/debug")
async def debug_endpoint():
    # Remote debugging with pdb
    pdb.Pdb(stdout=sys.stdout).set_trace()
    return {"status": "debugging"}
```

## Log Analysis

### 1. View Logs

```bash
# Docker logs
docker logs metamaster-api
docker logs -f metamaster-api  # Follow
docker logs --tail=100 metamaster-api  # Last 100 lines
docker logs --since 2024-01-15 metamaster-api  # Since date

# System logs
tail -f /var/log/metamaster/api.log
grep ERROR /var/log/metamaster/api.log
grep -i "connection refused" /var/log/metamaster/api.log

# Database logs
tail -f /var/log/postgresql/postgresql.log
grep ERROR /var/log/postgresql/postgresql.log

# Redis logs
tail -f /var/log/redis/redis-server.log
```

### 2. Parse Logs

```bash
# Extract errors
grep -i error /var/log/metamaster/api.log | head -20

# Extract warnings
grep -i warning /var/log/metamaster/api.log | head -20

# Extract specific time range
grep "2024-01-15 10:" /var/log/metamaster/api.log

# Count errors by type
grep -i error /var/log/metamaster/api.log | cut -d: -f2 | sort | uniq -c

# Find slow queries
grep "duration:" /var/log/postgresql/postgresql.log | sort -t: -k2 -rn | head -10
```

### 3. Centralized Logging

```bash
# Setup ELK Stack (Elasticsearch, Logstash, Kibana)
docker-compose up -d elasticsearch logstash kibana

# Configure application to send logs
# In app/main.py:
import logging
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

# View logs in Kibana
# http://localhost:5601
```

## Performance Troubleshooting

### 1. Slow API Responses

**Diagnosis:**

```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/movies

# Monitor in real-time
docker stats metamaster-api

# Check database query performance
psql -U metamaster -d metamaster -c "
SELECT query, calls, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

**Solutions:**

```bash
# Solution 1: Add database indexes
psql -U metamaster -d metamaster -c "
CREATE INDEX idx_movies_title ON movies(title);
CREATE INDEX idx_movies_year ON movies(year);
"

# Solution 2: Enable caching
# In app/api/movies.py:
from app.services.redis_cache import RedisCache

cache = RedisCache()

@app.get("/api/v1/movies")
async def get_movies():
    cached = cache.get("movies_list")
    if cached:
        return cached
    
    movies = db.query(Movie).all()
    cache.set("movies_list", movies, ttl=3600)
    return movies

# Solution 3: Optimize queries
# Use select() to fetch only needed columns
movies = db.query(Movie.id, Movie.title).all()

# Use join() instead of separate queries
movies = db.query(Movie).join(Director).all()

# Solution 4: Add pagination
@app.get("/api/v1/movies")
async def get_movies(skip: int = 0, limit: int = 10):
    return db.query(Movie).offset(skip).limit(limit).all()
```

### 2. High Memory Usage

**Diagnosis:**

```bash
# Check memory usage
docker stats metamaster-api
free -h

# Check memory by process
ps aux --sort=-%mem | head -10

# Check memory leaks
docker exec metamaster-api python -m memory_profiler app/main.py
```

**Solutions:**

```bash
# Solution 1: Increase memory limit
# In docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G

# Solution 2: Fix memory leaks
# Profile application
python -m memory_profiler app/main.py

# Use memory_profiler decorator
from memory_profiler import profile

@profile
def get_movies():
    movies = db.query(Movie).all()
    return movies

# Solution 3: Reduce cache size
# In app/services/redis_cache.py:
redis_client.config_set('maxmemory', '512mb')
redis_client.config_set('maxmemory-policy', 'allkeys-lru')

# Solution 4: Implement pagination
# Fetch data in chunks instead of all at once
```

### 3. High CPU Usage

**Diagnosis:**

```bash
# Check CPU usage
docker stats metamaster-api
top -p $(pgrep -f uvicorn)

# Profile CPU usage
python -m cProfile -o profile.stats app/main.py
python -m pstats profile.stats
```

**Solutions:**

```bash
# Solution 1: Optimize algorithms
# Use faster algorithms
# Avoid nested loops
# Cache expensive computations

# Solution 2: Add worker processes
# In docker-compose.yml:
# command: uvicorn app.main:app --workers 4

# Solution 3: Use async operations
# Use async/await for I/O operations
@app.get("/api/v1/movies")
async def get_movies():
    movies = await db.query(Movie).all()
    return movies

# Solution 4: Reduce query complexity
# Use select() to fetch only needed columns
# Use join() instead of separate queries
```

## Health Check Procedures

### 1. API Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-15T10:30:00Z",
#   "version": "1.0.0"
# }

# Check with verbose output
curl -v http://localhost:8000/health

# Check response time
curl -w "Response time: %{time_total}s\n" http://localhost:8000/health
```

### 2. Database Health Check

```bash
# Check database connectivity
curl http://localhost:8000/health/db

# Expected response:
# {
#   "database": "connected",
#   "response_time_ms": 5
# }

# Manual check
psql -U metamaster -d metamaster -c "SELECT 1;"
```

### 3. Cache Health Check

```bash
# Check cache connectivity
curl http://localhost:8000/health/cache

# Expected response:
# {
#   "cache": "connected",
#   "response_time_ms": 2
# }

# Manual check
redis-cli ping
```

### 4. Celery Health Check

```bash
# Check Celery worker status
celery -A app.celery_app inspect active

# Check task queue
redis-cli LLEN celery

# Check worker stats
celery -A app.celery_app inspect stats
```

## Recovery Procedures

### 1. Service Recovery

```bash
# Restart single service
docker-compose restart api
systemctl restart metamaster-api

# Restart all services
docker-compose restart
systemctl restart metamaster-*

# Rebuild and restart
docker-compose up -d --build api
```

### 2. Data Recovery

```bash
# Restore from backup
psql -U metamaster -d metamaster < backup_full.sql

# Restore specific table
psql -U metamaster -d metamaster < backup_movies.sql

# Restore Redis
redis-cli FLUSHALL
redis-cli < redis_backup.rdb
```

### 3. Full System Recovery

```bash
# 1. Stop all services
docker-compose down

# 2. Backup current data
cp -r /var/lib/postgresql/14/main /var/lib/postgresql/14/main.backup

# 3. Restore from backup
psql -U metamaster -d metamaster < backup_full.sql

# 4. Start services
docker-compose up -d

# 5. Verify recovery
curl http://localhost:8000/health
```

## Monitoring and Diagnostics

### 1. System Diagnostics

```bash
# Check system resources
free -h
df -h
top -b -n 1

# Check network connectivity
ping 8.8.8.8
traceroute example.com
netstat -tlnp

# Check DNS resolution
nslookup localhost
dig localhost
```

### 2. Application Diagnostics

```bash
# Check running processes
ps aux | grep metamaster

# Check open files
lsof -p $(pgrep -f uvicorn)

# Check network connections
netstat -an | grep ESTABLISHED | wc -l

# Check system load
uptime
```

### 3. Create Diagnostic Bundle

```bash
# Create diagnostic bundle
#!/bin/bash
BUNDLE_DIR="diagnostics_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BUNDLE_DIR

# Collect logs
docker logs metamaster-api > $BUNDLE_DIR/api.log
docker logs metamaster-postgres > $BUNDLE_DIR/postgres.log
docker logs metamaster-redis > $BUNDLE_DIR/redis.log

# Collect system info
uname -a > $BUNDLE_DIR/system.txt
free -h >> $BUNDLE_DIR/system.txt
df -h >> $BUNDLE_DIR/system.txt

# Collect network info
netstat -tlnp > $BUNDLE_DIR/network.txt
ps aux > $BUNDLE_DIR/processes.txt

# Create archive
tar -czf $BUNDLE_DIR.tar.gz $BUNDLE_DIR
echo "Diagnostic bundle created: $BUNDLE_DIR.tar.gz"
```

## Issue Resolution Flowchart

```
Start
  │
  ├─ Is service running?
  │  ├─ No → Start service → Test
  │  └─ Yes → Continue
  │
  ├─ Is database connected?
  │  ├─ No → Check database service → Verify connection string
  │  └─ Yes → Continue
  │
  ├─ Is cache connected?
  │  ├─ No → Check cache service → Verify connection string
  │  └─ Yes → Continue
  │
  ├─ Are API endpoints responding?
  │  ├─ No → Check API logs → Restart API
  │  └─ Yes → Continue
  │
  ├─ Is performance acceptable?
  │  ├─ No → Check resource usage → Optimize queries
  │  └─ Yes → Continue
  │
  └─ Issue resolved ✓
```

## Support Resources

### 1. Documentation
- [Main Deployment Guide](DEPLOYMENT.md)
- [Database Management](DEPLOYMENT_DATABASE.md)
- [Security Configuration](DEPLOYMENT_SECURITY.md)

### 2. Monitoring Tools
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Kibana: http://localhost:5601

### 3. Logging
- Application logs: `/var/log/metamaster/`
- Database logs: `/var/log/postgresql/`
- System logs: `/var/log/syslog`

### 4. Contact
- On-call engineer: [contact info]
- Incident channel: #incidents
- Documentation: [wiki link]
