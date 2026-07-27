import React from 'react';

export const HeroBanner: React.FC = () => {
  return (
    <div className="hero-banner">
      <svg className="hero-watermark" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
        <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
        <path d="M7 21h10" />
        <path d="M12 3v18" />
        <path d="M3 7h18" />
      </svg>

      <div className="hero-eyebrow">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
        <span>الديوان الرقمي • المرجع الذكي الأول للقانون المدني</span>
      </div>

      <h1 className="hero-title">
        المعلّم الذكي <span>للقانون المدني اليمني</span>
      </h1>

      <p className="hero-desc">
        منصة تفاعلية موثّقة لتقديم الشروح والاستشارات الأكاديمية المستندة{' '}
        <strong>حصرياً</strong> على النص الرسمي للقرار الجمهوري بالقانون رقم (14) لسنة 2002م، دون هلوسة أو اجتهاد خارجي.
      </p>

      <div className="trust-badges-row">
        <div className="trust-badge">
          <span className="trust-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <polyline points="9 12 11 14 15 10" />
            </svg>
          </span>
          <span>إسناد نصي حرفي موثّق 100%</span>
        </div>
        <div className="trust-badge">
          <span className="trust-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </span>
          <span>1,385 مادة قانونية مفهرسة</span>
        </div>
        <div className="trust-badge">
          <span className="trust-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </span>
          <span>بحث دلالي فوري فائق الدقة</span>
        </div>
        <div className="trust-badge">
          <span className="trust-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2v20" />
              <path d="m17 5-5-3-5 3" />
              <path d="m17 19-5 3-5-3" />
              <path d="M2 12h20" />
            </svg>
          </span>
          <span>خالٍ من الهلوسة والاجتهاد</span>
        </div>
      </div>

      <div className="legal-warning-banner" style={{ marginTop: '10px' }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <div>
          <strong>تنبيه قانوني هام:</strong> الإجابات المقدمة هي لأغراض الدراسة والتعليم والأبحاث الأكاديمية فقط، ولا تُعد استشارة قانونية رسمية ملزمة. يُرجى مراجعة محامٍ مرخص أو قاضٍ متخصص عند معالجة القضايا الفعلية.
        </div>
      </div>
    </div>
  );
};
