import os
import json
import glob
import sys
import hashlib

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

base_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base_dir)

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from utils.legal_splitter import split_law_by_article
from config.settings import EMBEDDING_MODEL


def read_txt_file(txt_path: str) -> str:
    """يقرأ ملف نصي TXT مع دعم عدة ترميزات عربية."""
    encodings = ["utf-8", "utf-8-sig", "windows-1256", "iso-8859-6"]
    for enc in encodings:
        try:
            with open(txt_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, Exception):
            continue
    print(f"  Warning: تعذّر قراءة: {os.path.basename(txt_path)}")
    return ""


def read_pdf_file(pdf_path: str) -> str:
    """يقرأ ملف PDF ويعيد النص المستخرج."""
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        text = ""
        for page in pages:
            if page.page_content:
                text += page.page_content + "\n\n"
        return text
    except Exception as e:
        print(f"  Warning: خطأ أثناء قراءة PDF {os.path.basename(pdf_path)}: {e}")
        return ""


def ingest_documents(rebuild: bool = False):
    """
    يقرأ جميع ملفات PDF و TXT من مجلد data/،
    يقسّمها بالمادة القانونية، ويبني قاعدة البيانات المتجهة.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "data")
    persist_dir = os.path.join(base_dir, "chroma_db_v2")

    pdf_files = sorted(glob.glob(os.path.join(data_dir, "*.pdf")))
    txt_files = sorted(glob.glob(os.path.join(data_dir, "*.txt")))
    all_files = pdf_files + txt_files

    if not all_files:
        print("لم يتم العثور على أي ملفات (PDF أو TXT) في مجلد data/.")
        return None

    print(f"الملفات المكتشفة: {len(pdf_files)} PDF  +  {len(txt_files)} TXT")

    seen_hashes = set()
    unique_files = []
    skipped = 0
    for fp in all_files:
        try:
            with open(fp, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            if file_hash in seen_hashes:
                print(f"  مكرر — تم تخطيه: {os.path.basename(fp)}")
                skipped += 1
            else:
                seen_hashes.add(file_hash)
                unique_files.append(fp)
        except Exception:
            unique_files.append(fp)

    if skipped:
        print(f"تم تخطي {skipped} ملف مكرر.")
    print(f"الملفات الفريدة للمعالجة: {len(unique_files)}")

    documents = []
    for file_path in unique_files:
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        print(f"جاري معالجة: {filename}")

        if ext == ".pdf":
            raw_text = read_pdf_file(file_path)
        elif ext == ".txt":
            raw_text = read_txt_file(file_path)
        else:
            continue

        if not raw_text.strip():
            print(f"  الملف فارغ أو تعذّر قراءته.")
            continue

        docs = split_law_by_article(raw_text, source_name=filename)
        if docs:
            documents.extend(docs)
            print(f"  تم استخراج {len(docs)} مادة قانونية.")
        else:
            print(f"  لم يتم استخراج أي مادة (تأكد من صيغة مادة رقم).")

    if not documents:
        print("لم يتم استخراج أي مواد قانونية من جميع الملفات.")
        return None

    print(f"إجمالي المواد القانونية المستخرجة: {len(documents)}")

    print(f"جاري تهيئة نموذج التضمين المحلي ({EMBEDDING_MODEL})...")
    print("ملاحظة: سيتم تحميل النموذج أول مرة فقط (~120MB) ثم يُخزّن محلياً")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    if rebuild and os.path.exists(persist_dir):
        import shutil
        try:
            print("إفراغ قاعدة البيانات القديمة قبل إعادة البناء...")
            shutil.rmtree(persist_dir, ignore_errors=True)
        except Exception as e:
            print(f"تنبيه أثناء إفراغ المجموعة: {e}")

    print(f"جاري بناء المتجهات وحفظها في: {persist_dir}")
    try:
        vectorstore = Chroma(
            embedding_function=embeddings,
            persist_directory=persist_dir
        )

        batch_size = 50
        total_batches = (len(documents) + batch_size - 1) // batch_size

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            batch_num = i // batch_size + 1
            print(f"  الدفعة {batch_num}/{total_batches} (معالجة {i} حتى {min(i + batch_size, len(documents))} من أصل {len(documents)})...")
            try:
                vectorstore.add_documents(batch)
            except Exception as e:
                print(f"\n❌ خطأ أثناء تضمين الدفعة {batch_num}: {e}")

        total_in_db = vectorstore._collection.count()
        print(f"\n✅ اكتملت عملية البناء بنجاح! إجمالي السجلات في قاعدة البيانات: {total_in_db}")
        return vectorstore

    except Exception as e:
        print(f"خطأ أثناء بناء المتجهات: {e}")
        return None


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))

    print("بدء عملية التضمين وبناء قاعدة البيانات...")
    print("هل تريد إعادة بناء القاعدة من الصفر؟ [y/N]: ", end="")
    user_input = input().strip().lower()
    rebuild = user_input == "y"

    vectorstore = ingest_documents(rebuild=rebuild)

    if vectorstore:
        print("العملية اكتملت بنجاح! يمكنك الآن تشغيل: streamlit run app.py")
    else:
        print("العملية لم تكتمل. راجع الأخطاء أعلاه.")
