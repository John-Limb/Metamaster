# Media Management Web Tool - Technical Architecture Design

## 1. System Architecture Overview

### 1.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser / UI                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Web Application                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  REST API Endpoints                                      │   │
│  │  - Media CRUD operations                                 │   │
│  │  - Search and filtering                                  │   │
│  │  - Metadata retrieval                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────┬──────────────────────────────────────────────────┬─────┘
         │                                                  │
         ▼                                                  ▼
┌──────────────────────────┐                    ┌──────────────────────────┐
│   SQLite Database        │                    │  Background Task Queue   │
│  ┌────────────────────┐  │                    │  (Celery + Redis)        │
│  │ Movies Table       │  │                    │  ┌────────────────────┐  │
│  │ TV Shows Table     │  │                    │  │ File Monitoring    │  │
│  │ Episodes Table     │  │                    │  │ API Sync Tasks     │  │
│  │ File Metadata      │  │                    │  │ Metadata Updates   │  │
│  │ Cache Tables       │  │                    │  └────────────────────┘  │
│  └────────────────────┘  │                    └──────────────────────────┘
└──────────────────────────┘                             │
         ▲                                                │
         │                                                ▼
         │                                    ┌──────────────────────────┐
         │                                    │  File System Monitor     │
         │                                    │  (Watchdog Library)      │
         │                                    │  ┌────────────────────┐  │
         │                                    │  │ Watch Media Dir    │  │
         │                                    │  │ Detect New Files   │  │
         │                                    │  │ Pattern Matching   │  │
         │                                    │  └────────────────────┘  │
         │                                    └──────────────────────────┘
         │                                                │
         └────────────────────────────────────────────────┘
                        Database Updates
                        
┌─────────────────────────────────────────────────────────────────┐
│                    External APIs                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │   OMDB API           │  │   TVDB API           │             │
│  │  (Movie Metadata)    │  │  (TV Show Metadata)  │             │
│  └──────────────────────┘  └──────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    System Tools                                  │
│  ┌──────────────────────┐                                       │
│  │   FFPROBE            │                                       │
│  │  (File Analysis)     │                                       │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

1. **File Detection Flow:**
   - Watchdog monitors media directory for new files
   - Detects file creation/modification events
   - Triggers pattern matching to classify as movie or TV show
   - Queues file analysis task

2. **File Analysis Flow:**
   - FFPROBE analyzes file for resolution, bitrate, codec
   - File metadata stored in database
   - Triggers metadata lookup task

3. **Metadata Enrichment Flow:**
   - Pattern matching extracts title, year, season, episode
   - Queries OMDB (movies) or TVDB (TV shows)
   - Caches results in database
   - Updates media inventory

4. **API Request Flow:**
   - User requests media via REST API
   - FastAPI retrieves from database
   - Returns cached metadata or triggers background refresh

---

## 2. Technology Stack

### 2.1 Core Framework & Web Server
- **FastAPI** - Modern async Python web framework
  - Rationale: Built-in async support, automatic API documentation, excellent performance, type hints support
  - Alternative considered: Flask (simpler but less performant), Django (overkill for this use case)

### 2.2 Database
- **SQLite** - Embedded relational database
  - Rationale: Meets requirement, no separate database server needed, sufficient for single-instance deployment
  - ORM: SQLAlchemy for database abstraction and query building

### 2.3 Background Task Processing
- **Celery** - Distributed task queue
  - Rationale: Handles long-running tasks (file monitoring, API calls) without blocking web requests
  - Message Broker: Redis for task queue management
  - Alternative considered: APScheduler (simpler but less scalable)

### 2.4 File System Monitoring
- **Watchdog** - Cross-platform file system event monitoring
  - Rationale: Reliable, well-maintained, supports multiple platforms, efficient event handling
  - Alternative considered: inotify (Linux-only), polling (inefficient)

### 2.5 External API Integration
- **HTTPX** - Async HTTP client
  - Rationale: Async support, connection pooling, timeout handling
  - Alternative considered: Requests (synchronous, less efficient)

