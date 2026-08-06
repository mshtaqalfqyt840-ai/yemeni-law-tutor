# ⚖️ المعلّم الذكي – الديوان الرقمي للقانون المدني اليمني
**(Yemeni Civil Law AI Tutor - Unified Flat Fullstack React + Node.js App)**

مشروع ذكاء اصطناعي تفاعلي متقدم مصمم لشرح وتوضيح مواد **القانون المدني اليمني (القرار الجمهوري رقم 14 لسنة 2002م)**.  
يعتمد النظام على معمارية **التوليد المعزز بالاسترجاع (RAG: BM25 + Google Gemini Flash)** مع واجهة أمامية فاخرة بـ **React + Vite** وخادم خلفي سريع بـ **Node.js / Express** مدمجين في **هيكل مسطح موحّد (Single Directory App)** جاهز للرفع المباشر على **GitHub** والاستضافة الفورية على **Hostinger**.

---

## 🗺️ خريطة المشروع الموحّد (Flat Directory Structure)

تم دمج كافة الملفات في جذر المشروع ليعمل كتطبيق Fullstack واحد بدون أي تقسيم؛ حيث يقوم ملف `package.json` واحد بإدارة اعتمادات الخادم والواجهة الأمامية معاً:

```
yemeni-law-tutor/
├── package.json               # ملف الاعتمادات والسكريبتات الموحد (للتثبيت والبناء والتشغيل على Hostinger)
├── server.js                  # خادم Node.js / Express (يخدم مسارات الـ API + يخدم واجهة React)
├── index.html                 # صفحة واجهة React الرئيسية
├── vite.config.ts             # إعدادات بناء الواجهة الأمامية Vite
├── tsconfig.*.json            # إعدادات TypeScript
├── run_web.bat                # سكريبت التشغيل المحلي المباشر لبيئة ويندوز
│
├── 📁 src/                    # كود واجهة المستخدم (React 19 + TypeScript)
│   ├── App.tsx                # المكون الرئيسي وإدارة حالة المحادثة والبث الحي SSE
│   ├── index.css              # نظام التصميم الفاخر (Digital Diwan Design System)
│   └── components/            # مكونات الواجهة (TopBar, Sidebar, HeroBanner, ChatInput, ...)
│
├── 📁 config/                 # إعدادات خادم Node.js
│   ├── settings.js            # إعدادات النماذج والمهل الزمنية
│   ├── systemPrompt.js        # التوجيه الأساسي (System Prompt) للمعلّم الذكي ومبادئ عدم الهلوسة
│   ├── suggestions.js         # الاقتراحات القانونية الافتراضية للواجهة
│   └── api_keys.json          # قائمة مفاتيح Google Gemini API مع التناوب التلقائي
│
├── 📁 services/               # الخدمات البرمجية للخادم
│   ├── gemini.js              # التفاعل مع Google Gemini API والدوران الذكي للمفاتيح (Rotation + SSE)
│   ├── retrieval.js           # محرك البحث BM25 وتقسيم وتحميل 1430 مادة قانونية
│   └── cache.js               # التخزين المؤقت في الذاكرة (In-Memory Cache) لتسريع الطلبات
│
└── 📁 data/                   # النصوص القانونية المعتمدة
    └── yemeni_civil_law_official.txt  # النص الرسمي الكامل للقانون المدني اليمني (1430 مادة)
```

---

## 🌍 دليل الرفع على GitHub وربطه باستضافة Hostinger

المشروع مصمم ليعمل مباشرةً عند اختيار استضافة **Node.js Application** من **Hostinger**:

### الخطوة 1: الرفع إلى GitHub
افتح موجه الأوامر في مجلد المشروع وقم برفع الكود إلى مستودعك:
```bash
git add .
git commit -m "feat: flat single-directory fullstack React and Node.js app for Hostinger"
git push origin main
```

---

### الخطوة 2: ربط المستودع في Hostinger (Node.js App)
1. ادخل إلى لوحة تحكم **Hostinger** واختر استضافة تطبيقات **Node.js** (أو قائمة التطبيقات في الـ VPS).
2. اضغط على **Create App** ثم **Connect GitHub Repository** واختر مستودع المشروع.
3. استخدم الإعدادات الافتراضية التالية (ستعمل مباشرة دون أي تعديل):
   - **Root Directory:** `/` *(اتركه فارغاً أو الجذر)*
   - **Build Command:** `npm run build` *(يقوم تلقائياً ببناء واجهة React في مجلد `dist`)*
   - **Start Command:** `npm start` *(يشغل `node server.js` الذي يخدم الواجهة والـ API معاً)*
   - **Node.js Version:** `18.x` أو أعلى.

---

### الخطوة 3: إعداد مفاتيح الذكاء الاصطناعي (Environment Variables)
لحماية مفاتيح API الخاصة بك من التسرب في مستودعات الكود:
1. في لوحة تحكم تطبيقك على Hostinger، انتقل إلى قسم **Environment Variables (متغيرات البيئة)**.
2. أضف المتغير التالي:
   - **KEY:** `GEMINI_API_KEY`
   - **VALUE:** `أدخل مفتاح Gemini API الخاص بك هنا`
3. احفظ الإعدادات واضغط على **Deploy / Re-deploy**.

---

## 🚀 دليل التشغيل المحلي (Local Development)

### الطريقة الأولى: التشغيل السريع بضغطة زر
قم بتشغيل السكريبت المرفق:
```powershell
.\run_web.bat
```

### الطريقة الثانية: التشغيل الإنتاجي الموحّد (Fullstack Mode)
هذا هو نفس الوضع الذي يعمل به الموقع على Hostinger:
```powershell
# 1. تثبيت كافة الاعتمادات
npm install

# 2. بناء واجهة React وحفظها في مجلد dist
npm run build

# 3. تشغيل الخادم الموحد
npm start
```
- **رابط التطبيق الشامل (الواجهة + الـ API):** [http://localhost:8000](http://localhost:8000)
- **فحص صحة الخادم:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
