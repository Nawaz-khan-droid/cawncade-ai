# STAGE 1: Build the React Frontend
FROM node:20-alpine AS build-frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# STAGE 2: Build the Backend & Serve
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for AI/Vision
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend code
COPY backend/ .

# Copy built frontend from Stage 1 into the backend's static folder
# This ensures FastAPI can see the React build
COPY --from=build-frontend /app/frontend/dist /app/static

# Persistent Storage & Permissions
RUN mkdir -p /data && chmod 777 /data

# Environment
ENV ENVIRONMENT=production \
    PYTHONUNBUFFERED=1 \
    PORT=7860

EXPOSE 7860

# Start FastAPI on the mandatory HF port
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]