### 2.6 File Analysis
- **FFPROBE** - FFmpeg tool for media file analysis
  - Rationale: Industry standard, accurate metadata extraction, supports all media formats
  - Python wrapper: `ffmpeg-python` or direct subprocess calls

### 2.7 Containerization
- **Docker** - Container platform
  - Rationale: Meets requirement, ensures consistent environment across deployments
  - Docker Compose for multi-container orchestration (app + Redis)

### 2.8 Additional Libraries
- **Pydantic** - Data validation and settings management
- **python-dotenv** - Environment variable management
- **Requests-cache** - HTTP caching for API responses
- **APScheduler** - Scheduled tasks (periodic cleanup, cache refresh)
- **Logging** - Python standard logging with structured output

---

## 3. Database Schema

### 3.1 Entity Relationship Diagram

```
┌─────────────────────┐
│      Movies         │
├─────────────────────┤
│ id (PK)             │
│ title               │
│ year                │
│ omdb_id             │
│ plot                │
│ rating              │
│ runtime             │
│ genres              │
│ created_at          │
│ updated_at          │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│   MovieFiles        │
├─────────────────────┤
│ id (PK)             │
│ movie_id (FK)       │
│ file_path           │
│ file_size           │
│ resolution          │
│ bitrate             │
│ codec_video         │
│ codec_audio         │
│ duration            │
│ last_modified       │
│ created_at          │
└─────────────────────┘

┌─────────────────────┐
│     TVShows         │
├─────────────────────┤
│ id (PK)             │
│ title               │
│ tvdb_id             │
│ plot                │
│ rating              │
│ genres              │
│ status              │
│ created_at          │
│ updated_at          │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│     Seasons         │
├─────────────────────┤
│ id (PK)             │
│ show_id (FK)        │
│ season_number       │
│ tvdb_id             │
│ created_at          │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│     Episodes        │
├─────────────────────┤
│ id (PK)             │
│ season_id (FK)      │
│ episode_number      │
│ tvdb_id             │
│ title               │
│ plot                │
│ air_date            │
│ rating              │
│ created_at          │
│ updated_at          │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│   EpisodeFiles      │
├─────────────────────┤
│ id (PK)             │
│ episode_id (FK)     │
│ file_path           │
│ file_size           │
│ resolution          │
│ bitrate             │
│ codec_video         │
│ codec_audio         │
│ duration            │
│ last_modified       │
│ created_at          │
└─────────────────────┘

┌─────────────────────┐
│   APICache          │
├─────────────────────┤
│ id (PK)             │
│ api_type            │
│ query_key           │
│ response_data       │
│ expires_at          │
│ created_at          │
└─────────────────────┘

┌─────────────────────┐
│   FileQueue         │
├─────────────────────┤
│ id (PK)             │
│ file_path           │
│ status              │
│ media_type          │
│ error_message       │
│ created_at          │
│ processed_at        │
└─────────────────────┘
```

### 3.2 Table Definitions

#### Movies Table
```sql
CREATE TABLE movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    year INTEGER,
    omdb_id TEXT UNIQUE,
    plot TEXT,
    rating REAL,
    runtime INTEGER,
    genres TEXT,  -- JSON array stored as string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_movies_title ON movies(title);
CREATE INDEX idx_movies_omdb_id ON movies(omdb_id);
CREATE INDEX idx_movies_year ON movies(year);
```

#### MovieFiles Table
```sql
CREATE TABLE movie_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    file_size INTEGER,
    resolution TEXT,  -- e.g., "1920x1080"
    bitrate INTEGER,  -- in kbps
    codec_video TEXT,
    codec_audio TEXT,
    duration INTEGER,  -- in seconds
    last_modified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);
CREATE INDEX idx_movie_files_movie_id ON movie_files(movie_id);
CREATE INDEX idx_movie_files_path ON movie_files(file_path);
```

#### TVShows Table
```sql
CREATE TABLE tv_shows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    tvdb_id TEXT UNIQUE,
    plot TEXT,
    rating REAL,
    genres TEXT,  -- JSON array stored as string
    status TEXT,  -- "Continuing" or "Ended"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_tv_shows_title ON tv_shows(title);
CREATE INDEX idx_tv_shows_tvdb_id ON tv_shows(tvdb_id);
```

