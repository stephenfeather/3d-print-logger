# 3D Print Logger - Dockerfile
# Placeholder for Phase 6 deployment implementation

# TODO: Implement multi-stage build
# - Stage 1: Build frontend (when implemented)
# - Stage 2: Production image with Python app

FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config.example.yml ./config.yml

# Expose API port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
