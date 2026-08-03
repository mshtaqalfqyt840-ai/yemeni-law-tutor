# ── المرحلة 1: بناء واجهة React Vite الحديثة ──
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── المرحلة 2: تشغيل الخادم الخلفي (Python FastAPI + RAG) ──
FROM python:3.11-slim
WORKDIR /app

# تثبيت متطلبات النظام البسيطة
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# تثبيت حزم بايثون
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود المشروع وقاعدة البيانات المتجهة chroma_db_v2
COPY . .
# نسخ ملفات بناء الواجهة من المرحلة الأولى
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# تحديد المنفذ الرسمي للمنصة السحابية (Railway)
ENV PORT=8000
EXPOSE 8000

# تشغيل خادم FastAPI على المنفذ 8000 مباشرة
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