#### Seasons Table
```sql
CREATE TABLE seasons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id INTEGER NOT NULL,
    season_number INTEGER NOT NULL,
    tvdb_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES tv_shows(id) ON DELETE CASCADE,
    UNIQUE(show_id, season_number)
);
CREATE INDEX idx_seasons_show_id ON seasons(show_id);
```

#### Episodes Table
```sql
CREATE TABLE episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    tvdb_id TEXT UNIQUE,
    title TEXT,
    plot TEXT,
    air_date DATE,
    rating REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE CASCADE
);
CREATE INDEX idx_episodes_season_id ON episodes(season_id);
CREATE INDEX idx_episodes_tvdb_id ON episodes(tvdb_id);
```

#### EpisodeFiles Table
```sql
CREATE TABLE episode_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    file_size INTEGER,
    resolution TEXT,
    bitrate INTEGER,
    codec_video TEXT,
    codec_audio TEXT,
    duration INTEGER,
    last_modified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE CASCADE
);
CREATE INDEX idx_episode_files_episode_id ON episode_files(episode_id);
CREATE INDEX idx_episode_files_path ON episode_files(file_path);
```

#### APICache Table
```sql
CREATE TABLE api_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_type TEXT NOT NULL,  -- "omdb" or "tvdb"
    query_key TEXT NOT NULL,
    response_data TEXT NOT NULL,  -- JSON response
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(api_type, query_key)
);
CREATE INDEX idx_api_cache_expires ON api_cache(expires_at);
```

#### FileQueue Table
```sql
CREATE TABLE file_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    media_type TEXT,  -- "movie" or "tv_show"
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
CREATE INDEX idx_file_queue_status ON file_queue(status);
CREATE INDEX idx_file_queue_created ON file_queue(created_at);
```

### 3.3 Indexing Strategy

**Primary Indexes:**
- All primary keys (automatic)
- Foreign keys for join performance

**Search Indexes:**
- `movies.title` - for movie search
- `tv_shows.title` - for TV show search
- `movies.omdb_id`, `tv_shows.tvdb_id` - for API lookups

**File Path Indexes:**
- `movie_files.file_path`, `episode_files.file_path` - for duplicate detection

**Status/Time Indexes:**
- `file_queue.status` - for processing queue queries
- `api_cache.expires_at` - for cache cleanup

---

## 4. API Integration Strategy

### 4.1 OMDB API Integration

**Purpose:** Retrieve movie metadata (plot, rating, runtime, genres, etc.)

**Integration Points:**
- Movie title and year → OMDB search
- Cache results with 30-day TTL
- Fallback to local data if API fails

**Rate Limiting:**
- OMDB free tier: 1 request/second
- Implement queue-based request throttling
- Use exponential backoff for retries

**Error Handling:**
- Log API errors
- Retry failed requests with exponential backoff
- Store partial data if API unavailable

**Configuration:**
```
OMDB_API_KEY=<key>
OMDB_RATE_LIMIT=1  # requests per second
OMDB_CACHE_TTL=2592000  # 30 days in seconds
```

### 4.2 TVDB API Integration

**Purpose:** Retrieve TV show, season, and episode metadata

**Integration Points:**
- Show title → TVDB search
- Season/episode details → TVDB lookup
- Cache results with 30-day TTL

**Authentication:**
- TVDB requires API key and PIN
- Implement token refresh mechanism

**Rate Limiting:**
- TVDB free tier: 30 requests/10 seconds
- Implement sliding window rate limiter
- Queue requests to respect limits

**Error Handling:**
- Log API errors
- Retry with exponential backoff
- Store partial data if API unavailable

**Configuration:**
```
TVDB_API_KEY=<key>
TVDB_PIN=<pin>
TVDB_RATE_LIMIT=3  # requests per second (30/10)
TVDB_CACHE_TTL=2592000  # 30 days in seconds
```

### 4.3 Caching Strategy

**Multi-Level Caching:**

