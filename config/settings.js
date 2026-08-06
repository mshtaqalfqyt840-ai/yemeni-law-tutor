// ── الإعدادات المركزية للمشروع (Single Source of Truth) ──

module.exports = {
  // نموذج المحادثة
  LLM_MODEL: "gemini-3.5-flash",
  LLM_TEMPERATURE: 0.1,

  // إعدادات البحث
  RETRIEVER_K: 5, // عدد المواد المسترجعة في كل بحث

  // حد تاريخ المحادثة
  CHAT_HISTORY_MAX_MESSAGES: 10, // آخر 10 رسائل (5 أزواج)

  // مدة التخزين المؤقت (ملي ثانية)
  CACHE_TTL_MS: 5 * 60 * 1000, // 5 دقائق

  // حد معدل الطلبات
  RATE_LIMIT_WINDOW_MS: 60 * 1000, // دقيقة واحدة
  RATE_LIMIT_MAX: 300, // 300 طلب في الدقيقة

  // منفذ الخادم
  PORT: process.env.PORT || 8000,

  // مسار ملف القانون
  LAW_FILE_PATH: "../data/yemeni_civil_law_official.txt",

  // مسار ملف مفاتيح API
  API_KEYS_FILE_PATH: "./api_keys.json",
};
