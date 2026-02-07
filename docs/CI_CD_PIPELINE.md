# CI/CD Pipeline Documentation

## Overview

This document describes the complete CI/CD pipeline for the Media Management Tool project. The pipeline is built using GitHub Actions and provides automated testing, building, and deployment capabilities.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI/CD                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │   CI Pipeline    │  │  Code Quality    │  │   Docker     │ │
│  │  (ci.yml)        │  │  (code-quality)  │  │  (docker.yml)│ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│           │                    │                      │         │
│           ├─ Lint              ├─ Bandit             ├─ Build  │
│           ├─ Type Check        ├─ Safety             ├─ Scan   │
│           ├─ Unit Tests        ├─ SonarQube          └─ Push   │
│           ├─ Integration Tests ├─ Coverage           (Docker)  │
│           └─ Coverage          └─ Complexity                   │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Deployment      │  │  Scheduled       │  │  Dependabot  │ │
│  │  (deploy.yml)    │  │  (scheduled)     │  │  (dependabot)│ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│           │                    │                      │         │
│           ├─ Staging           ├─ Nightly Tests      └─ Auto   │
│           ├─ Smoke Tests       ├─ Performance        Updates   │
│           └─ Production        ├─ Security Audit              │
│                                └─ Dependency Check             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Trigger**: Push to `main` or `develop`, Pull Requests

**Purpose**: Automated testing and code quality checks on every commit

#### Jobs:

##### Lint and Type Check
- **Runs on**: Ubuntu Latest
- **Python Version**: 3.11
- **Tasks**:
  - Black formatter check
  - isort import check
  - Flake8 linting
  - mypy type checking

##### Test Matrix
- **Runs on**: Ubuntu, macOS, Windows
- **Python Versions**: 3.9, 3.10, 3.11, 3.12
- **Tasks**:
  - Install dependencies
  - Run unit tests with coverage
  - Run integration tests
  - Upload coverage to Codecov

##### Coverage Report
- **Runs on**: Ubuntu Latest
- **Tasks**:
  - Generate HTML coverage report
  - Upload artifacts
  - Comment on PR with coverage metrics

**Caching**: Dependencies are cached using GitHub's built-in pip cache

### 2. Docker Build and Push (`.github/workflows/docker.yml`)

**Trigger**: Push to `main`, Release tags, Pull Requests

**Purpose**: Build, scan, and push Docker images

#### Jobs:

##### Build and Push
- **Runs on**: Ubuntu Latest
- **Tasks**:
  - Set up Docker Buildx
  - Log in to Docker Hub
  - Extract metadata (tags, labels)
  - Build and push multi-architecture images (amd64, arm64)
  - Cache layers for faster builds

##### Security Scan
- **Runs on**: Ubuntu Latest
- **Requires**: Build job completion
- **Tasks**:
  - Run Trivy vulnerability scanner
  - Upload SARIF results to GitHub Security tab

**Image Tagging**:
- Branch: `branch-name`
- Semantic Version: `v1.0.0`, `1.0`, `1`
- SHA: `sha-<commit-hash>`
- Latest: `latest` (for main branch)

### 3. Deployment Pipeline (`.github/workflows/deploy.yml`)

**Trigger**: Release published, Manual workflow dispatch

**Purpose**: Automated deployment to staging and production

#### Jobs:

##### Build and Test
- **Runs on**: Ubuntu Latest
- **Tasks**:
  - Checkout code
  - Set up Python
  - Install dependencies
  - Run tests
  - Build Docker image

##### Deploy to Staging
- **Requires**: Build and Test
- **Trigger**: Release or manual dispatch with staging environment
- **Tasks**:
  - Deploy to staging environment
  - Run smoke tests
  - Verify deployment health

##### Deploy to Production
- **Requires**: Deploy to Staging
- **Trigger**: Release or manual dispatch with production environment
- **Tasks**:
  - Deploy to production environment
  - Verify deployment
  - Run health checks
  - Notify on success/failure

### 4. Code Quality Analysis (`.github/workflows/code-quality.yml`)

