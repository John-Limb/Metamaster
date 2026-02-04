# Media Management Web Tool - Full Stack Integration Guide

## Overview

This document describes how the React frontend and Python backend integrate to form a complete media management system.

---

## 1. System Architecture Overview

### 1.1 Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ SSL/TLS Termination                                      │   │
│  │ Static Asset Caching                                     │   │
│  │ Request Routing                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────┬──────────────────────────────────────────────────┬─────┘
         │                                                  │
         ▼                                                  ▼
┌──────────────────────────┐                    ┌──────────────────────────┐
│   React Frontend         │                    │   FastAPI Backend        │
│  ┌────────────────────┐  │                    │  ┌────────────────────┐  │
│  │ Components         │  │                    │  │ REST API Endpoints │  │
│  │ State Management   │  │                    │  │ Business Logic     │  │
│  │ API Integration    │  │                    │  │ Database Access    │  │
│  │ UI/UX              │  │                    │  │ External APIs      │  │
│  └────────────────────┘  │                    │  └────────────────────┘  │
└──────────────────────────┘                    └──────────────────────────┘
         │                                                  │
         │ JSON/REST                                        │
         └──────────────────────────────────────────────────┘
                        API Communication
                        
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                    │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │   SQLite Database    │  │   Redis Cache        │             │
│  │  (Persistent Data)   │  │  (Session/Cache)     │             │
│  └──────────────────────┘  └──────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Background Processing                         │
│  ┌──────────────────────┐                                       │
│  │   Celery Workers     │                                       │
│  │  (File Monitoring)   │                                       │
│  │  (API Sync)          │                                       │
│  │  (Metadata Enrichment)                                       │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │   OMDB API           │  │   TVDB API           │             │
│  │  (Movie Metadata)    │  │  (TV Show Metadata)  │             │
│  └──────────────────────┘  └──────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Communication Flow

### 2.1 Request/Response Cycle

```
User Action (Frontend)
    ↓
React Component Event Handler
    ↓
API Service Call (Axios)
    ↓
HTTP Request to Backend
    ↓
Nginx Routes to FastAPI
    ↓
FastAPI Route Handler
    ↓
Service Layer Processing
    ↓
Database Query/Update
    ↓
HTTP Response (JSON)
    ↓
Axios Response Interceptor
    ↓
TanStack Query Cache Update
    ↓
Zustand Store Update
    ↓
React Component Re-render
    ↓
UI Update
```

### 2.2 Data Flow Example: Movie Search

```
User enters search term in SearchBar
    ↓
useSearch hook triggered
    ↓
Debounced API call: searchService.search(query)
    ↓
POST /api/search with query parameter
    ↓
Backend searchService processes query
    ↓
Database query for matching movies/shows
    ↓
Results returned as JSON
    ↓
TanStack Query caches results
    ↓
SearchResults component receives data
    ↓
Renders MovieCard and TVShowCard components
    ↓
User sees search results
```

---

## 3. API Contract

### 3.1 Request Format

**Standard Request:**
```http
GET /api/movies?page=1&limit=20&sort=-created_at HTTP/1.1
Host: yourdomain.com
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body (POST/PUT):**
```json
{
  "title": "The Matrix",
  "year": 1999,
  "plot": "A computer hacker learns...",
  "rating": 8.7,
  "runtime": 136,
  "genres": ["Action", "Sci-Fi"]
}
```

### 3.2 Response Format

**Success Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "The Matrix",
    "year": 1999,
    "rating": 8.7
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "year": "Must be between 1900 and 2024"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3.3 HTTP Status Codes

| Code | Meaning | Frontend Action |
|------|---------|-----------------|
| 200 | Success | Update UI with data |
| 201 | Created | Show success notification |
| 400 | Bad Request | Show validation errors |
| 401 | Unauthorized | Redirect to login |
| 404 | Not Found | Show 404 page |
| 409 | Conflict | Show conflict error |
| 429 | Rate Limited | Show rate limit message |
| 500 | Server Error | Show error notification |
| 503 | Service Unavailable | Show maintenance message |

---

## 4. Frontend-Backend Integration Points

### 4.1 Movie Management

**Frontend Components:**
- `MovieList` - Displays paginated movie list
- `MovieCard` - Shows movie summary
- `MovieDetail` - Shows full movie information
- `MovieForm` - Create/edit movie

**Backend Endpoints:**
- `GET /api/movies` - List movies
- `GET /api/movies/{id}` - Get movie details
- `POST /api/movies` - Create movie
- `PUT /api/movies/{id}` - Update movie
- `DELETE /api/movies/{id}` - Delete movie
- `POST /api/movies/{id}/sync-metadata` - Sync with OMDB

**Data Flow:**
```
MovieList Component
    ↓
