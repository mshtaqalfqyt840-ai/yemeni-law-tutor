# ── إعدادات مركزية للمشروع (Single Source of Truth) ──
# أي تعديل هنا ينعكس تلقائياً على app.py و ingestion.py

# نموذج التضمين المحلي — مجاني، بلا حصة يومية، يدعم العربية
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# إعدادات نموذج المحادثة
LLM_MODEL = "gemini-1.5-flash"  # النموذج المعتمد والفعال رسمياً في Gemini API
LLM_TEMPERATURE = 0.1

# إعدادات البحث
RETRIEVER_K = 5  # عدد المواد المسترجعة في كل بحث

# حد تاريخ المحادثة — آخر N رسالة فقط لتجنب تجاوز حد الـ context window
CHAT_HISTORY_MAX_MESSAGES = 10  # 5 أزواج سؤال/جواب
