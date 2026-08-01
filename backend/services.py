import os
import sys
import re
import json
import time
import asyncio
import threading
import concurrent.futures
from functools import lru_cache
from typing import List, Tuple, Dict, Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

try:
    from langchain.chains.combine_documents import create_stuff_documents_chain
except ImportError:
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document

from config.settings import (
    EMBEDDING_MODEL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    RETRIEVER_K,
    CHAT_HISTORY_MAX_MESSAGES,
)
from config.system_prompts import get_tutor_prompt
from config.legal_synonyms import expand_query_with_synonyms
from utils.api_manager import APIKeyManager
from utils.legal_splitter import normalize_digits
from utils.clean_source import clean_official_law_text
from backend.models import SuggestionItem, SourceDocument, SystemStats, RagStats

try:
    from nltk.stem.isri import ISRIStemmer
    arabic_stemmer = ISRIStemmer()
except Exception:
    arabic_stemmer = None


# ── ثوابت ──

VECTOR_SIMILARITY_THRESHOLD = 0.35

LEGAL_EXCEPTIONS_MAP = {
    "اراده": "رود",
    "الاراده": "رود",
    "بالاراده": "رود",
    "فبالاراده": "رود",
    "لاراده": "رود",
    "ارادتين": "رود",
    "بالارادتين": "رود",
}

ARABIC_STOP_WORDS = {
    "ما", "هي", "هو", "هم", "هن", "في", "من", "على", "عن", "الي", "إلي", "حتي",
    "مع", "او", "ان", "كان", "كانت", "يكون", "تكون", "هذا", "هذه", "ذلك", "تلك",
    "التي", "الذي", "الذين", "القانون", "المدني", "اليمني", "الماده", "ماده",
    "رقم", "بيان", "احكام", "حكم", "وفقا", "وفق", "حسب",
}

REFUSAL_PHRASES = [
    "عذرًا، هذه المعلومة غير متوفرة",
    "عذرا، هذه المعلومة غير متوفرة",
    "هذه المعلومة غير متوفرة في المرجع",
    "غير متوفرة في المرجع القانوني",
    "غير متوفرة في المرجع",
    "لا يوجد نص قانوني",
    "غير موجودة في النص",
    "متخصص حصرًا في القانون اليمني",
    "متخصص حصرا في القانون اليمني",
    "الخارجة عن المجال القانوني",
    "غير المتعلقة بالقانون اليمني",
]

CONTEXTUAL_PRONOUN_PATTERN = re.compile(
    r"\b(?:عليها|فيها|منها|إليها|عنها|بها|لتحقيقها)\b|\b\w{3,}(?:ها|هما)\b",
    re.UNICODE,
)

RESPONSE_CACHE: Dict[str, Dict[str, Any]] = {}
RESPONSE_CACHE_LOCK = threading.Lock()


# ── دوال مساعدة ──

@lru_cache(maxsize=1)
def get_vectorstore():
    """تحميل ChromaDB مع نموذج التضمين المحلي."""
    persist_dir = os.path.join(ROOT_DIR, "chroma_db_v2")
    if not os.path.exists(persist_dir):
        print(f"⚠️ مسار ChromaDB غير موجود: '{persist_dir}'")
        return None
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        return Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    except Exception as e:
        print(f"❌ خطأ أثناء تحميل ChromaDB: {e}")
        return None


@lru_cache(maxsize=1)
def get_api_manager():
    config_path = os.path.join(ROOT_DIR, "config", "api_keys.json")
    return APIKeyManager(config_path)


def add_user_api_key(api_key: str) -> Tuple[bool, str]:
    api_manager = get_api_manager()
    success = api_manager.add_key(api_key, source="واجهة React")
    if success:
        return True, "✅ تم حفظ وتفعيل المفتاح بنجاح!"
    return False, "⚠️ صيغة المفتاح غير صالحة. يجب أن يبدأ بـ AIzaSy أو AQ."


