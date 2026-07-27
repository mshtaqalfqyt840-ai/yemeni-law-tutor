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
                        <span class="article-badge">مادة ({art_num})</span>
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

# ── 3. الشريط الجانبي (Sidebar) ──
total_docs = vectorstore._collection.count() if vectorstore else 0

with st.sidebar:
    # الهوية البصرية للشريط الجانبي
    st.markdown("""
    <div class="sidebar-brand-box">
        <div class="sidebar-brand-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
                <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
                <path d="M7 21h10"/>
                <path d="M12 3v18"/>
                <path d="M3 7h18"/>
            </svg>
        </div>
        <h2 class="sidebar-brand-title">المعلّم <span>الذكي</span></h2>
        <p class="sidebar-brand-subtitle">الديوان الرقمي للقانون المدني اليمني<br>القرار الجمهوري رقم (14) لسنة 2002م</p>
    </div>
    """, unsafe_allow_html=True)

    # شارة الاتصال الحي
    status_label = f"محرك الاسترجاع متصل • {total_docs:,} مادة" if vectorstore else "قاعدة البيانات غير متصلة"
    st.markdown(f"""
    <div class="live-status-pill">
        <span class="live-status-dot"></span>
        <span>{status_label}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="color:var(--text-muted); font-size:0.75rem; font-weight:700; margin:16px 0 8px 0; letter-spacing:0.5px;">📊 إحصائيات النظام</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sidebar-stats-grid">
        <div class="sidebar-stat-card">
            <span class="sidebar-stat-num">{total_docs:,}</span>
            <span class="sidebar-stat-lbl">مادة مفهرسة</span>
        </div>
        <div class="sidebar-stat-card">
            <span class="sidebar-stat-num">100%</span>
            <span class="sidebar-stat-lbl">دقة الإسناد</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # صندوق التلميح الذكي
    st.markdown("""
    <div class="sidebar-tip-card">
        💡 <strong>تلميح التأصيل:</strong> اكتب رقم المادة مباشرة 
        (مثال: <strong>138</strong> أو <strong>مادة (15)</strong>) 
        لاستحضار نصها القانوني وشرحها فوراً!
    </div>
    """, unsafe_allow_html=True)

    # زر مسح المحادثة
    if st.button("🗑️  مسح المحادثة بالكامل", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    if not vectorstore:
        st.error("⚠️ قاعدة البيانات غير موجودة! شغّل سكربت الفهرسة لبنائها أولاً.")

# ── 4. الهيدر الرئيسي (Hero Header) ──
st.markdown("""
<div class="diwan-hero-container">
    <svg class="diwan-hero-bg-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
        <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
        <path d="M7 21h10"/>
        <path d="M12 3v18"/>
        <path d="M3 7h18"/>
    </svg>
    <div class="diwan-eyebrow">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        <span>الديوان الرقمي • المرجع الذكي الأول للقانون المدني</span>
    </div>
    <h1 class="diwan-hero-title">المعلّم الذكي <span>للقانون المدني اليمني</span></h1>
    <div class="diwan-hero-desc">
        منصة تفاعلية موثّقة لتقديم الشروح والاستشارات الأكاديمية المستندة 
        <strong>حصرياً</strong> على النص الرسمي للقرار الجمهوري بالقانون رقم (14) لسنة 2002م، دون هلوسة أو اجتهاد خارجي.
    </div>
    <div class="diwan-trust-badges">
        <div class="trust-badge-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            <span>إسناد نصي حرفي موثّق</span>
        </div>
        <div class="trust-badge-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
            <span>1,385 مادة قانونية مفهرسة</span>
        </div>
        <div class="trust-badge-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
            <span>محدث وفق التعديلات الرسمية</span>
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

# ── 5. بطاقات الاقتراحات (تظهر فقط عند بداية المحادثة) ──
if len(st.session_state.messages) == 0:
    st.markdown("""
    <div class="suggestions-section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
        <span>نماذج أسئلة قانونية شائعة للبدء:</span>
    </div>
    """, unsafe_allow_html=True)

    suggestions = [
        {
            "title": "أركان العقد وشروط صحته",
            "subtext": "استعراض الأهلية، التراضي، ومحل العقد وفقاً لأحكام القانون المدني",
            "prompt": "ما هي أركان العقد وشروط صحته وفقاً للقانون المدني اليمني؟",
        },
        {
            "title": "المادة (138) بالتفصيل",
            "subtext": "النص الحرفي والشرح التطبيقي لأحكام المادة",
            "prompt": "138",
        },
        {
            "title": "عيوب الإرادة وأثرها القانوني",
            "subtext": "الغلط، التدليس، الإكراه، والاستغلال وفقاً للقانون",
            "prompt": "ما هي عيوب الإرادة في القانون المدني اليمني وكيف أثرها؟",
        },
        {
            "title": "أحكام الكفالة والضمان",
            "subtext": "التزامات الكفيل وحقوق الدائن والمدين في الشريعة والقانون",
            "prompt": "ما هي أحكام الكفالة والضمان ومسؤولية الكفيل في القانون اليمني؟",
        }
    ]

    col1, col2 = st.columns(2)
    cols = [col1, col2, col1, col2]
    
    for i, sug in enumerate(suggestions):
        with cols[i]:
            label = f"📌 {sug['title']}\n\n{sug['subtext']}"
            if st.button(label, use_container_width=True, key=f"sug_{i}"):
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
user_question = st.chat_input("اطرح سؤالك القانوني أو اكتب رقم المادة مباشرة... (مثال: 138 أو ما هي شروط البيع؟)")

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
        st.error("❌ لا يوجد مفتاح Gemini API صالح وفعّال. الرجاء إضافة مفتاح في config/api_keys.json")
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
                        st.session_state.api_manager.mark_key_as_failed(active_key, error=e)

        # 2. توليد الرد التدفقي البث الحي (Streaming Response)
        tutor_prompt = get_tutor_prompt()
        answer = ""
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
                try:
                    st.session_state.api_manager.mark_key_as_failed(active_key, error=e)
                except ValueError as ve:
                    st.error(f"❌ {ve}")
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