1. **Database Cache (APICache table)**
   - Store full API responses
   - TTL-based expiration
   - Automatic cleanup of expired entries

2. **In-Memory Cache (Redis)**
   - Cache frequently accessed metadata
   - 24-hour TTL for hot data
   - Reduces database queries

3. **HTTP Response Caching**
   - Cache API responses at HTTP client level
   - Use `requests-cache` library
   - 1-hour TTL for API responses

**Cache Invalidation:**
- Manual refresh endpoint for specific media
- Automatic refresh on file modification
- Periodic background refresh (weekly)

### 4.4 API Request Flow

```
User Request
    ↓
Check In-Memory Cache (Redis)
    ↓ (miss)
Check Database Cache (APICache)
    ↓ (miss)
Queue API Request Task
    ↓
Rate Limiter (respect API limits)
    ↓
Make HTTP Request
    ↓
Parse Response
    ↓
Store in Database Cache
    ↓
Store in Redis Cache
    ↓
Return to User
```

---

## 5. File Monitoring Approach

### 5.1 File System Monitoring

**Library:** Watchdog
- Cross-platform file system event monitoring
- Efficient event handling (uses OS-level APIs)
- Supports recursive directory watching

**Monitored Events:**
- File creation
- File modification
- File deletion (for cleanup)

**Configuration:**
```
MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
WATCH_RECURSIVE=true
WATCH_PATTERNS=["*.mp4", "*.mkv", "*.avi", "*.mov", "*.flv", "*.wmv"]
```

### 5.2 File Pattern Recognition

**Movie Pattern Matching:**
```
Patterns:
- Title (Year).ext
- Title - Year.ext
- Title.ext (if year not found, assume movie)

Examples:
- The Matrix (1999).mkv
- Inception-2010.mp4
- Avatar.avi
```

**TV Show Pattern Matching:**
```
Patterns:
- Show Title SxxExx.ext
- Show Title - SxxExx.ext
- Show Title/Season xx/SxxExx.ext
- Show Title/Season xx/Episode xx.ext

Examples:
- Breaking Bad S01E01.mkv
- Game of Thrones - S08E06.mp4
- The Office/Season 01/S01E01.avi
```

**Pattern Extraction Logic:**
```python
# Pseudo-code
def classify_media(file_path):
    filename = extract_filename(file_path)
    
    # Check for TV show patterns (SxxExx)
    if match_pattern(filename, r'S\d{2}E\d{2}'):
        return classify_tv_show(filename)
    
    # Check for year pattern (YYYY)
    if match_pattern(filename, r'\(\d{4}\)'):
        return classify_movie(filename)
    
    # Default to movie if ambiguous
    return 'movie'
```

### 5.3 File Detection Workflow

```
File Created/Modified
    ↓
Watchdog Event Handler
    ↓
Extract filename and path
    ↓
Pattern matching (movie vs TV show)
    ↓
Check if already in FileQueue
    ↓ (new file)
Add to FileQueue with status='pending'
    ↓
Queue background task: analyze_file
    ↓
Task: Run FFPROBE on file
    ↓
Extract resolution, bitrate, codec
    ↓
Queue background task: enrich_metadata
    ↓
Task: Query OMDB/TVDB
    ↓
Update database with metadata
    ↓
Mark FileQueue entry as 'completed'
```

### 5.4 Duplicate Detection

- Check `file_path` uniqueness in `movie_files` and `episode_files`
- Skip processing if file already exists
- Update `last_modified` timestamp if file changed

---

## 6. Application Structure

### 6.1 Project Directory Structure

