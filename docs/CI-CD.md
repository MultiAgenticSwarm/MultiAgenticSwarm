# CI/CD Setup for MultiAgenticSwarm

This document describes the comprehensive CI/CD pipeline implemented for the MultiAgenticSwarm project.

## 🔄 Overview

Our CI/CD pipeline follows industry best practices and includes:

- **Continuous Integration (CI)**: Automated testing, linting, security scanning
- **Continuous Deployment (CD)**: Automated releases to PyPI and Docker Hub
- **Quality Assurance**: Code quality metrics, performance testing, documentation
- **Security**: Vulnerability scanning, dependency updates, secrets detection

## 🏗️ Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Code Push     │───▶│  CI Pipeline    │───▶│ Quality Gates   │
│                 │    │                 │    │                 │
│ • Feature       │    │ • Lint & Format │    │ • All Tests Pass│
│ • Bugfix        │    │ • Security Scan │    │ • Coverage > 80%│
│ • Documentation │    │ • Multi-OS Test │    │ • No Vulnerab.  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Deployment    │◄───│  CD Pipeline    │◄───│   Merge to      │
│                 │    │                 │    │     Main        │
│ • PyPI Release  │    │ • Build Package │    │                 │
│ • Docker Image  │    │ • Create Release│    │ • Tag Creation  │
│ • Documentation │    │ • Update Docs   │    │ • Manual Trigger│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual dispatch

**Jobs:**
- **Lint**: Code formatting, import sorting, linting, type checking
- **Security**: Security scanning with Bandit and Safety
- **Test**: Multi-OS (Ubuntu, Windows, macOS) and multi-Python (3.9-3.12) testing
- **Integration Test**: Example scripts and CLI functionality
- **Documentation**: README validation and doc generation
- **Build**: Package building and validation

### 2. CD Workflow (`.github/workflows/cd.yml`)

**Triggers:**
- Tags matching `v*` pattern
- GitHub releases
- Manual dispatch with version input

**Jobs:**
- **Validate Release**: Version validation and prerelease detection
- **Run Tests**: Full CI pipeline execution
- **Build and Publish**: Package building and PyPI publication
- **Docker Build**: Multi-platform Docker image creation
- **GitHub Release**: Automated release creation with changelog
- **Documentation Update**: Version updates in documentation

### 3. Quality Workflow (`.github/workflows/quality.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests
- Weekly scheduled runs

**Jobs:**
- **Code Quality**: Complexity analysis, maintainability metrics
- **Documentation Quality**: Docstring coverage, style checking
- **Test Quality**: Comprehensive test analysis
- **Performance Analysis**: Benchmarking and profiling

### 4. Dependencies Workflow (`.github/workflows/dependencies.yml`)

**Triggers:**
- Weekly scheduled runs (Mondays at 9 AM UTC)
- Manual dispatch

**Jobs:**
- **Update Dependencies**: Automated dependency updates
- **Security Audit**: Vulnerability scanning and reporting

### 5. Documentation Workflow (`.github/workflows/docs.yml`)

**Triggers:**
- Push to `main` (docs changes)
- Pull requests affecting documentation

**Jobs:**
- **Build Documentation**: Sphinx documentation generation
- **Deploy to GitHub Pages**: Automated documentation deployment
- **Link Validation**: Broken link detection
- **Wiki Updates**: GitHub Wiki synchronization

## 🛠️ Development Tools

### Pre-commit Hooks

Installed via `.pre-commit-config.yaml`:

```bash
make setup-dev  # Installs pre-commit hooks
```

**Hooks:**
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting with extensions
- **mypy**: Type checking
- **bandit**: Security scanning
- **Conventional Commits**: Commit message validation
- **General**: Trailing whitespace, file size checks, etc.

### Makefile Commands

Common development tasks:

```bash
# Setup
make setup-dev          # Complete development environment setup
make install-dev        # Install with development dependencies

# Code Quality
make format             # Format code with black and isort
make lint               # Run all linting tools
make security           # Run security checks
make pre-commit         # Run pre-commit hooks

# Testing
make test               # Run tests
make test-coverage      # Run tests with coverage
make test-performance   # Run performance benchmarks

# Build & Deploy
make build              # Build package
make docker             # Build Docker image
make clean              # Clean build artifacts

# Development
make dev                # Quick development cycle (format, lint, test)
make validate           # Full validation (like CI)
```

## 🔐 Secrets and Configuration

### Required Secrets

Configure these secrets in your GitHub repository:

```bash
# PyPI deployment
PYPI_API_TOKEN          # Production PyPI token
TEST_PYPI_API_TOKEN     # Test PyPI token

# Optional: For enhanced features
CODECOV_TOKEN           # Code coverage reporting
DISCORD_WEBHOOK         # Discord notifications
```