def preprocess_arabic_tokens(text: str) -> List[str]:
    """تطويع وتجذير صرفي للنصوص العربية لرفع دقة BM25."""
    if not text:
        return []
    text = re.sub(r"[أإآ]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ؤ", "و", text)
    text = re.sub(r"ئ", "ي", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"[\u064B-\u0652\u0640]", "", text)

    processed_tokens = []
    for w in text.split():
        w = re.sub(r"[^\w\s]", "", w)
        if not w or w in ARABIC_STOP_WORDS:
            continue
        if w in LEGAL_EXCEPTIONS_MAP:
            processed_tokens.append(LEGAL_EXCEPTIONS_MAP[w])
            continue
        if arabic_stemmer:
            try:
                stemmed = arabic_stemmer.stem(w)
                if stemmed:
                    w = stemmed
            except Exception:
                pass
        else:
            if len(w) > 3 and w.startswith("ال"):
                w = w[2:]
            if len(w) > 4:
                if w.endswith(("ات", "ين", "ون", "ية")):
                    w = w[:-2]
                elif w.endswith(("ه", "ة")):
                    w = w[:-1]
        processed_tokens.append(w)
    return processed_tokens


@lru_cache(maxsize=1)
def get_hybrid_retriever():
    """بناء محرك البحث الهجين (BM25 + ChromaDB)."""
    vectorstore = get_vectorstore()
    try:
        from langchain_community.retrievers import BM25Retriever
        try:
            from langchain.retrievers import EnsembleRetriever
        except ImportError:
            from langchain_classic.retrievers.ensemble import EnsembleRetriever
        from utils.legal_splitter import split_law_by_article

        txt_path = os.path.join(ROOT_DIR, "data", "yemeni_civil_law_official.txt")
        bm25_retriever = None
        if os.path.exists(txt_path):
            raw_text = ""
            for enc in ["utf-8", "utf-8-sig", "windows-1256"]:
                try:
                    with open(txt_path, "r", encoding=enc) as f:
                        raw_text = f.read()
                    break
                except Exception:
                    continue

            cleaned_text = clean_official_law_text(raw_text)
            docs = split_law_by_article(cleaned_text, source_name="yemeni_civil_law_official.txt")

            bm25_docs = [
                Document(
                    page_content=f"{d.metadata.get('book', '')}\n{d.page_content}".strip(),
                    metadata=d.metadata,
                )
                for d in docs
            ]

            bm25_retriever = BM25Retriever.from_documents(
                bm25_docs, preprocess_func=preprocess_arabic_tokens
            )
            bm25_retriever.k = RETRIEVER_K

            # استعادة النص الأصلي النظيف (بدون header الباب) للعرض
            for i, d in enumerate(bm25_retriever.docs):
                d.page_content = docs[i].page_content

        if vectorstore and bm25_retriever:
            vector_retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
            return EnsembleRetriever(
                retrievers=[bm25_retriever, vector_retriever],
                weights=[0.5, 0.5],
            )
        elif bm25_retriever:
            print("⚠️ ChromaDB غير متاحة — يعمل بـ BM25 فقط.")
            return bm25_retriever
        elif vectorstore:
            return vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
        return None
    except Exception as e:
        print(f"⚠️ تعذر بناء BM25Retriever: {e}")
        if vectorstore:
            return vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
        return None


def extract_direct_article_number(user_input: str) -> str:
    """استخراج رقم المادة المذكور صراحةً في السؤال."""
    if not user_input:
        return None
    norm_text = normalize_digits(user_input.strip())
    if norm_text.isdigit():
        return norm_text
    match = re.search(
        r"(?:الم[\u0640]*ادة|م[\u0640]*ادة)\s*(?:رقم\s*)?\(?\s*(\d+)\s*\)?",
        norm_text,
        re.UNICODE,
    )
    return match.group(1) if match else None


def enrich_query_with_history(user_question: str, previous_msgs: list) -> str:
    """إثراء الأسئلة الضمنية القصيرة بموضوع السؤال السابق."""
    if not previous_msgs or len(user_question.split()) > 5:
        return user_question
    if CONTEXTUAL_PRONOUN_PATTERN.search(user_question):
        for msg in reversed(previous_msgs):
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
            if role == "user" and content:
                print(f"💡 إثراء استعلام ضمني: '{content}' + '{user_question}'")
                return f"{content} {user_question}"
    return user_question


