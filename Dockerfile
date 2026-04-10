# CAWNCADE AI — Unified Dockerfile for Hugging Face Spaces (Docker mode)
# Builds frontend (React) → serves it via FastAPI alongside the backend API
# ONE container, ONE process, FULLY DYNAMIC

# ============================================================
# STAGE 1: Build React frontend
# ============================================================
FROM node:20-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build
# Output: /frontend/dist/ (static HTML/JS/CSS)

# ============================================================
# STAGE 2: Python backend + built frontend
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from Stage 1
COPY --from=frontend-build /frontend/dist /app/static

# Create data directory for SQLite
RUN mkdir -p /app/data

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    DATABASE_URL=sqlite:////app/data/cawncade.db \
    PORT=7860

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:7860/health')" || exit 1

# Start server on port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