**Trigger**: Push to `main` or `develop`, Pull Requests, Daily schedule

**Purpose**: Comprehensive code quality and security analysis

#### Jobs:

##### Code Quality Checks
- **Runs on**: Ubuntu Latest
- **Tasks**:
  - Bandit security scanner (JSON + text output)
  - Safety vulnerability check
  - Upload reports as artifacts

##### Coverage Threshold
- **Runs on**: Ubuntu Latest
- **Tasks**:
  - Run tests with coverage
  - Check coverage >= 70%
  - Upload to Codecov

##### SonarQube Analysis
- **Runs on**: Ubuntu Latest
- **Requires**: Secrets configured
- **Tasks**:
  - Run tests with coverage
  - SonarQube scan
  - Quality gate check

##### Dependency Check
- **Runs on**: Ubuntu Latest
- **Tasks**:
  - Run OWASP dependency-check
  - Generate JSON report
  - Upload artifacts

##### Code Metrics
- **Runs on**: Ubuntu Latest
- **Tasks**:
  - Calculate cyclomatic complexity (Radon)
  - Calculate maintainability index
  - Upload metrics report

### 5. Scheduled Tests (`.github/workflows/scheduled-tests.yml`)

**Trigger**: Scheduled cron jobs

**Purpose**: Automated testing and audits on a schedule

#### Jobs:

##### Nightly Full Test Suite
- **Schedule**: Daily at 2 AM UTC
- **Tasks**:
  - Run all unit tests
  - Run all integration tests
  - Run end-to-end tests
  - Generate coverage report
  - Notify on failure

##### Weekly Performance Benchmarks
- **Schedule**: Sunday at 3 AM UTC
- **Tasks**:
  - Run performance benchmarks
  - Run database performance tests
  - Compare with baseline
  - Notify on regression

##### Monthly Security Audit
- **Schedule**: 1st of month at 4 AM UTC
- **Tasks**:
  - Comprehensive Bandit scan
  - Comprehensive Safety check
  - OWASP dependency check
  - Generate security report
  - Notify on issues

##### Dependency Updates Check
- **Schedule**: Daily at 2 AM UTC
- **Tasks**:
  - Check for outdated packages
  - Create issue for outdated dependencies

## Configuration Files

### Dependabot Configuration (`.github/dependabot.yml`)

Automated dependency updates for:
- **Python packages**: Weekly on Monday at 3 AM UTC
- **GitHub Actions**: Weekly on Monday at 4 AM UTC
- **Docker**: Weekly on Monday at 5 AM UTC

**Features**:
- Automatic PR creation
- Configurable limits (5 for pip, 3 for actions, 2 for docker)
- Semantic commit messages
- Auto-rebase strategy

### Code Owners (`.github/CODEOWNERS`)

Defines code ownership for automatic reviewer assignment:
- Default: `@john`
- API layer: `@john`
- Database: `@john`
- Services: `@john`
- Tests: `@john`
- CI/CD: `@john`

### Pull Request Template (`.github/pull_request_template.md`)

Standardized PR template with sections for:
- Description and related issues
- Type of change
- Testing details
- Checklist (code quality, tests, documentation)
- Code quality checks
- Performance impact
- Screenshots
- Additional context

### Issue Templates (`.github/issue_template/`)

#### Bug Report
- Description of bug
- Steps to reproduce
- Expected vs actual behavior
- Screenshots
- Environment details
- Error logs
- Possible solution

#### Feature Request
- Problem description
- Proposed solution
- Alternatives considered
- Acceptance criteria
- Implementation notes
- Testing strategy
- Documentation needs

#### Performance Issue
- Performance problem description
- Expected vs actual metrics
- Environment details
- Steps to reproduce
- Profiling data
- Possible root cause

## Environment Variables and Secrets

### Required Secrets

```
DOCKER_USERNAME      # Docker Hub username
DOCKER_PASSWORD      # Docker Hub password/token
SONAR_HOST_URL       # SonarQube server URL (optional)
SONAR_TOKEN          # SonarQube authentication token (optional)
```

### Optional Secrets

