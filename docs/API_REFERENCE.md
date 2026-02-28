# API Reference

Interactive documentation is available when the application is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login (returns JWT access + refresh tokens) |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Logout |
| `GET` | `/api/v1/auth/me` | Get current user |
| `PUT` | `/api/v1/auth/change-password` | Change password |
| `GET` | `/api/v1/auth/profile` | Get user profile |

### Movies

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/movies` | List movies |
| `POST` | `/api/v1/movies` | Create movie |
| `GET` | `/api/v1/movies/{id}` | Get movie details |
| `PUT` | `/api/v1/movies/{id}` | Update movie |
| `DELETE` | `/api/v1/movies/{id}` | Delete movie |
| `POST` | `/api/v1/movies/{id}/enrich` | Trigger TMDB metadata enrichment |

### TV Shows

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tv-shows` | List TV shows |
| `POST` | `/api/v1/tv-shows` | Create TV show |
| `GET` | `/api/v1/tv-shows/{id}` | Get TV show details |
| `PUT` | `/api/v1/tv-shows/{id}` | Update TV show |
| `DELETE` | `/api/v1/tv-shows/{id}` | Delete TV show |
| `POST` | `/api/v1/tv-shows/{id}/enrich` | Trigger TMDB metadata enrichment |

### Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/files` | List files |
| `GET` | `/api/v1/files/{id}` | Get file details |
| `POST` | `/api/v1/files/scan` | Trigger directory scan |

### Storage

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/storage/analytics` | Storage analytics |
| `GET` | `/api/v1/storage/usage` | Storage usage by media type |

### Organisation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/organisation` | Get organisation settings |
| `PUT` | `/api/v1/organisation` | Update organisation settings |

### Cache

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/cache` | Cache info |
| `DELETE` | `/api/v1/cache` | Clear all cache |
| `GET` | `/api/v1/cache/{key}` | Get cache value by key |
| `DELETE` | `/api/v1/cache/{key}` | Delete cache key |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/config` | Get configuration |
| `PUT` | `/api/v1/config` | Update configuration |

### Enrichment

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/enrichment/pending` | List items pending enrichment |

### Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/queue/stats` | Queue statistics |
| `GET` | `/api/v1/queue/tasks` | List queue tasks |
| `GET` | `/api/v1/queue/tasks/{task_id}` | Get task details |
| `GET` | `/api/v1/queue/tasks/{task_id}/progress` | Get task progress |
| `POST` | `/api/v1/queue/tasks/{task_id}/retry` | Retry a task |
| `POST` | `/api/v1/queue/tasks/{task_id}/cancel` | Cancel a task |
| `POST` | `/api/v1/queue/clear-completed` | Clear completed tasks |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tasks` | List tasks |
| `GET` | `/api/v1/tasks/{task_id}` | Get task details |
| `DELETE` | `/api/v1/tasks/{task_id}` | Cancel task |
| `POST` | `/api/v1/tasks/{task_id}/retry` | Retry failed task |
| `GET` | `/api/v1/tasks/errors` | List task errors |
| `GET` | `/api/v1/tasks/errors/{error_id}` | Get error details |
| `POST` | `/api/v1/tasks/batch/metadata-sync` | Start batch metadata sync |
| `POST` | `/api/v1/tasks/batch/file-import` | Start batch file import |
| `GET` | `/api/v1/tasks/batch` | List batch operations |
| `GET` | `/api/v1/tasks/batch/{batch_id}` | Get batch operation details |
| `GET` | `/api/v1/tasks/batch/{batch_id}/progress` | Get batch operation progress |
| `DELETE` | `/api/v1/tasks/batch/{batch_id}` | Cancel batch operation |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health/` | Basic health check |
| `GET` | `/health/db` | Database connectivity check |
