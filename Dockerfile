# ==============================================================================
# PricePulse BD — Production Multi-Stage Container Engine
# Stage 1: Frontend Build (Node 20 Alpine)
# Stage 2: Unified Backend & Runtime Container (Python 3.11 Slim)
# ==============================================================================

# --- Stage 1: Frontend Build Environment ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# Install frontend dependencies
COPY frontend/package*.json ./
RUN npm ci --prefer-offline || npm install

# Copy frontend source code and compile optimized production bundle
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Runtime ---
FROM python:3.11-slim AS production

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATABASE_URL="sqlite:////app/data/pricepulse.db"

WORKDIR /app

# Install minimal OS dependencies for healthchecks and SQLite WAL operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code and canonical data taxonomy
COPY app/ ./app/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY run_system.py ./

# Copy compiled frontend distribution from Stage 1 into FastAPI static root
COPY --from=frontend-builder /build/dist ./frontend/dist

# Create persistent storage volume directory for SQLite WAL database
RUN mkdir -p /app/data && chmod 777 /app/data

VOLUME ["/app/data"]

EXPOSE 8000

# Automated container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Production WSGI/ASGI Runner
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