```
SLACK_WEBHOOK        # Slack webhook for notifications
GITHUB_TOKEN         # GitHub token (auto-provided)
```

## Best Practices

### 1. Caching

- **Pip dependencies**: Cached automatically using `actions/setup-python@v4`
- **Docker layers**: Cached using GitHub Actions cache backend
- **Build artifacts**: Uploaded and retained for 90 days

### 2. Matrix Testing

- Test across multiple Python versions (3.9, 3.10, 3.11, 3.12)
- Test across multiple OS (Ubuntu, macOS, Windows)
- Fail fast disabled to see all failures

### 3. Security

- Secrets never logged or exposed
- Trivy scanning for container vulnerabilities
- Bandit for code security issues
- Safety for dependency vulnerabilities
- OWASP dependency-check for known vulnerabilities

### 4. Performance

- Parallel job execution where possible
- Dependency caching to reduce install time
- Multi-architecture Docker builds
- Scheduled jobs during off-peak hours

### 5. Notifications

- PR comments with coverage metrics
- GitHub Security tab integration
- Issue creation for outdated dependencies
- Failure notifications (can be extended to Slack, email, etc.)

## Troubleshooting

### Common Issues

#### 1. Tests Failing on Windows

**Problem**: Tests pass on Linux/macOS but fail on Windows

**Solution**:
- Check for path separators (use `pathlib.Path`)
- Check for line ending differences (CRLF vs LF)
- Check for environment-specific code

#### 2. Docker Build Timeout

**Problem**: Docker build takes too long

**Solution**:
- Check for large files in build context
- Use `.dockerignore` to exclude unnecessary files
- Consider multi-stage builds
- Check for network issues during dependency installation

#### 3. Coverage Not Uploading

**Problem**: Coverage reports not appearing in Codecov

**Solution**:
- Verify Codecov token is configured
- Check coverage.xml is generated
- Verify file paths are correct
- Check Codecov service status

#### 4. Dependabot Not Creating PRs

**Problem**: Dependabot configuration not working

**Solution**:
- Verify `.github/dependabot.yml` syntax
- Check repository settings allow Dependabot
- Verify branch protection rules don't block Dependabot
- Check for rate limiting

#### 5. SonarQube Quality Gate Failing

**Problem**: Quality gate check fails

**Solution**:
- Verify SonarQube server is accessible
- Check SONAR_TOKEN is valid
- Review quality gate criteria
- Check coverage thresholds
- Verify project key matches

### Debug Tips

1. **View workflow logs**: Click on workflow run in GitHub Actions tab
2. **Enable debug logging**: Set `ACTIONS_STEP_DEBUG=true` secret
3. **Test locally**: Use `act` tool to run workflows locally
4. **Check syntax**: Use `yamllint` to validate YAML files
5. **Review artifacts**: Download and inspect uploaded artifacts

## Monitoring and Metrics

### Key Metrics to Track

- **Build Success Rate**: Target > 95%
- **Test Coverage**: Target > 70%
- **Code Quality**: SonarQube rating A or B
- **Security Issues**: Target 0 critical/high
- **Deployment Success Rate**: Target > 99%
- **Performance**: Monitor response times and resource usage

### Viewing Metrics

- **GitHub Actions**: Dashboard shows workflow statistics
- **Codecov**: Coverage trends and comparisons
- **SonarQube**: Code quality metrics and trends
- **Artifacts**: Download reports for detailed analysis

## Maintenance

### Regular Tasks

- **Weekly**: Review Dependabot PRs and merge
- **Monthly**: Review security audit reports
- **Quarterly**: Review and update workflow versions
- **Annually**: Review and update Python versions

### Updating Workflows

1. Test changes in a feature branch
2. Create PR with workflow changes
3. Review and test in PR
4. Merge to main
5. Monitor first execution

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/guides)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [Trivy Scanner](https://github.com/aquasecurity/trivy-action)
- [SonarQube Action](https://github.com/SonarSource/sonarqube-scan-action)

## Support

For issues or questions about the CI/CD pipeline:

1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Check GitHub Actions status page
4. Open an issue with `ci-cd` label