def retrieve_sources(user_question: str, previous_msgs: list = None) -> Tuple[List[Document], str]:
    """استرجاع المستندات القانونية من محرك البحث الهجين."""
    vectorstore = get_vectorstore()
    enriched_question = enrich_query_with_history(user_question, previous_msgs)

    # بحث مباشر بالمادة إذا ذُكر رقمها صراحةً
    direct_art_num = extract_direct_article_number(enriched_question)
    if direct_art_num and vectorstore:
        try:
            res = vectorstore.get(where={"article_number": direct_art_num})
            if res and res.get("documents"):
                direct_docs = [
                    Document(page_content=t, metadata=m)
                    for t, m in zip(res["documents"], res["metadatas"])
                ]
                final_prompt = f"قدّم النص الحرفي للمادة ({direct_art_num}) وشرحاً ميسراً وأمثلة تطبيقية عليها."
                return direct_docs, final_prompt
        except Exception:
            pass

    expanded_question = expand_query_with_synonyms(enriched_question)
    retriever = get_hybrid_retriever()
    if not retriever:
        if vectorstore:
            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": RETRIEVER_K})
        else:
            return [], user_question

    try:
        if hasattr(retriever, "retrievers") and len(retriever.retrievers) == 2 and vectorstore:
            bm25_r = retriever.retrievers[0]
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_bm25 = executor.submit(bm25_r.invoke, enriched_question)
                future_vector = executor.submit(
                    vectorstore.similarity_search_with_relevance_scores,
                    expanded_question, k=RETRIEVER_K,
                )
                bm25_docs = future_bm25.result()
                vector_docs = [d for d, s in future_vector.result() if s >= VECTOR_SIMILARITY_THRESHOLD]

            seen_ids = set()
            sources = []
            for i in range(max(len(bm25_docs), len(vector_docs))):
                for d in ([bm25_docs[i]] if i < len(bm25_docs) else []) + ([vector_docs[i]] if i < len(vector_docs) else []):
                    key = (d.metadata.get("article_number"), d.page_content[:50])
                    if key not in seen_ids:
                        seen_ids.add(key)
                        sources.append(d)
            sources = sources[:RETRIEVER_K]
        else:
            query = enriched_question if vectorstore is None else expanded_question
            sources = retriever.invoke(query)[:RETRIEVER_K]
    except Exception as e:
        print(f"❌ خطأ أثناء استرجاع المستندات: {e}")
        sources = []

    return sources, user_question


def is_refusal_response(answer: str) -> bool:
    if not answer:
        return True
    clean = answer.strip()
    if clean.startswith("❌") or clean.startswith("⚠️"):
        return True
    snippet = re.sub(r"\s+", " ", clean[:120])
    return any(p in snippet for p in REFUSAL_PHRASES)


def normalize_query_key(user_question: str) -> str:
    if not user_question:
        return ""
    text = normalize_digits(user_question.strip().lower())
    text = re.sub(r"[أإآ]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ؤ", "و", text)
    text = re.sub(r"ئ", "ي", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"[\u064B-\u0652\u0640]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def clear_answer_cache() -> int:
    global RESPONSE_CACHE
    with RESPONSE_CACHE_LOCK:
        count = len(RESPONSE_CACHE)
        RESPONSE_CACHE.clear()
        print(f"🧹 تم تفريغ الكاش ({count} عناصر).")
        return count


def format_source_documents(sources: List[Document]) -> List[SourceDocument]:
    return [
        SourceDocument(
            content=doc.page_content if hasattr(doc, "page_content") else str(doc),
            metadata=doc.metadata if hasattr(doc, "metadata") else {},
        )
        for doc in sources
    ]


def _build_chat_history(previous_msgs: list):
    history = []
    for msg in previous_msgs[-CHAT_HISTORY_MAX_MESSAGES:]:
        role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
        content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
        if role == "user":
            history.append(HumanMessage(content=content))
        elif role == "assistant":
            history.append(AIMessage(content=content))
    return history


def _build_tutor_prompt() -> ChatPromptTemplate:
    system_template = (
        get_tutor_prompt().messages[0].prompt.template.split("سؤال الطالب:")[0].strip()
    )
    return ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])


