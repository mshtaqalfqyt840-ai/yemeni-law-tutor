// ── التخزين المؤقت في الذاكرة (In-Memory Response Cache) ──

const { CACHE_TTL_MS } = require("../config/settings");

class InMemoryCache {
  constructor(ttlMs = CACHE_TTL_MS) {
    this.store = new Map();
    this.ttlMs = ttlMs;
  }

  /** توليد مفتاح للتخزين المؤقت من الطلب */
  _makeKey(prompt, messages = []) {
    const historySnippet = messages
      .slice(-4)
      .map((m) => `${m.role}:${m.content}`)
      .join("|");
    return `${prompt}__${historySnippet}`;
  }

  /** جلب قيمة من الكاش */
  get(prompt, messages) {
    const key = this._makeKey(prompt, messages);
    const entry = this.store.get(key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > this.ttlMs) {
      this.store.delete(key);
      return null;
    }
    return entry.value;
  }

  /** تخزين قيمة في الكاش */
  set(prompt, messages, value) {
    const key = this._makeKey(prompt, messages);
    this.store.set(key, { value, timestamp: Date.now() });
    // تنظيف تلقائي للإدخالات المنتهية الصلاحية
    if (this.store.size > 200) {
      this._cleanup();
    }
  }

  /** تنظيف الإدخالات القديمة */
  _cleanup() {
    const now = Date.now();
    for (const [key, entry] of this.store.entries()) {
      if (now - entry.timestamp > this.ttlMs) {
        this.store.delete(key);
      }
    }
  }

  /** إحصاءات الكاش */
  stats() {
    return {
      size: this.store.size,
      ttl_seconds: this.ttlMs / 1000,
    };
  }

  /** مسح الكاش بالكامل */
  clear() {
    this.store.clear();
  }
}

const responseCache = new InMemoryCache();

module.exports = { responseCache, InMemoryCache };
