import re
from langchain_core.documents import Document


def normalize_digits(text: str) -> str:
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return text.translate(trans)


def split_law_by_article(full_text: str, source_name: str) -> list[Document]:
    """
    يقسّم نص القانون أو المذكرات إلى مستندات (Document):
    1. يستخرج النص التمهيدي والمبادئ العامة في بداية الملف كمستند مستقل.
    2. يقسّم المواد القانونية بدقة اعتماداً على مرساة بداية السطر (MULTILINE)،
       مما يمنع شطر المواد عند ظهور الإشارات المرجعية في المتن (مثل 'وفقاً للمادة (XX)').
    3. يحفظ رقم المادة، اسم القانون، الباب، والفصل كبيانات وصفية (metadata) جديدة ومثراة.
    """
    documents = []
    current_book = "المبادئ العامة والقواعد الكلية"
    current_chapter = ""

    header_regex = re.compile(
        r"^\s*((?:الكتاب|الباب|القسم|الفصل)\s+[^\n]+)", re.MULTILINE
    )

    # النمط المحكم: يطابق رأس المادة فقط إذا كان في بداية السطر (MULTILINE) ومتبوعاً بالنقطتين الرأسيتين (:)
    # مما يحمي الإشارات المرجعية الداخلية في المتن من التقطيع الوهمي
    article_pattern = re.compile(
        r"^\s*(?:الم[\u0640]*ادة|م[\u0640]*ادة)\s*(?:رقم\s*)?\(?\s*([\d\u0660-\u0669]+)\s*\)?\s*:",
        re.MULTILINE | re.UNICODE,
    )
    parts = article_pattern.split(full_text)

    # 1. عدم إهمال النص التمهيدي في بداية الملف
    preamble = parts[0].strip() if parts else ""
    if len(preamble) > 50:
        documents.append(
            Document(
                page_content=preamble,
                metadata={
                    "article_number": "تمهيد ومبادئ عامة",
                    "book": current_book,
                    "chapter": current_chapter,
                },
            )
        )

    # 2. تقشير واستخراج كل مادة رسمية مع الحفاظ على الهيكل التنظيمي كاملًا
    for i in range(1, len(parts), 2):
        raw_article_number = parts[i]
        article_number = normalize_digits(raw_article_number)
        article_text = parts[i + 1].strip() if i + 1 < len(parts) else ""

        # تجاهل السجلات الفارغة والمكسورة (أقل من 15 حرفاً)
        if len(article_text) < 15:
            continue

        # تحديث الباب والفصل بناءً على العناوين السابقة للمادة
        text_before_article = parts[i - 1]
        headers = header_regex.findall(text_before_article)
        for h in headers:
            h_clean = h.strip()
            if len(h_clean) < 80:
                h_clean = re.sub(r"[\:\-\=\_]+$", "", h_clean).strip()
                if any(h_clean.startswith(w) for w in ["الكتاب", "الباب", "القسم"]):
                    current_book = h_clean
                    current_chapter = ""
                elif h_clean.startswith("الفصل"):
                    current_chapter = h_clean

        documents.append(
            Document(
                page_content=f"مادة ({article_number}): {article_text}",
                metadata={
                    "article_number": article_number,
                    "book": current_book,
                    "chapter": current_chapter,
                },
            )
        )

    return documents
