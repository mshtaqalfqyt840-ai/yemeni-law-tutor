import os
import json
import itertools
import threading
import time
import re
from typing import List, Optional, Set, Dict

# مدة تعافي المفتاح الفاشل بسبب 429 (بالثواني)
COOLDOWN_SECONDS: float = 60.0



class APIKeyManager:
    """
    مدير مفاتيح API مسؤول عن:
    1. Rotation: التناوب بين المفاتيح لتوزيع الأحمال وتفادي الـ Rate Limits.
    2. Fallback: التبديل التلقائي للمفتاح التالي في حال فشل المفتاح الحالي (429 / 401 / 403 / Quota Exceeded).
    3. State Tracking: الاحتفاظ بحالة كل مفتاح (نشط / منتهي الحصة / غير صالح) في الذاكرة لتجنب إعادة استخدامه بنفس الجلسة.
    4. Privacy Logging: تسجيل المفتاح المستخدَم فعلياً بإظهار آخر 4 أحرف فقط لضمان الخصوصية.

    يدعم الصيغتين الرسميتين لمفاتيح Google Gemini / AI Studio:
      - الصيغة الكلاسيكية: تبدأ بالبادئة "AIzaSy"
      - الصيغة الحديثة: تبدأ بالبادئة "AQ."
    """

    # صيغة مفاتيح Google Gemini / AI Studio الرسمية:
    # 1. الصيغة الكلاسيكية (AIzaSy)
    # 2. الصيغة الأحدث (AQ.)
    KEY_PATTERN = re.compile(
        r"^(AIzaSy[A-Za-z0-9_\-]{27,40}|AQ\.[A-Za-z0-9_\-]{20,80})$"
    )

    # قيم Placeholder شائعة يجب تجاهلها دوماً
    _PLACEHOLDER_VALUES = {
        "YOUR_API_KEY_1",
        "YOUR_API_KEY_2",
        "YOUR_API_KEY",
        "YOUR_GEMINI_API_KEY_HERE",
        "DEFAULT_DUMMY_KEY",
        "",
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.keys: List[str] = []
        self.failed_keys: Dict[str, float] = {}  # مفاتيح فشلت مؤقتاً {key: timestamp}
        self.invalid_keys: Set[str] = set()  # مفاتيح غير صالحة نهائياً (401 / 403 / API_KEY_INVALID)
        self.key_usage: Dict[str, List[float]] = {}  # تتبع وقت استخدام المفتاح {key: [timestamps]}
        self.lock = threading.Lock()
        self._key_iterator = None
        self.proactive_rpm_limit = 12  # الحد الأقصى الاستباقي لعدد الطلبات في الدقيقة للمفتاح الواحد
        self.rolling_window_seconds = 60.0

        # 0. محاولة القراءة من أسرار Streamlit (st.secrets) عند الاستضافة السحابية
        try:
            import streamlit as st

            if hasattr(st, "secrets"):
                if "GEMINI_API_KEY" in st.secrets:
                    self._add_key_if_valid(
                        st.secrets["GEMINI_API_KEY"], source="st.secrets"
                    )
                if "gemini_api_keys" in st.secrets:
                    for k in st.secrets["gemini_api_keys"]:
                        self._add_key_if_valid(k, source="st.secrets")
        except Exception:
            pass

        # 1. محاولة القراءة من المتغيرات البيئية (.env) كخيار أمان أولي
        env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if env_key:
            self._add_key_if_valid(env_key, source="متغير بيئي (Environment Variable)")

        # 2. القراءة من ملف الإعدادات json
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "gemini_api_keys" in data:
                        for k in data["gemini_api_keys"]:
                            self._add_key_if_valid(k, source=config_path)
            except Exception as e:
                print(f"❌ خطأ أثناء قراءة ملف المفاتيح: {e}")

        self._rebuild_iterator()

    @classmethod
    def is_valid_key_format(cls, key: Optional[str]) -> bool:
        """تحقق شكلي سريع يستبعد المدخلات المشوّهة أو الفارغة."""
        if not key or not isinstance(key, str):
            return False
        key = key.strip()
        if key in cls._PLACEHOLDER_VALUES:
            return False
        return bool(cls.KEY_PATTERN.match(key))

    @staticmethod
    def _mask_key(key: str) -> str:
        """إخفاء المفتاح وإظهار آخر 4 أحرف فقط لحماية الخصوصية."""
        if not key or not isinstance(key, str):
            return "(فارغ)"
        clean_key = key.strip()
        return f"[...{clean_key[-4:]}]" if len(clean_key) >= 4 else "[...]"

    def _add_key_if_valid(self, key: str, source: str = "") -> bool:
        """يضيف المفتاح للقائمة الداخلية فقط إذا اجتاز فحص الصيغة."""
        key = key.strip() if isinstance(key, str) else key
        if not self.is_valid_key_format(key):
            if key and key not in self._PLACEHOLDER_VALUES:
                print(
                    f"⚠️ تحذير: تم تجاهل مفتاح غير صالح الصيغة من [{source}]: '{self._mask_key(key)}' — "
                    f"مفاتيح Gemini الرسمية يجب أن تبدأ بـ 'AIzaSy' أو 'AQ.'."
                )
            return False
        if key not in self.keys:
            self.keys.append(key)
        return True

    def _rebuild_iterator(self) -> None:
        self._key_iterator = itertools.cycle(self.keys) if self.keys else None

    def add_key(self, key: str, source: str = "إدخال المستخدم") -> bool:
        """يضيف مفتاحاً جديداً في وقت التشغيل بعد التحقق من صيغته (AIzaSy أو AQ.)."""
        with self.lock:
            added = self._add_key_if_valid(key, source=source)
            if added:
                self._rebuild_iterator()
                if self.config_path and os.path.exists(self.config_path):
                    try:
                        with open(self.config_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        keys_list = data.get("gemini_api_keys", [])
                        clean_key = key.strip()
                        if clean_key not in keys_list:
                            keys_list.append(clean_key)
                            data["gemini_api_keys"] = keys_list
                            with open(self.config_path, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        print(f"⚠️ تعذر حفظ المفتاح في {self.config_path}: {e}")
        return added

    def has_keys(self) -> bool:
        """هل يوجد أي مفتاح اجتاز فحص الصيغة (بصرف النظر عن حالة الفشل)؟"""
        return len(self.keys) > 0

    def has_usable_key(self) -> bool:
        """هل يوجد مفتاح واحد على الأقل لم يُصنَّف كـ 'غير صالح' أو انقضت فترة تعافيه؟"""
        now = time.time()
        with self.lock:
            expired = [
                k for k, ts in self.failed_keys.items() if now - ts >= COOLDOWN_SECONDS
            ]
            for k in expired:
                del self.failed_keys[k]
            return any(
                k not in self.invalid_keys and k not in self.failed_keys
                for k in self.keys
            )

    def get_active_key(self) -> str:
        """
        يُرجع المفتاح التالي الفعّال في دورة التناوب (Rotation).
        تطبيق التدوير الاستباقي (Proactive Rotation) لمنع تجاوز حد RPM قبل حدوث خطأ 429.
        """
        with self.lock:
            if not self.keys:
                raise RuntimeError("⚠️ لا يوجد أي مفتاح API مضبوط في النظام.")

            now = time.time()
            # 1. تصفية المفاتيح الفاشلة مؤقتاً عند انقضاء مدة التعافي
            expired = [
                k for k, ts in self.failed_keys.items() if now - ts >= COOLDOWN_SECONDS
            ]
            for k in expired:
                del self.failed_keys[k]

            # 2. تنظيف طوابع الأوقات المنتهية للمفاتيح (النافذة الزمنية المتحركة 60 ثانية)
            for k in list(self.key_usage.keys()):
                self.key_usage[k] = [
                    ts for ts in self.key_usage[k] if now - ts < self.rolling_window_seconds
                ]

            usable = [
                k
                for k in self.keys
                if k not in self.invalid_keys and k not in self.failed_keys
            ]
            if not usable:
                raise RuntimeError("⚠️ جميع مفاتيح API غير متاحة حالياً")

            # 3. محاولة اختيار مفتاح لم يتجاوز السقف الاستباقي RPM (مثلاً 12 طلب/دقيقة)
            selected_key = None
            for _ in range(len(self.keys)):
                candidate = next(self._key_iterator)
                if candidate in self.invalid_keys or candidate in self.failed_keys:
                    continue
                req_count = len(self.key_usage.get(candidate, []))
                if req_count < self.proactive_rpm_limit:
                    selected_key = candidate
                    break

            # 4. إذا كانت جميع المفاتيح القابلة للاستخدام قد بلغت السقف الاستباقي، اختر الأقل استهلاكاً
            if not selected_key:
                selected_key = min(usable, key=lambda k: len(self.key_usage.get(k, [])))

            # تسجيل الطابع الزمني للطلب للمفتاح المختار
            self.key_usage.setdefault(selected_key, []).append(now)
            print(f"🔑 [التدوير الاستباقي] تم استخدام المفتاح: {self._mask_key(selected_key)} (طلبات النافذة الحالية: {len(self.key_usage[selected_key])})")
            return selected_key

    def mark_key_as_failed(self, key: str, error: Exception = None) -> bool:
        """
        يسجّل فشل المفتاح ويحدد حالته (منتهي الحصة / غير صالح).
        يستبعده مؤقتاً لمدة COOLDOWN_SECONDS إذا كان الخطأ 429.
        """
        if not key or not isinstance(key, str):
            return False
        err_msg = str(error) if error else "Unknown"
        masked = self._mask_key(key)

        is_invalid = any(
            code in err_msg.upper()
            for code in [
                "API_KEY_INVALID",
                "API KEY NOT VALID",
                "401",
                "403",
                "UNAUTHENTICATED",
                "PERMISSION_DENIED",
                "INVALID_ARGUMENT",
            ]
        )

        if is_invalid:
            with self.lock:
                self.invalid_keys.add(key)
            print(
                f"⛔ المفتاح {masked} غير صالح لدى Google (401/403/API_KEY_INVALID)، وتم استبعاده نهائياً من التدوير."
            )
        else:
            with self.lock:
                self.failed_keys[key] = time.time()
            print(
                f"⚠️ المفتاح {masked} استنفد الحصة (429)، وتم استبعاده مؤقتاً لمدة {int(COOLDOWN_SECONDS)} ثانية."
            )

        if not self.has_usable_key():
            print("⚠️ جميع مفاتيح API غير متاحة حالياً")
            raise RuntimeError("⚠️ جميع مفاتيح API غير متاحة حالياً")

        return True

