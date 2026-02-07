# API Authentication Guide

## Overview

This document provides comprehensive information about authentication methods, API key management, token handling, and security best practices for the Media Management API.

---

## Table of Contents

1. [Current Authentication Status](#current-authentication-status)
2. [Authentication Methods](#authentication-methods)
3. [API Key Management](#api-key-management)
4. [Token Handling](#token-handling)
5. [Security Best Practices](#security-best-practices)
6. [Rate Limiting](#rate-limiting)
7. [Troubleshooting](#troubleshooting)

---

## Current Authentication Status

### Current Implementation

The Media Management API currently operates **without authentication requirements**. All endpoints are publicly accessible without credentials.

### Future Implementation

Authentication will be implemented in a future phase with the following methods:

- **API Key Authentication**: Simple key-based authentication
- **Bearer Token**: JWT-based token authentication
- **OAuth 2.0**: Third-party integration support

---

## Authentication Methods

### Method 1: API Key Authentication (Future)

API Key authentication is the simplest method for server-to-server communication.

#### How It Works

1. Client includes API key in request header
2. Server validates API key
3. Request is processed if key is valid

#### Request Format

```bash
curl -X GET "http://localhost:8000/movies" \
  -H "X-API-Key: your-api-key-here"
```

#### Python Example

```python
import requests

headers = {
    "X-API-Key": "your-api-key-here"
}

response = requests.get(
    "http://localhost:8000/movies",
    headers=headers
)
```

#### JavaScript Example

```javascript
const headers = {
  'X-API-Key': 'your-api-key-here'
};

fetch('http://localhost:8000/movies', {
  method: 'GET',
  headers: headers
})
  .then(response => response.json())
  .then(data => console.log(data));
```

#### Advantages

- Simple to implement
- No token refresh needed
- Good for server-to-server communication
- Easy to revoke

#### Disadvantages

- Less secure than tokens
- No expiration
- Cannot be scoped to specific resources

### Method 2: Bearer Token (Future)

Bearer Token authentication uses JWT tokens for stateless authentication.

#### How It Works

1. Client authenticates with credentials
2. Server returns JWT token
3. Client includes token in Authorization header
4. Server validates token signature and expiration

#### Request Format

```bash
curl -X GET "http://localhost:8000/movies" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Python Example

```python
import requests
import jwt
from datetime import datetime, timedelta

# Generate token (server-side)
payload = {
    'user_id': 123,
    'exp': datetime.utcnow() + timedelta(hours=1),
    'iat': datetime.utcnow()
}
token = jwt.encode(payload, 'secret-key', algorithm='HS256')

# Use token (client-side)
headers = {
    'Authorization': f'Bearer {token}'
}

response = requests.get(
    "http://localhost:8000/movies",
    headers=headers
)
```

#### JavaScript Example

```javascript
// Generate token (server-side)
const jwt = require('jsonwebtoken');

const payload = {
  user_id: 123,
  exp: Math.floor(Date.now() / 1000) + (60 * 60) // 1 hour
};

const token = jwt.sign(payload, 'secret-key', { algorithm: 'HS256' });

// Use token (client-side)
const headers = {
  'Authorization': `Bearer ${token}`
};

fetch('http://localhost:8000/movies', {
  method: 'GET',
  headers: headers
})
  .then(response => response.json())
  .then(data => console.log(data));
```

#### Token Structure

JWT tokens consist of three parts separated by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "iat": 1516239022,
  "exp": 1516242622
}
```

**Signature:**
```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret
)
```

#### Advantages

- Stateless authentication
- Token expiration
- Can include claims/scopes
- Better security than API keys
- Supports refresh tokens

#### Disadvantages

- More complex to implement
- Token refresh needed
- Larger request headers

### Method 3: OAuth 2.0 (Future)

OAuth 2.0 enables third-party integrations and delegated access.

#### Authorization Code Flow

```
1. User clicks "Login with API"
2. Redirected to authorization server
3. User grants permission
4. Authorization code returned
5. Client exchanges code for access token
6. Client uses access token to access API
```

#### Request Format

```bash
curl -X GET "http://localhost:8000/movies" \
  -H "Authorization: Bearer access_token_here"
```

#### Python Example

```python
from requests_oauthlib import OAuth2Session

client_id = 'your-client-id'
client_secret = 'your-client-secret'
redirect_uri = 'http://localhost:8000/callback'

oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)

# Get authorization URL
authorization_url, state = oauth.authorization_url(
    'http://auth-server.com/oauth/authorize'
)

# After user authorizes, exchange code for token
token = oauth.fetch_token(
    'http://auth-server.com/oauth/token',
    client_secret=client_secret,
    authorization_response=authorization_response
)

# Use token to access API
response = oauth.get('http://localhost:8000/movies')
```

---

## API Key Management

### Generating API Keys

```python
import secrets
import hashlib

def generate_api_key():
    """Generate a secure API key"""
    # Generate random bytes
    key_bytes = secrets.token_bytes(32)
    
    # Convert to hex string
    api_key = secrets.token_hex(32)
    
    return api_key

# Usage
api_key = generate_api_key()
print(f"API Key: {api_key}")
```

### Storing API Keys

**DO NOT:**
- Store in version control
- Log API keys
- Share in emails
- Hardcode in code

**DO:**
- Store in environment variables
- Use secrets management system
- Rotate regularly
- Use different keys for different environments

### Environment Variable Setup

```bash
# .env file
API_KEY=your-api-key-here
OMDB_API_KEY=your-omdb-key
TVDB_API_KEY=your-tvdb-key
```

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('API_KEY')
omdb_key = os.getenv('OMDB_API_KEY')
tvdb_key = os.getenv('TVDB_API_KEY')
```

### Key Rotation

```python
from datetime import datetime, timedelta

class APIKeyManager:
    def __init__(self):
        self.keys = {}
    
    def create_key(self, name, expires_in_days=90):
        """Create API key with expiration"""
        key = secrets.token_hex(32)
        self.keys[key] = {
            'name': name,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(days=expires_in_days),
            'active': True
        }
        return key
    
    def revoke_key(self, key):
        """Revoke API key"""
        if key in self.keys:
            self.keys[key]['active'] = False
    
    def is_valid(self, key):
        """Check if key is valid"""
        if key not in self.keys:
            return False
        
        key_info = self.keys[key]
        
        # Check if active
        if not key_info['active']:
            return False
        
        # Check if expired
        if datetime.now() > key_info['expires_at']:
            return False
        
        return True
```

---

## Token Handling

### Token Refresh

```python
import jwt
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, secret_key):
        self.secret_key = secret_key
    
    def create_tokens(self, user_id):
        """Create access and refresh tokens"""
        # Access token (short-lived)
        access_payload = {
            'user_id': user_id,
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        access_token = jwt.encode(
            access_payload,
            self.secret_key,
            algorithm='HS256'
        )
        
        # Refresh token (long-lived)
        refresh_payload = {
            'user_id': user_id,
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow()
        }
        refresh_token = jwt.encode(
            refresh_payload,
            self.secret_key,
            algorithm='HS256'
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    
    def refresh_access_token(self, refresh_token):
        """Generate new access token from refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=['HS256']
            )
            
            if payload['type'] != 'refresh':
                raise ValueError("Invalid token type")
            
            # Create new access token
            access_payload = {
                'user_id': payload['user_id'],
                'type': 'access',
                'exp': datetime.utcnow() + timedelta(hours=1),
                'iat': datetime.utcnow()
            }
            access_token = jwt.encode(
                access_payload,
                self.secret_key,
                algorithm='HS256'
            )
            
            return {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 3600
            }
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token")
```

### Token Validation

```python
def validate_token(token, secret_key):
    """Validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
```

---

## Security Best Practices

### 1. Use HTTPS

Always use HTTPS in production to encrypt credentials in transit.

```python
# Enforce HTTPS
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)
```

### 2. Secure Headers

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 3. Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

### 4. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/movies")
@limiter.limit("100/minute")
async def list_movies(request: Request):
    return {"items": []}
```

### 5. Input Validation

```python
from pydantic import BaseModel, validator

class MovieCreate(BaseModel):
    title: str
    plot: str = None
    rating: float = None
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v
    
    @validator('rating')
    def rating_range(cls, v):
        if v is not None and not (0 <= v <= 10):
            raise ValueError('Rating must be between 0 and 10')
        return v
```

### 6. Logging and Monitoring

```python
import logging

logger = logging.getLogger(__name__)

def log_authentication_attempt(user_id, success, ip_address):
    """Log authentication attempts"""
    logger.info(
        f"Authentication attempt",
        extra={
            'user_id': user_id,
            'success': success,
            'ip_address': ip_address,
            'timestamp': datetime.now()
        }
    )
```

### 7. Secrets Management

```python
# Using environment variables
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
API_KEY = os.getenv('API_KEY')

# Using AWS Secrets Manager
import boto3

client = boto3.client('secretsmanager')

secret = client.get_secret_value(SecretId='api-secret-key')
SECRET_KEY = secret['SecretString']
```

---

## Rate Limiting

### Current Status

Rate limiting is not currently enforced.

### Future Implementation

When implemented, the following limits will apply:

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Standard Endpoints | 1000 | 1 hour |
| Search Endpoints | 500 | 1 hour |
| Batch Operations | 100 | 1 hour |
| Authentication | 10 | 1 minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1644245474
```

### Handling Rate Limits

```python
import time
import requests

def handle_rate_limit(response):
    """Handle rate limit response"""
    if response.status_code == 429:
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        wait_time = reset_time - time.time()
        
        if wait_time > 0:
            print(f"Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            return True
    
    return False
```

---

## Troubleshooting

### Issue: "Unauthorized" Error

**Symptoms:**
- 401 Unauthorized response
- Cannot access protected endpoints

**Solutions:**
1. Verify API key is included in request
2. Check API key is valid and not expired
3. Verify Authorization header format
4. Check API key has required permissions

### Issue: "Invalid Token" Error

**Symptoms:**
- 401 Invalid token response
- Token validation fails

**Solutions:**
1. Verify token is not expired
2. Check token signature
3. Verify token format (Bearer token)
4. Refresh token if expired

### Issue: "Forbidden" Error

**Symptoms:**
- 403 Forbidden response
- Authenticated but access denied

**Solutions:**
1. Verify user has required permissions
2. Check resource ownership
3. Verify API key scope
4. Contact administrator for access

### Issue: "Rate Limit Exceeded"

**Symptoms:**
- 429 Too Many Requests
- Requests being rejected

**Solutions:**
1. Implement exponential backoff
2. Reduce request frequency
3. Use batch operations
4. Wait for rate limit window to reset

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [Error Reference](./API_ERRORS.md)
- [API Client Examples](./API_CLIENT_EXAMPLES.md)
