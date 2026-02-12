# Media Management Web Tool

[![CI Pipeline](https://github.com/YOUR_USERNAME/media-management-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/media-management-tool/actions/workflows/ci.yml)
[![Docker Build](https://github.com/YOUR_USERNAME/media-management-tool/actions/workflows/docker.yml/badge.svg)](https://github.com/YOUR_USERNAME/media-management-tool/actions/workflows/docker.yml)
[![Code Quality](https://github.com/YOUR_USERNAME/media-management-tool/actions/workflows/code-quality.yml/badge.svg)](https://github.com/YOUR_USERNAME/media-management-tool/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/media-management-tool/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/media-management-tool)

A comprehensive web-based media management system for organizing and managing your movie and TV show library with automatic metadata enrichment from OMDB and TVDB APIs.

## Features

- **Media Library Management**: Organize movies and TV shows with detailed metadata
- **Automatic File Detection**: Monitor directories for new media files
- **Metadata Enrichment**: Automatic metadata lookup from OMDB (movies) and TVDB (TV shows)
- **File Analysis**: Extract technical details (resolution, bitrate, codec) using FFPROBE
- **Caching System**: Multi-level caching to reduce API calls
- **Background Processing**: Celery-based task queue for long-running operations
- **REST API**: Comprehensive REST API with automatic documentation
- **Web Interface**: Modern React-based frontend with file navigation and management
- **Docker Support**: Full Docker and Docker Compose setup

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLite (with SQLAlchemy ORM)
- **Background Tasks**: Celery + Redis
- **File Monitoring**: Watchdog
- **Containerization**: Docker & Docker Compose
- **API Clients**: HTTPX (async HTTP client)

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand + TanStack Query
- **Styling**: Tailwind CSS
- **Routing**: React Router 6
- **Testing**: Vitest + React Testing Library
- **Documentation**: Storybook

## Project Structure

```
.
├── app/                              # Backend application
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration settings
│   ├── database.py                  # Database setup and session management
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── tasks.py                     # Celery task definitions
│   └── api/                         # API endpoints
│       ├── __init__.py
│       ├── v1/                      # API version 1
│       │   ├── movies/
│       │   ├── tv_shows/
│       │   ├── cache/
│       │   ├── health/
│       │   └── tasks/
├── frontend/                        # Frontend application (React)
│   ├── src/
│   │   ├── components/             # React components
│   │   │   ├── common/             # Reusable components
│   │   │   ├── file/               # File management components
│   │   │   ├── layout/             # Layout components
│   │   │   ├── dashboard/          # Dashboard components
│   │   │   ├── queue/              # Queue management
│   │   │   ├── search/             # Search components
│   │   │   └── settings/           # Settings components
│   │   ├── pages/                  # Page components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── services/               # API service layer
│   │   ├── stores/                 # Zustand state stores
│   │   ├── types/                  # TypeScript types
│   │   ├── utils/                  # Utility functions
│   │   └── styles/                 # Global styles
│   ├── .storybook/                 # Storybook configuration
│   ├── .github/workflows/          # CI/CD pipelines
│   ├── Dockerfile                  # Frontend Docker image
│   ├── package.json                # Frontend dependencies
│   └── vite.config.ts             # Vite configuration
├── requirements.txt                 # Python dependencies
├── docker-compose.yml              # Multi-container orchestration
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Installation

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)
- Redis (for background tasks)
- FFmpeg (for file analysis)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd media-management-tool
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   python -c "from app.database import init_db; init_db()"
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The application will be available at `http://localhost:8000`

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

3. **View logs**
   ```bash
   docker-compose logs -f app
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

## Frontend Setup

### Prerequisites

- Node.js 18+
- npm or yarn
- Git

### Local Development

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
   # Edit .env with your settings
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

### Frontend Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run linting
npm run lint

# Format code
npm run format

# Type checking
npm run type-check
```

### Storybook

Start Storybook to view component documentation:

```bash
npm run storybook
```

Storybook will be available at `http://localhost:6006`

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Check Endpoints

- `GET /health` - Basic health check
- `GET /health/db` - Database health check

## Configuration

Edit `.env` file to configure:

```env
# Application
DEBUG=False
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./media.db

# Redis
REDIS_URL=redis://localhost:6379/0

# OMDB API
OMDB_API_KEY=your_key_here
OMDB_RATE_LIMIT=1

# TVDB API
TVDB_API_KEY=your_key_here
TVDB_PIN=your_pin_here
TVDB_RATE_LIMIT=3

# File Monitoring
MEDIA_DIRECTORY=./media
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/

# Sort imports
isort app/
```

### Database Migrations

Using Alembic for database migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Implementation Phases

This project follows a phased implementation approach:

1. **Phase 1**: Foundation & Core Infrastructure ✓
2. **Phase 2**: API Layer & Basic CRUD Operations
3. **Phase 3**: External API Integration
4. **Phase 4**: File System Monitoring
5. **Phase 5**: Background Task Processing
6. **Phase 6**: Advanced Features & Optimization
7. **Phase 7**: Testing & Quality Assurance
8. **Phase 8**: Documentation & Deployment

See `plans/IMPLEMENTATION_ROADMAP.md` for detailed roadmap.

## CI/CD Pipeline

This project includes a comprehensive CI/CD pipeline with:

- **Automated Testing**: Unit, integration, and end-to-end tests on every commit
- **Code Quality**: Linting, type checking, and code analysis
- **Security Scanning**: Vulnerability detection and dependency audits
- **Docker Builds**: Multi-architecture image builds and security scanning
- **Automated Deployment**: Staging and production deployment pipelines
- **Scheduled Tasks**: Nightly tests, weekly benchmarks, monthly security audits

See `docs/CI_CD_PIPELINE.md` for detailed CI/CD documentation.

## Architecture

See `plans/ARCHITECTURE.md` for detailed architecture documentation including:
- System architecture overview
- Technology stack rationale
- Database schema design
- API integration strategy
- Caching strategy

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the repository.