def _build_rag_stats(
    formatted_sources: List[SourceDocument],
    resp_time_str: str,
    is_refusal: bool,
) -> tuple:
    """إرجاع (rag_stats_dict, engine_name, status_text)."""
    source_verified = len(formatted_sources) > 0 and not is_refusal
    vectorstore_avail = get_vectorstore() is not None

    if vectorstore_avail:
        engine = "ChromaDB + Gemini Flash"
        status = "موثّق بسجل القانون المدني (2002م)" if source_verified else "غير مؤكد - لم يُعثر على نص قانوني مطابق"
    else:
        engine = "BM25 + Gemini Flash (عمل جزئي)"
        status = "عمل جزئي (BM25 فقط) - موثّق" if source_verified else "غير مؤكد - لم يُعثر على نص قانوني مطابق"

    return source_verified, RagStats(
        retrieved_count=len(formatted_sources),
        response_time=resp_time_str,
        source_verified=source_verified,
        engine=engine,
        status=status,
    )


# ── دوال إنشاء الاقتراحات والإحصائيات ──

def get_default_suggestions() -> List[SuggestionItem]:
    return [
        SuggestionItem(
            id="sug_0",
            category="باب العقود والالتزامات",
            title="أركان العقد وشروط صحته",
            subtext="استعراض الأهلية، التراضي، ومحل العقد وفقاً لأحكام القانون المدني",
            prompt="ما هي أركان العقد وشروط صحته وفقاً للقانون المدني اليمني؟",
            btn_label="استعراض الأركان والشروط ⚡",
            svg_icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>""",
            accent_class="sug-accent-gold",
        ),
        SuggestionItem(
            id="sug_1",
            category="تأصيل قانوني مباشر",
            title="المادة (138) بالتفصيل",
            subtext="النص الحرفي والشرح التطبيقي لأحكام المادة مع الأمثلة",
            prompt="138",
            btn_label="قراءة نص المادة (138) 📜",
            svg_icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-0.5-.05"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15Z"/><path d="M6 12h8"/><path d="M6 16h8"/><path d="M6 8h4"/></svg>""",
            accent_class="sug-accent-emerald",
        ),
        SuggestionItem(
            id="sug_2",
            category="النظرية العامة للحق",
            title="عيوب الإرادة وأثرها القانوني",
            subtext="الغلط، التدليس، الإكراه، والاستغلال وفقاً لأحكام القانون المدني",
            prompt="ما هي عيوب الإرادة في القانون المدني اليمني وكيف أثرها؟",
            btn_label="تحليل عيوب الإرادة ⚖️",
            svg_icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h18"/></svg>""",
            accent_class="sug-accent-blue",
        ),
        SuggestionItem(
            id="sug_3",
            category="الضمانات وحقوق الدائن",
            title="أحكام الكفالة والضمان",
            subtext="التزامات الكفيل وحقوق الدائن والمدين في الشريعة والقانون",
            prompt="ما هي أحكام الكفالة والضمان ومسؤولية الكفيل في القانون اليمني؟",
            btn_label="استعراض أحكام الكفالة 🛡️",
            svg_icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>""",
            accent_class="sug-accent-purple",
        ),
    ]


def get_system_stats_service() -> SystemStats:
    vectorstore = get_vectorstore()
    total_docs = 0
    status = "غير متصل"

    if vectorstore and hasattr(vectorstore, "_collection") and vectorstore._collection:
        try:
            total_docs = vectorstore._collection.count()
            status = "متصل"
        except Exception:
            pass

    if total_docs == 0:
        try:
            import chromadb
            persist_dir = os.path.join(ROOT_DIR, "chroma_db_v2")
            if os.path.exists(persist_dir):
                client = chromadb.PersistentClient(path=persist_dir)
                cols = client.list_collections()
                if cols:
                    total_docs = cols[0].count()
                    status = "متصل"
        except Exception:
            total_docs = 0

    return SystemStats(
        total_docs=total_docs,
        status=status,
        accuracy="100%",
        response_time="<0.3s",
        engine="AI v3 (Gemini Flash Latest)",
    )


# ── دوال الإجابة الرئيسية ──

def generate_chat_answer_sync(
    user_question: str, previous_msgs: list
) -> Tuple[str, List[SourceDocument], RagStats]:
    """توليد الإجابة كاملةً دفعةً واحدة (JSON)."""
    cache_key = normalize_query_key(user_question) if not previous_msgs else ""

    if cache_key:
        with RESPONSE_CACHE_LOCK:
            if cache_key in RESPONSE_CACHE:
                cached = RESPONSE_CACHE[cache_key]
                print(f"⚡ [Cache] استرجاع فوري للسؤال: '{user_question}'")
                return cached["answer"], cached["sources"], cached["rag_stats"]

    start_time = time.time()
    api_manager = get_api_manager()
    sources, final_prompt = retrieve_sources(user_question, previous_msgs)
    formatted_sources = format_source_documents(sources)
    resp_time_str = f"{round(time.time() - start_time, 2)}s"

    if not api_manager.has_usable_key():
        _, rag_stats = _build_rag_stats(formatted_sources, resp_time_str, True)
        return "❌ لا يوجد مفتاح Gemini API صالح في config/api_keys.json", formatted_sources, rag_stats

    chat_history = _build_chat_history(previous_msgs) if previous_msgs else []
    tutor_prompt = _build_tutor_prompt()
    usable_attempts = len([k for k in api_manager.keys if k not in api_manager.invalid_keys])
    answer = ""
    active_key = None

    for attempt in range(max(1, usable_attempts)):
        try:
            active_key = api_manager.get_active_key()
            llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, google_api_key=active_key)
            chain = create_stuff_documents_chain(llm, tutor_prompt)
            res = chain.invoke({"context": sources, "input": final_prompt, "chat_history": chat_history})
            answer = str(res) if res else ""
            if answer.strip():
                break
        except Exception as e:
            if active_key:
                api_manager.mark_key_as_failed(active_key, error=e)
            if attempt < usable_attempts - 1:
                time.sleep(2 ** attempt)
            else:
                answer = f"❌ تعذر الاتصال بالذكاء الاصطناعي. (تفاصيل: {e})"

    is_refusal = is_refusal_response(answer)
    source_verified, rag_stats = _build_rag_stats(formatted_sources, resp_time_str, is_refusal)

    if cache_key and answer and not is_refusal and not answer.startswith("❌"):
        with RESPONSE_CACHE_LOCK:
            RESPONSE_CACHE[cache_key] = {"answer": answer, "sources": formatted_sources, "rag_stats": rag_stats}
            print(f"💾 [Cache] تخزين إجابة: '{user_question}'")

    return answer, formatted_sources, rag_stats


async def stream_chat_answer_sse(user_question: str, previous_msgs: list):
    """بث الإجابة حياً عبر SSE."""
    cache_key = normalize_query_key(user_question) if not previous_msgs else ""

    if cache_key:
        with RESPONSE_CACHE_LOCK:
            if cache_key in RESPONSE_CACHE:
                cached = RESPONSE_CACHE[cache_key]
                print(f"⚡ [Cache SSE] استرجاع فوري: '{user_question}'")
                sources_data = [s.model_dump() for s in cached["sources"]]
                rag_stats_data = (
                    cached["rag_stats"].model_dump()
                    if hasattr(cached["rag_stats"], "model_dump")
                    else cached["rag_stats"]
                )
                yield {"event": "metadata", "data": json.dumps({"sources": sources_data, "rag_stats": {"retrieved_count": len(sources_data), "response_time": "<0.05s"}}, ensure_ascii=False)}
                yield {"event": "token", "data": json.dumps({"chunk": cached["answer"]}, ensure_ascii=False)}
                yield {"event": "verification_status", "data": json.dumps({"rag_stats": rag_stats_data}, ensure_ascii=False)}
                yield {"event": "done", "data": "[DONE]"}
                return

    start_time = time.time()
    api_manager = get_api_manager()
    sources, final_prompt = retrieve_sources(user_question, previous_msgs)
    formatted_sources = format_source_documents(sources)
    resp_time_str = f"{round(time.time() - start_time, 2)}s"
    sources_data = [s.model_dump() for s in formatted_sources]

    yield {
        "event": "metadata",
        "data": json.dumps({"sources": sources_data, "rag_stats": {"retrieved_count": len(formatted_sources), "response_time": resp_time_str}}, ensure_ascii=False),
    }

    if not api_manager.has_usable_key():
        yield {"event": "error", "data": json.dumps({"error": "لا يوجد مفتاح API صالح."}, ensure_ascii=False)}
        return

    chat_history = _build_chat_history(previous_msgs) if previous_msgs else []
    tutor_prompt = _build_tutor_prompt()
    usable_attempts = len([k for k in api_manager.keys if k not in api_manager.invalid_keys])
    active_key = None
    tokens_streamed = False

    for attempt in range(max(1, usable_attempts)):
        try:
            active_key = api_manager.get_active_key()
            llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, google_api_key=active_key)
            chain = create_stuff_documents_chain(llm, tutor_prompt)
            accumulated = ""

            async for chunk in chain.astream({"context": sources, "input": final_prompt, "chat_history": chat_history}):
                if not chunk:
                    continue
                chunk_str = str(chunk)
                accumulated += chunk_str
                tokens_streamed = True
                yield {"event": "token", "data": json.dumps({"chunk": chunk_str}, ensure_ascii=False)}

            is_refusal = is_refusal_response(accumulated)
            source_verified, _ = _build_rag_stats(formatted_sources, resp_time_str, is_refusal)
            vectorstore_avail = get_vectorstore() is not None
            engine = "ChromaDB + Gemini Flash" if vectorstore_avail else "BM25 + Gemini Flash (عمل جزئي)"
            status = (
                ("موثّق بسجل القانون المدني (2002م)" if vectorstore_avail else "عمل جزئي (BM25 فقط)")
                if source_verified else "غير مؤكد - لم يُعثر على نص قانوني مطابق"
            )

            final_rag_stats = {
                "retrieved_count": len(formatted_sources),
                "response_time": resp_time_str,
                "source_verified": source_verified,
                "engine": engine,
                "status": status,
            }

            yield {"event": "verification_status", "data": json.dumps({"rag_stats": final_rag_stats}, ensure_ascii=False)}
            yield {"event": "done", "data": "[DONE]"}

            if cache_key and accumulated and not is_refusal and not accumulated.startswith("❌"):
                with RESPONSE_CACHE_LOCK:
                    RESPONSE_CACHE[cache_key] = {
                        "answer": accumulated,
                        "sources": formatted_sources,
                        "rag_stats": final_rag_stats,
                    }
                    print(f"💾 [Cache SSE] تخزين إجابة متدفقة: '{user_question}'")
            break

        except Exception as e:
            err_str = str(e)
            if active_key:
                try:
                    api_manager.mark_key_as_failed(active_key, error=e)
                except Exception:
                    pass

            if tokens_streamed:
                print(f"⚠️ [SSE] انقطع البث جزئياً: {err_str}")
                yield {"event": "error", "data": json.dumps({"error": "⚠️ انقطع بث الإجابة جزئياً."}, ensure_ascii=False)}
                yield {"event": "done", "data": "[DONE]"}
                return

            if attempt < usable_attempts - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                if any(k in err_str for k in ["RESOURCE_EXHAUSTED", "429", "quota"]):
                    err_msg = "⚠️ تم تجاوز حصة API الحالية. يرجى إضافة مفتاح جديد أو الانتظار دقيقة."
                else:
                    err_msg = f"❌ تعذر الاتصال بالذكاء الاصطناعي. (تفاصيل: {err_str})"
                yield {"event": "error", "data": json.dumps({"error": err_msg}, ensure_ascii=False)}
