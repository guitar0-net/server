# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Stage 1: Builder
FROM python:3.14.7-slim AS builder

WORKDIR /app

# Upgrade pip to fix known vulnerabilities, then install PDM
RUN pip install --no-cache-dir "pip==26.1.2" && pip install --no-cache-dir pdm

# Copy dependency files
COPY pyproject.toml pdm.lock ./

# Export dependencies to requirements.txt (production only, no dev/test)
RUN pdm export --no-hashes -o requirements.txt --prod

# Stage 2: Production
FROM python:3.14.7-slim AS production

# Build arguments for versioning
ARG VERSION=unknown
ARG GIT_SHA=unknown
ARG BUILD_DATETIME=unknown

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VERSION=${VERSION} \
    GIT_SHA=${GIT_SHA} \
    BUILD_DATETIME=${BUILD_DATETIME}

WORKDIR /app

# Install system dependencies (libpango/cairo required by WeasyPrint)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Copy requirements from builder
COPY --from=builder /app/requirements.txt .

# Upgrade pip to fix known vulnerabilities, then install dependencies
RUN pip install --no-cache-dir "pip==26.1.2" && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser manage.py ./
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser apps/ ./apps/

# Create directories for static files and logs
RUN mkdir -p /app/staticfiles /app/logs \
    && chown -R appuser:appuser /app/staticfiles /app/logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/metrics/ || exit 1

CMD ["gunicorn", "--config", "config/gunicorn.py", "config.wsgi:application"]
