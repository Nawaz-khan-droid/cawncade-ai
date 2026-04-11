# CAWNCADE AI v3.0 — Unified Dockerfile for Hugging Face Spaces
# Builds React frontend -> serves via FastAPI alongside backend API
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

# Create data directories for persistent storage (HF Persistent Storage mount)
RUN mkdir -p /data /data/chroma && chmod 777 /data /data/chroma

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    DATABASE_URL=sqlite:////data/cawncade.db \
    CHROMA_PATH=/data/chroma \
    PORT=7860

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:7860/api/health', timeout=5)" || exit 1

# Start server on port 7860
# We use 'app.main:app' because /app/app/main.py exists after copying
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