### Environment Variables

Set in workflow files or repository settings:

```yaml
env:
  OPENAI_API_KEY: test-key        # For testing
  ANTHROPIC_API_KEY: test-key     # For testing
  AWS_ACCESS_KEY_ID: test-key     # For testing
  AWS_SECRET_ACCESS_KEY: test-key # For testing
```

## 📊 Quality Gates

### Test Coverage
- Minimum: 80% overall coverage
- Critical paths: 95% coverage required
- Coverage reports uploaded to Codecov

### Code Quality
- **Complexity**: Maximum cyclomatic complexity of B
- **Maintainability**: Minimum maintainability index of A
- **Security**: No high or critical vulnerabilities
- **Style**: 100% compliance with Black and flake8

### Performance
- **Import time**: < 1 second
- **Basic operations**: < 100ms
- **Memory usage**: < 100MB baseline

## 🚨 Monitoring and Alerts

### Automated Monitoring
- **Dependency vulnerabilities**: Weekly scans
- **Code quality regression**: On every commit
- **Performance degradation**: Benchmark comparisons
- **Documentation coverage**: Minimum 80% docstring coverage

### Notifications
- **Failed builds**: GitHub Actions notifications
- **Security issues**: Automated issue creation
- **Dependency updates**: Pull request creation

## 🔄 Release Process

### Automatic Releases

1. **Create a tag**: `git tag v1.0.0 && git push --tags`
2. **CI/CD automatically**:
   - Runs full test suite
   - Builds package
   - Publishes to PyPI
   - Creates GitHub release
   - Builds and pushes Docker image
   - Updates documentation

### Manual Releases

```bash
# Update version
make bump-version

# Create and push tag
git tag v$(grep 'version = ' pyproject.toml | cut -d'"' -f2)
git push --tags

# Or use GitHub Actions manual dispatch
```

### Versioning Strategy

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Pre-releases**: v1.0.0-alpha.1, v1.0.0-beta.1, v1.0.0-rc.1
- **Automatic**: Patch version bumps for hotfixes
- **Manual**: Minor/major version control

## 🐛 Debugging CI/CD Issues

### Common Issues

1. **Test Failures**
   ```bash
   # Run tests locally
   make test-coverage

   # Check specific environment
   python3.9 -m pytest tests/
   ```

2. **Linting Failures**
   ```bash
   # Fix formatting
   make format

   # Check linting
   make lint
   ```

3. **Security Issues**
   ```bash
   # Run security checks
   make security

   # Update dependencies
   make update-deps
   ```

4. **Build Failures**
   ```bash
   # Clean and rebuild
   make clean build

   # Check package
   twine check dist/*
   ```

### Workflow Debugging

- **GitHub Actions logs**: Check the Actions tab
- **Local simulation**: Use `act` to run workflows locally
- **Matrix debugging**: Test specific OS/Python combinations
- **Artifacts**: Download build artifacts for inspection

## 📈 Metrics and Reporting

### Automated Reports
- **Test Coverage**: HTML and XML reports
- **Code Quality**: Complexity and maintainability metrics
- **Security**: Vulnerability and dependency reports
- **Performance**: Benchmark results and trends

### Dashboard Integration
- **GitHub**: Built-in Actions dashboard
- **Codecov**: Coverage trends and reports
- **Badges**: README status badges for quick overview

## 🔧 Customization

### Adding New Checks

1. **New Linter**: Add to `.pre-commit-config.yaml` and CI workflow
2. **New Test Type**: Add job to `ci.yml` workflow
3. **New Quality Gate**: Update quality workflow and Makefile

### Environment-Specific Configuration

```yaml
# Example: Add environment-specific testing
strategy:
  matrix:
    include:
      - os: ubuntu-latest
        python-version: "3.10"
        environment: "production"
      - os: ubuntu-latest
        python-version: "3.10"
        environment: "staging"
```

## 📞 Support

For CI/CD related issues:

1. **Check workflow logs** in GitHub Actions tab
2. **Run locally** using Makefile commands
3. **Create issue** with workflow run details
4. **Join Discord** for real-time help

## 🎯 Best Practices Applied

1. **Fail Fast**: Early detection of issues
2. **Matrix Testing**: Multiple OS and Python versions
3. **Security First**: Automated vulnerability scanning
4. **Documentation**: Always up-to-date docs
5. **Reproducible**: Consistent environments across stages
6. **Monitoring**: Comprehensive metrics and alerts
7. **Automation**: Minimal manual intervention required

This CI/CD setup ensures high code quality, security, and reliability while enabling rapid and safe deployments.
