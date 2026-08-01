import React, { useState, useEffect } from 'react';

interface DeveloperModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DeveloperModal: React.FC<DeveloperModalProps> = ({
  isOpen,
  onClose
}) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => {
      setCopiedField(null);
    }, 2500);
  };

  return (
    <div className="dev-modal-overlay" onClick={onClose}>
      <div
        className="dev-modal-card glass-luxury"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── رأس النافذة ── */}
        <div className="dev-modal-header">
          <div className="dev-modal-title">
            <span className="dev-badge-icon">👨‍💻</span>
            <span>بطاقة المطور ومهندس النظام</span>
          </div>
          <button className="dev-modal-close" onClick={onClose} title="إغلاق النافذة">
            &times;
          </button>
        </div>

        {/* ── الملف الشخصي والصورة ── */}
        <div className="dev-hero-section">
          <div className="dev-avatar-wrapper">
            <img
              src="/mushtaq_profile.jpg"
              alt="المطور مشتاق الفقية"
              className="dev-avatar-img"
              onError={(e) => {
                // في حال عدم تحميل الصورة نعرض رمز افتراضي
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <div className="dev-status-badge">
              <span className="status-dot-green"></span>
              <span>متاح للتطوير</span>
            </div>
          </div>

          <div className="dev-info-header">
            <h2 className="dev-name-gold">مشتاق الفقية</h2>
            <p className="dev-subtitle">
              مطور برمجيات وذكاء اصطناعي • مهندس منظومة القانون اليمني الذكي
            </p>
            <div className="dev-location-pill">
              <span>📍</span>
              <span>صنعاء، الجمهورية اليمنية</span>
            </div>
          </div>
        </div>

        {/* ── بطاقات الاتصال والتواصل الفوري ── */}
        <div className="dev-contact-grid">
          {/* واتساب / الهاتف */}
          <div className="dev-contact-box">
            <div className="dev-box-icon whatsapp">💬</div>
            <div className="dev-box-details">
              <span className="dev-box-label">رقم الهاتف / واتساب</span>
              <strong className="dev-box-value" dir="ltr">+967 775 336 886</strong>
            </div>
            <div className="dev-box-actions">
              <a
                href="https://wa.me/967775336886"
                target="_blank"
                rel="noopener noreferrer"
                className="dev-btn-action whatsapp-btn"
                title="مراسلة واتساب الفورية"
              >
                واتساب 🚀
              </a>
              <a
                href="tel:+967775336886"
                className="dev-btn-action call-btn"
                title="اتصال مباشر"
              >
                اتصال 📞
              </a>
              <button
                className={`dev-btn-action copy-btn ${copiedField === 'phone' ? 'copied' : ''}`}
                onClick={() => handleCopy('+967775336886', 'phone')}
              >
                {copiedField === 'phone' ? '✓ تم النسخ' : '📋 نسخ'}
              </button>
            </div>
          </div>

          {/* البريد الإلكتروني */}
          <div className="dev-contact-box">
            <div className="dev-box-icon email">📧</div>
            <div className="dev-box-details">
              <span className="dev-box-label">البريد الإلكتروني</span>
              <strong className="dev-box-value">mshtaqalfqyt840@gmail.com</strong>
            </div>
            <div className="dev-box-actions">
              <a
                href="mailto:mshtaqalfqyt840@gmail.com"
                className="dev-btn-action email-btn"
                title="إرسال رسالة بريد إلكتروني"
              >
                إرسال ✉️
              </a>
              <button
                className={`dev-btn-action copy-btn ${copiedField === 'email' ? 'copied' : ''}`}
                onClick={() => handleCopy('mshtaqalfqyt840@gmail.com', 'email')}
              >
                {copiedField === 'email' ? '✓ تم النسخ' : '📋 نسخ'}
              </button>
            </div>
          </div>
        </div>

        {/* ── مميزات التطوير والتقنيات ── */}
        <div className="dev-skills-section">
          <div className="dev-skills-title">🌟 تقنيات ومميزات المنصة المطوّرة:</div>
          <div className="dev-skills-badges">
            <span className="dev-badge gold">⚖️ القانون المدني اليمني (100% RAG)</span>
            <span className="dev-badge cyan">⚡ استرجاع فوري للوثائق القانونية</span>
            <span className="dev-badge purple">🤖 Gemini Flash الذكي</span>
            <span className="dev-badge emerald">🛡️ واجهة ديوان زجاجية فاخرة</span>
          </div>
        </div>

        {/* ── تذييل وبصمة المطور ── */}
        <div className="dev-modal-footer">
          <p>
            ✨ <strong>تم التطوير والتصميم بكل شغف وإتقان في صنعاء</strong> لخدمة المحامين والقضاة وطلاب القانون في اليمن.
          </p>
        </div>
      </div>
    </div>
  );
};
