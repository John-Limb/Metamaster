# Metamaster - Environment & CI/CD Strategy

## Important Note

This document clarifies the environment and CI/CD strategy for Metamaster. The application is **development-only** and should not have references to staging or production environments.

---

## Application Scope

### Development-Only Application
- **Purpose**: Local development tool for managing media libraries
- **Deployment**: Local machine only (Docker Compose)
- **No Remote Deployment**: Application is not deployed to staging or production servers
- **No Multi-Environment Support**: No need for dev/staging/production environment configurations

### Implications
- Remove all references to staging and production environments
- Remove deployment documentation for cloud platforms
- Remove multi-environment configuration strategies
- Simplify configuration to development-only settings
- Remove CI/CD deployment workflows

---

## CI/CD Pipeline (Simplified)

### Current State (To Be Removed)
The existing CI/CD pipeline includes:
- ❌ Deployment to staging environment
- ❌ Deployment to production environment
- ❌ Multi-environment configuration
- ❌ Cloud platform deployment (AWS, GCP, Azure)
- ❌ Kubernetes deployment
- ❌ Helm charts
- ❌ Infrastructure as Code (Terraform, CloudFormation)

### New CI/CD Pipeline (Development-Only)

The CI/CD pipeline should only include:
- ✅ **Lint**: Check code quality and style
- ✅ **Test**: Run unit, integration, and E2E tests
- ✅ **Build**: Build the application (backend + frontend)
- ❌ **Deploy**: No deployment step

#### GitHub Actions Workflow Structure

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Lint Backend
        run: cd app && npm run lint
      - name: Lint Frontend
        run: cd frontend && npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Backend
        run: cd app && npm run test
      - name: Test Frontend
        run: cd frontend && npm run test
      - name: E2E Tests
        run: cd frontend && npm run test:e2e

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v3
      - name: Build Backend
        run: cd app && npm run build
      - name: Build Frontend
        run: cd frontend && npm run build
      - name: Build Docker Image
        run: docker build -t metamaster:latest .
```

---

## Configuration Strategy

### Environment Variables (Simplified)

Only support development configuration:

```env
# Application
APP_NAME=Metamaster
APP_ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql://metamaster:metamaster@localhost:5432/metamaster

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Security (development only)
SECRET_KEY=dev-secret-key-change-if-needed
ALGORITHM=HS256

# Logging
LOG_LEVEL=INFO

# File Monitoring
FILE_MONITOR_ENABLED=true
MEDIA_PATHS=/media

