import os
import sys

# ── فحص بيئة التشغيل (Venv Guard) ──
if sys.prefix == sys.base_prefix:
    print("\n" + "=" * 75)
    print("❌ خطأ تشغيلي: يتم تشغيل النظام عبر بايثون العام (Global Python)!")
    print("⚠️ لم يتم تفعيل البيئة الافتراضية الخاصة بالمشروع (venv).")
    print("-" * 75)
    print("💡 الحل: يرجى تفعيل البيئة الافتراضية أو استخدام المسار المباشر لبايثون البيئة:")
    print("   • طريقة التفعيل:      .\\venv\\Scripts\\activate")
    print("   • أمر التشغيل المباشر: .\\venv\\Scripts\\python.exe -m uvicorn backend.main:app --reload --port 8000")
    print("=" * 75 + "\n")
    sys.exit(1)

import time
import collections
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Request, Response
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sse_starlette.sse import EventSourceResponse


# Ensure root directory is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.models import (
    ChatRequest,
    ChatResponse,
    SuggestionItem,
    SystemStats,
    APIKeyRequest,
    APIKeyResponse,
)
from backend.services import (
    get_system_stats_service,
    get_default_suggestions,
    generate_chat_answer_sync,
    stream_chat_answer_sse,
    add_user_api_key,
    clear_answer_cache,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    مُدير دورة حياة تطبيق FastAPI (Lifespan Context Manager):
    يفحص عند إقلاع الخادم سلامة تحميل قاعدة البيانات المتجهة ChromaDB دون منع الخادم من الإقلاع (Fail-Open).
    """
    try:
        from backend.services import get_vectorstore
        vectorstore = get_vectorstore()
        if vectorstore is not None:
            print("✅ [Lifespan Check] تم التثبت بنجاح من سلامة تحميل قاعدة البيانات المتجهة ChromaDB عند بدء الخادم.")
        else:
            print("⚠️ [Lifespan Check] تنبيه: تعذّر تحميل قاعدة ChromaDB (مفقودة أو تالفة). سيعمل الخادم بنظام التراجع الذكي (BM25 فقط).")
    except Exception as e:
        print(f"⚠️ [Lifespan Check] تنبيه: حدث خطأ غير متوقع أثناء فحص ChromaDB عند الإقلاع ({e}). سيعمل الخادم بنظام التراجع الذكي.")
    yield


class ClientRateLimitMiddleware(BaseHTTPMiddleware):
    """
    طبقة وسيطة لحماية الخادم من إغراق الطلبات المتتالية بتصنيف متدرج حسب خطورة المسار (Rate Limiter per IP).
    - مسارات المحادثة (/api/chat, /api/chat/stream): 20 طلب / دقيقة
    - المسارات الحساسة (/api/keys, /api/cache/clear): 5 طلبات / دقيقة
    - مسارات الإحصائيات والاقتراحات (/api/stats, /api/suggestions): 60 طلب / دقيقة
    """

    def __init__(self, app, window_seconds: int = 60):
        super().__init__(app)
        self.window_seconds = window_seconds
        self.route_limits = {
            "/api/chat": 20,
            "/api/chat/stream": 20,
            "/api/keys": 5,
            "/api/cache/clear": 5,
            "/api/stats": 60,
            "/api/suggestions": 60,
        }
        self.client_records = collections.defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self.route_limits:
            max_requests = self.route_limits[path]
            client_ip = request.client.host if request.client else "127.0.0.1"
            record_key = (client_ip, path)
            now = time.time()

            # 1. تنظيف الطلبات القديمة الخارجة عن النافذة الزمنية
            timestamps = [
                ts
                for ts in self.client_records[record_key]
                if now - ts < self.window_seconds
            ]
            self.client_records[record_key] = timestamps

            # 2. فحص ما إذا تجاوز العميل الحد الأقصى المسموح به لهذا المسار
            if len(timestamps) >= max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "⚠️ تم تجاوز حد الطلبات المسموح به لهذا المسار من عنوان جهازك "
                            f"({max_requests} طلبات / دقيقة). يرجى الانتظار بضع ثوانٍ."
                        )
                    },
                )
            self.client_records[record_key].append(now)

        return await call_next(request)


app = FastAPI(
    title="المعلّم الذكي - الديوان الرقمي للقانون المدني اليمني API",
    description="واجهة برمجة تطبيقات (API) لتقديم الاستشارات القانونية المستندة لحرفية القانون اليمني مع بث حي (SSE).",
    version="2.0.0",
    lifespan=lifespan,
)

# تفعيل طبقة تحديد معدل الطلبات بتصنيف متدرج (Differentiated Rate Limiting Middleware)
app.add_middleware(ClientRateLimitMiddleware, window_seconds=60)

# تفعيل CORS السماح لجميع النطاقات في الإنتاج (Vercel / Netlify / محلي) دون أخطاء CORS
raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
if raw_origins == "*":
    allowed_origins = ["*"]
elif raw_origins and raw_origins.strip():
    allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_admin_secret(request: Request):
    """
    فحص التوثيق للمسارات الإدارية الحساسة عبر الهيدر X-Admin-Secret.
    يتم تجاوز الفحص تلقائياً (Fail-Open) إذا لم يكن ADMIN_SECRET_KEY معرّفاً في بيئة التشغيل.
    """
    admin_secret = os.getenv("ADMIN_SECRET_KEY")
    if admin_secret and admin_secret.strip():
        provided_secret = request.headers.get("X-Admin-Secret")
        if not provided_secret or provided_secret != admin_secret:
            raise HTTPException(
                status_code=403,
                detail="⛔ الوصول مرفوض: الهيدر X-Admin-Secret مفقود أو غير مطابق.",
            )


@app.get("/", tags=["Health"])
def health_check():
    """فحص حالة الخادم."""
    return {
        "status": "online",
        "app": "Yemeni Law Tutor API",
        "version": "2.0.0",
        "architecture": "FastAPI + LangChain + ChromaDB + Google Gemini",
    }


@app.get("/api/stats", response_model=SystemStats, tags=["System"])
def get_system_stats():
    """الحصول على إحصائيات قاعدة البيانات والأداء."""
    return get_system_stats_service()


@app.get("/api/suggestions", response_model=list[SuggestionItem], tags=["Chat"])
def get_suggestions():
    """الحصول على بطاقات الاقتراحات الأربعة للواجهة."""
    return get_default_suggestions()


@app.post("/api/keys", response_model=APIKeyResponse, tags=["System"])
def set_api_key(key_request: APIKeyRequest, request: Request):
    """إضافة وتفعيل مفتاح Gemini API جديد من واجهة المستخدم."""
    verify_admin_secret(request)
    success, message = add_user_api_key(key_request.api_key)
    return APIKeyResponse(success=success, message=message)


@app.post("/api/cache/clear", tags=["System"])
def clear_cache(request: Request):
    """تفريغ التخزين المؤقت في الذاكرة بالكامل."""
    verify_admin_secret(request)
    count = clear_answer_cache()
    return {"success": True, "message": f"تم تفريغ التخزين المؤقت بالكامل ({count} عناصر)."}


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
def chat_sync(request: ChatRequest):
    """إرسال سؤال والحصول على الإجابة الكاملة والمصادر دفعة واحدة (JSON)."""
    answer, sources, rag_stats = generate_chat_answer_sync(request.prompt, request.messages)
    return ChatResponse(answer=answer, sources=sources, rag_stats=rag_stats)


@app.post("/api/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    بث الإجابة حياً كلمة بكلمة باستخدام Server-Sent Events (SSE) بتصميم متعدد المراحل:
    - حدث metadata: يُرسل فوراً بمستندات RAG الجاهزة.
    - حدث token (متكرر): يُبث حياً لحظة وصول كل كلمة بدون ذاكرة مؤقتة.
    - حدث verification_status: يُرسل عند اكتمال البث بحالة التوثيق النهائية.
    """
    return EventSourceResponse(stream_chat_answer_sse(request.prompt, request.messages))