```
media-management-tool/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration management
│   ├── database.py             # Database setup and session management
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── movie.py            # Movie SQLAlchemy models
│   │   ├── tv_show.py          # TV show SQLAlchemy models
│   │   ├── file.py             # File metadata models
│   │   └── cache.py            # Cache models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── movie.py            # Pydantic schemas for movies
│   │   ├── tv_show.py          # Pydantic schemas for TV shows
│   │   └── file.py             # Pydantic schemas for files
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── movies.py       # Movie endpoints
│   │   │   ├── tv_shows.py     # TV show endpoints
│   │   │   ├── search.py       # Search endpoints
│   │   │   └── health.py       # Health check endpoints
│   │   └── dependencies.py     # Shared dependencies
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── movie_service.py    # Movie business logic
│   │   ├── tv_service.py       # TV show business logic
│   │   ├── file_service.py     # File analysis logic
│   │   ├── omdb_service.py     # OMDB API integration
│   │   ├── tvdb_service.py     # TVDB API integration
│   │   └── cache_service.py    # Caching logic
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py       # Celery configuration
│   │   ├── file_monitor.py     # File monitoring task
│   │   ├── file_analysis.py    # FFPROBE analysis task
│   │   ├── metadata_sync.py    # API metadata sync task
│   │   └── cleanup.py          # Periodic cleanup tasks
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # Logging configuration
│   │   ├── patterns.py         # File pattern matching
│   │   ├── ffprobe.py          # FFPROBE wrapper
│   │   ├── validators.py       # Input validation
│   │   └── exceptions.py       # Custom exceptions
│   │
│   └── middleware/
│       ├── __init__.py
│       └── error_handler.py    # Global error handling
│
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   ├── test_tasks/
│   └── test_utils/
│
├── docker/
│   ├── Dockerfile              # Application container
│   ├── Dockerfile.redis        # Redis container (optional)
│   └── docker-compose.yml      # Multi-container orchestration
│
├── migrations/
│   └── init_schema.sql         # Database schema initialization
│
├── config/
│   ├── .env.example            # Example environment variables
│   └── logging.yaml            # Logging configuration
│
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── .gitignore
```

### 6.2 Module Organization

**Models Layer** (`app/models/`)
- SQLAlchemy ORM models
- Database table definitions
- Relationships and constraints

**Schemas Layer** (`app/schemas/`)
- Pydantic request/response models
- Input validation
- API documentation

**Services Layer** (`app/services/`)
- Business logic
- API integrations
- Data transformations
- Caching logic

**API Layer** (`app/api/`)
- FastAPI route handlers
- Request/response handling
- HTTP status codes

**Tasks Layer** (`app/tasks/`)
- Celery task definitions
- Background job processing
- Scheduled tasks

**Utils Layer** (`app/utils/`)
- Helper functions
- Pattern matching
- File analysis wrappers
- Logging

### 6.3 Configuration Management

**Environment-Based Configuration:**
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./media.db"
    
    # API Keys
    OMDB_API_KEY: str
    TVDB_API_KEY: str
    TVDB_PIN: str
    
    # File Monitoring
    MEDIA_WATCH_PATHS: list = ["/media/movies", "/media/tv_shows"]
    WATCH_PATTERNS: list = ["*.mp4", "*.mkv", "*.avi"]
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Caching
    CACHE_TTL: int = 2592000  # 30 days
    REDIS_URL: str = "redis://localhost:6379/2"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Environment Variables (.env):**
```
DATABASE_URL=sqlite:///./media.db
OMDB_API_KEY=your_key_here
TVDB_API_KEY=your_key_here
TVDB_PIN=your_pin_here
MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
REDIS_URL=redis://redis:6379/2
LOG_LEVEL=INFO
```

---

## 7. Docker Strategy

### 7.1 Container Architecture

**Multi-Container Setup:**
1. **Application Container** - FastAPI web application
2. **Redis Container** - Message broker and cache
3. **Celery Worker Container** - Background task processing (optional, can run in app container)

### 7.2 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/
COPY migrations/ ./migrations/

# Create media directories
RUN mkdir -p /media/movies /media/tv_shows

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.3 Docker Compose Configuration

```yaml
# docker-compose.yml
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
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - /media/movies:/media/movies
      - /media/tv_shows:/media/tv_shows
    depends_on:
      - redis
    networks:
      - media-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: media-management-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - media-network
    restart: unless-stopped

  celery-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: media-management-celery
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=sqlite:///./data/media.db
      - OMDB_API_KEY=${OMDB_API_KEY}
      - TVDB_API_KEY=${TVDB_API_KEY}
      - TVDB_PIN=${TVDB_PIN}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - REDIS_URL=redis://redis:6379/2
      - MEDIA_WATCH_PATHS=["/media/movies", "/media/tv_shows"]
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - /media/movies:/media/movies
      - /media/tv_shows:/media/tv_shows
    depends_on:
      - redis
      - app
    networks:
      - media-network
    restart: unless-stopped

volumes:
  redis-data:

networks:
  media-network:
    driver: bridge
```

