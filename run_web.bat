@echo off
chcp 65001 >nul
echo ====================================================================
echo Starting Yemeni Law Tutor - React + FastAPI
echo ====================================================================

echo [1/2] Starting FastAPI Backend on Port 8000...
start "FastAPI Backend" /MIN cmd /c ".\venv\Scripts\activate && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting React Vite Frontend on Port 5173...
start "React Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev -- --host"

echo ====================================================================
echo  Servers Launched Successfully!
echo  - React Frontend: http://localhost:5173
echo  - FastAPI Docs:   http://localhost:8000/docs
echo ====================================================================
