# Media Management Web Tool

A comprehensive web-based media management system for organizing and managing your movie and TV show library with automatic metadata enrichment from OMDB and TVDB APIs.

## Features

- **Media Library Management**: Organize movies and TV shows with detailed metadata
- **Automatic File Detection**: Monitor directories for new media files
- **Metadata Enrichment**: Automatic metadata lookup from OMDB (movies) and TVDB (TV shows)
- **File Analysis**: Extract technical details (resolution, bitrate, codec) using FFPROBE
- **Caching System**: Multi-level caching to reduce API calls
- **Background Processing**: Celery-based task queue for long-running operations
- **REST API**: Comprehensive REST API with automatic documentation
- **Docker Support**: Full Docker and Docker Compose setup

## Technology Stack

- **Framework**: FastAPI
- **Database**: SQLite (with SQLAlchemy ORM)
- **Background Tasks**: Celery + Redis
- **File Monitoring**: Watchdog
- **Containerization**: Docker & Docker Compose
- **API Clients**: HTTPX (async HTTP client)

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database setup and session management
│   ├── models.py            # SQLAlchemy ORM models
│   ├── tasks.py             # Celery task definitions
│   └── api/
│       ├── __init__.py
│       └── health.py        # Health check endpoints
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Multi-container orchestration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
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
