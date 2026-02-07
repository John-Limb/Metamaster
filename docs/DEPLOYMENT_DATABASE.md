# Database Deployment and Management Guide

## Table of Contents
1. [Overview](#overview)
2. [Database Initialization](#database-initialization)
3. [Migration Procedures](#migration-procedures)
4. [Backup and Restore](#backup-and-restore)
5. [Database Optimization](#database-optimization)
6. [Connection Pooling](#connection-pooling)
7. [Replication Setup](#replication-setup)
8. [Disaster Recovery](#disaster-recovery)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

## Overview

This guide covers PostgreSQL database deployment, management, and optimization for the Metamaster application.

### Database Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Cluster                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Primary Database                        │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ Movies Table                                   │  │   │
│  │  │ TV Shows Table                                 │  │   │
│  │  │ Tasks Table                                    │  │   │
│  │  │ Cache Table                                    │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                   │
│        ┌──────────────────┼──────────────────┐               │
│        │                  │                  │               │
│  ┌─────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐       │
│  │ Replica 1  │  │ Replica 2      │  │ Replica N  │       │
│  │ (Read-only)│  │ (Read-only)    │  │ (Read-only)│       │
│  └────────────┘  └────────────────┘  └────────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Backup Storage                          │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ Daily Backups (30 days retention)              │  │   │
│  │  │ Weekly Backups (12 weeks retention)            │  │   │
│  │  │ Monthly Backups (12 months retention)          │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Database Initialization

### 1. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# Create database
CREATE DATABASE metamaster
  WITH
  ENCODING = 'UTF8'
  LC_COLLATE = 'en_US.UTF-8'
  LC_CTYPE = 'en_US.UTF-8'
  TEMPLATE = template0;

# Create user
CREATE USER metamaster WITH PASSWORD 'secure_password_here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE metamaster TO metamaster;

# Connect to database
\c metamaster

# Grant schema privileges
GRANT ALL ON SCHEMA public TO metamaster;

# Exit
\q
```

### 2. Initialize Schema

```bash
# Run migrations
alembic upgrade head

# Verify tables
psql -U metamaster -d metamaster -c "\dt"

# Expected output:
# Schema |       Name        | Type  |   Owner
# --------+-------------------+-------+-----------
# public | movies            | table | metamaster
# public | tv_shows          | table | metamaster
# public | tasks             | table | metamaster
# public | cache             | table | metamaster
```

### 3. Seed Initial Data

```bash
# Run initialization script
python -m app.init_db

# Verify data
psql -U metamaster -d metamaster -c "SELECT COUNT(*) FROM movies;"
```

### 4. Create Indexes

```bash
# Create indexes for performance
psql -U metamaster -d metamaster << EOF
CREATE INDEX idx_movies_title ON movies(title);
CREATE INDEX idx_movies_year ON movies(year);
CREATE INDEX idx_tv_shows_title ON tv_shows(title);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_cache_key ON cache(key);
CREATE INDEX idx_cache_expires_at ON cache(expires_at);
EOF

# Verify indexes
psql -U metamaster -d metamaster -c "\di"
```

## Migration Procedures

### 1. Create Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Add new column to movies"

# Review migration file
cat alembic/versions/004_add_new_column.py

# Expected structure:
# def upgrade():
#     op.add_column('movies', sa.Column('new_column', sa.String(), nullable=True))
#
# def downgrade():
#     op.drop_column('movies', 'new_column')
```

### 2. Apply Migration

```bash
# Apply single migration
alembic upgrade +1

# Apply all pending migrations
alembic upgrade head

# Apply to specific version
alembic upgrade 003_add_batch_operations

# View current version
alembic current

# View migration history
alembic history
```

### 3. Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 002_add_database_indexes

# Rollback all migrations
alembic downgrade base
```

### 4. Zero-Downtime Migrations

```bash
# For large tables, use online migrations
# 1. Add column with default value
alembic revision --autogenerate -m "Add column with default"

# 2. Backfill data in batches
psql -U metamaster -d metamaster << EOF
UPDATE movies SET new_column = 'default_value' 
WHERE new_column IS NULL 
LIMIT 1000;
EOF

# 3. Add NOT NULL constraint
alembic revision --autogenerate -m "Add NOT NULL constraint"

# 4. Apply migration
alembic upgrade head
```

## Backup and Restore

### 1. Full Database Backup

```bash
# Backup entire database
pg_dump -U metamaster -h localhost -d metamaster > backup_full.sql

# Backup with compression
pg_dump -U metamaster -h localhost -d metamaster | gzip > backup_full.sql.gz

# Backup with custom format (faster restore)
pg_dump -U metamaster -h localhost -d metamaster -Fc > backup_full.dump

# Backup specific table
pg_dump -U metamaster -h localhost -d metamaster -t movies > backup_movies.sql
```

### 2. Restore from Backup

```bash
# Restore from SQL backup
psql -U metamaster -h localhost -d metamaster < backup_full.sql

# Restore from compressed backup
gunzip -c backup_full.sql.gz | psql -U metamaster -h localhost -d metamaster

# Restore from custom format
pg_restore -U metamaster -h localhost -d metamaster backup_full.dump

# Restore specific table
psql -U metamaster -h localhost -d metamaster < backup_movies.sql
```

### 3. Point-in-Time Recovery

```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal_archive/%f'

# Backup base
pg_basebackup -U metamaster -h localhost -D /backup/base -Fp -Pv

# Restore to specific time
# 1. Stop PostgreSQL
# 2. Copy base backup
# 3. Create recovery.conf
cat > /var/lib/postgresql/14/main/recovery.conf << EOF
restore_command = 'cp /backup/wal_archive/%f %p'
recovery_target_time = '2024-01-15 10:30:00'
recovery_target_timeline = 'latest'
EOF

# 4. Start PostgreSQL
```

### 4. Automated Backups

```bash
# Create backup script
cat > /usr/local/bin/backup_metamaster.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/metamaster"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

pg_dump -U metamaster -h localhost -d metamaster | gzip > $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
EOF

chmod +x /usr/local/bin/backup_metamaster.sh

# Schedule with cron
crontab -e
# Add: 0 2 * * * /usr/local/bin/backup_metamaster.sh
```

## Database Optimization

### 1. Query Optimization

```bash
# Analyze query performance
EXPLAIN ANALYZE SELECT * FROM movies WHERE title LIKE '%test%';

# Expected output shows execution plan and actual time

# Optimize slow queries
CREATE INDEX idx_movies_title_gin ON movies USING GIN(to_tsvector('english', title));

# Use optimized query
SELECT * FROM movies WHERE to_tsvector('english', title) @@ plainto_tsquery('english', 'test');
```

### 2. Vacuum and Analyze

```bash
# Vacuum database (remove dead rows)
VACUUM ANALYZE;

# Vacuum specific table
VACUUM ANALYZE movies;

# Full vacuum (locks table)
VACUUM FULL movies;

# Autovacuum configuration
ALTER TABLE movies SET (autovacuum_vacuum_scale_factor = 0.01);
ALTER TABLE movies SET (autovacuum_analyze_scale_factor = 0.005);
```

### 3. Statistics

```bash
# Update table statistics
ANALYZE movies;

# View table statistics
SELECT * FROM pg_stat_user_tables WHERE relname = 'movies';

# View index statistics
SELECT * FROM pg_stat_user_indexes WHERE relname = 'idx_movies_title';

# View query statistics (requires pg_stat_statements)
SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### 4. Configuration Tuning

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Key settings:
# shared_buffers = 256MB (25% of RAM)
# effective_cache_size = 1GB (50-75% of RAM)
# work_mem = 16MB (RAM / max_connections / 2)
# maintenance_work_mem = 64MB
# random_page_cost = 1.1 (for SSD)
# effective_io_concurrency = 200 (for SSD)

# Reload configuration
sudo systemctl reload postgresql
```

## Connection Pooling

### 1. PgBouncer Setup

```bash
# Install PgBouncer
sudo apt-get install pgbouncer

# Configure pgbouncer.ini
sudo nano /etc/pgbouncer/pgbouncer.ini

# Configuration:
[databases]
metamaster = host=localhost port=5432 dbname=metamaster

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
max_user_connections = 100

# Start PgBouncer
sudo systemctl start pgbouncer

# Connect through PgBouncer
psql -U metamaster -h localhost -p 6432 -d metamaster
```

### 2. Application Connection Pooling

```python
# In app/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
```

### 3. Monitor Connections

```bash
# View active connections
psql -U metamaster -d metamaster -c "SELECT * FROM pg_stat_activity;"

# View connection limits
psql -U metamaster -d metamaster -c "SHOW max_connections;"

# Kill idle connections
psql -U metamaster -d metamaster -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND query_start < now() - interval '10 minutes';
"
```

## Replication Setup

### 1. Primary-Replica Replication

```bash
# On Primary: Enable replication
sudo nano /etc/postgresql/14/main/postgresql.conf

# Settings:
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB

# Create replication user
psql -U postgres -c "
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';
"

# Reload configuration
sudo systemctl reload postgresql
```

### 2. Setup Replica

```bash
# On Replica: Stop PostgreSQL
sudo systemctl stop postgresql

# Backup primary data
pg_basebackup -h primary_host -D /var/lib/postgresql/14/main -U replicator -v -P

# Create standby.signal
touch /var/lib/postgresql/14/main/standby.signal

# Configure recovery
cat > /var/lib/postgresql/14/main/postgresql.auto.conf << EOF
primary_conninfo = 'host=primary_host port=5432 user=replicator password=replicator_password'
EOF

# Start replica
sudo systemctl start postgresql

# Verify replication
psql -U postgres -c "SELECT * FROM pg_stat_replication;"
```

### 3. Failover Procedure

```bash
# On Replica: Promote to primary
psql -U postgres -c "SELECT pg_promote();"

# Verify promotion
psql -U postgres -c "SELECT pg_is_in_recovery();"
# Should return: f (false)

# Update application connection string to new primary
# Restart application
```

## Disaster Recovery

### 1. RTO/RPO Targets

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single server failure | 1 hour | 1 hour |
| Data corruption | 4 hours | 1 hour |
| Complete data loss | 24 hours | 1 day |
| Regional failure | 4 hours | 1 hour |

### 2. Disaster Recovery Plan

```bash
# 1. Regular backups
# - Daily full backups
# - Hourly incremental backups
# - WAL archiving

# 2. Backup verification
# - Monthly restore tests
# - Document restore procedures
# - Test failover procedures

# 3. Monitoring
# - Monitor backup completion
# - Alert on backup failures
# - Monitor replication lag

# 4. Documentation
# - Keep runbooks updated
# - Document recovery procedures
# - Test procedures regularly
```

### 3. Recovery Procedures

```bash
# Scenario 1: Single table corruption
# 1. Identify corruption
SELECT * FROM movies WHERE id = 123;

# 2. Restore from backup
pg_restore -U metamaster -d metamaster -t movies backup_full.dump

# Scenario 2: Complete database loss
# 1. Create new database
CREATE DATABASE metamaster;

# 2. Restore from backup
pg_restore -U metamaster -d metamaster backup_full.dump

# 3. Verify data
SELECT COUNT(*) FROM movies;
```

## Monitoring

### 1. Database Health

```bash
# Check database size
psql -U metamaster -d metamaster -c "
SELECT pg_size_pretty(pg_database_size('metamaster'));
"

# Check table sizes
psql -U metamaster -d metamaster -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema') 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Check index sizes
psql -U metamaster -d metamaster -c "
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid)) 
FROM pg_indexes 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema') 
ORDER BY pg_relation_size(indexrelid) DESC;
"
```

### 2. Performance Metrics

```bash
# Slow queries
psql -U metamaster -d metamaster -c "
SELECT query, calls, mean_time, max_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Cache hit ratio
psql -U metamaster -d metamaster -c "
SELECT 
  sum(heap_blks_read) as heap_read, 
  sum(heap_blks_hit) as heap_hit, 
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio 
FROM pg_statio_user_tables;
"

# Transaction rate
psql -U metamaster -d metamaster -c "
SELECT 
  xact_commit, 
  xact_rollback, 
  xact_commit / (xact_commit + xact_rollback) as commit_ratio 
FROM pg_stat_database 
WHERE datname = 'metamaster';
"
```

### 3. Alerts

```bash
# Setup monitoring alerts
# - Database size > 80% of allocated
# - Replication lag > 1 minute
# - Cache hit ratio < 90%
# - Slow queries > 1 second
# - Connection count > 80% of max
# - Backup failure
```

## Troubleshooting

### 1. Connection Issues

```bash
# Test connection
psql -U metamaster -h localhost -d metamaster -c "SELECT 1;"

# Check connection limits
psql -U postgres -c "SHOW max_connections;"

# View active connections
psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Kill specific connection
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = 12345;"
```

### 2. Performance Issues

```bash
# Identify slow queries
psql -U metamaster -d metamaster -c "
SELECT query, calls, mean_time 
FROM pg_stat_statements 
WHERE mean_time > 1000 
ORDER BY mean_time DESC;
"

# Analyze query plan
EXPLAIN ANALYZE SELECT * FROM movies WHERE title LIKE '%test%';

# Create missing indexes
CREATE INDEX idx_movies_title ON movies(title);

# Vacuum and analyze
VACUUM ANALYZE;
```

### 3. Replication Issues

```bash
# Check replication status
psql -U postgres -c "SELECT * FROM pg_stat_replication;"

# Check replica lag
psql -U postgres -c "SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;"

# Restart replication
psql -U postgres -c "SELECT pg_wal_replay_resume();"
```

### 4. Disk Space Issues

```bash
# Check disk usage
df -h /var/lib/postgresql

# Check WAL archive size
du -sh /backup/wal_archive

# Clean old WAL files
psql -U postgres -c "SELECT pg_wal_keep_size = '1GB';"

# Vacuum to reclaim space
VACUUM FULL;
```

## Next Steps

1. [Main Deployment Guide](DEPLOYMENT.md)
2. [Backup and Recovery Guide](DEPLOYMENT_BACKUP_RECOVERY.md)
3. [Security Configuration](DEPLOYMENT_SECURITY.md)
4. [Troubleshooting Guide](DEPLOYMENT_TROUBLESHOOTING.md)
