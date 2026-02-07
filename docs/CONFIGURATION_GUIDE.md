# Configuration Guide

This guide provides comprehensive documentation for configuring the Media Library Management System.

## Table of Contents

1. [Configuration File Overview](#configuration-file-overview)
2. [Environment Variables](#environment-variables)
3. [Database Configuration](#database-configuration)
4. [Redis Configuration](#redis-configuration)
5. [Celery Configuration](#celery-configuration)
6. [API Configuration](#api-configuration)
7. [Logging Configuration](#logging-configuration)
8. [Security Configuration](#security-configuration)

## Configuration File Overview

### Configuration Files

The system uses multiple configuration files:

- **`.env`**: Environment variables (local development)
- **`app/config.py`**: Python configuration module
- **`docker-compose.yml`**: Docker Compose configuration
- **`alembic.ini`**: Database migration configuration
- **`requirements.txt`**: Python dependencies

### Configuration Hierarchy

Configuration is loaded in this order (later overrides earlier):

1. Default values in `app/config.py`
2. Environment variables from `.env` file
3. System environment variables
4. Runtime configuration changes

### Configuration Environments

The system supports multiple environments:

- **Development**: Local development with debug enabled
- **Testing**: Test environment with test database
- **Staging**: Pre-production environment
- **Production**: Live production environment

Set the environment using:
```bash
export ENVIRONMENT=production
```

## Environment Variables

### Core Environment Variables

#### Application Settings

```bash
# Application environment
ENVIRONMENT=production  # development, testing, staging, production

# Application host and port
APP_HOST=0.0.0.0
APP_PORT=8000

# Application secret key (for session encryption)
SECRET_KEY=your-secret-key-here

# Debug mode (disable in production)
DEBUG=False

# CORS allowed origins
CORS_ORIGINS=http://localhost:3000,https://example.com
```

#### Database Configuration

```bash
# Database connection string
DATABASE_URL=postgresql://user:password@localhost:5432/media_library

# Database pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

#### Redis Configuration

```bash
# Redis connection string
REDIS_URL=redis://localhost:6379/0

# Redis settings
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_SOCKET_KEEPALIVE=True
REDIS_SOCKET_KEEPALIVE_OPTIONS={}
```

#### Celery Configuration

```bash
# Celery broker URL
CELERY_BROKER_URL=redis://localhost:6379/1

# Celery result backend
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Celery settings
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
```

#### Metadata API Keys

```bash
# OMDB API key
OMDB_API_KEY=your-omdb-api-key

# TMDB API key
TMDB_API_KEY=your-tmdb-api-key

# TVDB API key
TVDB_API_KEY=your-tvdb-api-key
```

#### File Storage

```bash
# File storage path
STORAGE_PATH=/data/media_library

# Maximum file upload size (in bytes)
MAX_UPLOAD_SIZE=104857600  # 100MB

# Allowed file extensions
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf
```

#### Logging

```bash
# Log level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Log file path
LOG_FILE=/var/log/media_library/app.log

# Log format
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Creating .env File

1. Copy the example file:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```bash
nano .env
```

3. Set appropriate values for your environment

4. Never commit `.env` to version control

## Database Configuration

### PostgreSQL Configuration

#### Connection String Format

```
postgresql://username:password@host:port/database_name
```

#### Example Configurations

**Local Development**:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/media_library_dev
```

**Docker**:
```bash
DATABASE_URL=postgresql://postgres:password@postgres:5432/media_library
```

**Production**:
```bash
DATABASE_URL=postgresql://user:secure_password@db.example.com:5432/media_library
```

### Database Connection Pool

Configure connection pooling in `.env`:

```bash
# Pool size (number of connections to keep open)
DB_POOL_SIZE=20

# Maximum overflow (additional connections when pool is full)
DB_MAX_OVERFLOW=40

# Pool timeout (seconds to wait for connection)
DB_POOL_TIMEOUT=30

# Pool recycle (recycle connections after this many seconds)
DB_POOL_RECYCLE=3600
```

### Database Initialization

Initialize the database:

```bash
# Create database
createdb media_library

# Run migrations
alembic upgrade head

# Seed initial data (optional)
python -m app.init_db
```

### Database Backup Configuration

Configure automatic backups:

```bash
# Backup location
BACKUP_PATH=/backups/media_library

# Backup schedule (cron format)
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM

# Backup retention (days)
BACKUP_RETENTION=30
```

## Redis Configuration

### Redis Connection

#### Connection String Format

```
redis://[:password]@host:port/database
```

#### Example Configurations

**Local Development**:
```bash
REDIS_URL=redis://localhost:6379/0
```

**Docker**:
```bash
REDIS_URL=redis://redis:6379/0
```

**Production with Password**:
```bash
REDIS_URL=redis://:secure_password@redis.example.com:6379/0
```

### Redis Database Numbers

The system uses multiple Redis databases:

- **Database 0**: Cache (REDIS_URL)
- **Database 1**: Celery Broker (CELERY_BROKER_URL)
- **Database 2**: Celery Results (CELERY_RESULT_BACKEND)

### Redis Configuration Options

```bash
# Socket timeout (seconds)
REDIS_SOCKET_TIMEOUT=5

# Connection timeout (seconds)
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Keep-alive enabled
REDIS_SOCKET_KEEPALIVE=True

# Keep-alive options
REDIS_SOCKET_KEEPALIVE_OPTIONS={}

# Connection pool size
REDIS_CONNECTION_POOL_SIZE=50

# Max connections
REDIS_MAX_CONNECTIONS=100
```

### Redis Cache Configuration

```bash
# Cache TTL (time-to-live in seconds)
CACHE_TTL=3600  # 1 hour

# Cache key prefix
CACHE_KEY_PREFIX=media_library:

# Cache eviction policy
CACHE_EVICTION_POLICY=allkeys-lru
```

## Celery Configuration

### Celery Broker and Backend

```bash
# Broker URL (message queue)
CELERY_BROKER_URL=redis://localhost:6379/1

# Result backend (store task results)
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Celery Task Configuration

```bash
# Task serializer
CELERY_TASK_SERIALIZER=json

# Result serializer
CELERY_RESULT_SERIALIZER=json

# Accepted content types
CELERY_ACCEPT_CONTENT=json

# Timezone
CELERY_TIMEZONE=UTC

# Task time limit (seconds)
CELERY_TASK_TIME_LIMIT=3600

# Task soft time limit (seconds)
CELERY_TASK_SOFT_TIME_LIMIT=3000
```

### Celery Worker Configuration

```bash
# Number of worker processes
CELERY_WORKER_CONCURRENCY=4

# Worker pool type
CELERY_WORKER_POOL=prefork  # prefork, solo, threads, eventlet, gevent

# Worker prefetch multiplier
CELERY_WORKER_PREFETCH_MULTIPLIER=4

# Worker max tasks per child
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
```

### Celery Beat Configuration

```bash
# Beat scheduler
CELERY_BEAT_SCHEDULER=celery.beat:PersistentScheduler

# Beat schedule database
CELERY_BEAT_SCHEDULE_FILENAME=/var/lib/celery/beat-schedule
```

### Starting Celery Workers

```bash
# Start worker
celery -A app.celery_app worker --loglevel=info

# Start beat scheduler
celery -A app.celery_app beat --loglevel=info

# Start both in one process (development only)
celery -A app.celery_app worker --beat --loglevel=info
```

## API Configuration

### API Server Settings

```bash
# API host
API_HOST=0.0.0.0

# API port
API_PORT=8000

# API base URL
API_BASE_URL=http://localhost:8000

# API version
API_VERSION=v1
```

### API Documentation

```bash
# Enable API documentation
API_DOCS_ENABLED=True

# Documentation URL
API_DOCS_URL=/docs

# ReDoc URL
API_REDOC_URL=/redoc

# OpenAPI schema URL
API_OPENAPI_URL=/openapi.json
```

### API Rate Limiting

```bash
# Enable rate limiting
RATE_LIMIT_ENABLED=True

# Rate limit (requests per minute)
RATE_LIMIT_REQUESTS=100

# Rate limit window (seconds)
RATE_LIMIT_WINDOW=60

# Rate limit storage
RATE_LIMIT_STORAGE=redis
```

### API Pagination

```bash
# Default page size
DEFAULT_PAGE_SIZE=25

# Maximum page size
MAX_PAGE_SIZE=100

# Minimum page size
MIN_PAGE_SIZE=1
```

### API Timeout

```bash
# Request timeout (seconds)
API_REQUEST_TIMEOUT=30

# Database query timeout (seconds)
DB_QUERY_TIMEOUT=30
```

## Logging Configuration

### Log Levels

```bash
# Application log level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Database log level
DB_LOG_LEVEL=WARNING

# Celery log level
CELERY_LOG_LEVEL=INFO
```

### Log Output

```bash
# Log to file
LOG_FILE=/var/log/media_library/app.log

# Log to console
LOG_CONSOLE=True

# Log format
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Log date format
LOG_DATE_FORMAT=%Y-%m-%d %H:%M:%S
```

### Log Rotation

```bash
# Log file size (bytes) before rotation
LOG_MAX_SIZE=10485760  # 10MB

# Number of backup log files to keep
LOG_BACKUP_COUNT=10

# Log rotation interval
LOG_ROTATION_INTERVAL=midnight
```

### Structured Logging

```bash
# Enable structured logging (JSON)
STRUCTURED_LOGGING=False

# Structured logging format
STRUCTURED_LOG_FORMAT=json
```

## Security Configuration

### Secret Key

```bash
# Application secret key (for session encryption)
SECRET_KEY=your-very-secure-random-key-here

# Generate a new secret key:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### CORS Configuration

```bash
# CORS allowed origins
CORS_ORIGINS=http://localhost:3000,https://example.com

# CORS allowed methods
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS

# CORS allowed headers
CORS_HEADERS=Content-Type,Authorization

# CORS allow credentials
CORS_ALLOW_CREDENTIALS=True

# CORS max age (seconds)
CORS_MAX_AGE=3600
```

### HTTPS/SSL Configuration

```bash
# Enable HTTPS
HTTPS_ENABLED=True

# SSL certificate path
SSL_CERT_PATH=/etc/ssl/certs/cert.pem

# SSL key path
SSL_KEY_PATH=/etc/ssl/private/key.pem

# SSL verify
SSL_VERIFY=True
```

### Authentication Configuration

```bash
# JWT secret key
JWT_SECRET_KEY=your-jwt-secret-key

# JWT algorithm
JWT_ALGORITHM=HS256

# JWT expiration (seconds)
JWT_EXPIRATION=3600

# Refresh token expiration (seconds)
REFRESH_TOKEN_EXPIRATION=604800  # 7 days
```

### Password Policy

```bash
# Minimum password length
PASSWORD_MIN_LENGTH=8

# Require uppercase letters
PASSWORD_REQUIRE_UPPERCASE=True

# Require lowercase letters
PASSWORD_REQUIRE_LOWERCASE=True

# Require numbers
PASSWORD_REQUIRE_NUMBERS=True

# Require special characters
PASSWORD_REQUIRE_SPECIAL=True
```

### Session Configuration

```bash
# Session timeout (seconds)
SESSION_TIMEOUT=3600

# Session cookie secure
SESSION_COOKIE_SECURE=True

# Session cookie httponly
SESSION_COOKIE_HTTPONLY=True

# Session cookie samesite
SESSION_COOKIE_SAMESITE=Lax
```

### API Key Configuration

```bash
# Enable API keys
API_KEYS_ENABLED=True

# API key header name
API_KEY_HEADER=X-API-Key

# API key length
API_KEY_LENGTH=32
```

## Configuration Examples

### Development Configuration

```bash
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://postgres:password@localhost:5432/media_library_dev
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Production Configuration

```bash
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:secure_password@db.example.com:5432/media_library
REDIS_URL=redis://:secure_password@redis.example.com:6379/0
CELERY_BROKER_URL=redis://:secure_password@redis.example.com:6379/1
HTTPS_ENABLED=True
CORS_ORIGINS=https://example.com
RATE_LIMIT_ENABLED=True
```

### Docker Configuration

```bash
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=postgresql://postgres:password@postgres:5432/media_library
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
APP_HOST=0.0.0.0
APP_PORT=8000
```

## Configuration Validation

### Validating Configuration

1. Check environment variables:
```bash
env | grep -E "^(DATABASE_|REDIS_|CELERY_|API_|LOG_)"
```

2. Test database connection:
```bash
python -c "from app.database import engine; engine.connect()"
```

3. Test Redis connection:
```bash
python -c "from app.services.redis_cache import redis_client; redis_client.ping()"
```

4. Test API startup:
```bash
python -m app.main
```

### Common Configuration Issues

#### Database Connection Failed

**Problem**: Cannot connect to database

**Solution**:
1. Verify DATABASE_URL is correct
2. Check database server is running
3. Verify credentials are correct
4. Check firewall rules

#### Redis Connection Failed

**Problem**: Cannot connect to Redis

**Solution**:
1. Verify REDIS_URL is correct
2. Check Redis server is running
3. Verify credentials if password is set
4. Check firewall rules

#### API Keys Not Working

**Problem**: Metadata sync fails with API key errors

**Solution**:
1. Verify API keys are correct
2. Check API key quotas haven't been exceeded
3. Verify API keys are enabled
4. Check API key permissions

---

For more information, see:
- [Deployment Guide](DEPLOYMENT.md)
- [Administrator Guide](ADMIN_GUIDE.md)
- [Troubleshooting Guide](USER_TROUBLESHOOTING.md)
