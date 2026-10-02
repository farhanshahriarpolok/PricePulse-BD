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
    DATABASE_URL="sqlite:////app/data/pricepulse.db" \
    BACKUP_DIR="/app/data/backups"

WORKDIR /app

# Install minimal OS dependencies for healthchecks and SQLite WAL operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create dedicated unprivileged service user and group (UID/GID 1000)
RUN groupadd --gid 1000 pricepulse \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin pricepulse

# Copy backend application code and canonical data taxonomy
COPY app/ ./app/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY run_system.py ./

# Copy compiled frontend distribution from Stage 1 into FastAPI static root
COPY --from=frontend-builder /build/dist ./frontend/dist

# Create persistent storage volume directory and backup directory with explicit user ownership
RUN mkdir -p /app/data/backups \
    && chown -R pricepulse:pricepulse /app

# Declare persistent storage volume
VOLUME ["/app/data"]

EXPOSE 8000

# Automated container healthcheck (executable by unprivileged user)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Switch to unprivileged runtime user (UID 1000)
USER pricepulse

# Production WSGI/ASGI Runner — Single Worker prevents duplicate in-process scheduler instances
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
