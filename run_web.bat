@echo off
chcp 65001 > nul
echo ====================================================================
echo   Yemeni Law AI Tutor (Unified Fullstack App)
echo   Node.js Backend + React Frontend
echo ====================================================================

echo [1/2] Starting Node.js Backend Server on Port 8000...
start "Node.js Backend" /MIN cmd /k "cd /d %~dp0 && node server.js"

ping 127.0.0.1 -n 3 > nul

echo [2/2] Starting React Frontend Dev Server on Port 5173...
start "React Frontend" cmd /k "cd /d %~dp0 && npm run dev -- --host"

echo ====================================================================
echo  Servers Launched Successfully!
echo  - React Frontend:  http://localhost:5173
echo  - Node.js Backend: http://localhost:8000
echo  - Health Check:    http://localhost:8000/api/health
echo ====================================================================
