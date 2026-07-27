import os
import json
import itertools
import threading
import re
from typing import List, Optional, Set


class APIKeyManager:
    """
    مدير مفاتيح API مسؤول عن:
    1. Rotation: التناوب بين المفاتيح لتوزيع الأحمال وتفادي الـ Rate Limits.
    2. Fallback: التبديل التلقائي للمفتاح التالي في حال فشل المفتاح الحالي.
    3. Validation: التحقق من صيغة المفتاح الشكلية قبل استخدامه، لمنع مفاتيح
       مشوّهة أو منسوخة من مكان خاطئ من التسبب بانهيار التطبيق لاحقاً بخطأ API_KEY_INVALID.

    يدعم الصيغتين الرسميتين لمفاتيح Google Gemini / AI Studio:
      - الصيغة الكلاسيكية: تبدأ بالبادئة "AIzaSy"
      - الصيغة الحديثة: تبدأ بالبادئة "AQ."
    """

    # صيغة مفاتيح Google Gemini / AI Studio الرسمية:
    # 1. الصيغة الكلاسيكية (AIzaSy)
    # 2. الصيغة الأحدث (AQ.)
    KEY_PATTERN = re.compile(r'^(AIzaSy[A-Za-z0-9_\-]{27,40}|AQ\.[A-Za-z0-9_\-]{20,80})$')

    # قيم Placeholder شائعة يجب تجاهلها دوماً
    _PLACEHOLDER_VALUES = {
        "YOUR_API_KEY_1", "YOUR_API_KEY_2", "YOUR_API_KEY",
        "DEFAULT_DUMMY_KEY", "",
    }

    def __init__(self, config_path: Optional[str] = None):
        self.keys: List[str] = []
        self.failed_keys: Set[str] = set()   # فشل مؤقت (مثال: 429 Rate Limit)
        self.invalid_keys: Set[str] = set()  # فشل دائم مؤكَّد من Google (API_KEY_INVALID)
        self.lock = threading.Lock()
        self._key_iterator = None

        # 0. محاولة القراءة من أسرار Streamlit (st.secrets) عند الاستضافة السحابية
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "GEMINI_API_KEY" in st.secrets:
                    self._add_key_if_valid(st.secrets["GEMINI_API_KEY"], source="st.secrets")
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
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "gemini_api_keys" in data:
                        for k in data["gemini_api_keys"]:
                            self._add_key_if_valid(k, source=config_path)
            except Exception as e:
                print(f"❌ خطأ أثناء قراءة ملف المفاتيح: {e}")

        self._rebuild_iterator()

    @classmethod
    def is_valid_key_format(cls, key: Optional[str]) -> bool:
        """
        تحقق شكلي سريع يستبعد المدخلات المشوّهة أو الفارغة.
        مفاتيح Gemini الرسمية تبدأ بـ 'AIzaSy' أو 'AQ.'.
        """
        if not key or not isinstance(key, str):
            return False
        key = key.strip()
        if key in cls._PLACEHOLDER_VALUES:
            return False
        return bool(cls.KEY_PATTERN.match(key))

    def _add_key_if_valid(self, key: str, source: str = "") -> bool:
        """يضيف المفتاح للقائمة الداخلية فقط إذا اجتاز فحص الصيغة."""
        key = key.strip() if isinstance(key, str) else key
        if not self.is_valid_key_format(key):
            masked = f"{key[:6]}..." if key else "(فارغ)"
            print(
                f"⚠️ تحذير: تم تجاهل مفتاح غير صالح الصيغة من [{source}]: '{masked}' — "
                f"مفاتيح Gemini الرسمية يجب أن تبدأ بـ 'AIzaSy' أو 'AQ.'."
            )
            return False
        if key not in self.keys:
            self.keys.append(key)
        return True

    def _rebuild_iterator(self) -> None:
        self._key_iterator = itertools.cycle(self.keys) if self.keys else None

    def add_key(self, key: str, source: str = "إدخال المستخدم (Streamlit)") -> bool:
        """يضيف مفتاحاً جديداً في وقت التشغيل بعد التحقق من صيغته (AIzaSy أو AQ.)."""
        with self.lock:
            added = self._add_key_if_valid(key, source=source)
            if added:
                self._rebuild_iterator()
        return added

    def has_keys(self) -> bool:
        """هل يوجد أي مفتاح اجتاز فحص الصيغة (بصرف النظر عن حالة الفشل)؟"""
        return len(self.keys) > 0

    def has_usable_key(self) -> bool:
        """هل يوجد مفتاح واحد على الأقل لم يُصنَّف بعد كـ 'غير صالح نهائياً'؟"""
        return any(k not in self.invalid_keys for k in self.keys)

    def get_active_key(self) -> str:
        """يُرجع المفتاح التالي في دورة التناوب (Rotation)."""
        with self.lock:
            if not self.keys:
                raise RuntimeError(
                    "❌ لا يوجد أي مفتاح Gemini API صالح في النظام. الرجاء إدخال "
                    "مفتاحك الخاص (تبدأ بـ 'AIzaSy' أو 'AQ.') من واجهة التطبيق، أو ضبط "
                    "متغير البيئة GEMINI_API_KEY، أو تعديل api_keys.json."
                )

            usable = [k for k in self.keys if k not in self.invalid_keys]
            if not usable:
                raise RuntimeError(
                    "❌ جميع المفاتيح المسجَّلة غير صالحة (API_KEY_INVALID). "
                    "الرجاء إدخال مفتاح Gemini API صحيح وفعّال من Google AI Studio."
                )

            if all(k in self.failed_keys for k in usable):
                print("⏳ تنبيه: كل المفاتيح فشلت مؤقتاً (Rate Limit). سيتم تصفير القائمة والمحاولة من جديد.")
                self.failed_keys.clear()

            for _ in range(len(self.keys)):
                key = next(self._key_iterator)
                if key in self.invalid_keys:
                    continue
                if key not in self.failed_keys:
                    return key

            return usable[0]

    def mark_key_as_failed(self, key: str, error: Exception = None) -> bool:
        """يسجّل فشل المفتاح ويحلل نوع الخطأ (404, 429, API_KEY_INVALID)."""
        err_msg = str(error) if error else "Unknown"
        print(f"⚠️ تسجيل خطأ للمفتاح '{key[:10]}...': {err_msg}")

        if "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg or "400" in err_msg:
            with self.lock:
                self.invalid_keys.add(key)
            print(f"⛔ المفتاح '{key[:10]}...' غير صالح لدى Google، وتم استبعاده نهائياً من التدوير.")
            if not self.has_usable_key():
                raise ValueError(
                    f"جميع المفاتيح غير صالحة لدى Google (API_KEY_INVALID). "
                    f"يجب إدخال مفتاح Gemini API صحيح وفعّال (يبدأ بـ AIzaSy أو AQ.). تفاصيل الخطأ: {err_msg}"
                )
            return True

        if "404" in err_msg:
            raise ValueError(f"النموذج غير موجود (404). تحقق من اسم النموذج بدلاً من تدوير المفتاح. تفاصيل: {err_msg}")

        if "429" in err_msg:
            if "limit: 0" in err_msg.lower() or ("quota" in err_msg.lower() and " 0 " in err_msg):
                print("⚠️ تنبيه: حصة الاستخدام (Quota) صفر أو النموذج غير مفعّل لهذا المشروع.")
            else:
                print("⚠️ تنبيه Fallback: استنفاد الحصة أو Rate Limit. سيتم التدوير.")

        with self.lock:
            if key not in self.failed_keys:
                print(f"⚠️ تم استبعاد المفتاح '{key[:10]}...' مؤقتاً.")
                self.failed_keys.add(key)

        return True
