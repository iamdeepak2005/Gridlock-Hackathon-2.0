# ─────────────────────────────────────────────────────────────
#  TRINETRA AI — Backend Dockerfile
#  FastAPI + ML Models (Python 3.12)
# ─────────────────────────────────────────────────────────────

FROM python:3.12-slim AS base

# System dependencies for geopandas/GDAL/osmnx
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libspatialindex-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/
COPY tests/ ./tests/

# Create directories for runtime data
RUN mkdir -p trained_models data osmnx_cache

# Copy data if available (optional — can be mounted via volume)
COPY data/ ./data/ 2>/dev/null || true

# Copy pre-trained models if available (optional — can be mounted via volume)
COPY trained_models/ ./trained_models/ 2>/dev/null || true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
