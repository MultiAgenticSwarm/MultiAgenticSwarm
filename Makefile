# Makefile for MultiAgenticSwarm development

.PHONY: help install install-dev test test-verbose test-coverage lint format type-check security clean build publish docker run-examples setup-dev pre-commit docs

# Default target
help:
	@echo "MultiAgenticSwarm Development Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  install         Install package in editable mode"
	@echo "  install-dev     Install with development dependencies"
	@echo "  setup-dev       Complete development environment setup"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint            Run all linting tools"
	@echo "  format          Format code with black and isort"
	@echo "  type-check      Run mypy type checking"
	@echo "  security        Run security checks"
	@echo "  pre-commit      Install and run pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  test            Run tests"
	@echo "  test-verbose    Run tests with verbose output"
	@echo "  test-coverage   Run tests with coverage report"
	@echo "  test-performance Run performance benchmarks"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  clean           Clean build artifacts"
	@echo "  build           Build package"
	@echo "  publish         Publish to PyPI (requires credentials)"
	@echo "  docker          Build Docker image"
	@echo ""
	@echo "Documentation:"
	@echo "  docs            Generate documentation"
	@echo "  docs-serve      Serve documentation locally"
	@echo ""
	@echo "Examples:"
	@echo "  run-examples    Run example scripts"
	@echo ""

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,examples]"

setup-dev: install-dev
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "Development environment setup complete!"

# Code quality targets
lint: flake8 mypy bandit

flake8:
	@echo "Running flake8..."
	flake8 multiagenticswarm/ tests/

mypy:
	@echo "Running mypy..."
	mypy multiagenticswarm/

bandit:
	@echo "Running bandit..."
	bandit -r multiagenticswarm/ -c pyproject.toml

format:
	@echo "Formatting code..."
	black multiagenticswarm/ tests/
	isort multiagenticswarm/ tests/

type-check: mypy

security: bandit
	@echo "Running safety check..."
	safety check --full-report

pre-commit:
	pre-commit install
	pre-commit run --all-files

# Testing targets
test:
	@echo "Running tests..."
	pytest tests/ -v

test-verbose:
	@echo "Running tests with verbose output..."
	pytest tests/ -v -s

test-coverage:
	@echo "Running tests with coverage..."
	pytest tests/ \
		--cov=multiagenticswarm \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-report=xml \
		-v

test-performance:
	@echo "Running performance benchmarks..."
	pytest tests/ -k benchmark --benchmark-json=benchmark-results.json

# Build and deployment targets
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	@echo "Building package..."
	python -m build

publish: build
	@echo "Publishing to PyPI..."
	twine check dist/*
	twine upload dist/*

docker:
	@echo "Building Docker image..."
	docker build -t multiagenticswarm:latest .

docker-compose:
	@echo "Starting services with docker-compose..."
	docker-compose up -d

# Documentation targets
docs:
	@echo "Generating documentation..."
	@if [ ! -d "docs" ]; then \
		mkdir -p docs; \
		echo "# MultiAgenticSwarm Documentation" > docs/index.md; \
		echo "Documentation directory created."; \
	fi
	@echo "Documentation generated in docs/"

docs-serve:
	@echo "Serving documentation locally..."
	@if command -v python -m http.server >/dev/null 2>&1; then \
		cd docs && python -m http.server 8080; \
	else \
		echo "Python http.server not available"; \
	fi

# Example targets
run-examples:
	@echo "Running example scripts..."
	@if [ -f "examples/logging_demo.py" ]; then \
		python examples/logging_demo.py; \
	else \
		echo "No examples found"; \
	fi

# Development workflow targets
check-all: format lint test-coverage security
	@echo "All checks completed!"

ci-local: clean install-dev check-all
	@echo "Local CI pipeline completed!"

# Release targets
bump-version:
	@echo "Current version: $(shell grep 'version = ' pyproject.toml | cut -d'"' -f2)"
	@read -p "Enter new version: " version; \
	sed -i "s/version = \".*\"/version = \"$$version\"/" pyproject.toml; \
	sed -i "s/__version__ = \".*\"/__version__ = \"$$version\"/" multiagenticswarm/__init__.py; \
	echo "Version bumped to $$version"

# Monitoring targets
logs:
	@echo "Showing recent logs..."
	@if [ -d "logs" ]; then \
		find logs/ -name "*.log" -exec tail -n 20 {} \; ; \
	else \
		echo "No logs directory found"; \
	fi

monitor:
	@echo "Monitoring logs..."
	@if [ -d "logs" ]; then \
		tail -f logs/*.log; \
	else \
		echo "No logs directory found"; \
	fi

# Database/cache targets (for development with docker-compose)
db-reset:
	@echo "Resetting database..."
	docker-compose down
	docker volume rm multiagenticswarm_postgres-data || true
	docker-compose up -d postgres

cache-clear:
	@echo "Clearing Redis cache..."
	docker-compose exec redis redis-cli FLUSHALL

# Quality reports
quality-report:
	@echo "Generating quality report..."
	@mkdir -p reports
	@echo "# Quality Report" > reports/quality.md
	@echo "" >> reports/quality.md
	@echo "## Code Complexity" >> reports/quality.md
	@echo '```' >> reports/quality.md
	@radon cc multiagenticswarm/ -a >> reports/quality.md || echo "radon not installed" >> reports/quality.md
	@echo '```' >> reports/quality.md
	@echo "" >> reports/quality.md
	@echo "## Maintainability Index" >> reports/quality.md
	@echo '```' >> reports/quality.md
	@radon mi multiagenticswarm/ >> reports/quality.md || echo "radon not installed" >> reports/quality.md
	@echo '```' >> reports/quality.md
	@echo "Quality report generated in reports/quality.md"

# Development utilities
requirements:
	@echo "Generating requirements.txt..."
	pip-compile pyproject.toml

requirements-dev:
	@echo "Generating dev-requirements.txt..."
	pip-compile --extra dev pyproject.toml -o dev-requirements.txt

update-deps:
	@echo "Updating dependencies..."
	pip-compile --upgrade pyproject.toml
	pip-compile --upgrade --extra dev pyproject.toml -o dev-requirements.txt

# Environment info
env-info:
	@echo "Environment Information"
	@echo "======================"
	@echo "Python: $(shell python --version)"
	@echo "Pip: $(shell pip --version)"
	@echo "Platform: $(shell python -c 'import platform; print(platform.platform())')"
	@echo "MultiAgenticSwarm: $(shell python -c 'import multiagenticswarm; print(multiagenticswarm.__version__)' 2>/dev/null || echo 'Not installed')"

# Quick development cycle
dev: format lint test
	@echo "Development cycle completed!"

# Full validation (like CI)
validate: clean install-dev check-all build
	@echo "Full validation completed!"
