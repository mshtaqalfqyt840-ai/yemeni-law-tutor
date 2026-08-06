// ── خدمة Gemini API: Key Rotation + SSE Streaming ──

const { GoogleGenerativeAI } = require("@google/generative-ai");
const fs = require("fs");
const path = require("path");
const { LLM_MODEL, LLM_TEMPERATURE, CHAT_HISTORY_MAX_MESSAGES } = require("../config/settings");
const { SYSTEM_PROMPT } = require("../config/systemPrompt");

// مدة تعافي المفتاح الفاشل (60 ثانية)
const COOLDOWN_MS = 60 * 1000;

// ------ إدارة مفاتيح API ------
class APIKeyManager {
  constructor() {
    this.keys = [];
    this.failedKeys = new Map(); // key → timestamp
    this.invalidKeys = new Set();
    this.currentIndex = 0;
    this._loadKeys();
  }

  _isValidKey(key) {
    if (!key || typeof key !== "string") return false;
    key = key.trim();
    return /^(AIzaSy[A-Za-z0-9_\-]{27,40}|AQ\.[A-Za-z0-9_\-]{20,80})$/.test(key);
  }

  _maskKey(key) {
    return key && key.length >= 4 ? `[...${key.slice(-4)}]` : "[...]";
  }

  _loadKeys() {
    // 1. من المتغيرات البيئية
    const envKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    if (envKey && this._isValidKey(envKey)) {
      this.keys.push(envKey.trim());
    }

    // 2. من ملف api_keys.json
    const keysFilePath = path.resolve(__dirname, "../config/api_keys.json");
    if (fs.existsSync(keysFilePath)) {
      try {
        const data = JSON.parse(fs.readFileSync(keysFilePath, "utf-8"));
        if (Array.isArray(data.gemini_api_keys)) {
          for (const k of data.gemini_api_keys) {
            if (this._isValidKey(k) && !this.keys.includes(k.trim())) {
              this.keys.push(k.trim());
            }
          }
        }
      } catch (e) {
        console.error("❌ خطأ في قراءة ملف المفاتيح:", e.message);
      }
    }

    if (this.keys.length === 0) {
      console.warn("⚠️ لا يوجد أي مفتاح Gemini API مضبوط!");
    } else {
      console.log(`🔑 تم تحميل ${this.keys.length} مفاتيح Gemini API`);
    }
  }

  _cleanFailedKeys() {
    const now = Date.now();
    for (const [key, ts] of this.failedKeys.entries()) {
      if (now - ts >= COOLDOWN_MS) {
        this.failedKeys.delete(key);
      }
    }
  }

  getActiveKey() {
    this._cleanFailedKeys();
    const usable = this.keys.filter(
      (k) => !this.invalidKeys.has(k) && !this.failedKeys.has(k)
    );
    if (usable.length === 0) {
      throw new Error("⚠️ جميع مفاتيح Gemini API غير متاحة حالياً. يرجى إضافة مفتاح جديد.");
    }
    // دوران بسيط بين المفاتيح
    const key = usable[this.currentIndex % usable.length];
    this.currentIndex = (this.currentIndex + 1) % usable.length;
    console.log(`🔑 استخدام المفتاح: ${this._maskKey(key)}`);
    return key;
  }

  markFailed(key, error) {
    const errMsg = String(error || "");
    const isInvalid =
      /401|403|API_KEY_INVALID|API KEY NOT VALID|UNAUTHENTICATED|PERMISSION_DENIED/i.test(errMsg);

    if (isInvalid) {
      this.invalidKeys.add(key);
      console.error(`⛔ المفتاح ${this._maskKey(key)} غير صالح نهائياً.`);
    } else {
      this.failedKeys.set(key, Date.now());
      console.warn(`⚠️ المفتاح ${this._maskKey(key)} مؤقتاً معطل (429).`);
    }
  }

