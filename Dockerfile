# ==========================================
# STAGE 1: Build the React Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Install dependencies first for layer caching
COPY frontend/package*.json ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Setup FastAPI Backend
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Install necessary system libraries (required by FAISS/PyTorch if needed, and Tesseract for Phase 4 OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory
COPY backend/ ./backend/

# Copy the compiled React App from Stage 1 into the FastAPI static folder
# main.py looks for: os.path.join(..., "..", "static") -> backend/static
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# IMPORTANT: Render STRICTLY requires port 10000
EXPOSE 10000

# Run the Uvicorn server on port 10000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "10000"]