FROM python:3.12-slim AS builder
LABEL maintainer="ttek.com"

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python packages
COPY requirements.txt /tmp/
RUN python -m venv /py && \
    /py/bin/pip install --no-cache-dir --upgrade pip && \
    /py/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# Build dev dependencies conditionally
ARG DEV=false
COPY requirements.dev.txt /tmp/
RUN if [ "$DEV" = "true" ]; then \
        /py/bin/pip install --no-cache-dir -r /tmp/requirements.dev.txt; \
    fi

# Runtime stage
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/py/bin:$PATH" \
    XDG_CACHE_HOME="/var/cache/fontconfig" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install only runtime dependencies in a single layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq5 \
        fontconfig \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        shared-mime-info \
        libcairo2 \
        libglib2.0-0 \
        libjpeg62-turbo \
        libopenjp2-7 \
        libtiff6 \
        libwebp7 && \
    fc-cache -fv

# Copy virtual environment from builder
COPY --from=builder /py /py

# Create non-root user
RUN adduser \
        --disabled-password \
        --gecos '' \
        ttek_user && \
    mkdir -p /var/cache/fontconfig /app && \
    chown -R ttek_user:ttek_user /var/cache/fontconfig /app /py

WORKDIR /app
USER ttek_user

# Copy application code (after switching to non-root user)
COPY --chown=ttek_user:ttek_user . .

EXPOSE 8000