  addKey(newKey) {
    if (!this._isValidKey(newKey)) return false;
    const trimmed = newKey.trim();
    if (!this.keys.includes(trimmed)) {
      this.keys.push(trimmed);
      // حفظ في ملف JSON
      const keysFilePath = path.resolve(__dirname, "../config/api_keys.json");
      try {
        let data = { gemini_api_keys: [] };
        if (fs.existsSync(keysFilePath)) {
          data = JSON.parse(fs.readFileSync(keysFilePath, "utf-8"));
        }
        if (!data.gemini_api_keys.includes(trimmed)) {
          data.gemini_api_keys.push(trimmed);
          fs.writeFileSync(keysFilePath, JSON.stringify(data, null, 2), "utf-8");
        }
      } catch (e) {
        console.warn("⚠️ تعذر حفظ المفتاح في الملف:", e.message);
      }
      return true;
    }
    return false;
  }

  hasKeys() {
    return this.keys.length > 0;
  }
}

const keyManager = new APIKeyManager();

/**
 * بناء سجل المحادثة بصيغة Gemini
 */
function buildHistory(messages) {
  const limited = messages.slice(-CHAT_HISTORY_MAX_MESSAGES);
  return limited
    .filter((m) => m.role === "user" || m.role === "model")
    .map((m) => ({
      role: m.role === "assistant" ? "model" : m.role,
      parts: [{ text: m.content }],
    }));
}

/**
 * توليد إجابة مع بث SSE
 * @param {string} prompt - سؤال المستخدم
 * @param {string} context - نص المواد القانونية المسترجعة
 * @param {Array} messages - سجل المحادثة
 * @param {import('http').ServerResponse} res - كائن الاستجابة (SSE)
 */
async function streamAnswer(prompt, context, messages, res) {
  let lastError = null;
  const maxRetries = keyManager.keys.length || 1;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    let currentKey;
    try {
      currentKey = keyManager.getActiveKey();
      const genAI = new GoogleGenerativeAI(currentKey);
      const model = genAI.getGenerativeModel({
        model: LLM_MODEL,
        generationConfig: { temperature: LLM_TEMPERATURE },
      });

      const fullPrompt = `${SYSTEM_PROMPT}

السياق المرجعي المتاح من القانون المدني اليمني:
${context}

سؤال الطالب أو المستشار: ${prompt}

إجابة المعلّم الذكي الخبير:`;

      const history = buildHistory(messages.slice(0, -1)); // بدون الرسالة الأخيرة
      const chat = model.startChat({ history });

      const result = await chat.sendMessageStream(fullPrompt);

      for await (const chunk of result.stream) {
        const text = chunk.text();
        if (text) {
          res.write(`event: token\ndata: ${JSON.stringify({ chunk: text })}\n\n`);
        }
      }

      res.write(`event: done\ndata: [DONE]\n\n`);
      return; // نجح — خروج

    } catch (err) {
      lastError = err;
      if (currentKey) {
        keyManager.markFailed(currentKey, err);
      }
      // إذا كانت الأخطاء خطأ غير صالح (4xx)، نتوقف فوراً
      if (/401|403|API_KEY_INVALID/i.test(String(err))) break;
      // محاولة بمفتاح آخر
      console.warn(`🔄 إعادة المحاولة مع مفتاح آخر (المحاولة ${attempt + 1})`);
    }
  }

  throw lastError || new Error("فشل الاتصال بخادم Gemini API");
}

/**
 * توليد إجابة كاملة (sync — بدون بث)
 */
async function generateAnswer(prompt, context, messages) {
  let lastError = null;
  const maxRetries = keyManager.keys.length || 1;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    let currentKey;
    try {
      currentKey = keyManager.getActiveKey();
      const genAI = new GoogleGenerativeAI(currentKey);
      const model = genAI.getGenerativeModel({
        model: LLM_MODEL,
        generationConfig: { temperature: LLM_TEMPERATURE },
      });

      const fullPrompt = `${SYSTEM_PROMPT}

السياق المرجعي المتاح من القانون المدني اليمني:
${context}

سؤال الطالب أو المستشار: ${prompt}

إجابة المعلّم الذكي الخبير:`;

      const history = buildHistory(messages.slice(0, -1));
      const chat = model.startChat({ history });
      const result = await chat.sendMessage(fullPrompt);
      return result.response.text();

    } catch (err) {
      lastError = err;
      if (currentKey) keyManager.markFailed(currentKey, err);
      if (/401|403|API_KEY_INVALID/i.test(String(err))) break;
    }
  }

  throw lastError || new Error("فشل الاتصال بخادم Gemini API");
}

module.exports = { streamAnswer, generateAnswer, keyManager };