### 7.4 Volume Mounting Strategy

**Data Volumes:**
- `./data:/app/data` - Persistent database and cache storage
- `/media/movies:/media/movies` - Host movie directory
- `/media/tv_shows:/media/tv_shows` - Host TV show directory

**Benefits:**
- Database persists across container restarts
- Media files accessible from host
- Easy backup of database

### 7.5 Environment Configuration

**Docker Environment Variables:**
- All sensitive data (API keys) passed via environment
- Configuration file at `config/.env`
- Example file at `config/.env.example`

**Startup Sequence:**
1. Redis starts first
2. App container starts, initializes database
3. Celery worker starts, connects to Redis
4. File monitoring begins automatically

---

## 8. Key Technical Decisions & Rationale

### 8.1 Web Framework: FastAPI

**Decision:** Use FastAPI instead of Flask or Django

**Rationale:**
- **Async Support:** Native async/await for non-blocking I/O (API calls, file operations)
- **Performance:** Significantly faster than Flask, comparable to Node.js
- **Type Safety:** Pydantic integration for automatic validation and documentation
- **Auto Documentation:** Automatic OpenAPI/Swagger documentation
- **Modern Python:** Leverages Python 3.7+ features
- **Scalability:** Better suited for high-concurrency scenarios

**Trade-offs:**
- Steeper learning curve than Flask
- Smaller ecosystem than Django
- Overkill for very simple applications

### 8.2 Background Task Processing: Celery + Redis

**Decision:** Use Celery with Redis broker instead of APScheduler or threading

**Rationale:**
- **Scalability:** Can distribute tasks across multiple workers
- **Reliability:** Task persistence and retry mechanisms
- **Monitoring:** Built-in task monitoring and result tracking
- **Flexibility:** Supports scheduled tasks, periodic tasks, and event-driven tasks
- **Production-Ready:** Battle-tested in production environments

**Trade-offs:**
- Additional infrastructure (Redis)
- More complex setup than simple threading
- Overkill for very simple background tasks

### 8.3 File Monitoring: Watchdog

**Decision:** Use Watchdog instead of polling or inotify

**Rationale:**
- **Cross-Platform:** Works on Linux, macOS, Windows
- **Efficient:** Uses OS-level APIs (inotify, FSEvents, ReadDirectoryChangesW)
- **Reliable:** Well-maintained, widely used
- **Event-Driven:** Immediate notification of file changes
- **Recursive Watching:** Supports nested directory monitoring

**Trade-offs:**
- External dependency
- Slight overhead compared to raw OS APIs

### 8.4 Database: SQLite

**Decision:** Use SQLite as specified in requirements

**Rationale:**
- **Simplicity:** No separate database server needed
- **Portability:** Single file database
- **Performance:** Sufficient for single-instance deployments
- **Reliability:** ACID compliance
- **Backup:** Easy file-based backups

**Limitations:**
- Not suitable for high-concurrency write scenarios
- Limited to single-instance deployments
- Scaling requires migration to PostgreSQL/MySQL

### 8.5 API Integration: Caching Strategy

**Decision:** Implement multi-level caching (database + Redis + HTTP)

**Rationale:**
- **Performance:** Reduces API calls and database queries
- **Cost:** Minimizes API usage (important for rate-limited APIs)
- **Reliability:** Graceful degradation if APIs are unavailable
- **Flexibility:** Multiple cache layers for different use cases

**Cache Hierarchy:**
1. In-Memory (Redis) - Fastest, 24-hour TTL
2. Database (APICache) - Persistent, 30-day TTL
3. HTTP Client - Transparent, 1-hour TTL

### 8.6 File Pattern Recognition: Regex-Based

