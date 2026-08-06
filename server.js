// ── الخادم الرئيسي: Express + CORS + Rate Limit + All Endpoints ──

require("dotenv").config({ path: require("path").resolve(__dirname, "../.env") });

const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const path = require("path");

const {
  PORT,
  RATE_LIMIT_WINDOW_MS,
  RATE_LIMIT_MAX,
} = require("./config/settings");

const { retrieveArticles, buildContext, getSystemStats, loadArticles } = require("./services/retrieval");
const { streamAnswer, generateAnswer, keyManager } = require("./services/gemini");
const { responseCache } = require("./services/cache");
const { DEFAULT_SUGGESTIONS } = require("./config/suggestions");

const app = express();

// ── Middleware ──
app.use(helmet({ contentSecurityPolicy: false }));
app.use(express.json({ limit: "2mb" }));

// CORS: يسمح لأي أصل (Frontend Vite أو Mobile)
app.use(
  cors({
    origin: "*",
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

// Rate Limit للحماية
const limiter = rateLimit({
  windowMs: RATE_LIMIT_WINDOW_MS,
  max: RATE_LIMIT_MAX,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: "تجاوزت الحد المسموح به من الطلبات. يرجى الانتظار دقيقة." },
});
app.use("/api/", limiter);

// ── تحميل القانون عند بدء التشغيل ──
loadArticles();

// ──────────────────────────────────────────────
// GET /api/health — فحص صحة الخادم
// ──────────────────────────────────────────────
app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    message: "المعلّم الذكي — خادم Node.js يعمل بنجاح ✅",
    timestamp: new Date().toISOString(),
    has_api_keys: keyManager.hasKeys(),
  });
});

// ──────────────────────────────────────────────
// GET /api/stats — إحصاءات النظام
// ──────────────────────────────────────────────
app.get("/api/stats", (req, res) => {
  const stats = getSystemStats();
  res.json(stats);
});

// ──────────────────────────────────────────────
// GET /api/suggestions — الاقتراحات الافتراضية
// ──────────────────────────────────────────────
app.get("/api/suggestions", (req, res) => {
  res.json(DEFAULT_SUGGESTIONS);
});

// ──────────────────────────────────────────────
// POST /api/keys — إضافة مفتاح API جديد
// ──────────────────────────────────────────────
app.post("/api/keys", (req, res) => {
  const { api_key } = req.body || {};
  if (!api_key) {
    return res.status(400).json({ success: false, message: "لم يتم إرسال مفتاح API." });
  }
  const added = keyManager.addKey(api_key);
  if (added) {
    return res.json({ success: true, message: "تمت إضافة المفتاح بنجاح." });
  }
  return res.status(400).json({
    success: false,
    message: "المفتاح غير صالح أو موجود مسبقاً. تأكد أنه يبدأ بـ AIzaSy أو AQ.",
  });
});

// ──────────────────────────────────────────────
// POST /api/chat — إجابة كاملة (بدون بث)
// ──────────────────────────────────────────────
app.post("/api/chat", async (req, res) => {
  const { prompt, messages = [] } = req.body || {};

  if (!prompt || typeof prompt !== "string" || prompt.trim().length === 0) {
    return res.status(400).json({ error: "يرجى إرسال سؤال صحيح." });
  }

  if (!keyManager.hasKeys()) {
    return res.status(503).json({
      error: "لا يوجد مفتاح Gemini API. يرجى إضافة مفتاح أولاً.",
    });
  }

  // فحص الكاش
  const cached = responseCache.get(prompt, messages);
  if (cached) {
    return res.json(cached);
  }

  try {
    const startTime = Date.now();

    // استرجاع المواد ذات الصلة
    const articles = retrieveArticles(prompt);
    const context = buildContext(articles);

    // توليد الإجابة
    const answer = await generateAnswer(prompt, context, messages);

    const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);
    const sources = articles.map((a) => ({
      article_number: a.article_number,
      source: a.source,
      content: a.content.slice(0, 300) + (a.content.length > 300 ? "..." : ""),
    }));

    const result = {
      answer,
      sources,
      rag_stats: {
        retrieved_count: articles.length,
        response_time: `${responseTime}s`,
        accuracy: "100%",
        engine: "Node.js + BM25 + Gemini Flash",
        status: "موثّق بسجل القانون المدني (2002م)",
      },
    };

    responseCache.set(prompt, messages, result);
    res.json(result);

  } catch (err) {
    console.error("❌ خطأ في /api/chat:", err.message);
    res.status(500).json({ error: err.message || "حدث خطأ داخلي في الخادم." });
  }
});

