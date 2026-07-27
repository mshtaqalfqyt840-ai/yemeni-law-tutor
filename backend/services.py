import os
import sys
import re
import json
from functools import lru_cache
from typing import List, Tuple, Dict, Any

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

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
from backend.models import SuggestionItem, SourceDocument


@lru_cache(maxsize=1)
def get_vectorstore():
    """تحميل قاعدة البيانات المتجهة بنموذج التضمين المحلي وتخزينها في الذاكرة."""
    persist_dir = os.path.join(ROOT_DIR, "chroma_db_v2")
    if not os.path.exists(persist_dir):
        return None
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(persist_directory=persist_dir, embedding_function=embeddings)


@lru_cache(maxsize=1)
def get_api_manager():
    """تحميل مدير المفاتيح."""
    config_path = os.path.join(ROOT_DIR, "config", "api_keys.json")
    return APIKeyManager(config_path)


def add_user_api_key(api_key: str) -> Tuple[bool, str]:
    """إضافة وتفعيل مفتاح Gemini API جديد من واجهة المستخدم."""
    api_manager = get_api_manager()
    success = api_manager.add_key(api_key, source="واجهة React")
    if success:
        return True, "✅ تم حفظ وتفعيل المفتاح بنجاح!"
    else:
        return False, "⚠️ صيغة المفتاح غير صالحة. يجب أن يبدأ بـ AIzaSy أو AQ."


def extract_direct_article_number(user_input: str) -> str:
    """استخراج رقم المادة مباشرة من السؤال إذا طُلبت صراحةً."""
    cleaned = user_input.strip()
    norm_text = normalize_digits(cleaned)
    match = re.search(r'^(?:مادة|المادة)?\s*(?:رقم\s*)?\(?\s*(?:رقم\s*)?(\d+)\s*\)?\s*[؟\?\.\!]*$', norm_text)
    if match:
        return match.group(1)
    return None


