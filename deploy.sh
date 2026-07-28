#!/usr/bin/env bash
# CAWNCADE AI — Quick Deploy Script
# Usage: bash deploy.sh [railway|render|local]

set -e

MODE="${1:-local}"

echo "============================================"
echo "  CAWNCADE AI — Deploy: $MODE"
echo "============================================"

case "$MODE" in
  local)
    echo "Starting local Docker stack..."
    docker-compose down 2>/dev/null || true
    docker-compose build
    docker-compose up -d
    echo ""
    echo "Frontend: http://localhost"
    echo "Backend:  http://localhost:8000"
    echo "Docs:     http://localhost:8000/docs"
    ;;

  railway)
    echo "Deploying to Railway..."
    echo "Prerequisites: railway CLI installed and logged in"
    echo "Install: npm install -g @railway/cli"
    echo ""
    railway init --name cawncade-ai
    railway up
    echo "Deployed! Check Railway dashboard for URL."
    ;;

  render)
    echo "Deploying to Render..."
    echo "1. Connect your GitHub repo at https://render.com"
    echo "2. Create new Web Service"
    echo "3. Use Dockerfile from /backend"
    echo "4. Set environment variables from .env.example"
    echo "5. For frontend, create static site pointing to /frontend/dist"
    ;;

  gcp)
    echo "Deploying to Google Cloud Run..."
    echo "Prerequisites: gcloud CLI installed and configured"
    echo ""
    # Backend
    echo "Building backend image..."
    docker build -t gcr.io/$(gcloud config get-value project)/cawncade-backend ./backend
    docker push gcr.io/$(gcloud config get-value project)/cawncade-backend
    gcloud run deploy cawncade-backend --image gcr.io/$(gcloud config get-value project)/cawncade-backend --port 8000 --allow-unauthenticated
    ;;

  *)
    echo "Unknown deploy mode: $MODE"
    echo "Usage: bash deploy.sh [local|railway|render|gcp]"
    exit 1
    ;;
esac