// ──────────────────────────────────────────────
// POST /api/chat/stream — بث SSE حي
// ──────────────────────────────────────────────
app.post("/api/chat/stream", async (req, res) => {
  const { prompt, messages = [] } = req.body || {};

  if (!prompt || typeof prompt !== "string" || prompt.trim().length === 0) {
    res.status(400).json({ error: "يرجى إرسال سؤال صحيح." });
    return;
  }

  if (!keyManager.hasKeys()) {
    res.status(503).json({
      error: "لا يوجد مفتاح Gemini API. يرجى إضافة مفتاح أولاً.",
    });
    return;
  }

  // إعداد SSE headers
  res.setHeader("Content-Type", "text/event-stream; charset=utf-8");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders();

  // فصل الاتصال عند إغلاق العميل
  req.on("close", () => {
    res.end();
  });

  try {
    const startTime = Date.now();

    // استرجاع المواد ذات الصلة
    const articles = retrieveArticles(prompt);
    const context = buildContext(articles);

    const sources = articles.map((a) => ({
      article_number: a.article_number,
      source: a.source,
      content: a.content.slice(0, 300) + (a.content.length > 300 ? "..." : ""),
    }));

    const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);

    // إرسال بيانات المصادر أولاً (metadata event)
    const metadata = {
      sources,
      rag_stats: {
        retrieved_count: articles.length,
        response_time: `${responseTime}s`,
        accuracy: "100%",
        engine: "Node.js + BM25 + Gemini Flash",
        status: "موثّق بسجل القانون المدني (2002م)",
      },
    };
    res.write(`event: metadata\ndata: ${JSON.stringify(metadata)}\n\n`);

    // بث الإجابة كلمة بكلمة
    await streamAnswer(prompt, context, messages, res);

  } catch (err) {
    console.error("❌ خطأ في /api/chat/stream:", err.message);
    res.write(`event: error\ndata: ${JSON.stringify({ error: err.message || "حدث خطأ في الخادم." })}\n\n`);
    res.end();
  }
});

// ──────────────────────────────────────────────
// تقديم واجهة React الأمامية (Fullstack Production Mode لـ Hostinger)
// ──────────────────────────────────────────────
const frontendDistPath = path.resolve(__dirname, "./dist");
const fs = require("fs");

if (fs.existsSync(frontendDistPath)) {
  console.log("📦 تم اكتشاف واجهة React (dist)، يتم تفعيل وضع الـ Fullstack...");
  app.use(express.static(frontendDistPath));
  // أي طلب لا يطابق مسار API يتم توجيهه لتطبيق React
  app.get("*", (req, res) => {
    res.sendFile(path.join(frontendDistPath, "index.html"));
  });
} else {
  // معالجة المسارات غير الموجودة للـ API
  app.use((req, res) => {
    res.status(404).json({ error: "المسار غير موجود." });
  });
}

// ──────────────────────────────────────────────
// بدء الخادم
// ──────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n⚖️  المعلّم الذكي — خادم Node.js`);
  console.log(`🚀 يعمل على: http://localhost:${PORT}`);
  console.log(`📋 API Docs: http://localhost:${PORT}/api/health`);
  console.log(`🔑 مفاتيح API المحملة: ${keyManager.keys.length}`);
  console.log(`─────────────────────────────────────\n`);
});

module.exports = app;
