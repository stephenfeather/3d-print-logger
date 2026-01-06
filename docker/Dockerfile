# 3D Print Logger - Multi-Stage Dockerfile
# Stage 1: Build frontend
# Stage 2: Production Python application

# =============================================================================
# Stage 1: Build Frontend
# =============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

# Copy package files for dependency caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build production bundle
RUN npm run build-only

# =============================================================================
# Stage 2: Production Image
# =============================================================================
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/app/config.yml

WORKDIR /app

# Install system dependencies (required for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements-prod.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Remove gcc after pip install (no longer needed)
RUN apt-get purge -y gcc && apt-get autoremove -y

# Copy application code
COPY src/ ./src/
COPY alembic.ini ./
COPY config.example.yml ./config.yml

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/dist ./static

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

USER appuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