useMovies Hook (TanStack Query)
    ↓
movieService.getMovies()
    ↓
GET /api/movies
    ↓
Backend fetches from database
    ↓
Returns paginated results
    ↓
TanStack Query caches
    ↓
MovieCard components render
```

### 4.2 TV Show Management

**Frontend Components:**
- `TVShowList` - Displays paginated TV show list
- `TVShowCard` - Shows TV show summary
- `TVShowDetail` - Shows full TV show information
- `SeasonList` - Shows seasons
- `EpisodeList` - Shows episodes

**Backend Endpoints:**
- `GET /api/tv-shows` - List TV shows
- `GET /api/tv-shows/{id}` - Get TV show details
- `GET /api/tv-shows/{id}/seasons` - Get seasons
- `GET /api/tv-shows/{id}/seasons/{season_id}/episodes` - Get episodes
- `POST /api/tv-shows` - Create TV show
- `PUT /api/tv-shows/{id}` - Update TV show
- `DELETE /api/tv-shows/{id}` - Delete TV show
- `POST /api/tv-shows/{id}/sync-metadata` - Sync with TVDB

### 4.3 Search Functionality

**Frontend Components:**
- `SearchBar` - Input field with autocomplete
- `SearchResults` - Display search results
- `AdvancedSearch` - Advanced filtering

**Backend Endpoints:**
- `GET /api/search` - Global search
- `GET /api/search/advanced` - Advanced search with filters

**Data Flow:**
```
User types in SearchBar
    ↓
useDebounce Hook (300ms delay)
    ↓
useSearch Hook triggered
    ↓
searchService.search(query)
    ↓
GET /api/search?q=query
    ↓
Backend searches database
    ↓
Returns matching movies and TV shows
    ↓
SearchResults component renders
```

### 4.4 File Management

**Frontend Components:**
- `FileQueue` - Shows file processing queue
- `FileQueueItem` - Individual file status
- `FileDetails` - File technical information

**Backend Endpoints:**
- `GET /api/files` - List files
- `GET /api/files/{id}` - Get file details
- `POST /api/files/{id}/rescan` - Rescan file
- `POST /api/files/import` - Manual file import

**Background Tasks:**
- `analyze_file` - FFPROBE analysis
- `enrich_metadata` - API metadata lookup
- `sync_metadata` - Periodic refresh

### 4.5 Cache Management

**Frontend Components:**
- `CacheSettings` - Cache management UI

**Backend Endpoints:**
- `GET /api/cache/stats` - Cache statistics
- `DELETE /api/cache` - Clear cache
- `POST /api/cache/cleanup` - Cleanup expired entries

---

## 5. State Synchronization

### 5.1 Frontend State Management

**Zustand Stores:**
```typescript
// Movie Store
const movieStore = {
  movies: [],
  selectedMovie: null,
  loading: false,
  error: null,
  pagination: { page: 1, limit: 20, total: 0 },
  filters: {}
};

// TV Show Store
const tvShowStore = {
  tvShows: [],
  selectedShow: null,
  selectedSeason: null,
  loading: false,
  error: null,
  pagination: { page: 1, limit: 20, total: 0 },
  filters: {}
};

