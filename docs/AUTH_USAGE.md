# Authentication System Usage Guide

This document provides practical guidance for developers working with the MetaMaster authentication system. For architectural details, see [`AUTH_DESIGN.md`](./AUTH_DESIGN.md).

## Table of Contents

- [Overview](#overview)
- [Backend API Endpoints](#backend-api-endpoints)
- [Frontend Integration](#frontend-integration)
- [Token Management](#token-management)
- [User Flows](#user-flows)
- [Security Considerations](#security-considerations)
- [Development Setup](#development-setup)
- [Troubleshooting](#troubleshooting)

---

## Overview

MetaMaster uses a JWT-based authentication system with the following key characteristics:

| Aspect | Implementation |
|--------|----------------|
| **Password Hashing** | Argon2id (OWASP recommended) |
| **Access Tokens** | JWT, 15-minute expiration |
| **Refresh Tokens** | JWT, 7-day expiration, stored in httpOnly cookie |
| **Token Storage** | Access token in localStorage, refresh token in httpOnly cookie |
| **Rate Limiting** | Redis-based sliding window algorithm |

### Technology Choices

- **Argon2id**: Memory-hard password hashing algorithm resistant to GPU attacks, side-channel attacks, and time-memory trade-off attacks. See [`app/infrastructure/security/password.py`](../app/infrastructure/security/password.py).

- **JWT (JSON Web Tokens)**: Stateless authentication with HS256 algorithm. Tokens include type claims (`access` or `refresh`) for validation. See [`app/infrastructure/security/jwt.py`](../app/infrastructure/security/jwt.py).

- **httpOnly Cookies**: Refresh tokens are stored in httpOnly, secure, SameSite=strict cookies to prevent XSS and CSRF attacks.

---

## Backend API Endpoints

All auth endpoints are prefixed with `/api/v1/auth`. See [`app/api/v1/auth/endpoints.py`](../app/api/v1/auth/endpoints.py).

### Endpoint Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/register` | Create new user account | No |
| `POST` | `/login` | Authenticate and receive tokens | No |
| `POST` | `/refresh` | Refresh access token | No (uses cookie) |
| `POST` | `/logout` | Invalidate refresh token | No |
| `GET` | `/me` | Get current user info | Yes |
| `POST` | `/change-password` | Change user password | Yes |

### POST /register

Create a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecureP@ss123"
}
```

**Success Response (201 Created):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "avatar_url": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 409 | "Username already registered" |
| 409 | "Email already registered" |
| 422 | Validation error (see Password Requirements) |
| 429 | Rate limited (3 requests/hour per IP) |

### POST /login

Authenticate with username or email and password.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "SecureP@ss123"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "requires_password_change": false,
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "avatar_url": null,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Note:** The refresh token is set as an httpOnly cookie automatically.

**Error Responses:**
| Status | Detail |
|--------|--------|
| 401 | "Incorrect username or password" |
| 429 | Rate limited (5 requests/minute per IP) |

### POST /refresh

Get a new access token using the refresh token from the cookie.

**Request:** No body required. Refresh token is read from the `refresh_token` cookie.

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 401 | "Refresh token not found" |
| 401 | "Invalid refresh token" |
| 401 | "Refresh token revoked or expired" |
| 429 | Rate limited (20 requests/minute per IP) |

### POST /logout

Invalidate the current refresh token and clear the cookie.

**Request:** No body required.

**Success Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

### GET /me

Get the currently authenticated user's information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "avatar_url": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 401 | "Invalid or expired token" |
| 401 | "User not found or inactive" |

### POST /change-password

Change the current user's password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldP@ss123",
  "new_password": "NewSecureP@ss456"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
| Status | Detail |
|--------|--------|
| 400 | "Current password is incorrect" |
| 422 | Validation error (new password doesn't meet requirements) |

---

## Frontend Integration

### Using the `useAuth` Hook

The [`useAuth`](../frontend/src/context/AuthContext.tsx) hook provides access to authentication state and methods.

```tsx
import { useAuth } from '@/context/AuthContext'

function MyComponent() {
  const { 
    user,           // Current user object or null
    isAuthenticated, // boolean - derived from user presence
    isLoading,       // boolean - loading state for auth operations
    error,           // string | null - last error message
    requiresPasswordChange, // boolean - forced password change flag
    login,           // (credentials) => Promise<void>
    register,        // (data) => Promise<void>
    logout,          // () => Promise<void>
    changePassword,  // (data) => Promise<void>
    clearError,      // () => void
  } = useAuth()

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!isAuthenticated) {
    return <button onClick={() => login({ username, password })}>Login</button>
  }

  return (
    <div>
      <p>Welcome, {user?.username}!</p>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

### Protecting Routes with `ProtectedRoute`

Wrap routes that require authentication with [`ProtectedRoute`](../frontend/src/components/auth/ProtectedRoute.tsx):

```tsx
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Routes, Route } from 'react-router-dom'

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      
      {/* Protected routes */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
      
      {/* Route requiring password change */}
      <Route 
        path="/change-password" 
        element={
          <ProtectedRoute requirePasswordChange>
            <ChangePasswordPage />
          </ProtectedRoute>
        } 
      />
    </Routes>
  )
}
```

### Accessing User Data in Components

```tsx
import { useAuth } from '@/context/AuthContext'

function UserProfile() {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated || !user) {
    return null
  }

  return (
    <div className="user-profile">
      <img src={user.avatar_url || '/default-avatar.png'} alt={user.username} />
      <h2>{user.username}</h2>
      <p>{user.email}</p>
      <small>Member since {new Date(user.created_at).toLocaleDateString()}</small>
    </div>
  )
}
```

### Making Authenticated API Requests

The frontend stores the access token in localStorage. Include it in API requests:

```typescript
// In your API service
const token = localStorage.getItem('authToken')

const response = await fetch('/api/v1/movies', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
})
```

---

## Token Management

### Access Token Lifecycle

| Property | Value |
|----------|-------|
| **Expiration** | 15 minutes |
| **Storage** | localStorage (`authToken` key) |
| **Expiry Tracking** | localStorage (`tokenExpiry` key) |
| **Usage** | Sent in `Authorization: Bearer` header |

### Refresh Token Lifecycle

| Property | Value |
|----------|-------|
| **Expiration** | 7 days |
| **Storage** | httpOnly cookie (`refresh_token`) |
| **Cookie Attributes** | `httponly`, `secure`, `samesite=strict` |
| **Usage** | Automatically sent with `/auth/refresh` requests |

### Auto-Refresh Mechanism

The frontend implements automatic token refresh:

1. **Check Interval**: Every 10 minutes
2. **Refresh Threshold**: When token expires in less than 5 minutes
3. **Process**: 
   - Check `tokenExpiry` in localStorage
   - If within threshold, call `/auth/refresh`
   - Store new access token and update expiry

```typescript
// From AuthContext.tsx
const REFRESH_CHECK_INTERVAL = 10 * 60 * 1000  // 10 minutes
const REFRESH_THRESHOLD = 5 * 60 * 1000        // 5 minutes

// Check if token needs refresh
const shouldRefreshToken = (): boolean => {
  const expiry = parseInt(localStorage.getItem('tokenExpiry') || '0', 10)
  const timeUntilExpiry = expiry - Date.now()
  return timeUntilExpiry > 0 && timeUntilExpiry < REFRESH_THRESHOLD
}
```

### Manual Token Refresh

If needed, you can manually trigger a refresh:

```typescript
import { authService } from '@/services/authService'

const newToken = await authService.refreshToken()
// New access token is returned, refresh token cookie is updated
```

---

## User Flows

### Registration Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant DB

    User->>Frontend: Fill registration form
    Frontend->>Frontend: Validate password strength
    Frontend->>API: POST /auth/register
    API->>API: Check rate limit (3/hour per IP)
    API->>DB: Check username uniqueness
    API->>DB: Check email uniqueness
    API->>API: Hash password with Argon2id
    API->>DB: Create user record
    API-->>Frontend: 201 Created with user data
    Frontend->>Frontend: Redirect to login page
    Frontend-->>User: "Registration successful, please login"
```

### Login Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant DB
    participant Redis

    User->>Frontend: Enter credentials
    Frontend->>API: POST /auth/login
    API->>API: Check rate limit (5/min per IP)
    API->>DB: Find user by username/email
    API->>API: Verify password hash
    API->>API: Generate access token (15 min)
    API->>API: Generate refresh token (7 days)
    API->>DB: Store refresh token hash
    API->>Redis: Store token for validation
    API-->>Frontend: Set cookie + return tokens
    Frontend->>Frontend: Store access token
    Frontend->>Frontend: Set up refresh interval
    Frontend-->>User: Redirect to dashboard
```

### Password Change Flow (Including Forced Change)

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant DB

    Note over User,DB: Normal Password Change
    User->>Frontend: Navigate to settings
    User->>Frontend: Enter current & new password
    Frontend->>Frontend: Validate new password strength
    Frontend->>API: POST /auth/change-password
    API->>DB: Verify current password
    API->>API: Hash new password
    API->>DB: Update password
    API-->>Frontend: 200 OK
    Frontend-->>User: "Password changed successfully"

    Note over User,DB: Forced Password Change (First Login)
    User->>Frontend: Login with default password
    Frontend->>API: POST /auth/login
    API-->>Frontend: requires_password_change: true
    Frontend->>Frontend: Set requiresPasswordChange flag
    Frontend->>Frontend: Redirect to /change-password
    User->>Frontend: Enter new password
    Frontend->>API: POST /auth/change-password
    API-->>Frontend: 200 OK
    Frontend->>Frontend: Clear requiresPasswordChange
    Frontend-->>User: Redirect to dashboard
```

### Logout Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant DB

    User->>Frontend: Click logout
    Frontend->>API: POST /auth/logout
    API->>DB: Revoke refresh token
    API-->>Frontend: 200 OK + clear cookie
    Frontend->>Frontend: Clear localStorage tokens
    Frontend->>Frontend: Clear user state
    Frontend->>Frontend: Clear refresh interval
    Frontend-->>User: Redirect to login
```

---

## Security Considerations

### Password Requirements

Passwords must meet the following criteria (enforced in [`app/domain/auth/validators.py`](../app/domain/auth/validators.py)):

| Requirement | Description |
|-------------|-------------|
| **Length** | 8-128 characters |
| **Uppercase** | At least one uppercase letter (A-Z) |
| **Lowercase** | At least one lowercase letter (a-z) |
| **Digit** | At least one digit (0-9) |
| **Special Character** | At least one of: `!@#$%^&*()_+-=[]{};':"\\|,.<>/?` |

**Example valid password:** `SecureP@ss123`

### Rate Limiting

Rate limits are enforced per IP address using Redis-based sliding window algorithm. See [`app/infrastructure/security/rate_limiter.py`](../app/infrastructure/security/rate_limiter.py).

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/login` | 5 requests | 1 minute |
| `/register` | 3 requests | 1 hour |
| `/refresh` | 20 requests | 1 minute |
| `/password_reset` | 3 requests | 1 hour |
| `/email_verification` | 5 requests | 1 hour |

When rate limited, the API returns:
- Status: `429 Too Many Requests`
- Header: `Retry-After: <seconds>`
- Body: `{"detail": "Too many <action> attempts. Retry after <seconds> seconds."}`

### Token Storage Security

| Token Type | Storage | Security Rationale |
|------------|---------|-------------------|
| **Access Token** | localStorage | Short-lived (15 min), acceptable risk for SPA |
| **Refresh Token** | httpOnly cookie | Protected from XSS, secure + SameSite for CSRF protection |

**Cookie Security Attributes:**
```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,    # Not accessible via JavaScript
    secure=True,      # Only sent over HTTPS
    samesite="strict", # CSRF protection
    max_age=604800,   # 7 days in seconds
)
```

### Password Hashing Parameters

Argon2id is configured with OWASP-recommended parameters:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `time_cost` | 3 | Number of iterations |
| `memory_cost` | 65536 KiB | 64 MB memory usage |
| `parallelism` | 4 | Number of parallel threads |
| `hash_len` | 32 | Hash length in bytes |
| `salt_len` | 16 | Salt length in bytes |

---

## Development Setup

### Required Environment Variables

Add these to your `.env` file (see [`.env.example`](../.env.example)):

```bash
# Database
DATABASE_URL=postgresql+psycopg2://metamaster:metamaster@localhost:5432/metamaster

# Redis (for rate limiting and caching)
REDIS_URL=redis://localhost:6379/0

# JWT (auto-generated if not set, but recommended for production)
# JWT_SECRET_KEY=your-secret-key-here  # Optional, auto-generated if omitted
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Note:** `JWT_SECRET_KEY` is auto-generated on startup if not provided. For production, set a stable secret to prevent token invalidation on restart.

### Testing Authentication Locally

1. **Start the services:**
   ```bash
   docker-compose up -d postgres redis
   ```

2. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Start the backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

5. **Test registration:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"TestP@ss123"}'
   ```

6. **Test login:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"TestP@ss123"}' \
     -c cookies.txt
   ```

7. **Test protected endpoint:**
   ```bash
   # Replace <token> with access_token from login response
   curl http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer <token>"
   ```

8. **Test token refresh:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -b cookies.txt
   ```

### Creating an Admin User

Use the initialization script to create an admin user:

```bash
python -m app.core.init_db
```

This creates a default admin user:
- Username: `admin`
- Password: `admin123` (will require change on first login)

---

## Troubleshooting

### Common Issues and Solutions

#### "Invalid or expired token"

**Cause:** Access token has expired or is malformed.

**Solution:**
1. Check if token exists in localStorage
2. Verify token hasn't expired (check `tokenExpiry`)
3. Trigger a token refresh or re-login

```typescript
// Debug token state
console.log('Token:', localStorage.getItem('authToken'))
console.log('Expiry:', new Date(parseInt(localStorage.getItem('tokenExpiry') || '0', 10)))
```

#### "Refresh token not found"

**Cause:** The httpOnly cookie is missing or blocked.

**Solutions:**
1. Ensure cookies are enabled in the browser
2. Check that the request includes credentials (`withCredentials: true` for axios)
3. Verify the backend is setting the cookie correctly
4. Check for cookie blocking in browser settings

#### "Too many login attempts"

**Cause:** Rate limit exceeded for login endpoint.

**Solution:**
1. Wait for the retry period (check `Retry-After` header)
2. Rate limit is 5 requests per minute per IP
3. For development, you can clear Redis rate limit keys:
   ```bash
   redis-cli DEL rate_limit:login:<your-ip>
   ```

#### "Password must contain: ..."

**Cause:** Password doesn't meet complexity requirements.

**Solution:** Ensure password has:
- At least 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

#### "Username already registered" / "Email already registered"

**Cause:** Duplicate username or email in database.

**Solution:**
1. Use a different username or email
2. If you own the email, use the login endpoint instead
3. For development, you can delete the user from the database

#### Token refresh loop

**Cause:** Refresh token is invalid but frontend keeps trying to refresh.

**Solution:**
1. Clear localStorage and cookies
2. The `AuthContext` should handle this automatically by clearing state on refresh failure
3. Check browser console for refresh errors

```typescript
// Manual cleanup
localStorage.removeItem('authToken')
localStorage.removeItem('tokenExpiry')
// Then reload the page
window.location.reload()
```

#### CORS errors with cookies

**Cause:** Cross-origin requests not configured for credentials.

**Solution:**
1. Ensure backend CORS allows your frontend origin
2. Set `credentials: 'include'` in fetch options
3. For axios, set `withCredentials: true`

```typescript
// Fetch example
fetch('/api/v1/auth/login', {
  method: 'POST',
  credentials: 'include', // Important for cookies
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(credentials),
})

// Axios example
axios.post('/api/v1/auth/login', credentials, {
  withCredentials: true, // Important for cookies
})
```

#### User stuck on password change page

**Cause:** `requiresPasswordChange` flag not cleared after successful password change.

**Solution:**
1. Check that `changePassword` was successful
2. Verify the API returned 200 OK
3. The flag should be cleared automatically by `AuthContext`

```typescript
// Debug state
const { requiresPasswordChange } = useAuth()
console.log('Requires password change:', requiresPasswordChange)
```

### Debugging Tips

1. **Check token contents:**
   ```javascript
   // Decode JWT payload (without verification)
   const token = localStorage.getItem('authToken')
   const payload = JSON.parse(atob(token.split('.')[1]))
   console.log('Token payload:', payload)
   console.log('Expires at:', new Date(payload.exp * 1000))
   ```

2. **Check cookie presence:**
   - Open DevTools → Application → Cookies
   - Look for `refresh_token` cookie
   - Verify it has `HttpOnly` and `Secure` flags

3. **Monitor network requests:**
   - Open DevTools → Network
   - Filter by `/auth/` to see auth requests
   - Check request/response headers for tokens and cookies

4. **Check Redis for rate limits:**
   ```bash
   redis-cli KEYS "rate_limit:*"
   redis-cli GET "rate_limit:login:127.0.0.1"
   ```

5. **Backend logs:**
   ```bash
   # Check for auth-related errors
   docker-compose logs backend | grep -i auth
   ```

---

## Related Files

| File | Purpose |
|------|---------|
| [`app/api/v1/auth/endpoints.py`](../app/api/v1/auth/endpoints.py) | Auth API endpoints |
| [`app/domain/auth/schemas.py`](../app/domain/auth/schemas.py) | Request/response schemas |
| [`app/domain/auth/service.py`](../app/domain/auth/service.py) | Auth business logic |
| [`app/domain/auth/validators.py`](../app/domain/auth/validators.py) | Password/username validation |
| [`app/infrastructure/security/jwt.py`](../app/infrastructure/security/jwt.py) | JWT token handling |
| [`app/infrastructure/security/password.py`](../app/infrastructure/security/password.py) | Argon2id password hashing |
| [`app/infrastructure/security/rate_limiter.py`](../app/infrastructure/security/rate_limiter.py) | Rate limiting |
| [`frontend/src/context/AuthContext.tsx`](../frontend/src/context/AuthContext.tsx) | React auth context |
| [`frontend/src/components/auth/ProtectedRoute.tsx`](../frontend/src/components/auth/ProtectedRoute.tsx) | Route guard component |
| [`frontend/src/services/authService.ts`](../frontend/src/services/authService.ts) | Auth API service |
