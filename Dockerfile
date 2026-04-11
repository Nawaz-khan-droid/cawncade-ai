# STAGE 1: Build the React Frontend
FROM node:20-alpine AS build-frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# STAGE 2: Build the Backend & Serve Frontend
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend code
COPY backend/ .

# Copy built frontend from Stage 1 into the backend's static folder
COPY --from=build-frontend /app/frontend/dist /app/static

# Environment variables for HF
ENV ENVIRONMENT=production \
    PORT=7860 \
    PYTHONUNBUFFERED=1

# Expose the mandatory HF port
EXPOSE 7860

# Start FastAPI and tell it to serve on 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]