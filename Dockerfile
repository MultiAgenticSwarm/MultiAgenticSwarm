# Dockerfile for MultiAgenticSwarm
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy and install Python dependencies
COPY pyproject.toml ./
RUN pip install -e .

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Create logs directory
RUN mkdir -p /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import multiagenticswarm; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "multiagenticswarm", "--help"]

# Labels for metadata
LABEL maintainer="MultiAgenticSwarm Team <contact@multiagenticswarm.dev>" \
      version="0.1.0" \
      description="A powerful LangGraph-based multi-agent system" \
      org.opencontainers.image.source="https://github.com/multiagenticswarm/multiagenticswarm"
