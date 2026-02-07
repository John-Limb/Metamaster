# Security Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [SSL/TLS Setup](#ssltls-setup)
3. [API Key Management](#api-key-management)
4. [Environment Variable Security](#environment-variable-security)
5. [Database Security](#database-security)
6. [Network Security](#network-security)
7. [Firewall Configuration](#firewall-configuration)
8. [Security Scanning](#security-scanning)
9. [Compliance Requirements](#compliance-requirements)
10. [Security Monitoring](#security-monitoring)

## Overview

This guide covers security configuration and best practices for deploying the Metamaster application in production environments.

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet / Users                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Layer 1: Edge Security                  │   │
│  │  - DDoS Protection (CloudFlare, AWS Shield)         │   │
│  │  - WAF (Web Application Firewall)                   │   │
│  │  - Rate Limiting                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Layer 2: Transport Security             │   │
│  │  - SSL/TLS Encryption                               │   │
│  │  - Certificate Management                           │   │
│  │  - HSTS Headers                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Layer 3: Application Security           │   │
│  │  - Authentication (JWT)                             │   │
│  │  - Authorization (RBAC)                             │   │
│  │  - Input Validation                                 │   │
│  │  - SQL Injection Prevention                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Layer 4: Data Security                  │   │
│  │  - Database Encryption                              │   │
│  │  - Secrets Management                               │   │
│  │  - Access Control                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## SSL/TLS Setup

### 1. Certificate Generation

```bash
# Generate self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Generate certificate signing request (CSR)
openssl req -new -newkey rsa:4096 -nodes -out server.csr -keyout server.key

# View certificate details
openssl x509 -in cert.pem -text -noout

# Verify certificate and key match
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in key.pem | openssl md5
```

### 2. Let's Encrypt Setup

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d metamaster.example.com

# Auto-renewal
sudo certbot renew --dry-run

# Setup auto-renewal cron
0 12 * * * /opt/certbot/bin/python -m certbot renew --quiet
```

### 3. Certificate Installation

```bash
# Copy certificates to application directory
sudo cp /etc/letsencrypt/live/metamaster.example.com/fullchain.pem /app/certs/
sudo cp /etc/letsencrypt/live/metamaster.example.com/privkey.pem /app/certs/

# Set permissions
sudo chown app:app /app/certs/*
sudo chmod 600 /app/certs/privkey.pem
sudo chmod 644 /app/certs/fullchain.pem
```

### 4. HTTPS Configuration

```python
# In app/main.py
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add HTTPS redirect middleware
@app.middleware("http")
async def https_redirect(request, call_next):
    if request.url.scheme == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=url)
    return await call_next(request)

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### 5. Nginx SSL Configuration

```nginx
# /etc/nginx/sites-available/metamaster
server {
    listen 80;
    server_name metamaster.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name metamaster.example.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/metamaster.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/metamaster.example.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Proxy to application
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## API Key Management

### 1. API Key Generation

```python
# In app/services/api_key_service.py
import secrets
import hashlib
from datetime import datetime, timedelta

class APIKeyService:
    @staticmethod
    def generate_api_key():
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key):
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def create_api_key(user_id, name, expires_in_days=90):
        """Create new API key"""
        api_key = APIKeyService.generate_api_key()
        hashed_key = APIKeyService.hash_api_key(api_key)
        
        # Store in database
        db_key = APIKey(
            user_id=user_id,
            name=name,
            hashed_key=hashed_key,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
        db.add(db_key)
        db.commit()
        
        return api_key  # Return unhashed key only once
```

### 2. API Key Validation

```python
# In app/api/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key"""
    hashed_key = APIKeyService.hash_api_key(api_key)
    
    db_key = db.query(APIKey).filter(
        APIKey.hashed_key == hashed_key,
        APIKey.expires_at > datetime.utcnow()
    ).first()
    
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    
    return db_key
```

### 3. API Key Rotation

```bash
# Rotate API keys
# 1. Generate new key
# 2. Update application configuration
# 3. Revoke old key after grace period

# Script to rotate keys
#!/bin/bash
OLD_KEY=$1
NEW_KEY=$2
GRACE_PERIOD=7  # days

# Update configuration
sed -i "s/$OLD_KEY/$NEW_KEY/g" /app/.env

# Restart application
systemctl restart metamaster-api

# Schedule key revocation
echo "DELETE FROM api_keys WHERE key = '$OLD_KEY' AND created_at < NOW() - INTERVAL '$GRACE_PERIOD days';" | \
  psql -U metamaster -d metamaster
```

## Environment Variable Security

### 1. Secrets Management

```bash
# Using HashiCorp Vault
vault kv put secret/metamaster \
  DATABASE_URL="postgresql://..." \
  SECRET_KEY="..." \
  OMDB_API_KEY="..."

# Retrieve secrets
vault kv get secret/metamaster

# In application
import hvac

client = hvac.Client(url='http://vault:8200')
secrets = client.secrets.kv.read_secret_version(path='metamaster')
```

### 2. AWS Secrets Manager

```bash
# Create secret
aws secretsmanager create-secret \
  --name metamaster/prod \
  --secret-string '{
    "DATABASE_URL": "postgresql://...",
    "SECRET_KEY": "...",
    "OMDB_API_KEY": "..."
  }'

# Retrieve secret
aws secretsmanager get-secret-value --secret-id metamaster/prod

# In application
import boto3
import json

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='metamaster/prod')
secrets = json.loads(response['SecretString'])
```

### 3. Azure Key Vault

```bash
# Create secret
az keyvault secret set \
  --vault-name metamaster-kv \
  --name DATABASE-URL \
  --value "postgresql://..."

# Retrieve secret
az keyvault secret show \
  --vault-name metamaster-kv \
  --name DATABASE-URL

# In application
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://metamaster-kv.vault.azure.net/", credential=credential)
secret = client.get_secret("DATABASE-URL")
```

### 4. Environment Variable Best Practices

```bash
# .env file (never commit to version control)
# Use .env.example for template
# Add to .gitignore
echo ".env" >> .gitignore

# Restrict file permissions
chmod 600 .env

# Use environment-specific files
.env.development
.env.staging
.env.production

# Load appropriate file
if [ "$APP_ENV" = "production" ]; then
  source .env.production
else
  source .env.development
fi
```

## Database Security

### 1. Database User Permissions

```sql
-- Create limited user for application
CREATE USER app_user WITH PASSWORD 'secure_password';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE metamaster TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Create read-only user for analytics
CREATE USER analytics_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE metamaster TO analytics_user;
GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- Revoke public access
REVOKE ALL ON SCHEMA public FROM PUBLIC;
```

### 2. Database Encryption

```bash
# Enable encryption at rest (PostgreSQL 13+)
# In postgresql.conf
ssl = on
ssl_cert_file = '/etc/postgresql/server.crt'
ssl_key_file = '/etc/postgresql/server.key'

# Require SSL connections
# In pg_hba.conf
hostssl all all 0.0.0.0/0 md5

# Encrypt specific columns
CREATE EXTENSION pgcrypto;

-- Encrypt sensitive data
ALTER TABLE users ADD COLUMN email_encrypted bytea;
UPDATE users SET email_encrypted = pgp_sym_encrypt(email, 'encryption_key');
```

### 3. SQL Injection Prevention

```python
# Use parameterized queries (SQLAlchemy ORM)
from sqlalchemy import text

# Good - parameterized
query = db.query(Movie).filter(Movie.title == title)

# Bad - string concatenation (NEVER DO THIS)
# query = db.execute(f"SELECT * FROM movies WHERE title = '{title}'")

# For raw SQL, use parameters
query = db.execute(
    text("SELECT * FROM movies WHERE title = :title"),
    {"title": title}
)
```

### 4. Database Audit Logging

```sql
-- Enable audit logging
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Configure audit logging
ALTER SYSTEM SET pgaudit.log = 'ALL';
ALTER SYSTEM SET pgaudit.log_statement = 'all';
ALTER SYSTEM SET pgaudit.log_parameter = on;

-- Reload configuration
SELECT pg_reload_conf();

-- View audit logs
SELECT * FROM pg_audit_log ORDER BY timestamp DESC LIMIT 100;
```

## Network Security

### 1. VPC Configuration

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create private subnets
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a

# Create security groups
aws ec2 create-security-group \
  --group-name metamaster-api \
  --description "Security group for API" \
  --vpc-id vpc-xxxxx

# Add ingress rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 8000 \
  --source-security-group-id sg-yyyyy
```

### 2. Network Segmentation

```
┌─────────────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Public Subnet (10.0.1.0/24)                         │   │
│  │  - Load Balancer                                     │   │
│  │  - NAT Gateway                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Private Subnet (10.0.2.0/24)                        │   │
│  │  - API Servers                                       │   │
│  │  - Celery Workers                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Database Subnet (10.0.3.0/24)                       │   │
│  │  - PostgreSQL                                        │   │
│  │  - Redis                                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3. Bastion Host Setup

```bash
# Create bastion host
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name my-key \
  --security-groups bastion

# SSH through bastion
ssh -J ec2-user@bastion.example.com ec2-user@private-instance.internal

# SSH tunneling
ssh -L 5432:database.internal:5432 ec2-user@bastion.example.com
psql -h localhost -U metamaster -d metamaster
```

## Firewall Configuration

### 1. UFW (Ubuntu Firewall)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Allow specific IP
sudo ufw allow from 192.168.1.0/24 to any port 5432

# Deny all incoming
sudo ufw default deny incoming

# Allow all outgoing
sudo ufw default allow outgoing

# View rules
sudo ufw status verbose
```

### 2. iptables Configuration

```bash
# Flush existing rules
sudo iptables -F

# Set default policies
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Save rules
sudo iptables-save > /etc/iptables/rules.v4
```

### 3. AWS Security Groups

```bash
# Create security group
aws ec2 create-security-group \
  --group-name metamaster-api \
  --description "API security group"

# Allow HTTPS from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow database from API security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-database \
  --protocol tcp \
  --port 5432 \
  --source-security-group-id sg-api

# Deny all other traffic
aws ec2 revoke-security-group-egress \
  --group-id sg-xxxxx \
  --protocol -1 \
  --cidr 0.0.0.0/0
```

## Security Scanning

### 1. Dependency Scanning

```bash
# Scan Python dependencies
pip install safety
safety check

# Scan with pip-audit
pip install pip-audit
pip-audit

# Scan with Snyk
npm install -g snyk
snyk test
```

### 2. Container Scanning

```bash
# Scan Docker image
docker scan metamaster:latest

# Scan with Trivy
trivy image metamaster:latest

# Scan with Grype
grype metamaster:latest
```

### 3. SAST (Static Application Security Testing)

```bash
# Scan with Bandit
pip install bandit
bandit -r app/

# Scan with SonarQube
sonar-scanner \
  -Dsonar.projectKey=metamaster \
  -Dsonar.sources=app \
  -Dsonar.host.url=http://sonarqube:9000
```

### 4. DAST (Dynamic Application Security Testing)

```bash
# Scan with OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://metamaster.example.com

# Scan with Burp Suite
burpsuite --project-file=metamaster.burp
```

## Compliance Requirements

### 1. GDPR Compliance

```python
# Data retention policy
from datetime import datetime, timedelta

class DataRetentionPolicy:
    # Delete user data after 30 days of inactivity
    INACTIVITY_PERIOD = timedelta(days=30)
    
    @staticmethod
    def delete_inactive_users():
        cutoff_date = datetime.utcnow() - DataRetentionPolicy.INACTIVITY_PERIOD
        db.query(User).filter(User.last_login < cutoff_date).delete()
        db.commit()
    
    # Right to be forgotten
    @staticmethod
    def delete_user_data(user_id):
        # Delete user account
        db.query(User).filter(User.id == user_id).delete()
        
        # Delete user data
        db.query(UserData).filter(UserData.user_id == user_id).delete()
        
        # Delete audit logs
        db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()
        
        db.commit()
```

### 2. PCI DSS Compliance

```python
# Payment data security
class PaymentSecurity:
    # Never store full credit card numbers
    # Use tokenization instead
    
    @staticmethod
    def tokenize_card(card_number):
        # Use payment processor API
        token = payment_processor.tokenize(card_number)
        return token
    
    # Encrypt sensitive data
    @staticmethod
    def encrypt_sensitive_data(data):
        from cryptography.fernet import Fernet
        cipher = Fernet(ENCRYPTION_KEY)
        return cipher.encrypt(data.encode())
```

### 3. SOC 2 Compliance

```python
# Audit logging
class AuditLog:
    user_id: int
    action: str
    resource: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    result: str  # success/failure
    details: dict

# Log all security events
def log_security_event(user_id, action, resource, result, details=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        timestamp=datetime.utcnow(),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        result=result,
        details=details
    )
    db.add(log)
    db.commit()
```

## Security Monitoring

### 1. Security Alerts

```yaml
# Prometheus alert rules
groups:
  - name: security
    rules:
      - alert: FailedLoginAttempts
        expr: rate(failed_login_attempts[5m]) > 5
        for: 5m
        annotations:
          summary: "High rate of failed login attempts"
      
      - alert: UnauthorizedAPIAccess
        expr: rate(unauthorized_api_requests[5m]) > 10
        for: 5m
        annotations:
          summary: "High rate of unauthorized API requests"
      
      - alert: SQLInjectionAttempt
        expr: sql_injection_attempts > 0
        for: 1m
        annotations:
          summary: "SQL injection attempt detected"
```

### 2. Security Logging

```python
# Centralized security logging
import logging
from pythonjsonlogger import jsonlogger

security_logger = logging.getLogger("security")
handler = logging.FileHandler("security.log")
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
security_logger.addHandler(handler)

# Log security events
security_logger.warning("Unauthorized access attempt", extra={
    "user_id": user_id,
    "ip_address": request.client.host,
    "endpoint": request.url.path,
    "timestamp": datetime.utcnow().isoformat()
})
```

### 3. Intrusion Detection

```bash
# Install Fail2Ban
sudo apt-get install fail2ban

# Configure Fail2Ban
sudo nano /etc/fail2ban/jail.local

# Configuration:
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true

# Start Fail2Ban
sudo systemctl start fail2ban
```

## Next Steps

1. [Main Deployment Guide](DEPLOYMENT.md)
2. [Database Management](DEPLOYMENT_DATABASE.md)
3. [Troubleshooting Guide](DEPLOYMENT_TROUBLESHOOTING.md)
4. [Infrastructure as Code](INFRASTRUCTURE_AS_CODE.md)
