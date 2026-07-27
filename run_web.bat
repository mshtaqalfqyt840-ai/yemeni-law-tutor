@echo off
chcp 65001 >nul
echo ====================================================================
echo   تشغيل مشروع المعلّم الذكي - الواجهة الحديثة (React + FastAPI)
echo ====================================================================

echo [1/2] تشغيل خادم الكواليس (FastAPI Backend) على المنفذ 8000...
start "FastAPI Backend - Port 8000" /MIN cmd /k ".\venv\Scripts\activate && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] تشغيل واجهة المستخدم الحديثة (React Vite Frontend) على المنفذ 5173...
cd frontend
start "React Frontend - Port 5173" cmd /k "npm run dev -- --host"

echo ====================================================================
echo  تم إطلاق الخوادم بنجاح!
echo  - واجهة الويب (React):   http://localhost:5173
echo  - خادم الـ API (FastAPI):   http://localhost:8000/docs
echo ====================================================================
pause
