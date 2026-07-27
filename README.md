# ⚖️ المعلّم الذكي – القانون المدني اليمني
**(Yemeni Civil Law AI Tutor - Dual RAG Architecture: Streamlit + React/FastAPI)**

مشروع ذكاء اصطناعي تفاعلي متقدم مصمم لشرح وتوضيح مواد **القانون المدني اليمني (القرار الجمهوري رقم 14 لسنة 2002م)**. يعتمد النظام على معمارية التوليد المعزز بالاسترجاع (RAG) ليضمن تقديم إجابات قانونية موثوقة ومقاومة للهلوسة 100%، حيث يلتزم المحرك باستخلاص إجاباته حصرياً من النصوص القانونية المعتمدة.

---

## 🌟 الهيكلية المزدوجة للمشروع (Dual Architecture)

يوفر المشروع الآن **خيارين للتشغيل والاستضافة** دون أي تداخل:

### 1️⃣ واجهة Streamlit السحابية (`app.py`)
- **الرابط المباشر:** [https://appbe.streamlit.app](https://appbe.streamlit.app)
- تطبيق واحد يجمع الواجهة ومحرك البحث بلغة Python، مع واجهة عربية متطورة (2026 Digital Diwan Design System)، وبطاقات استشارات قانونية سريعة.

### 2️⃣ تطبيق الويب الحديث (React Vite + FastAPI Backend)
- **خادم الكواليس (`backend/`):** مبني بـ **FastAPI** على المنفذ `8000`، يوفر بثاً حياً للردود كلمة بكلمة (**SSE Streaming**) مع إرسال نصوص المواد القانونية أولاً.
- **واجهة الويب (`frontend/`):** تطبيق **React + TypeScript + Vite** فائق السرعة وبدون أي إعادة تحميل للصفحة (Zero Page Reloads)، يتمتع بتصميم زجاجي مصقول (Glassmorphism) وتأثيرات بصرية حية.

---

## 🛠 المعمارية التقنية والتقنيات المستخدمة

- **LangChain & ChromaDB:** استخدام لغة التعبير (LCEL) لربط دوال الاسترجاع (`create_retrieval_chain`) وقاعدة البيانات المتجهة المحلية (`chroma_db_v2`).
- **Google Gemini API & Local Embeddings:** نموذج `gemini-flash-latest` بـ `Temperature=0.1` لمنع التأليف، ونموذج التضمين المحلي `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- **FastAPI & Pydantic v2:** خادم API عالي الأداء لخدمة واجهات الويب وتطبيقات الهاتف.
- **React 19 + Vite + TypeScript:** واجهة مستخدم احترافية متجاوبة بالكامل مع متصفحات الكمبيوتر والهواتف المحمولة.

---

## 🚀 دليل التشغيل السريع

### أولاً: إعداد البيئة الافتراضية وبناء قاعدة البيانات
```powershell
# تفعيل البيئة (ويندوز)
.\venv\Scripts\activate

# تثبيت متطلبات بايثون
pip install -r requirements.txt

# بناء قاعدة البيانات المتجهة (مرة واحدة فقط)
python utils/ingestion.py
```

---

### ثانياً: تشغيل واجهة Streamlit الحالية
```powershell
streamlit run app.py
```
سيفتح المتصفح تلقائياً على الرابط: `http://localhost:8501`

---

### ثالثاً: تشغيل تطبيق الويب الحديث (FastAPI + React)

#### 1. تشغيل خادم FastAPI (في نافذة طرفية أولى):
```powershell
.\venv\Scripts\uvicorn.exe backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- التوثيق التفاعلي للـ API (Swagger UI): `http://localhost:8000/docs`

#### 2. تشغيل واجهة React (في نافذة طرفية ثانية):
```powershell
cd frontend
npm install
npm run dev
```
- ستفتح الواجهة تلقائياً على الرابط: `http://localhost:5173`

---

## 📜 توثيق المجلدات
- [README_Backend.md](file:///c:/Users/hp/Desktop/yemeni-law-tutor/backend/README.md) – دليل خادم FastAPI
- [README_Frontend.md](file:///c:/Users/hp/Desktop/yemeni-law-tutor/frontend/README.md) – دليل واجهة React
- [walkthrough_web_app.md](file:///C:/Users/hp/.gemini/antigravity-ide/brain/3c4ea3da-57e8-45d2-a63a-58719c021103/walkthrough_web_app.md) – التوثيق المعماري للمشروع

---
*تم تطوير هذه البنية لتكون أداة تعليمية مساعدة قوية للطلاب والباحثين في قطاع الحقوق اليمني، ولا تغني بأي حال عن استشارة الجهات القانونية المتخصصة.*
