# MetaMaster

[![CI Pipeline](https://github.com/John-Limb/metamaster/actions/workflows/ci.yml/badge.svg)](https://github.com/John-Limb/metamaster/actions/workflows/ci.yml)
[![Docker Build](https://github.com/John-Limb/metamaster/actions/workflows/docker.yml/badge.svg)](https://github.com/John-Limb/metamaster/actions/workflows/docker.yml)
[![Code Quality](https://github.com/John-Limb/metamaster/actions/workflows/code-quality.yml/badge.svg)](https://github.com/John-Limb/metamaster/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/John-Limb/metamaster/branch/main/graph/badge.svg)](https://codecov.io/gh/John-Limb/metamaster)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/aa284990b5e0484a91dcfdf720b4a658)](https://app.codacy.com?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
A comprehensive web-based media metadata management system for organizing and managing your movie and TV show library with automatic metadata enrichment from OMDB and TVDB APIs.

## Features

- **Media Library Management**: Organize movies and TV shows with detailed metadata
- **Automatic File Detection**: Monitor directories for new media files
- **Metadata Enrichment**: Automatic metadata lookup from OMDB (movies) and TVDB (TV shows)
- **File Analysis**: Extract technical details (resolution, bitrate, codec) using FFPROBE
- **Caching System**: Multi-level Redis caching to reduce API calls
- **Background Processing**: Celery-based task queue for long-running operations
- **REST API**: Comprehensive REST API with automatic documentation
- **Web Interface**: Modern React-based frontend with file navigation and management
- **Docker Support**: Full Docker and Docker Compose setup with multi-service orchestration

---

## Technology Stack

### Backend

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | FastAPI | 0.104.1 | ASGI web framework |
| **ASGI Server** | Uvicorn | 0.24.0 | Production server |
| **Database** | PostgreSQL | 15 | Primary data store |
| **ORM** | SQLAlchemy | 2.0.23 | Database abstraction |
| **Migrations** | Alembic | 1.12.1 | Schema migrations |
| **Task Queue** | Celery | 5.3.4 | Background job processing |
| **Message Broker** | Redis | 7 | Celery broker & caching |
| **HTTP Client** | HTTPX | 0.25.2 | Async HTTP requests |
| **File Monitoring** | Watchdog | 3.0.0 | Directory monitoring |
| **Media Analysis** | FFmpeg-Python | 0.2.0 | FFPROBE wrapper |
| **Logging** | structlog | 23.2.0 | Structured logging |
| **Monitoring** | Prometheus Client | 0.17.1 | Metrics collection |

### Frontend

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | React | 19.2.0 | UI library |
| **Language** | TypeScript | 5.9 | Type safety |
| **Build Tool** | Vite | 7.3.1 | Fast bundler |
| **Styling** | Tailwind CSS | 4.1 | Utility-first CSS |
| **State Management** | Zustand | 5.0.11 | Global state |
| **Server State** | TanStack Query | 5.90.20 | API caching |
| **Routing** | React Router | 7.13.0 | Client-side routing |
| **Forms** | React Hook Form | 7.71.1 | Form handling |
| **Validation** | Zod | 4.3.6 | Schema validation |
| **Charts** | Recharts | 3.7.0 | Data visualization |
| **Icons** | Lucide React | 0.563.0 | Icon library |

### Infrastructure

| Category | Technology | Purpose |
|----------|------------|---------|
| **Containerization** | Docker | Application containers |
| **Orchestration** | Docker Compose | Multi-service deployment |
| **Registry** | GitHub Container Registry | Image storage |
| **CI/CD** | GitHub Actions | Automated pipelines |

---

## Development Tools

### Package Management

| Tool | Location | Purpose |
|------|----------|---------|
| pip | Backend | Python package manager |
| npm | Frontend | Node.js package manager |

### Build Tools

| Tool | Location | Purpose |
|------|----------|---------|
| setuptools | Backend | Python build backend (pyproject.toml) |
| Vite | Frontend | Fast build tool with Terser minification |

### Code Quality

#### Backend

| Tool | Version | Purpose |
|------|---------|---------|
| Black | 23.12.0 | Code formatter |
| isort | 5.13.2 | Import sorter |
| mypy | 1.7.1 | Static type checker |
| flake8 | 6.1.0 | Linter |

#### Frontend

| Tool | Purpose |
|------|---------|
| ESLint 9 | Linting with flat config |
| Prettier | Code formatting |
| TypeScript | Compile-time type checking |

### Testing Frameworks

#### Backend

| Tool | Version | Purpose |
|------|---------|---------|
| pytest | 7.4.3 | Test framework |
| pytest-asyncio | 0.21.1 | Async test support |
| pytest-cov | 4.1.0 | Coverage reporting |
| pytest-benchmark | 4.0.0 | Performance benchmarks |
| locust | 2.17.0 | Load testing |

#### Frontend

| Tool | Purpose |
|------|---------|
| Vitest | Unit testing with coverage |
| Playwright | End-to-end testing |
| Testing Library | React component testing |

### Containerization

| Tool | Purpose |
|------|---------|
| Docker | Application containerization |
| Docker Compose | Multi-service orchestration |

### CI/CD

| Workflow | Location | Purpose |
|----------|----------|---------|
| `ci.yml` | `.github/workflows/` | Backend CI pipeline |
| `docker.yml` | `.github/workflows/` | Docker build & push |
| `code-quality.yml` | `.github/workflows/` | SonarQube analysis |
| `deploy.yml` | `.github/workflows/` | Deployment pipeline |
| `lint.yml` | `.github/workflows/` | Linting checks |
| `scheduled-tests.yml` | `.github/workflows/` | Nightly/weekly tests |
| `ci.yml` | `frontend/.github/workflows/` | Frontend CI pipeline |
| `lighthouse.yml` | `frontend/.github/workflows/` | Performance monitoring |
| `security.yml` | `frontend/.github/workflows/` | Security scanning |

---

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose |
|----------|-----------------|---------|
| Python | 3.9+ | Backend runtime |
| Node.js | 18.0+ | Frontend runtime |
| Docker | 20.10+ | Containerization (optional) |
| Docker Compose | 2.0+ | Multi-container setup (optional) |
| FFmpeg/FFPROBE | 4.0+ | Media file analysis |
| PostgreSQL | 15+ | Database (or use Docker) |
| Redis | 7+ | Caching & task queue (or use Docker) |

### External API Keys

| API | Purpose | Get Key |
|-----|---------|---------|
| OMDB API | Movie metadata | [omdbapi.com](http://www.omdbapi.com/apikey.aspx) |
| TVDB API | TV show metadata | [thetvdb.com](https://thetvdb.com/api-information) |

---

## Installation & Setup

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd metamaster
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and media directories
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Manual Setup for Local Development

#### Backend Setup

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Initialize database**
   ```bash
   # Run migrations
   alembic upgrade head
   ```

5. **Start the application**
   ```bash
   # Start FastAPI server
   uvicorn app.main:app --reload
   
   # In a separate terminal, start Celery worker
   celery -A app.tasks.celery_app worker --loglevel=info
   
   # In another terminal, start Celery beat (optional, for scheduled tasks)
   celery -A app.tasks.celery_app beat --loglevel=info
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API URL
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

### Environment Configuration

Create a `.env` file based on `.env.example`:

```env
# Application
APP_NAME=MetaMaster
DEBUG=False
LOG_LEVEL=INFO

# Database (PostgreSQL for production)
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/metamaster

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# OMDB API (for movie metadata)
OMDB_API_KEY=your_omdb_api_key_here
OMDB_RATE_LIMIT=1

# TVDB API (for TV show metadata)
TVDB_API_KEY=your_tvdb_api_key_here
TVDB_PIN=your_tvdb_pin_here
TVDB_RATE_LIMIT=3

# File Monitoring
MOVIE_DIR=/path/to/your/movies
TV_DIR=/path/to/your/tv/shows
WATCH_EXTENSIONS=.mp4,.mkv,.avi,.mov,.flv,.wmv,.webm,.m4v
```

---

## Available Commands

ß### Backend Commands

```bash
# Development server
uvicorn app.main:app --reload

# Database migrations
alembic upgrade head              # Apply migrations
alembic downgrade -1              # Rollback one migration
alembic revision --autogenerate -m "Description"  # Create migration

# Testing
pytest                            # Run all tests
pytest -v                         # Verbose output
pytest --cov=app                  # With coverage
pytest -m "not slow"              # Skip slow tests
pytest -m "integration"           # Run only integration tests

# Code quality
black app/                        # Format code
isort app/                        # Sort importså
flake8 app/                       # Lint code
mypy app/                         # Type checking

# Celery
celery -A app.tasks.celery_app worker --loglevel=info    # Start worker
celery -A app.tasks.celery_app beat --loglevel=info      # Start scheduler
```

### Frontend Commands

```bash
# Development
npm run dev                        # Start dev server
npm run build                      # Production build
npm run preview                    # Preview production build

# Testing
npm run test                       # Run unit tests
npm run test:watch                 # Watch mode
npm run test:coverage              # With coverage report
npm run test:e2e                   # Run E2E tests
npm run test:e2e:ui                # E2E with UI

# Code quality
npm run lint                       # Run ESLint
npm run lint:fix                   # Fix linting issues
npm run format                     # Format with Prettier
npm run type-check                 # TypeScript check
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f             # All services
docker-compose logs -f app         # Backend only
docker-compose logs -f frontend    # Frontend only

# Stop services
docker-compose down                # Stop containers
docker-compose down -v             # Stop and remove volumes

# Rebuild containers
docker-compose up -d --build

# Scale workers
docker-compose up -d --scale celery_worker=3

# Execute commands in containers
docker-compose exec app bash       # Backend shell
docker-compose exec app pytest     # Run tests in container
```

---

## Project Structure

```
.
├── app/                              # Backend application
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── config.py                     # Legacy configuration
│   ├── database.py                   # Legacy database setup
│   ├── models.py                     # Legacy ORM models
│   ├── schemas.py                    # Pydantic schemas
│   ├── services_impl.py              # Service implementations
│   ├── tasks.py                      # Legacy Celery tasks
│   ├── api/                          # API endpoints
│   │   ├── middleware/               # Request middleware
│   │   └── v1/                       # API version 1
│   │       ├── cache/                # Cache endpoints
│   │       ├── config/               # Configuration endpoints
│   │       ├── files/                # File management
│   │       ├── health/               # Health checks
│   │       ├── movies/               # Movie endpoints
│   │       ├── tasks/                # Task management
│   │       └── tv_shows/             # TV show endpoints
│   ├── core/                         # Core utilities
│   │   ├── config.py                 # Configuration settings
│   │   ├── database.py               # Database setup
│   │   ├── init_db.py                # Database initialization
│   │   └── logging_config.py         # Logging configuration
│   ├── domain/                       # Domain models
│   │   ├── common/                   # Shared domain models
│   │   ├── files/                    # File domain
│   │   ├── movies/                   # Movie domain
│   │   └── tv_shows/                 # TV show domain
│   ├── infrastructure/               # Infrastructure layer
│   │   ├── cache/                    # Redis caching
│   │   ├── external_apis/            # OMDB & TVDB clients
│   │   ├── file_system/              # File monitoring & FFPROBE
│   │   └── monitoring/               # Prometheus & error handling
│   ├── application/                  # Application services
│   │   ├── batch_operations/         # Batch processing
│   │   ├── db_optimization/          # Query optimization
│   │   ├── pattern_recognition/      # Media pattern detection
│   │   └── search/                   # Search functionality
│   └── tasks/                        # Celery task definitions
│       ├── celery_app.py             # Celery configuration
│       ├── celery_beat.py            # Scheduled tasks
│       └── async_helpers.py          # Async utilities
├── frontend/                         # Frontend application
│   ├── src/
│   │   ├── components/               # React components
│   │   │   ├── common/               # Reusable components
│   │   │   ├── file/                 # File management
│   │   │   ├── layout/               # Layout components
│   │   │   ├── dashboard/            # Dashboard widgets
│   │   │   ├── queue/                # Queue management
│   │   │   ├── search/               # Search components
│   │   │   └── settings/             # Settings components
│   │   ├── pages/                    # Page components
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── services/                 # API service layer
│   │   ├── stores/                   # Zustand state stores
│   │   ├── types/                    # TypeScript types
│   │   └── utils/                    # Utility functions
│   ├── .storybook/                   # Storybook configuration
│   ├── .github/workflows/            # Frontend CI/CD
│   ├── Dockerfile                    # Frontend container
│   ├── package.json                  # Dependencies
│   ├── vite.config.ts                # Vite configuration
│   ├── vitest.config.ts              # Test configuration
│   ├── playwright.config.ts          # E2E test configuration
│   ├── eslint.config.js              # ESLint flat config
│   ├── tailwind.config.js            # Tailwind configuration
│   └── tsconfig.json                 # TypeScript configuration
├── alembic/                          # Database migrations
│   ├── env.py                        # Alembic environment
│   ├── script.py.mako                # Migration template
│   └── versions/                     # Migration files
├── .github/workflows/                # Backend CI/CD pipelines
├── docs/                             # Documentation
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Project configuration
├── docker-compose.yml                # Multi-service orchestration
├── Dockerfile                        # Backend container
├── alembic.ini                       # Alembic configuration
├── .env.example                      # Environment template
└── README.md                         # This file
```

---

## CI/CD Pipeline

### Overview

MetaMaster uses GitHub Actions for continuous integration and deployment with 10 workflow files across backend and frontend.

### Backend Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`ci.yml`](.github/workflows/ci.yml) | Push to main, PRs | Run tests, linting, type checking |
| [`docker.yml`](.github/workflows/docker.yml) | Push to main, tags | Build & push Docker images to GHCR |
| [`code-quality.yml`](.github/workflows/code-quality.yml) | Push to main, PRs | SonarQube code analysis |
| [`deploy.yml`](.github/workflows/deploy.yml) | Push to main | Deploy to production |
| [`lint.yml`](.github/workflows/lint.yml) | Push, PRs | Fast linting feedback |
| [`scheduled-tests.yml`](.github/workflows/scheduled-tests.yml) | Cron schedule | Nightly tests, weekly benchmarks |

### Frontend Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`ci.yml`](frontend/.github/workflows/ci.yml) | Push to main, PRs | Build, test, lint |
| [`lighthouse.yml`](frontend/.github/workflows/lighthouse.yml) | Push to main | Performance auditing |
| [`security.yml`](frontend/.github/workflows/security.yml) | Push, schedule | npm audit, CodeQL |
| [`storybook.yml`](frontend/.github/workflows/storybook.yml) | Push to main | Deploy Storybook to GitHub Pages |

### Required Secrets

Configure these secrets in your GitHub repository settings:

| Secret | Purpose |
|--------|---------|
| `SONAR_TOKEN` | SonarQube analysis |
| `DOCKER_USERNAME` | Container registry login |
| `DOCKER_PASSWORD` | Container registry password |
| `CODECOV_TOKEN` | Coverage reporting |

### Dependabot

Automated dependency updates are configured via Dependabot for:
- Python dependencies (pip)
- Node.js dependencies (npm)
- Docker base images
- GitHub Actions

---

## API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Check Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health/` | Basic health check |
| `GET /health/db` | Database connectivity check |

---

## Contributing Guidelines

### Code Style

#### Backend (Python)

- Follow PEP 8 conventions
- Use Black for formatting (line length: 100)
- Use isort for import sorting (Black-compatible profile)
- Add type hints for all functions
- Run mypy for type checking

```bash
# Format and lint before committing
black app/ && isort app/ && flake8 app/ && mypy app/
```

#### Frontend (TypeScript/React)

- Use ESLint 9 with flat config
- Format with Prettier
- Use TypeScript strict mode
- Follow React best practices

```bash
# Format and lint before committing
npm run lint:fix && npm run format && npm run type-check
```

### Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
```
feat(api): add batch movie import endpoint
fix(celery): resolve task retry logic
docs(readme): update installation instructions
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Ensure all tests pass: `pytest` (backend) and `npm run test` (frontend)
4. Run linting: `flake8 app/ && mypy app/` (backend) and `npm run lint` (frontend)
5. Update documentation if needed
6. Submit a pull request with a clear description

### Pre-commit Hooks

Frontend uses Husky and lint-staged for pre-commit checks:
- ESLint and Prettier run on staged files automatically

---

## License

[Add your license here]

---

## Support

For issues and questions, please open an issue on the repository.
