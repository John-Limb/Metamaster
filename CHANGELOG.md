# Changelog

All notable changes to MetaMaster are documented here.
Versions follow [Semantic Versioning](https://semver.org/).

## [0.0.11] - 2026-03-15

### Bug Fixes
- **tests:** Update API endpoint paths in plexService tests
- **tests:** Apply dependency overrides in a fixture for better test isolation

### Features
- **store:** Implement media store functionality with CRUD operations and pagination
- **dashboard:** Enhance ExternalApiStatus with Plex connection status and improve UI feedback
- **plex:** Integrate Plex connection management and health checks
- **plex:** Add function to seed Plex connection from environment variables
- **gitignore:** Add .superpowers to ignore list
- **plex:** Add watch status tracking for movies and TV shows with corresponding UI updates

### Other Changes
- Tidy up to do docs
- Updated codacy to not include test filed
- Add unit tests for Plex collection and playlist functionality

- Implement tests for PlexCollectionClient, PlexPlaylistClient, and their respective services.
- Create tests for collection and playlist schemas, ensuring proper validation and defaults.
- Add tests for collection and playlist API routes, verifying correct behavior for CRUD operations.
- Introduce tests for Celery tasks related to Plex collections and playlists.
- Enhance TMDBService tests to cover movie details response with collection data.

## [0.0.1] - 2026-03-13

### Bug Fixes
- Prevent log message truncation in system health page
- Fix
- **frontend:** Update ESLint config to properly configure React plugin and valid security rules
- **frontend:** Improve TypeScript type safety in component props and error handling
- **release:** Ensure PR creation command handles failures gracefully

### Dependency Updates
- **deps:** (deps): bump locust from 2.17.0 to 2.34.0
- **deps:** (deps): bump sqlalchemy from 2.0.23 to 2.0.46
- **deps:** (deps): bump pydantic from 2.5.0 to 2.12.5
- **deps:** (deps): bump pytest-asyncio from 0.21.1 to 1.2.0
- **deps:** (deps): bump structlog from 23.2.0 to 25.5.0
- **deps:** (deps): bump isort from 5.13.2 to 6.1.0
- **deps:** (deps): bump pydantic-settings from 2.1.0 to 2.11.0
- **deps:** (deps): bump python-dotenv from 1.0.0 to 1.2.1
- **deps:** (deps): bump pytest-benchmark from 4.0.0 to 5.2.3
- **deps:** (deps): bump pytest from 8.3.5 to 8.4.2
- **deps:** Remove unused ffmpeg-python dependency
- **deps:** Add frontend security overrides and document redis upgrade plan
- **deps:** Consolidate minimatch override in frontend package.json
- **deps:** (deps): bump sqlalchemy from 2.0.46 to 2.0.47
- **deps:** (deps): bump psutil from 5.9.6 to 7.2.2
- **deps:** (deps): bump prometheus-client from 0.17.1 to 0.24.1

### Documentation
- **readme:** Overhaul documentation with comprehensive project details
- **readme:** Overhaul documentation with comprehensive project details
- Update README for TMDB migration and new features
- Overhaul documentation with new architecture, API, CI/CD, and troubleshooting guides
- Add single admin user implementation plan
- Add changelog and versioning sync design document
- Update README badges
- **plex:** Add Plex integration design and implementation plans

### Features
- **plans:** Add project planning directory structure
- **api:** Add movies and tv shows routers
- **api:** Add metadata sync endpoints and cache management
- **services:** Add file renaming and organization to phase 3 implementation
- **tasks:** Implement comprehensive background task processing with celery
- **api,services,db:** Implement advanced caching, monitoring, and batch operations
- **auth:** Implement authentication system with security hardening
- Add Wednesday development and naming conventions guidelines
- Add media scanning configuration and user profile management
- Implement TV show scanning functionality and enhance movie detail page
- **queue:** Add file classification and queue management endpoints
- Add poster_url to movies and TV shows, update metadata sync and UI components
- Add audio_channels property to movie and episode models, enhance scanning and logging functionality
- Add enrichment_status and related columns to movies and tv_shows
- Implement NeedsAttentionPage for managing media enrichment status
- Migrate from OMDB/TVDB to TMDB for movie and TV show metadata
- Add TMDB_READ_ACCESS_TOKEN env var and Settings field
- Replace _get_headers with _get_auth supporting Bearer token and API Key fallback
- Replace _get_headers with _get_auth supporting Bearer token and API Key fallback
- Implement TMDB dual authentication with Read Access Token and API Key fallback
- Add duration_seconds, video_codec, video_width, video_height to FileItem
- Add StorageService pure helpers with TDD (resolution tier, efficiency tier, MB/min, savings)
- Enhance StorageService with disk stats and video file handling methods
- Add storage analytics API endpoints and tests
- Add technical metadata enrichment task for files and corresponding tests
- Add StoragePage and storage analytics service with dashboard integration
- Add design document for episode detail display enhancements
- Add quality and runtime fields to EpisodeResponse schema
- Enhance episode detail display with quality and runtime information
- Enhance episode detail display with quality and runtime information
- Add OrganisationModal component for file organization preview and renaming
- Enhance organisation page with episode grouping and preview details
- Implement Organisation page with collapsible TV show/season structure and update sidebar navigation
- **auth:** Implement single-admin user model with password reset CLI
- Add queue and system-health drilldown pages
- **ui:** Add media detail modal and enrichment badge components
- **plex:** Add Plex Media Server integration
- **plex:** Add database tables, ORM models, and API schemas for Plex integration
- **plex:** Add Plex Media Server integration for watch status sync and library refresh
- **plex:** Remove outdated plans for Plex Now Playing Page and token encryption
- **plex:** Add TMDB mismatch detection and resolution between MetaMaster and Plex
- **storage:** Add watched status filter for media files
- Add unwatched space optimisation feature
- **plex:** Enhance file handling with Plex section ID resolution and caching

### Other Changes
- Initial commit
- Add project initialization files and configuration

- Add Docker configuration (Dockerfile, docker-compose.yml)
- Add Python application structure with FastAPI setup
- Add requirements.txt with project dependencies
- Add README.md with project documentation
- Add .env.example with configuration template
- Update .gitignore for Python project standards
- Add comprehensive architecture and deployment planning documents
- Add database initialization and connection pooling configuration

- Add Alembic migration framework with initial configuration
- Enhance database.py with connection pooling for PostgreSQL
- Enable SQLite foreign key constraints via PRAGMA
- Add database initialization module with table creation and reset utilities
- Implement helper functions for engine and session factory access
- Enhance FastAPI application with middleware and request logging

- Add request/response logging middleware with unique request IDs
- Implement structured error handling for validation errors
- Add TrustedHostMiddleware for security
- Include X-Request-ID and X-Process-Time headers in responses
- Improve logging with timing information and client tracking
- Add Docker configuration and setup documentation

- Create docker-compose.test.yml for isolated testing environment
- Add .dockerignore to optimize Docker build context
- Create comprehensive DOCKER_SETUP.md with:
  - Quick start instructions
  - Development workflow guide
  - Environment configuration details
  - Common Docker commands
  - Troubleshooting guide
  - Performance optimization tips
  - Security considerations for production
- **docker:** Migrate from Docker Hub to GitHub Container Registry
- Black formatting
- More Formatting
- Moved Upload from V3 to V4
- Fix : Pipeline issues
- Fixes, V3 to V4 and grammar
- Added dependency package to SonarQube
- Forgot the F***ing sudo
- Full front end
- Tst
- Update README.md with new content.
- Remove Storybook stories for various components in the dashboard and features sections, including QuickActions, RecentActivity, StorageChart, FilterPanel, MovieCard, MovieDetailPage, MoviesPage, SortDropdown, TVShowCard, TVShowDetailPage, TVShowsPage, BatchOperationModal, and FileCard. This cleanup helps streamline the codebase by eliminating unused or redundant story files.
- Remove outdated plans and documentation for phased codebase improvement, summary changes, UI revamp, and file API implementation
- **actions:** (deps): bump codecov/codecov-action from 3 to 5
- **actions:** (deps): bump docker/metadata-action from 4 to 5
- **actions:** (deps): bump actions/upload-artifact from 4 to 6
- Refactor lint workflow to run manually and streamline steps
- Enhance logging for movie and TV show processing; add access logging for HTTP requests
- Refactor tests to replace 'omdb_id' and 'tvdb_id' with 'tmdb_id' for consistency across movie and TV show schemas. Remove TVDB service tests and add new TMDB service tests for unified metadata handling.
- Implement feature X to enhance user experience and optimize performance
- Remove Wednesday Solutions technical development guidelines and related complexity and naming convention references
- **actions:** (deps): bump actions/setup-node from 4 to 6
- **actions:** (deps): bump actions/checkout from 4 to 6
- Add entrypoint script and enhance storage page with scan functionality

- Introduced a new entrypoint script for handling database migrations and application startup.
- Updated Dockerfile to use the new entrypoint script.
- Added a scanning feature to the StoragePage component, allowing users to trigger a scan and view loading state.
- Configured periodic task for enriching file technical metadata in the Celery Beat scheduler.
- Doc for adjustments on organisation
- Add CheckboxInput and RadioInput components; update usages across the application
- Fixes : Minor security imrovements, containers no longer run as root!
- Add Codacy configuration file with specified runtimes and tools
- Removed Dead code from Migration from OMBDB
- Updated claude to not commit due to pasword needed on signing key
- Reduced CC as needed
- Bug fix: When organisation ran, if a job failed it did not show result but it also showed that "all files matched convention" which was not true.
- Add automated release workflow with version bump and changelog
- Add pull request trigger and frontend docker build
- Linted files to black standard
- Updated Readme
- Readme heading
- Version 0.1 release
- Fix for failing release
- Add GH_TOKEN environment variable for version bump

Added environment variable for GH_TOKEN in release workflow.
- Add rebase before pushing release branch
- Add permissions for pull-requests in release workflow

### Refactoring
- **ui:** Migrate to CSS variables for design system tokens
- **styles:** Update button styles for improved touch target sizes and accessibility
- **nginx:** Adjust registration rate limiting to improve retry handling
- Refactor(auth): update login function to return password change requirement and improve logout cookie handling
refactor(api): enhance token refresh logic in ApiClient to handle multiple requests
fix(nginx): correct proxy_pass directive in Nginx configuration
- Update configuration for media directories and improve path checks
- Remove episodes stat from LibraryStats and adjust grid layout
- Reduce complexity in FFProbeWrapper and update import path in tests
- Remove unused imports across codebase
- Replace Math.random() with crypto.randomUUID() in frontend utilities
- **frontend:** Replace Math.random() with crypto.randomUUID() in common components
- **db:** Migrate from SQLite to PostgreSQL-only configuration
- **frontend:** Improve TypeScript types and fix ESLint issues
- **core:** Improve logging config DRY and refactor sync_metadata task


