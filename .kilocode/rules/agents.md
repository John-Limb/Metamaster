# MetaMaster - Agent Guidelines

## Project Overview

MetaMaster is a web-based media metadata management system for organizing and enriching movie and TV show libraries.

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, PostgreSQL, SQLAlchemy, Celery, Redis, HTTPX, Watchdog, FFmpeg-Python, structlog, Prometheus |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS 4, Zustand, TanStack Query, React Router 7, React Hook Form, Zod, Recharts, Radix UI |
| **Infrastructure** | Docker, Docker Compose, GitHub Actions CI/CD |

## Project Structure

```
/Users/john/Code/Metamaster/
├── app/                      # Backend application
│   ├── api/                  # API endpoints (FastAPI)
│   │   └── v1/               # API v1 routes
│   │       ├── cache/
│   │       ├── config/
│   │       ├── files/
│   │       ├── health/
│   │       ├── movies/
│   │       ├── tasks/
│   │       └── tv_shows/
│   ├── application/          # Business logic layer
│   │   ├── batch_operations/
│   │   ├── db_optimization/
│   │   ├── pattern_recognition/
│   │   └── search/
│   ├── core/                 # Core configuration
│   ├── domain/               # Domain models
│   │   ├── common/
│   │   ├── files/
│   │   ├── movies/
│   │   └── tv_shows/
│   ├── infrastructure/       # External integrations
│   │   ├── cache/            # Redis caching
│   │   ├── external_apis/    # OMDB, TVDB clients
│   │   ├── file_system/      # FFprobe, Watchdog
│   │   └── monitoring/       # Prometheus, error handling
│   └── tasks/                # Celery tasks
├── frontend/                 # React frontend
│   └── src/
│       ├── components/      # React components
│       ├── pages/           # Page components
│       ├── hooks/           # Custom hooks
│       ├── stores/          # Zustand stores
│       ├── services/        # API services
│       └── types/           # TypeScript types
├── alembic/                  # Database migrations
└── docs/                     # Documentation
```

## Key Conventions

### Backend (Python/FastAPI)
- **API Endpoints**: Located in `app/api/v1/*/endpoints.py`
- **Models**: SQLAlchemy models in `app/domain/*/models.py`
- **Schemas**: Pydantic schemas in `app/domain/*/schemas.py`
- **Services**: Business logic in `app/domain/*/service.py`
- **Tasks**: Celery tasks in `app/tasks/` and `app/application/*/service.py`
- **Caching**: Redis cache in `app/infrastructure/cache/redis_cache.py`

### Frontend (React/TypeScript)
- **Components**: Functional components with TypeScript
- **State**: Zustand for global state, TanStack Query for server state
- **Forms**: React Hook Form with Zod validation
- **Styling**: Tailwind CSS 4 with utility classes
- **Routing**: React Router 7 with lazy loading

### Database
- **ORM**: SQLAlchemy with async support
- **Migrations**: Alembic for schema versioning
- **Models**: Defined in domain layer under `app/domain/*/models.py`

## Core Principles

1. **Separation of Concerns** - Clear layering across the stack
2. **Async-First Design** - Non-blocking I/O operations
3. **Type Safety** - Pydantic (backend) and TypeScript (frontend)
4. **Multi-Level Caching** - Redis caching strategy to reduce API calls
5. **Rate Limiting** - Compliance with external API rate limits
6. **Observability** - Comprehensive error handling and monitoring
7. **Docker-First Deployment** - Containerized services with orchestration
8. **CI/CD Automation** - GitHub Actions with conventional commits

## Main Features

- Media library management with detailed metadata (ratings, plots, genres)
- Automatic file detection via Watchdog directory monitoring
- Multi-level Redis caching to reduce API calls
- REST API with Swagger/ReDoc documentation
- Modern React frontend with file navigation
- Docker deployment with multi-service orchestration
- Batch operations with progress tracking

## API Integrations

- **OMDB API**: Movie metadata (http://www.omdbapi.com/)
- **TVDB API**: TV show metadata (https://www.thetvdb.com/)
- **FFprobe**: Media file analysis (resolution, bitrate, codec)

## Background Processing

- **Celery**: Async task queue with Redis broker
- **Queues**: Specialized queues for different task types
- **Beat**: Scheduled tasks for periodic operations

## Development Guidelines

- limit cyclomatic complexity to < 10
- Never commit API keys or secrets
- Validate all user inputs
- Use parameterized queries for database access

### Running the Project
```bash
# Backend
docker-compose up -d
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

### Code Style
- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Strict mode, use interfaces over types
- **Commits**: Conventional commits format

### Testing
- **Backend**: pytest with async support
- **Frontend**: Vitest, Playwright for e2e

### Documentation
- API docs available at `/docs` (Swagger) and `/redoc` (ReDoc)
- Inline documentation with docstrings
