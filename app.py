import os
import re
import streamlit as st
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

try:
    from langchain.chains import create_history_aware_retriever
    from langchain.chains.combine_documents import create_stuff_documents_chain
except ImportError:
    from langchain_classic.chains import create_history_aware_retriever
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document

from config.settings import (
    EMBEDDING_MODEL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    RETRIEVER_K,
    CHAT_HISTORY_MAX_MESSAGES
)
from config.system_prompts import get_tutor_prompt
from utils.api_manager import APIKeyManager
from utils.legal_splitter import normalize_digits

# ── 1. إعدادات الصفحة ونظام تصميم "الديوان الرقمي" ──
st.set_page_config(
    page_title="المعلّم الذكي – القانون المدني اليمني",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# تحميل ملف CSS الخارجي الموحد
css_path = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── 2. تهيئة الجلسة والحالة ──
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_manager" not in st.session_state:
    config_path = os.path.join(os.path.dirname(__file__), "config", "api_keys.json")
    st.session_state.api_manager = APIKeyManager(config_path)

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

@st.cache_resource
def load_vectorstore():
    """تحميل قاعدة البيانات المتجهة بنموذج التضمين المحلي."""
    persist_dir = os.path.join(os.path.dirname(__file__), "chroma_db_v2")
    if not os.path.exists(persist_dir):
        return None
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(persist_directory=persist_dir, embedding_function=embeddings)

vectorstore = load_vectorstore()

def extract_direct_article_number(user_input: str) -> str:
    """استخراج رقم المادة مباشرة من السؤال إذا طُلبت صراحةً."""
    cleaned = user_input.strip()
    norm_text = normalize_digits(cleaned)
    match = re.search(r'^(?:مادة|المادة)?\s*(?:رقم\s*)?\(?\s*(?:رقم\s*)?(\d+)\s*\)?\s*[؟\?\.\!]*$', norm_text)
    if match:
        return match.group(1)
    return None

def render_source_cards(sources):
    """دالة توقيعية لعرض المصادر القانونية بنمط 'السجل الرسمّي' (The Register Card)."""
    if not sources:
        return
    with st.expander("📜 السجل القانوني والمصادر الرسمية المعتمدة"):
        for idx, doc in enumerate(sources, 1):
            meta = doc.metadata if isinstance(doc, Document) or hasattr(doc, 'metadata') else (doc.get('metadata', {}) if isinstance(doc, dict) else {})
            content = doc.page_content if isinstance(doc, Document) or hasattr(doc, 'page_content') else (doc.get('page_content', '') if isinstance(doc, dict) else str(doc))
            art_num = meta.get("article_number", "؟")
            book = meta.get("book", "")
            
            st.markdown(f"""
            <div class="diwan-card">
                <div class="diwan-card-header">
                    <div class="diwan-card-meta">
                        <span class="article-badge">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-0.5-.05"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15Z"/><path d="M6 12h8"/><path d="M6 16h8"/><path d="M6 8h4"/></svg>
                            مادة ({art_num})
                        </span>
                        {f'<span class="book-badge">• {book}</span>' if book else ''}
                    </div>
                    <span class="diwan-source-label">سجل النص القانوني الأصلي — المرجع {idx}</span>
                </div>
                <div class="diwan-card-quote">
                    <div class="quote-accent-line"></div>
                    <p class="quote-text">{content}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── 3. البيانات الأساسية ──
total_docs = vectorstore._collection.count() if vectorstore else 0


# ── 4. الهيدر الرئيسي (Hero Header) ──
st.markdown(f"""
<div class="diwan-hero-container">
    <svg class="diwan-hero-bg-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
        <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
        <path d="M7 21h10"/>
        <path d="M12 3v18"/>
        <path d="M3 7h18"/>
    </svg>
    <div class="diwan-eyebrow">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        <span>الديوان الرقمي • المرجع الذكي الأول للقانون المدني</span>
    </div>
    <h1 class="diwan-hero-title">المعلّم الذكي <span>للقانون المدني اليمني</span></h1>
    <div class="diwan-hero-desc">
        منصة تفاعلية موثّقة لتقديم الشروح والاستشارات الأكاديمية المستندة 
        <strong>حصرياً</strong> على النص الرسمي للقرار الجمهوري بالقانون رقم (14) لسنة 2002م، دون هلوسة أو اجتهاد خارجي.
    </div>
    <div class="diwan-trust-badges">
        <div class="trust-badge-item">
            <div class="trust-icon-box">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
            </div>
            <span>إسناد نصي حرفي موثّق 100%</span>
        </div>
        <div class="trust-badge-item">
            <div class="trust-icon-box">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
            </div>
            <span>{total_docs:,} مادة قانونية مفهرسة</span>
        </div>
        <div class="trust-badge-item">
            <div class="trust-icon-box">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </div>
            <span>بحث دلالي فوري فائق الدقة</span>
        </div>
        <div class="trust-badge-item">
            <div class="trust-icon-box">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20"/><path d="m17 5-5-3-5 3"/><path d="m17 19-5 3-5-3"/><path d="M2 12h20"/></svg>
            </div>
            <span>خالٍ من الهلوسة والاجتهاد</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# تنبيه قانوني رسمي
st.markdown("""
<div class="diwan-warning-banner">
    <div class="warning-icon-wrapper">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
    </div>
    <div>
        <strong>تنبيه قانوني هام:</strong> الإجابات المقدمة هي لأغراض الدراسة والتعليم والأبحاث الأكاديمية فقط، ولا تُعد استشارة قانونية رسمية ملزمة. يُرجى مراجعة محامٍ مرخص أو قاضٍ متخصص عند معالجة القضايا الفعلية.
    </div>
</div>
""", unsafe_allow_html=True)

# ── 4.5. شريط أدوات التحكم والعمليات السريعة ──
ctrl_col1, ctrl_col2 = st.columns([1, 1])
with ctrl_col1:
    if st.button("🗑️ مسح المحادثة والبدء من جديد", use_container_width=True, key="reset_chat_main"):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

with ctrl_col2:
    has_key = st.session_state.api_manager.has_usable_key()
    with st.expander("🔑 إدارة مفتاح Gemini API", expanded=not has_key):
        main_api_key = st.text_input(
            "ألصق مفتاح Gemini API هنا لتفعيل المحادثة:",
            type="password",
            placeholder="AIzaSy... أو AQ...",
            key="main_page_api_key"
        )
        if main_api_key:
            if st.session_state.api_manager.add_key(main_api_key, source="الواجهة الرئيسية"):
                st.success("✅ تم تفعيل المفتاح بنجاح!")
                st.rerun()
            else:
                st.error("⚠️ صيغة المفتاح غير صالحة. يجب أن يبدأ بـ AIzaSy أو AQ.")
        elif not has_key:
            st.caption("💡 [احصل على مفتاح مجاني من Google AI Studio](https://aistudio.google.com/app/apikey)")


# ── 5. بطاقات الاقتراحات (تظهر فقط عند بداية المحادثة) ──
if len(st.session_state.messages) == 0:
    st.markdown("""
    <div class="suggestions-header-wrapper">
        <div class="suggestions-section-title">
            <div class="title-icon-pulse">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
            </div>
            <div>
                <span>نماذج أسئلة واستشارات قانونية شائعة للبدء</span>
                <p class="suggestions-section-subtitle">اختر أياً من الاستشارات والمواد القانونية الفورية أدناه للحصول على إجابة موثقة، أو اكتب سؤالك الخاص في شريط المحادثة</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    suggestions = [
        {
            "category": "باب العقود والالتزامات",
            "title": "أركان العقد وشروط صحته",
            "subtext": "استعراض الأهلية، التراضي، ومحل العقد وفقاً لأحكام القانون المدني",
            "prompt": "ما هي أركان العقد وشروط صحته وفقاً للقانون المدني اليمني؟",
            "btn_label": "استعراض الأركان والشروط ⚡",
            "svg_icon": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>""",
            "accent_class": "sug-accent-gold"
        },
        {
            "category": "تأصيل قانوني مباشر",
            "title": "المادة (138) بالتفصيل",
            "subtext": "النص الحرفي والشرح التطبيقي لأحكام المادة مع الأمثلة",
            "prompt": "138",
            "btn_label": "قراءة نص المادة (138) 📜",
            "svg_icon": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-0.5-.05"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15Z"/><path d="M6 12h8"/><path d="M6 16h8"/><path d="M6 8h4"/></svg>""",
            "accent_class": "sug-accent-emerald"
        },
        {
            "category": "النظرية العامة للحق",
            "title": "عيوب الإرادة وأثرها القانوني",
            "subtext": "الغلط، التدليس، الإكراه، والاستغلال وفقاً لأحكام القانون المدني",
            "prompt": "ما هي عيوب الإرادة في القانون المدني اليمني وكيف أثرها؟",
            "btn_label": "تحليل عيوب الإرادة ⚖️",
            "svg_icon": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h18"/></svg>""",
            "accent_class": "sug-accent-blue"
        },
        {
            "category": "الضمانات وحقوق الدائن",
            "title": "أحكام الكفالة والضمان",
            "subtext": "التزامات الكفيل وحقوق الدائن والمدين في الشريعة والقانون",
            "prompt": "ما هي أحكام الكفالة والضمان ومسؤولية الكفيل في القانون اليمني؟",
            "btn_label": "استعراض أحكام الكفالة 🛡️",
            "svg_icon": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>""",
            "accent_class": "sug-accent-purple"
        }
    ]

    col1, col2 = st.columns(2)
    cols = [col1, col2, col1, col2]
    
    for i, sug in enumerate(suggestions):
        with cols[i]:
            st.markdown(f"""
            <div class="sug-card-modern {sug['accent_class']}">
                <div class="sug-card-header">
                    <div class="sug-card-icon-wrapper">
                        {sug['svg_icon']}
                    </div>
                    <span class="sug-category-badge">{sug['category']}</span>
                </div>
                <h3 class="sug-card-title">{sug['title']}</h3>
                <p class="sug-card-desc">{sug['subtext']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(sug['btn_label'], use_container_width=True, key=f"sug_{i}"):
                st.session_state.pending_prompt = sug['prompt']
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

# ── 6. عرض سجل المحادثة ──
for message in st.session_state.messages:
    avatar_icon = "👤" if message["role"] == "user" else "⚖️"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])
        if message.get("sources"):
            render_source_cards(message["sources"])

# ── 7. حقل الإدخال المعزز ──
user_question = st.chat_input("💬 اسأل المعلم الذكي عن أي مسألة قانونية، أو اكتب رقم المادة مباشرة (مثال: 138 أو ما هي شروط البيع؟)...")

if st.session_state.pending_prompt and not user_question:
    user_question = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_question)

    if not vectorstore:
        st.error("لا يمكن معالجة السؤال. الرجاء بناء قاعدة البيانات المتجهة أولاً.")
        st.stop()

    if not st.session_state.api_manager.has_usable_key():
        st.error("❌ لا يوجد مفتاح Gemini API صالح وفعّال لتشغيل المحرك الذكي.")
        with st.expander("🔑 اضغط هنا لإدخال مفتاح Gemini API الخاص بك وتفعيل المحادثة فوراً", expanded=True):
            st.markdown("يمكنك الحصول على مفتاح مجاني وسريع في أقل من دقيقة عبر **[Google AI Studio](https://aistudio.google.com/app/apikey)**.")
            inline_key = st.text_input("ألصق مفتاح Gemini API هنا:", type="password", placeholder="AIzaSy... أو AQ...", key="inline_gemini_key")
            if inline_key:
                if st.session_state.api_manager.add_key(inline_key, source="واجهة المحادثة"):
                    st.success("✅ تم حفظ وتفعيل المفتاح بنجاح! أعد إرسال سؤالك الآن.")
                    st.rerun()
                else:
                    st.error("⚠️ صيغة المفتاح غير صالحة. يجب أن يبدأ بـ AIzaSy أو AQ.")
        st.stop()

    with st.chat_message("assistant", avatar="⚖️"):
        direct_art_num = extract_direct_article_number(user_question)
        direct_docs = []
        if direct_art_num:
            try:
                res_get = vectorstore.get(where={"article_number": direct_art_num})
                if res_get and res_get.get("documents"):
                    for doc_text, meta in zip(res_get["documents"], res_get["metadatas"]):
                        direct_docs.append(Document(page_content=doc_text, metadata=meta))
            except Exception:
                direct_docs = []

        chat_history = []
        previous_msgs = st.session_state.messages[:-1]
        if len(previous_msgs) > CHAT_HISTORY_MAX_MESSAGES:
            previous_msgs = previous_msgs[-CHAT_HISTORY_MAX_MESSAGES:]

        for msg in previous_msgs:
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_history.append(AIMessage(content=msg["content"]))

        sources = []
        final_prompt_input = user_question
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": RETRIEVER_K})
        usable_attempts = len([k for k in st.session_state.api_manager.keys if k not in st.session_state.api_manager.invalid_keys])

        # 1. استرجاع المستندات ذات الصلة (بصورة فورية وسريعة)
        with st.spinner("📜 جاري البحث في سجلات نصوص القانون المدني اليمني..."):
            if direct_docs:
                sources = direct_docs
                final_prompt_input = f"قدّم النص الحرفي للمادة ({direct_art_num}) وشرحاً ميسراً وأمثلة تطبيقية عليها وفقاً للنص المرفق."
            elif not chat_history:
                # محادثة جديدة أو سؤال مستقل: استرجاع مباشر وسريع دون طلب LLM إضافي
                sources = retriever.invoke(user_question)
            else:
                # توجد محادثة سابقة: إعادة صياغة السؤال بناءً على السياق السابق
                contextualize_q_system_prompt = (
                    "بالنظر إلى سجل المحادثة السابق والسؤال الأخير للمستخدم والذي قد يشير إلى سياق سابق (مثل 'عليها' أو 'المادة المذكورة')، "
                    "أعد صياغة السؤال ليكون سؤالاً مستقلاً يتضمن المادة أو الموضوع المقصود بالكامل ليتمكن محرك البحث من العثور عليه. "
                    "لا تجب على السؤال، فقط أعد صياغته إذا لزم الأمر، وإلا أعده كما هو."
                )
                contextualize_q_prompt = ChatPromptTemplate.from_messages([
                    ("system", contextualize_q_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ])
                active_key = None
                for attempt in range(max(1, usable_attempts)):
                    try:
                        active_key = st.session_state.api_manager.get_active_key()
                        llm_retriever = ChatGoogleGenerativeAI(
                            model=LLM_MODEL,
                            temperature=LLM_TEMPERATURE,
                            google_api_key=active_key
                        )
                        history_aware_retriever = create_history_aware_retriever(
                            llm_retriever, retriever, contextualize_q_prompt
                        )
                        sources = history_aware_retriever.invoke({
                            "input": user_question,
                            "chat_history": chat_history
                        })
                        break
                    except Exception as e:
                        if active_key:
                            try:
                                st.session_state.api_manager.mark_key_as_failed(active_key, error=e)
                            except Exception:
                                pass

        # 2. توليد الرد التدفقي البث الحي (Streaming Response)
        tutor_prompt = get_tutor_prompt()
        answer = ""
        active_key = None
        for attempt in range(max(1, usable_attempts)):
            try:
                active_key = st.session_state.api_manager.get_active_key()
                llm = ChatGoogleGenerativeAI(
                    model=LLM_MODEL,
                    temperature=LLM_TEMPERATURE,
                    google_api_key=active_key
                )
                combine_chain = create_stuff_documents_chain(llm, tutor_prompt)
                
                try:
                    # بث الإجابة حياً كلمة بكلمة فور توليدها
                    stream_res = combine_chain.stream({
                        "context": sources,
                        "input": final_prompt_input
                    })
                    answer = st.write_stream(stream_res)
                except Exception:
                    # التراجع التلقائي للاستدعاء المباشر في حال تعثر البث
                    res = combine_chain.invoke({
                        "context": sources,
                        "input": final_prompt_input
                    })
                    answer = str(res) if res else ""
                    if answer:
                        st.markdown(answer)

                if answer and len(str(answer).strip()) > 0:
                    break
            except Exception as e:
                if active_key:
                    try:
                        st.session_state.api_manager.mark_key_as_failed(active_key, error=e)
                    except ValueError as ve:
                        st.error(f"❌ {ve}")
                        st.stop()
                else:
                    st.error(f"❌ تعثر الحصول على مفتاح Gemini API صالح: {e}")
                    st.stop()

                if attempt < usable_attempts - 1:
                    st.toast("⚠️ جاري التبديل للمفتاح البديل...", icon="🔄")
                else:
                    st.error(f"❌ تعثر الحصول على الرد: {e}")
                    st.stop()

        if answer and len(str(answer).strip()) > 0:
            if sources:
                render_source_cards(sources)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })

# ── 8. تذييل الصفحة الفاخر (Luxury Digital Diwan Footer 2026) ──
st.markdown("""
<div class="diwan-footer">
    <div class="footer-brand">
        <span>⚖️ الديوان الرقمي للقانون المدني اليمني</span>
        <span class="footer-dot">•</span>
        <span>القرار الجمهوري رقم (14) لسنة 2002م</span>
    </div>
    <div class="footer-copy">
        تم التطوير وفق أحدث معايير الذكاء الاصطناعي القانوني 2026 | جميع الحقوق محفوظة
    </div>
</div>
""", unsafe_allow_html=True)