// UI Store
const uiStore = {
  sidebarOpen: true,
  notifications: [],
  modals: {}
};
```

### 5.2 TanStack Query Integration

```typescript
// Automatic cache management
const { data, isLoading, error } = useQuery({
  queryKey: ['movies', page, filters],
  queryFn: () => movieService.getMovies(page, filters),
  staleTime: 5 * 60 * 1000,  // 5 minutes
  gcTime: 10 * 60 * 1000,     // 10 minutes
});

// Automatic refetch on window focus
// Automatic background refetch
// Automatic cache invalidation
```

### 5.3 Real-time Updates

**Polling Strategy:**
```typescript
// Refetch file queue every 5 seconds
useQuery({
  queryKey: ['fileQueue'],
  queryFn: () => fileService.getQueue(),
  refetchInterval: 5000,
});
```

**WebSocket Strategy (Future):**
```typescript
// Real-time file processing updates
useEffect(() => {
  const ws = new WebSocket('wss://yourdomain.com/ws/files');
  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    updateFileQueue(update);
  };
}, []);
```

---

## 6. Error Handling

### 6.1 Frontend Error Handling

```typescript
// API Error Interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      // Show rate limit message
      showNotification('Rate limit exceeded. Please try again later.');
    } else if (error.response?.status >= 500) {
      // Show server error
      showNotification('Server error. Please try again later.');
    }
    return Promise.reject(error);
  }
);
```

### 6.2 Backend Error Handling

```python
# FastAPI error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": exc.detail.get("code"),
                "message": exc.detail.get("message"),
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 6.3 User Feedback

**Toast Notifications:**
```typescript
// Success
showNotification('Movie added successfully', 'success');

// Error
showNotification('Failed to add movie', 'error');

// Warning
showNotification('This action cannot be undone', 'warning');

// Info
showNotification('Syncing metadata...', 'info');
```

---

## 7. Performance Optimization

### 7.1 Frontend Optimization

**Code Splitting:**
```typescript
const MovieDetail = lazy(() => import('./pages/MovieDetail'));
const TVShowDetail = lazy(() => import('./pages/TVShowDetail'));
```

**Image Optimization:**
```typescript
<img 
  src={posterUrl} 
  alt={title}
  loading="lazy"
  srcSet={`${posterUrl}?w=300 300w, ${posterUrl}?w=600 600w`}
/>
```

**Query Caching:**
```typescript
// Cache movie list for 5 minutes
staleTime: 5 * 60 * 1000
```

### 7.2 Backend Optimization

**Database Indexing:**
```sql
CREATE INDEX idx_movies_title ON movies(title);
CREATE INDEX idx_tv_shows_title ON tv_shows(title);
```

**Query Optimization:**
```python
# Use select_related for foreign keys
movies = db.query(Movie).options(
    selectinload(Movie.files)
).all()
```

**Response Caching:**
```python
@app.get("/movies")
@cache(expire=300)  # 5 minutes
async def get_movies():
    return await movieService.getMovies()
```

### 7.3 Network Optimization

**Gzip Compression:**
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

**HTTP/2:**
```nginx
listen 443 ssl http2;
```

**Asset Caching:**
```nginx
location ~* \.(js|css|png|jpg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 8. Security Integration

### 8.1 Frontend Security

**CSRF Protection:**
```typescript
// Include CSRF token in requests
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
api.defaults.headers.common['X-CSRF-Token'] = csrfToken;
```

**XSS Prevention:**
```typescript
// React escapes by default
<div>{userInput}</div>  // Safe

// Use dangerouslySetInnerHTML only for trusted content
<div dangerouslySetInnerHTML={{ __html: trustedHTML }} />
```

**Secure Storage:**
```typescript
// Store sensitive data in memory, not localStorage
const authToken = useRef(null);

// Use httpOnly cookies for tokens (set by backend)
```

### 8.2 Backend Security

**CORS Configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Rate Limiting:**
```python
@app.get("/api/movies")
@limiter.limit("100/minute")
async def get_movies():
    pass
