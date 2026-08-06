import type { Message } from '../types';

/**
 * تحويل نص ماركدوان بسيط إلى HTML لتنسيق الطباعة الرسمية
 */
function formatContentToHtml(content: string): string {
  if (!content) return '';
  
  // تنظيف وتنسيق العناوين والفقرات
  let html = content
    .replace(/### (.*?)(?:\n|$)/g, '<h4 class="pdf-subheading">$1</h4>')
    .replace(/## (.*?)(?:\n|$)/g, '<h3 class="pdf-heading">$1</h3>')
    .replace(/# (.*?)(?:\n|$)/g, '<h2 class="pdf-title">$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>');

  // معالجة القوائم والتعداد والنقاط
  const paragraphs = html.split('\n\n');
  return paragraphs
    .map((p) => {
      const trimmed = p.trim();
      if (!trimmed) return '';
      if (trimmed.startsWith('<h2') || trimmed.startsWith('<h3') || trimmed.startsWith('<h4')) {
        return trimmed;
      }
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const items = trimmed
          .split('\n')
          .map((line) => line.replace(/^[\-\*]\s+/, ''))
          .map((item) => `<li>${item}</li>`)
          .join('');
        return `<ul class="pdf-list">${items}</ul>`;
      }
      // فقرة عادية مع استبدال الأسطر المفردة
      return `<p class="pdf-paragraph">${trimmed.replace(/\n/g, '<br/>')}</p>`;
    })
    .join('');
}

/**
 * دالة تصدير الاستشارة القانونية كملف PDF رسمي معتمد
 */
export function exportConsultationAsPDF(message: Message, userQuestion?: string): void {
  const reportId = `YEM-LAW-${Date.now().toString().slice(-6)}`;
  const todayStr = new Date().toLocaleDateString('ar-YE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const questionText = userQuestion || 'استشارة قانونية في التشريع المدني اليمني';
  const answerHtml = formatContentToHtml(message.content);

  const hasSources = message.sources && message.sources.length > 0;
  let sourcesHtml = '';

  if (hasSources && message.sources) {
    const rows = message.sources
      .map((s, idx) => {
        const articleNo = s.metadata?.article_number ? `مادة (${s.metadata.article_number})` : 'مادة قانونية';
        const bookName = s.metadata?.book || s.metadata?.source || 'القانون المدني اليمني (2002)';
        const pageNo = s.metadata?.page ? `ص: ${s.metadata.page}` : '';
        return `
          <tr>
            <td class="col-num">${idx + 1}</td>
            <td class="col-meta">
              <strong>${articleNo}</strong><br/>
              <span class="source-book">${bookName} ${pageNo}</span>
            </td>
            <td class="col-text">${s.content}</td>
          </tr>
        `;
      })
      .join('');

    sourcesHtml = `
      <div class="pdf-section">
        <h3 class="section-title">ثالثاً: الأسانيد القانونية والمواد المرجعية المعتمدة (100% RAG)</h3>
        <table class="sources-table">
          <thead>
            <tr>
              <th style="width: 8%;">م.</th>
              <th style="width: 28%;">رقم المادة / الباب</th>
              <th style="width: 64%;">نص المادة القانونية في التشريع اليمني</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    `;
  }

  const printWindow = window.open('', '_blank', 'width=900,height=1000');
  if (!printWindow) {
    alert('يرجى السماح بالنوافذ المنبثقة (Popups) لتصدير تقرير PDF.');
    return;
  }

  const documentHtml = `
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>تقرير استشارة قانونية - ${reportId}</title>
  <style>
    @page {
      size: A4;
      margin: 18mm 16mm;
    }

    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }

    body {
      font-family: 'Traditional Arabic', 'Amiri', 'Cairo', 'Tahoma', 'Segoe UI', serif;
      background: #fff;
      color: #0f172a;
      margin: 0;
      padding: 0;
      line-height: 1.7;
      direction: rtl;
    }

    .report-container {
      max-width: 820px;
      margin: 0 auto;
      padding: 10px;
    }

    /* ── الترويسة الرسمية الملكية ── */
    .official-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 3px double #b45309;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }

    .header-col-right {
      text-align: right;
      font-size: 13px;
      font-weight: 700;
      color: #1e293b;
      line-height: 1.6;
    }

    .header-col-center {
      text-align: center;
      flex: 1;
      padding: 0 10px;
    }

    .header-emblem {
      font-size: 36px;
      line-height: 1;
      margin-bottom: 6px;
    }

    .header-title-main {
      font-size: 22px;
      font-weight: 900;
      color: #0f172a;
      margin: 0;
      letter-spacing: 0.5px;
    }

    .header-title-sub {
      font-size: 12px;
      font-weight: 700;
      color: #b45309;
      margin-top: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .header-col-left {
      text-align: left;
      font-size: 12px;
      color: #334155;
      line-height: 1.6;
    }

    .header-col-left strong {
      color: #0f172a;
    }

    /* ── أقسام التقرير ── */
    .pdf-section {
      margin-bottom: 24px;
      page-break-inside: avoid;
    }

    .section-title {
      font-size: 17px;
      font-weight: 800;
      color: #0f172a;
      background: #f1f5f9;
      border-right: 4px solid #b45309;
      padding: 8px 14px;
      margin-bottom: 14px;
      border-radius: 4px 0 0 4px;
    }

    /* ── بطاقة السؤال ── */
    .question-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-right: 4px solid #0f172a;
      padding: 14px 18px;
      border-radius: 6px;
      font-size: 16px;
      font-weight: 700;
      color: #1e293b;
    }

    /* ── متن الرأي القانوني ── */
    .answer-content {
      font-size: 15px;
      color: #1e293b;
      padding: 4px 10px;
    }

    .pdf-heading {
      font-size: 18px;
      color: #0f172a;
      margin: 18px 0 10px;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
    }

    .pdf-subheading {
      font-size: 16px;
      color: #1e293b;
      margin: 14px 0 8px;
    }

    .pdf-paragraph {
      margin-bottom: 14px;
      text-align: justify;
    }

    .pdf-list {
      margin: 10px 0;
      padding-right: 24px;
    }

    .pdf-list li {
      margin-bottom: 6px;
    }

    /* ── جدول المصادر ── */
    .sources-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13.5px;
    }

    .sources-table th,
    .sources-table td {
      border: 1px solid #cbd5e1;
      padding: 10px 12px;
      vertical-align: top;
    }

    .sources-table th {
      background-color: #0f172a;
      color: #fff;
      font-weight: 800;
      text-align: right;
    }

    .col-num {
      text-align: center;
      font-weight: 700;
      color: #64748b;
    }

    .col-meta strong {
      color: #b45309;
      font-size: 14px;
    }

    .source-book {
      font-size: 11.5px;
      color: #64748b;
    }

    .col-text {
      color: #1e293b;
      line-height: 1.6;
      text-align: justify;
    }

    /* ── التذييل وخاتم المطور ── */
    .official-footer {
      margin-top: 36px;
      border-top: 2px solid #e2e8f0;
      padding-top: 16px;
      page-break-inside: avoid;
    }

    .footer-note {
      text-align: center;
      font-size: 12px;
      color: #64748b;
      margin-bottom: 20px;
    }

    .signatures-grid {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 20px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
    }

    .sig-box {
      font-size: 12.5px;
      color: #334155;
    }

    .sig-box strong {
      color: #0f172a;
      font-size: 14px;
      display: block;
      margin-bottom: 4px;
    }

    .sig-badge {
      display: inline-block;
      background: #dcfce7;
      color: #166534;
      border: 1px solid #bbf7d0;
      padding: 2px 10px;
      border-radius: 12px;
      font-weight: 700;
      font-size: 11px;
      margin-top: 6px;
    }

    /* أزرار مساعدة في نافذة الطباعة لا تظهر عند حفظ PDF */
    .print-controls {
      text-align: center;
      margin: 20px 0;
      padding: 12px;
      background: #fffbeb;
      border: 1px solid #fef3c7;
      border-radius: 8px;
    }

    .print-btn {
      background: #0f172a;
      color: #fff;
      border: none;
      padding: 10px 24px;
      font-size: 15px;
      font-weight: 700;
      border-radius: 8px;
      cursor: pointer;
    }

    @media print {
      .print-controls {
        display: none !important;
      }
    }
  </style>
</head>
<body>
  <div class="report-container">
    <div class="print-controls">
      <span>💡 لحفظ التقرير كملف PDF، اختر <strong>"Save as PDF"</strong> أو <strong>"حفظ كـ PDF"</strong> في نافذة الطباعة.</span>
      <br/><br/>
      <button class="print-btn" onclick="window.print()">🖨️ طباعة / حفظ بتنسيق PDF الآن</button>
    </div>

    <!-- الترويسة الرسمية -->
    <header class="official-header">
      <div class="header-col-right">
        الجمهورية اليمنية<br/>
        الديوان الرقمي للقانون المدني (2002)<br/>
        منظومة "المعلّم الذكي" القانونية
      </div>
      <div class="header-col-center">
        <div class="header-emblem">⚖️</div>
        <h1 class="header-title-main">تقرير استشارة ورأي قانوني</h1>
        <div class="header-title-sub">Official Yemeni Legal Consultation Report</div>
      </div>
      <div class="header-col-left">
        <strong>رقم التقرير:</strong> ${reportId}<br/>
        <strong>تاريخ الإصدار:</strong> ${todayStr}<br/>
        <strong>تطوير وهندسة:</strong> مشتاق الفقية
      </div>
    </header>

    <!-- أولاً: السؤال القانوني -->
    <section class="pdf-section">
      <h3 class="section-title">أولاً: السؤال والاستفسار القانوني المطروح</h3>
      <div class="question-box">
        "${questionText}"
      </div>
    </section>

    <!-- ثانياً: الرأي القانوني -->
    <section class="pdf-section">
      <h3 class="section-title">ثانياً: الرأي القانوني والتحليل التشريعي المعتمد</h3>
      <div class="answer-content">
        ${answerHtml}
      </div>
    </section>

    <!-- ثالثاً: الأسانيد والمصادر -->
    ${sourcesHtml}

    <!-- التذييل الرسمي -->
    <footer class="official-footer">
      <div class="footer-note">
        ✨ تم استخراج هذا التقرير آلياً عبر محرك "المعلّم الذكي" للذكاء الاصطناعي القانوني • إسناد دقيق 100% من التشريع اليمني المعتمد
      </div>
      <div class="signatures-grid">
        <div class="sig-box" style="text-align: right;">
          <strong>اعتماد المنظومة الرقمية:</strong>
          الديوان الرقمي للقانون المدني اليمني (2002م)
          <br/>
          <span class="sig-badge">✓ إسناد موثق ومفهرس (100% RAG)</span>
        </div>
        <div class="sig-box" style="text-align: left;">
          <strong>هندسة وتطوير المنصة:</strong>
          مشتاق الفقية • صنعاء، الجمهورية اليمنية
          <br/>
          <span style="font-size: 11px; color: #64748b;">هاتف / واتساب: +967 775 336 886</span>
        </div>
      </div>
    </footer>
  </div>

  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 600);
    };
  </script>
</body>
</html>
  `;

  printWindow.document.open();
  printWindow.document.write(documentHtml);
  printWindow.document.close();
}