**Decision:** Use regex patterns for file classification

**Rationale:**
- **Simplicity:** Easy to understand and maintain
- **Performance:** Fast pattern matching
- **Flexibility:** Easy to add new patterns
- **Accuracy:** Covers most common naming conventions

**Limitations:**
- Cannot handle all edge cases
- Requires manual pattern updates for new conventions
- May misclassify ambiguous filenames

**Fallback Strategy:**
- Default to movie classification if ambiguous
- Allow manual override via API
- Learn from user corrections

### 8.7 Error Handling & Logging

**Decision:** Structured logging with centralized error handling

**Rationale:**
- **Debugging:** Easier to trace issues across components
- **Monitoring:** Can aggregate logs for alerting
- **Performance:** Minimal overhead
- **Compliance:** Audit trail for operations

**Implementation:**
- Python `logging` module with JSON formatting
- Centralized error handler middleware
- Structured logging for all operations
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### 8.8 API Rate Limiting

**Decision:** Implement client-side rate limiting with queue-based throttling

**Rationale:**
- **Compliance:** Respects API provider limits
- **Reliability:** Prevents API blocks
- **Fairness:** Ensures fair distribution of requests
- **Simplicity:** No external rate limiting service needed

**Implementation:**
- Queue-based request throttling
- Exponential backoff for retries
- Per-API rate limit configuration
- Monitoring of rate limit status

---

## 9. Security Considerations

### 9.1 API Key Management
- Store API keys in environment variables (never in code)
- Use `.env` file for local development (not committed to git)
- Rotate keys periodically
- Monitor API usage for suspicious activity

### 9.2 Database Security
- SQLite file permissions restricted to application user
- Database backups encrypted
- No sensitive data in logs

### 9.3 File System Security
- Validate file paths to prevent directory traversal
- Run application with minimal required permissions
- Monitor file system for unauthorized changes

### 9.4 API Security
- Implement CORS if frontend is separate
- Rate limiting on API endpoints
- Input validation on all endpoints
- HTTPS in production

---

## 10. Monitoring & Observability

### 10.1 Health Checks
- `/health` endpoint for container orchestration
- Database connectivity check
- Redis connectivity check
- File system accessibility check

### 10.2 Metrics
- API response times
- Task processing times
- API call success/failure rates
- Cache hit/miss rates
- File processing queue depth

### 10.3 Logging
- Application logs to stdout (Docker best practice)
- Structured JSON logging for parsing
- Log aggregation ready (ELK, Datadog, etc.)

---

## 11. Deployment Considerations

### 11.1 Development Environment
```bash
# Local setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d redis
python -m app.main
```

### 11.2 Production Deployment
- Use Docker Compose or Kubernetes
- Reverse proxy (Nginx) for SSL/TLS
- Persistent volume for database
- Environment-specific configuration
- Automated backups of database

### 11.3 Scaling Considerations
- Multiple Celery workers for parallel task processing
- Redis cluster for high availability
- Database migration to PostgreSQL for multi-instance
- Load balancing for multiple app instances

---

## 12. Future Enhancements

### 12.1 Potential Features
- User authentication and authorization
- Multi-user support with separate libraries
- Streaming integration (Plex, Jellyfin)
- Advanced search and filtering
- Recommendation engine
- Mobile app
- Subtitle management
- Watched status tracking

### 12.2 Performance Optimizations
- Database query optimization
- Caching layer improvements
- Async file I/O
- Batch API requests
- Database connection pooling

### 12.3 Reliability Improvements
- Distributed tracing
- Alerting system
- Automated recovery
- Backup and restore procedures
- Disaster recovery plan

---

## Conclusion

This architecture provides a scalable, maintainable foundation for a media management web tool. The design emphasizes:

- **Modularity:** Clear separation of concerns
- **Scalability:** Async processing and background tasks
- **Reliability:** Error handling and caching strategies
- **Maintainability:** Well-organized code structure
- **Observability:** Comprehensive logging and monitoring

The technology choices balance simplicity with production-readiness, making the system suitable for both development and deployment in containerized environments.