# External APIs
OMDB_API_KEY=your_key_here
TVDB_API_KEY=your_key_here
```

### No Environment-Specific Files
- ❌ `.env.development`
- ❌ `.env.staging`
- ❌ `.env.production`
- ✅ `.env` (single development configuration)
- ✅ `.env.example` (template for users)

---

## Docker Compose (Simplified)

### Purpose
Local development environment only, not for production deployment.

### Services
- API (FastAPI)
- PostgreSQL
- Redis
- Celery Worker
- Celery Beat

### No Production Considerations
- ❌ No resource limits (deploy section)
- ❌ No health checks for production
- ❌ No restart policies for production
- ❌ No logging drivers for production
- ✅ Simple development configuration
- ✅ Hot-reload enabled
- ✅ Debug mode enabled

---

## Monitoring & Logging

### Simplified Approach
- ❌ No Prometheus metrics for production
- ❌ No Grafana dashboards
- ❌ No Sentry error tracking
- ❌ No production logging infrastructure
- ✅ Console logging for development
- ✅ File logging for debugging
- ✅ Simple health check endpoint

---

## Security Considerations

### Development-Only Security
- ✅ Use development secret keys
- ✅ Allow CORS from localhost
- ✅ Debug mode enabled
- ✅ Simple authentication for local use
- ❌ No SSL/TLS certificates required
- ❌ No production security hardening
- ❌ No secrets management system

---

## Documentation Cleanup

### Files to Remove
- ❌ `docs/DEPLOYMENT.md` - Multi-environment deployment guide
- ❌ `docs/DEPLOYMENT_DOCKER.md` - Docker production deployment
- ❌ `docs/DEPLOYMENT_KUBERNETES.md` - Kubernetes deployment
- ❌ `docs/DEPLOYMENT_CLOUD.md` - Cloud platform deployment
- ❌ `docs/DEPLOYMENT_FRONTEND.md` - Frontend deployment to staging/production
- ❌ `docs/INFRASTRUCTURE_AS_CODE.md` - Terraform, CloudFormation, Ansible
- ❌ `docs/CI_CD_PIPELINE.md` - Multi-environment CI/CD pipeline

### Files to Update
- ✅ `docs/DEPLOYMENT_LOCAL.md` - Keep, but remove references to other environments
- ✅ `docs/DOCKER_SETUP.md` - Keep, but simplify for local development only
- ✅ `docs/CONFIGURATION_GUIDE.md` - Remove staging/production environment configs
- ✅ `docs/DEPLOYMENT_SECURITY.md` - Remove production security considerations
- ✅ `docs/DEPLOYMENT_TROUBLESHOOTING.md` - Remove production troubleshooting

### Files to Create
- ✅ `docs/CI_CD_PIPELINE_DEVELOPMENT.md` - New simplified CI/CD documentation

---

## Implementation Checklist

### Documentation Cleanup
- [ ] Remove `docs/DEPLOYMENT.md`
- [ ] Remove `docs/DEPLOYMENT_DOCKER.md`
- [ ] Remove `docs/DEPLOYMENT_KUBERNETES.md`
- [ ] Remove `docs/DEPLOYMENT_CLOUD.md`
- [ ] Remove `docs/DEPLOYMENT_FRONTEND.md`
- [ ] Remove `docs/INFRASTRUCTURE_AS_CODE.md`
- [ ] Remove `docs/CI_CD_PIPELINE.md`
- [ ] Update `docs/DEPLOYMENT_LOCAL.md` (remove other environments)
- [ ] Update `docs/DOCKER_SETUP.md` (simplify for local only)
- [ ] Update `docs/CONFIGURATION_GUIDE.md` (remove staging/production)
- [ ] Update `docs/DEPLOYMENT_SECURITY.md` (development-only)
- [ ] Update `docs/DEPLOYMENT_TROUBLESHOOTING.md` (development-only)
- [ ] Create `docs/CI_CD_PIPELINE_DEVELOPMENT.md` (new simplified guide)

### Code Cleanup
- [ ] Remove staging/production environment checks
- [ ] Remove multi-environment configuration logic
- [ ] Remove cloud deployment code
- [ ] Remove Kubernetes manifests
- [ ] Remove Terraform/CloudFormation templates
- [ ] Remove Ansible playbooks
- [ ] Simplify configuration module

### CI/CD Cleanup
- [ ] Remove deployment workflows
- [ ] Keep lint, test, build workflows
- [ ] Remove staging deployment job
- [ ] Remove production deployment job
- [ ] Remove cloud deployment jobs
- [ ] Update GitHub Actions workflows

### Docker Cleanup
- [ ] Simplify docker-compose.yml
- [ ] Remove production resource limits
- [ ] Remove production health checks
- [ ] Remove production restart policies
- [ ] Keep development configuration

---

## Benefits of This Approach

1. **Simplified Codebase**: No multi-environment logic
2. **Clearer Documentation**: Only relevant information
3. **Faster Development**: No deployment overhead
4. **Reduced Complexity**: Single configuration
5. **Easier Onboarding**: Simpler setup process
6. **Focused CI/CD**: Only lint, test, build

---

## Future Considerations

If the application ever needs to be deployed remotely:
1. Create separate deployment documentation
2. Add multi-environment configuration
3. Implement cloud deployment workflows
4. Add monitoring and logging infrastructure
5. Implement security hardening

For now, keep it simple and development-focused.

---

## Summary

**Metamaster is a development-only application.**

- ✅ Local Docker Compose deployment
- ✅ Simple development configuration
- ✅ CI/CD for lint, test, build only
- ✅ No remote deployment
- ✅ No staging/production environments
- ✅ No cloud platform support
- ✅ No Kubernetes/Helm
- ✅ No Infrastructure as Code

This keeps the project focused, simple, and maintainable.