def get_default_suggestions() -> List[SuggestionItem]:
    """قائمة بطاقات الاقتراحات القانونية السريعة."""
    return [
        SuggestionItem(
            id="sug_0",
            category="باب العقود والالتزامات",
            title="أركان العقد وشروط صحته",
            subtext="استعراض الأهلية، التراضي، ومحل العقد وفقاً لأحكام القانون المدني",
            prompt="ما هي أركان العقد وشروط صحته وفقاً للقانون المدني اليمني؟",
            btn_label="استعراض الأركان والشروط ⚡",
            svg_icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>""",
            accent_class="sug-accent-gold"
        ),
        SuggestionItem(
            id="sug_1",
            category="تأصيل قانوني مباشر",
            title="المادة (138) بالتفصيل",
            subtext="النص الحرفي والشرح التطبيقي لأحكام المادة مع الأمثلة",
            prompt="138",
            btn_label="قراءة نص المادة (138) 📜",
            svg_icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-0.5-.05"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15Z"/><path d="M6 12h8"/><path d="M6 16h8"/><path d="M6 8h4"/></svg>""",
            accent_class="sug-accent-emerald"
        ),
        SuggestionItem(
            id="sug_2",
            category="النظرية العامة للحق",
            title="عيوب الإرادة وأثرها القانوني",
            subtext="الغلط، التدليس، الإكراه، والاستغلال وفقاً لأحكام القانون المدني",
            prompt="ما هي عيوب الإرادة في القانون المدني اليمني وكيف أثرها؟",
            btn_label="تحليل عيوب الإرادة ⚖️",
            svg_icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h18"/></svg>""",
            accent_class="sug-accent-blue"
        ),
        SuggestionItem(
            id="sug_3",
            category="الضمانات وحقوق الدائن",
            title="أحكام الكفالة والضمان",
            subtext="التزامات الكفيل وحقوق الدائن والمدين في الشريعة والقانون",
            prompt="ما هي أحكام الكفالة والضمان ومسؤولية الكفيل في القانون اليمني؟",
            btn_label="استعراض أحكام الكفالة 🛡️",
            svg_icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>""",
            accent_class="sug-accent-purple"
        )
    ]


def retrieve_sources(user_question: str, previous_msgs: list) -> Tuple[List[Document], str]:
    """استرجاع المستندات القانونية من قاعدة البيانات المتجهة."""
    vectorstore = get_vectorstore()
    api_manager = get_api_manager()

    if not vectorstore:
        return [], user_question

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

    if direct_docs:
        final_prompt_input = f"قدّم النص الحرفي للمادة ({direct_art_num}) وشرحاً ميسراً وأمثلة تطبيقية عليها وفقاً للنص المرفق."
        return direct_docs, final_prompt_input

    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": RETRIEVER_K})
    if not previous_msgs:
        sources = retriever.invoke(user_question)
        return sources, user_question

    if len(previous_msgs) > CHAT_HISTORY_MAX_MESSAGES:
        previous_msgs = previous_msgs[-CHAT_HISTORY_MAX_MESSAGES:]

    chat_history = []
    for msg in previous_msgs:
        if msg.role == "user":
            chat_history.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            chat_history.append(AIMessage(content=msg.content))

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

    usable_attempts = len([k for k in api_manager.keys if k not in api_manager.invalid_keys])
    if usable_attempts == 0:
        try:
            return retriever.invoke(user_question), user_question
        except Exception:
            return [], user_question

    sources = []
    for attempt in range(usable_attempts):
        active_key = None
        try:
            active_key = api_manager.get_active_key()
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
                    api_manager.mark_key_as_failed(active_key, error=e)
                except Exception:
                    pass

    return sources, user_question


def format_source_documents(sources: List[Document]) -> List[SourceDocument]:
    """تحويل مستندات LangChain إلى نماذج Pydantic للواجهة البرمجية."""
    result = []
    for doc in sources:
        meta = doc.metadata if hasattr(doc, 'metadata') else {}
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        result.append(SourceDocument(content=content, metadata=meta))
    return result


def generate_chat_answer_sync(user_question: str, previous_msgs: list) -> Tuple[str, List[SourceDocument]]:
    """توليد الإجابة بشكل غير تدفقي (JSON عادٍ)."""
    api_manager = get_api_manager()
    sources, final_prompt = retrieve_sources(user_question, previous_msgs)
    formatted_sources = format_source_documents(sources)

    if not api_manager.has_usable_key():
        return "❌ لا يوجد مفتاح Gemini API صالح وفعّال في config/api_keys.json", formatted_sources

    tutor_prompt = get_tutor_prompt()
    usable_attempts = len([k for k in api_manager.keys if k not in api_manager.invalid_keys])
    answer = ""
    active_key = None

    for attempt in range(max(1, usable_attempts)):
        try:
            active_key = api_manager.get_active_key()
            llm = ChatGoogleGenerativeAI(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                google_api_key=active_key
            )
            combine_chain = create_stuff_documents_chain(llm, tutor_prompt)
            res = combine_chain.invoke({
                "context": sources,
                "input": final_prompt
            })
            answer = str(res) if res else ""
            if answer and len(answer.strip()) > 0:
                break
        except Exception as e:
            if active_key:
                api_manager.mark_key_as_failed(active_key, error=e)
            if attempt == usable_attempts - 1:
                answer = (
                    "❌ تنبيه: تعذر الاتصال بمحرك الذكاء الاصطناعي.\n"
                    "يرجى التأكد من إضافة مفتاح Google Gemini API صحيح داخل ملف `config/api_keys.json` "
                    f"(تفاصيل الخطأ: {str(e)})"
                )

    return answer, formatted_sources


async def stream_chat_answer_sse(user_question: str, previous_msgs: list):
    """بث الإجابة حياً عبر Server-Sent Events (SSE)."""
    api_manager = get_api_manager()
    sources, final_prompt = retrieve_sources(user_question, previous_msgs)
    formatted_sources = format_source_documents(sources)

    # 1. إرسال المصادر أولاً لتعرضها واجهة React فوراً قبل الإجابة
    sources_data = [s.model_dump() for s in formatted_sources]
    yield {
        "event": "metadata",
        "data": json.dumps({"sources": sources_data}, ensure_ascii=False)
    }

    if not api_manager.has_usable_key():
        yield {
            "event": "error",
            "data": json.dumps({"error": "لا يوجد مفتاح API صالح وفعال."}, ensure_ascii=False)
        }
        return

    tutor_prompt = get_tutor_prompt()
    usable_attempts = len([k for k in api_manager.keys if k not in api_manager.invalid_keys])
    active_key = None

    for attempt in range(max(1, usable_attempts)):
        try:
            active_key = api_manager.get_active_key()
            llm = ChatGoogleGenerativeAI(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                google_api_key=active_key
            )
            combine_chain = create_stuff_documents_chain(llm, tutor_prompt)
            
            # البث الحي كلمة بكلمة
            async for chunk in combine_chain.astream({
                "context": sources,
                "input": final_prompt
            }):
                if chunk:
                    yield {
                        "event": "token",
                        "data": json.dumps({"chunk": str(chunk)}, ensure_ascii=False)
                    }
            
            yield {
                "event": "done",
                "data": "[DONE]"
            }
            break
        except Exception as e:
            err_str = str(e)
            if active_key:
                try:
                    api_manager.mark_key_as_failed(active_key, error=e)
                except Exception:
                    pass
            if attempt == usable_attempts - 1:
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "quota" in err_str.lower():
                    err_msg = (
                        "⚠️ **تنبيه الحصة:** تم تجاوز الحد المؤقت لاستخدام مفتاح Gemini API الحالي (Rate Limit / Quota Exceeded).\n\n"
                        "💡 **حل سريع:** يرجى إدخال مفتاح Gemini API جديد وبديل في الواجهة أو الانتظار دقيقة واحدة وإعادة السؤال."
                    )
                else:
                    err_msg = (
                        "❌ تنبيه: تعذر الاتصال بمحرك الذكاء الاصطناعي.\n"
                        "يرجى التأكد من إضافة مفتاح Google Gemini API صالح وفعّال. "
                        f"(تفاصيل الخطأ: {err_str})"
                    )
                yield {
                    "event": "error",
                    "data": json.dumps({"error": err_msg}, ensure_ascii=False)
                }