```

**Input Validation:**
```python
class MovieCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    year: int = Field(..., ge=1900, le=2100)
    rating: float = Field(..., ge=0, le=10)
```

---

## 9. Deployment Integration

### 9.1 Docker Compose Setup

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://app:8000/api
    depends_on:
      - app

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/media.db
    volumes:
      - ./data:/app/data
      - /media:/media

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery-worker:
    build: .
    command: celery -A app.tasks.celery_app worker
    depends_on:
      - redis
      - app
```

### 9.2 Nginx Configuration

```nginx
upstream frontend {
    server frontend:3000;
}

upstream backend {
    server app:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://frontend;
    }

    location /api {
        proxy_pass http://backend;
    }
}
```

---

## 10. Development Workflow

### 10.1 Local Development

```bash
# Terminal 1: Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Terminal 3: Celery Worker
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker

# Terminal 4: Redis
docker run -p 6379:6379 redis:7-alpine
```

### 10.2 Testing Integration

```bash
# Backend tests
pytest tests/

# Frontend tests
npm run test

# E2E tests
npm run test:e2e
```

### 10.3 API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Frontend Storybook:** http://localhost:6006

---

## 11. Monitoring & Debugging

### 11.1 Frontend Debugging

```typescript
// Enable debug logging
localStorage.setItem('debug', 'app:*');

// React DevTools
// Redux DevTools (if using Redux)
// Network tab in browser DevTools
```

### 11.2 Backend Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()

# Check logs
docker-compose logs -f app
```

### 11.3 Network Debugging

```bash
# Monitor API calls
curl -v http://localhost:8000/api/movies

# Check response headers
curl -i http://localhost:8000/api/movies

# Monitor WebSocket (if implemented)
wscat -c ws://localhost:8000/ws
```

---

## 12. Troubleshooting Common Issues

### 12.1 CORS Errors

**Problem:** "Access to XMLHttpRequest blocked by CORS policy"

**Solution:**
```python
# Backend: Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 12.2 API Connection Issues

**Problem:** Frontend can't connect to backend

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check frontend API URL
echo $VITE_API_URL

# Check network connectivity
docker-compose exec frontend curl http://app:8000/health
```

### 12.3 State Synchronization Issues

**Problem:** Frontend state doesn't match backend data

**Solution:**
```typescript
// Invalidate cache and refetch
queryClient.invalidateQueries({ queryKey: ['movies'] });

// Manual refetch
refetch();
```

### 12.4 Performance Issues

**Problem:** Slow API responses

**Solution:**
```bash
# Check backend logs
docker-compose logs app

# Monitor database queries
sqlite3 data/media.db "EXPLAIN QUERY PLAN SELECT ..."

# Check Celery queue
celery -A app.tasks.celery_app inspect active
```

---

## 13. Scaling Considerations

### 13.1 Horizontal Scaling

```yaml
# Multiple frontend instances
frontend:
  deploy:
    replicas: 3

# Multiple backend instances
app:
  deploy:
    replicas: 3

# Multiple Celery workers
celery-worker:
  deploy:
    replicas: 5
```

### 13.2 Database Scaling

```python
# Migrate from SQLite to PostgreSQL
DATABASE_URL = "postgresql://user:password@db:5432/media"
```

### 13.3 Caching Layer

```python
# Add Redis caching
REDIS_URL = "redis://redis:6379/0"
```

---

## Conclusion

This full-stack integration guide provides a comprehensive overview of how the React frontend and Python backend work together to create a complete media management system. The architecture emphasizes:

- **Clear Separation of Concerns:** Frontend handles UI, backend handles business logic
- **Efficient Communication:** RESTful API with JSON payloads
- **Robust Error Handling:** Graceful degradation and user feedback
- **Performance Optimization:** Caching, compression, and efficient queries
- **Security:** CORS, CSRF protection, input validation
- **Scalability:** Horizontal scaling and database optimization

The system is designed to be maintainable, testable, and ready for production deployment.
