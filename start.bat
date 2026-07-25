@echo off
title CAWNCADE AI - Full Stack

echo ===================================================
echo   CAWNCADE AI - Starting Verification Pipeline
echo ===================================================

echo [1/2] Starting FastAPI Backend on port 8000...
start /B cmd /c "cd backend && if not exist venv (echo Creating venv... && python -m venv venv && echo Installing dependencies... && venv\Scripts\python -m pip install -r requirements.txt) && venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Vite Frontend on port 3000/3001...
start /B cmd /c "cd frontend && "C:\Program Files\nodejs\npm.cmd" run dev || npm run dev"

echo ===================================================
echo   Services are running! (Unified Logging)
echo   Press CTRL+C in this window to terminate.
echo ===================================================
