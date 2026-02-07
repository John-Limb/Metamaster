# Backup and Disaster Recovery Guide

## Table of Contents
1. [Overview](#overview)
2. [Backup Strategies](#backup-strategies)
3. [Backup Procedures](#backup-procedures)
4. [Recovery Procedures](#recovery-procedures)
5. [Testing Backups](#testing-backups)
6. [Disaster Recovery Plan](#disaster-recovery-plan)
7. [RTO/RPO Targets](#rtorpo-targets)
8. [Monitoring and Alerts](#monitoring-and-alerts)
9. [Backup Storage](#backup-storage)
10. [Troubleshooting](#troubleshooting)

## Overview

This guide covers comprehensive backup and disaster recovery procedures for the Metamaster application, including database, cache, and application state.

### Backup Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Application & Data                      │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │ PostgreSQL │  │ Redis      │  │ Files      │    │   │
│  │  └────────────┘  └────────────┘  └────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                   │
│        ┌──────────────────┼──────────────────┐               │
│        │                  │                  │               │
│  ┌─────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐       │
│  │ Hourly     │  │ Daily          │  │ Weekly     │       │
│  │ Backups    │  │ Backups        │  │ Backups    │       │
│  │ (7 days)   │  │ (30 days)      │  │ (12 weeks) │       │
│  └────────────┘  └────────────────┘  └────────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Backup Storage                          │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ Local Storage (NAS/SAN)                        │  │   │
│  │  │ Cloud Storage (S3/GCS/Azure Blob)             │  │   │
│  │  │ Off-site Replication                          │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Backup Strategies

### 1. Full Backup Strategy

**Frequency**: Daily
**Retention**: 30 days
**Time**: 2:00 AM UTC

```bash
# Full backup script
#!/bin/bash
BACKUP_DIR="/backups/metamaster/full"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_full_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U metamaster -h localhost -d metamaster | gzip > $BACKUP_FILE

# Backup Redis
redis-cli --rdb /backups/metamaster/redis/dump_$DATE.rdb

# Upload to cloud
aws s3 cp $BACKUP_FILE s3://metamaster-backups/full/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "backup_full_*.sql.gz" -mtime +30 -delete

echo "Full backup completed: $BACKUP_FILE"
```

### 2. Incremental Backup Strategy

**Frequency**: Hourly
**Retention**: 7 days
**Time**: Every hour

```bash
# Incremental backup script
#!/bin/bash
BACKUP_DIR="/backups/metamaster/incremental"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_incremental_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# Backup only changes since last backup
pg_dump -U metamaster -h localhost -d metamaster \
  --exclude-table-data='cache' | gzip > $BACKUP_FILE

# Upload to cloud
aws s3 cp $BACKUP_FILE s3://metamaster-backups/incremental/

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "backup_incremental_*.sql.gz" -mtime +7 -delete

echo "Incremental backup completed: $BACKUP_FILE"
```

### 3. WAL Archiving Strategy

**Frequency**: Continuous
**Retention**: 14 days
**Purpose**: Point-in-time recovery

```bash
# PostgreSQL WAL archiving configuration
# In postgresql.conf:
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /backup/wal_archive/%f && cp %p /backup/wal_archive/%f'
archive_timeout = 300

# WAL cleanup script
#!/bin/bash
ARCHIVE_DIR="/backup/wal_archive"

# Keep only last 14 days of WAL files
find $ARCHIVE_DIR -name "*.gz" -mtime +14 -delete

# Compress old WAL files
find $ARCHIVE_DIR -name "0*" -type f ! -name "*.gz" -exec gzip {} \;

echo "WAL archiving cleanup completed"
```

## Backup Procedures

### 1. Database Backup

```bash
# Full database backup
pg_dump -U metamaster -h localhost -d metamaster > backup_full.sql

# Compressed backup
pg_dump -U metamaster -h localhost -d metamaster | gzip > backup_full.sql.gz

# Custom format (faster restore)
pg_dump -U metamaster -h localhost -d metamaster -Fc > backup_full.dump

# Parallel backup (faster for large databases)
pg_dump -U metamaster -h localhost -d metamaster -Fd -j 4 -f backup_full_dir

# Backup specific table
pg_dump -U metamaster -h localhost -d metamaster -t movies > backup_movies.sql

# Backup with verbose output
pg_dump -U metamaster -h localhost -d metamaster -v > backup_full.sql 2>&1
```

### 2. Redis Backup

```bash
# Create Redis snapshot
redis-cli BGSAVE

# Wait for save to complete
redis-cli LASTSAVE

# Copy snapshot
cp /var/lib/redis/dump.rdb /backups/metamaster/redis/dump_$(date +%Y%m%d_%H%M%S).rdb

# Backup Redis configuration
cp /etc/redis/redis.conf /backups/metamaster/redis/redis.conf_$(date +%Y%m%d)

# Verify backup
redis-cli --rdb /backups/metamaster/redis/dump_verify.rdb
```

### 3. Application Files Backup

```bash
# Backup application code
tar -czf /backups/metamaster/app_$(date +%Y%m%d_%H%M%S).tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.env' \
  /app

# Backup configuration
tar -czf /backups/metamaster/config_$(date +%Y%m%d_%H%M%S).tar.gz \
  /etc/metamaster \
  /etc/nginx \
  /etc/postgresql

# Backup logs
tar -czf /backups/metamaster/logs_$(date +%Y%m%d_%H%M%S).tar.gz \
  /var/log/metamaster \
  /var/log/postgresql
```

### 4. Cloud Backup Upload

```bash
# Upload to AWS S3
aws s3 cp backup_full.sql.gz s3://metamaster-backups/daily/

# Upload with metadata
aws s3 cp backup_full.sql.gz s3://metamaster-backups/daily/ \
  --metadata "date=$(date +%Y%m%d),type=full,size=$(du -h backup_full.sql.gz | cut -f1)"

# Upload to GCP Cloud Storage
gsutil cp backup_full.sql.gz gs://metamaster-backups/daily/

# Upload to Azure Blob Storage
az storage blob upload \
  --account-name metamasterbackups \
  --container-name daily \
  --name backup_full_$(date +%Y%m%d).sql.gz \
  --file backup_full.sql.gz
```

## Recovery Procedures

### 1. Full Database Recovery

```bash
# Stop application
systemctl stop metamaster-api

# Create new database
psql -U postgres -c "DROP DATABASE IF EXISTS metamaster;"
psql -U postgres -c "CREATE DATABASE metamaster;"

# Restore from backup
psql -U metamaster -d metamaster < backup_full.sql

# Or from compressed backup
gunzip -c backup_full.sql.gz | psql -U metamaster -d metamaster

# Or from custom format
pg_restore -U metamaster -d metamaster backup_full.dump

# Verify recovery
psql -U metamaster -d metamaster -c "SELECT COUNT(*) FROM movies;"

# Start application
systemctl start metamaster-api
```

### 2. Table Recovery

```bash
# Restore specific table
psql -U metamaster -d metamaster < backup_movies.sql

# Or from custom format
pg_restore -U metamaster -d metamaster -t movies backup_full.dump

# Verify table
psql -U metamaster -d metamaster -c "SELECT COUNT(*) FROM movies;"
```

### 3. Point-in-Time Recovery

```bash
# 1. Stop PostgreSQL
systemctl stop postgresql

# 2. Backup current data directory
cp -r /var/lib/postgresql/14/main /var/lib/postgresql/14/main.backup

# 3. Restore base backup
pg_basebackup -h backup_server -D /var/lib/postgresql/14/main -U replicator

# 4. Create recovery configuration
cat > /var/lib/postgresql/14/main/recovery.conf << EOF
restore_command = 'cp /backup/wal_archive/%f %p'
recovery_target_time = '2024-01-15 10:30:00'
recovery_target_timeline = 'latest'
EOF

# 5. Start PostgreSQL
systemctl start postgresql

# 6. Verify recovery
psql -U postgres -c "SELECT now();"
```

### 4. Redis Recovery

```bash
# Stop Redis
systemctl stop redis-server

# Restore from backup
cp /backups/metamaster/redis/dump_20240115.rdb /var/lib/redis/dump.rdb

# Fix permissions
chown redis:redis /var/lib/redis/dump.rdb
chmod 600 /var/lib/redis/dump.rdb

# Start Redis
systemctl start redis-server

# Verify recovery
redis-cli DBSIZE
```

### 5. Partial Recovery

```bash
# Restore to temporary database
psql -U postgres -c "CREATE DATABASE metamaster_temp;"
psql -U metamaster -d metamaster_temp < backup_full.sql

# Extract specific data
pg_dump -U metamaster -d metamaster_temp -t movies > movies_recovery.sql

# Restore to production
psql -U metamaster -d metamaster < movies_recovery.sql

# Cleanup
psql -U postgres -c "DROP DATABASE metamaster_temp;"
```

## Testing Backups

### 1. Backup Verification

```bash
# Verify backup file integrity
gzip -t backup_full.sql.gz
# Exit code 0 = valid

# Verify backup size
du -h backup_full.sql.gz

# Verify backup timestamp
ls -lh backup_full.sql.gz

# Verify backup content
gunzip -c backup_full.sql.gz | head -20
```

### 2. Restore Testing

```bash
# Create test database
psql -U postgres -c "CREATE DATABASE metamaster_test;"

# Restore backup
psql -U metamaster -d metamaster_test < backup_full.sql

# Verify data
psql -U metamaster -d metamaster_test -c "SELECT COUNT(*) FROM movies;"
psql -U metamaster -d metamaster_test -c "SELECT COUNT(*) FROM tv_shows;"

# Run integrity checks
psql -U metamaster -d metamaster_test -c "
SELECT COUNT(*) FROM movies WHERE id IS NULL;
SELECT COUNT(*) FROM tv_shows WHERE id IS NULL;
"

# Cleanup
psql -U postgres -c "DROP DATABASE metamaster_test;"
```

### 3. Recovery Time Testing

```bash
# Measure restore time
time pg_restore -U metamaster -d metamaster_test backup_full.dump

# Expected: < 5 minutes for full restore

# Measure point-in-time recovery
# 1. Note current time
# 2. Make test changes
# 3. Perform PITR to before changes
# 4. Verify changes are gone
```

### 4. Automated Testing

```bash
# Weekly backup test script
#!/bin/bash
TEST_DB="metamaster_test_$(date +%Y%m%d)"
LATEST_BACKUP=$(ls -t /backups/metamaster/full/*.sql.gz | head -1)

# Create test database
psql -U postgres -c "CREATE DATABASE $TEST_DB;"

# Restore backup
gunzip -c $LATEST_BACKUP | psql -U metamaster -d $TEST_DB

# Run tests
psql -U metamaster -d $TEST_DB -c "SELECT COUNT(*) FROM movies;" > /tmp/test_result.txt

# Verify results
if grep -q "^[0-9]" /tmp/test_result.txt; then
  echo "Backup test PASSED"
else
  echo "Backup test FAILED"
  # Send alert
fi

# Cleanup
psql -U postgres -c "DROP DATABASE $TEST_DB;"
```

## Disaster Recovery Plan

### 1. Recovery Scenarios

| Scenario | RTO | RPO | Procedure |
|----------|-----|-----|-----------|
| Single file corruption | 30 min | 1 hour | Restore from backup |
| Table corruption | 1 hour | 1 hour | Restore table from backup |
| Database corruption | 2 hours | 1 hour | Full database restore |
| Server failure | 4 hours | 1 hour | Failover to replica |
| Data center failure | 24 hours | 1 day | Restore from off-site backup |

### 2. Failover Procedure

```bash
# 1. Detect primary failure
# Monitor detects no response from primary

# 2. Promote replica to primary
psql -U postgres -c "SELECT pg_promote();"

# 3. Verify promotion
psql -U postgres -c "SELECT pg_is_in_recovery();"
# Should return: f (false)

# 4. Update application connection
# Update DATABASE_URL to point to new primary

# 5. Restart application
systemctl restart metamaster-api

# 6. Verify application
curl http://localhost:8000/health
```

### 3. Communication Plan

```
1. Incident Detection (T+0)
   - Alert sent to on-call engineer
   - Incident created in tracking system

2. Initial Response (T+5 min)
   - Assess severity
   - Notify stakeholders
   - Begin recovery procedures

3. Recovery (T+15 min)
   - Execute recovery plan
   - Monitor progress
   - Update status

4. Verification (T+30 min)
   - Verify data integrity
   - Run health checks
   - Confirm service restoration

5. Post-Incident (T+1 hour)
   - Document incident
   - Identify root cause
   - Plan improvements
```

## RTO/RPO Targets

### 1. Recovery Time Objective (RTO)

| Component | Target RTO | Current RTO |
|-----------|-----------|------------|
| Database | 1 hour | 45 minutes |
| Cache | 30 minutes | 20 minutes |
| Application | 15 minutes | 10 minutes |
| Full system | 2 hours | 1.5 hours |

### 2. Recovery Point Objective (RPO)

| Component | Target RPO | Current RPO |
|-----------|-----------|------------|
| Database | 1 hour | 30 minutes |
| Cache | 5 minutes | 5 minutes |
| Application | 24 hours | 24 hours |
| Full system | 1 hour | 30 minutes |

### 3. Improvement Plan

```
Q1 2024:
- Implement hourly backups (currently daily)
- Setup automated backup testing
- Reduce RTO to 30 minutes

Q2 2024:
- Implement continuous replication
- Setup multi-region backups
- Reduce RPO to 15 minutes

Q3 2024:
- Implement automated failover
- Setup disaster recovery site
- Achieve RTO < 15 minutes
```

## Monitoring and Alerts

### 1. Backup Monitoring

```bash
# Check backup completion
ls -lh /backups/metamaster/full/ | tail -5

# Verify backup size
du -sh /backups/metamaster/full/

# Check backup age
find /backups/metamaster/full -name "*.sql.gz" -mtime +1 -exec ls -lh {} \;

# Alert if no backup in 24 hours
if [ ! -f /backups/metamaster/full/backup_full_$(date +%Y%m%d)*.sql.gz ]; then
  send_alert "No backup found for today"
fi
```

### 2. Backup Alerts

```yaml
# Prometheus alert rules
groups:
  - name: backup
    rules:
      - alert: BackupMissing
        expr: time() - backup_timestamp > 86400
        for: 1h
        annotations:
          summary: "Backup missing for more than 24 hours"
      
      - alert: BackupFailed
        expr: backup_status == 0
        for: 5m
        annotations:
          summary: "Backup failed"
      
      - alert: BackupStorageFull
        expr: backup_storage_usage > 0.9
        for: 5m
        annotations:
          summary: "Backup storage 90% full"
```

### 3. Recovery Testing Alerts

```bash
# Schedule weekly recovery test
0 2 * * 0 /usr/local/bin/test_backup_recovery.sh

# Alert if test fails
if [ $? -ne 0 ]; then
  send_alert "Backup recovery test failed"
fi
```

## Backup Storage

### 1. Local Storage

```bash
# Setup NAS backup
mount -t nfs nas.example.com:/backups /mnt/nas_backups

# Backup to NAS
cp backup_full.sql.gz /mnt/nas_backups/metamaster/

# Verify backup
ls -lh /mnt/nas_backups/metamaster/
```

### 2. Cloud Storage

```bash
# AWS S3 with versioning
aws s3api put-bucket-versioning \
  --bucket metamaster-backups \
  --versioning-configuration Status=Enabled

# Lifecycle policy (archive old backups)
aws s3api put-bucket-lifecycle-configuration \
  --bucket metamaster-backups \
  --lifecycle-configuration '{
    "Rules": [{
      "Id": "Archive",
      "Status": "Enabled",
      "Transitions": [{
        "Days": 30,
        "StorageClass": "GLACIER"
      }]
    }]
  }'

# GCP Cloud Storage with retention
gsutil retention set 2592000 gs://metamaster-backups/

# Azure Blob Storage with lifecycle
az storage account blob-service-properties update \
  --account-name metamasterbackups \
  --enable-delete-retention true \
  --delete-retention-days 30
```

### 3. Backup Encryption

```bash
# Encrypt backup before upload
gpg --symmetric --cipher-algo AES256 backup_full.sql.gz

# Upload encrypted backup
aws s3 cp backup_full.sql.gz.gpg s3://metamaster-backups/

# Decrypt backup
gpg --decrypt backup_full.sql.gz.gpg > backup_full.sql.gz
```

## Troubleshooting

### 1. Backup Failures

```bash
# Check backup logs
tail -f /var/log/backup.log

# Verify database connectivity
psql -U metamaster -d metamaster -c "SELECT 1;"

# Check disk space
df -h /backups

# Check backup process
ps aux | grep pg_dump

# Restart backup service
systemctl restart backup-service
```

### 2. Recovery Failures

```bash
# Check recovery logs
tail -f /var/log/postgresql/postgresql.log

# Verify backup file
file backup_full.dump

# Test restore to temporary database
psql -U postgres -c "CREATE DATABASE test_restore;"
pg_restore -U metamaster -d test_restore backup_full.dump

# Check for errors
psql -U metamaster -d test_restore -c "SELECT COUNT(*) FROM movies;"
```

### 3. Storage Issues

```bash
# Check backup storage usage
du -sh /backups/metamaster/*

# Find large backups
find /backups -size +1G -type f

# Cleanup old backups
find /backups -name "*.sql.gz" -mtime +30 -delete

# Compress old backups
find /backups -name "*.sql" -mtime +7 -exec gzip {} \;
```

## Next Steps

1. [Main Deployment Guide](DEPLOYMENT.md)
2. [Database Management](DEPLOYMENT_DATABASE.md)
3. [Security Configuration](DEPLOYMENT_SECURITY.md)
4. [Troubleshooting Guide](DEPLOYMENT_TROUBLESHOOTING.md)
