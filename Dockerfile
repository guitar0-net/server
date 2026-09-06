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

# Install system dependencies (libpango/cairo required by WeasyPrint).
#
# util-linux is pulled from trixie-security on top of whatever the base image
# ships. python:*-slim carries 2.41-5, which still has CVE-2026-53612..53615
# (mount(8) SUID privesc, libblkid overflow) and hard-fails the CRITICAL/HIGH
# Trivy gate in deploy.yml. Strict versioned deps make apt drag the rest of the
# source package along (mount, bsdutils, libblkid1, libmount1, libsmartcols1,
# libuuid1, liblastlog2-2, login), so naming util-linux alone is enough.
#
# This is a stopgap, not a permanent hand-managed pin: the build uses
# `pull: true`, so once the python image is rebuilt against current
# trixie-security the line becomes a no-op and can be dropped.
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
    && apt-get install -y --no-install-recommends --only-upgrade util-linux \
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


CMD ["gunicorn", "--config", "config/gunicorn.py", "config.wsgi:application"]
