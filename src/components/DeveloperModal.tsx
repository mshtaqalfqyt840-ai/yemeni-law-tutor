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
        className="dev-modal-card sci-fi-cockpit"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── زوايا المركبة الفضائية (Sci-Fi HUD Corner Brackets) ── */}
        <div className="hud-corner top-left"></div>
        <div className="hud-corner top-right"></div>
        <div className="hud-corner bottom-left"></div>
        <div className="hud-corner bottom-right"></div>

        {/* ── شريط الحالة الفضائي العلوى (Sci-Fi HUD Top Bar) ── */}
        <div className="hud-top-telemetry">
          <span className="hud-telemetry-item">
            <span className="status-dot-green"></span>
            <strong>COCKPIT:</strong> YEMEN-AI-01
          </span>
          <span className="hud-telemetry-item">
            <strong>SEC-LEVEL:</strong> ALPHA-5
          </span>
          <span className="hud-telemetry-item cyan-pulse">
            <strong>SYSTEM:</strong> RAG MATRIX ONLINE
          </span>
        </div>

        {/* ── رأس النافذة ── */}
        <div className="dev-modal-header">
          <div className="dev-modal-title">
            <span className="dev-badge-icon pulse-glow">🛰️</span>
            <span>مركز قيادة المطور ومهندس المنظومة</span>
          </div>
          <button className="dev-modal-close sci-fi-close" onClick={onClose} title="إغلاق النافذة">
            &times;
          </button>
        </div>

        {/* ── الملف الشخصي الهولوغرامي (Hologram Profile Hero) ── */}
        <div className="dev-hero-section">
          <div className="dev-avatar-wrapper sci-fi-avatar">
            {/* الحلقات المدارية المتحركة للمركبة الفضائية */}
            <div className="orbital-ring ring-outer"></div>
            <div className="orbital-ring ring-inner"></div>
            <div className="cyber-scanner-beam"></div>

            <img
              src="/mushtaq_profile.jpg"
              alt="المطور مشتاق الفقية"
              className="dev-avatar-img"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <div className="dev-status-badge sci-fi-status">
              <span className="status-dot-green"></span>
              <span>AI CHIEF ARCHITECT</span>
            </div>
          </div>

          <div className="dev-info-header">
            <h2 className="dev-name-gold sci-fi-title">مشتاق الفقية</h2>
            <div className="dev-role-tag">
              ⚡ مهندس برمجيات وذكاء اصطناعي • مصمم معمارية القرار الجمهوري رقم 14
            </div>
            <div className="dev-location-pill sci-fi-location">
              <span>🛰️ BASE: صنعاء، الجمهورية اليمنية</span>
              <span className="telemetry-coords" dir="ltr">[ 15.3694° N, 44.1910° E ]</span>
            </div>
          </div>
        </div>

        {/* ── وحدات الاتصال الفضائية (Spaceship Comm Pods) ── */}
        <div className="dev-contact-grid">
          {/* وحدة الهاتف / واتساب */}
          <div className="dev-contact-box sci-fi-pod">
            <div className="dev-box-icon whatsapp pulse-icon">💬</div>
            <div className="dev-box-details">
              <span className="dev-box-label">COMMS / TELEPHONE & WHATSAPP</span>
              <strong className="dev-box-value" dir="ltr">+967 775 336 886</strong>
            </div>
            <div className="dev-box-actions">
              <a
                href="https://wa.me/967775336886"
                target="_blank"
                rel="noopener noreferrer"
                className="dev-btn-action whatsapp-btn sci-fi-btn"
                title="مراسلة واتساب الفورية"
              >
                واتساب 🚀
              </a>
              <a
                href="tel:+967775336886"
                className="dev-btn-action call-btn sci-fi-btn"
                title="اتصال مباشر"
              >
                اتصال 📞
              </a>
              <button
                className={`dev-btn-action copy-btn sci-fi-btn ${copiedField === 'phone' ? 'copied' : ''}`}
                onClick={() => handleCopy('+967775336886', 'phone')}
              >
                {copiedField === 'phone' ? '✓ تم النسخ' : '📋 نسخ'}
              </button>
            </div>
          </div>

          {/* وحدة البريد الإلكتروني (معدلة بالشكل الصحيح) */}
          <div className="dev-contact-box sci-fi-pod email-pod">
            <div className="dev-box-icon email pulse-icon">📧</div>
            <div className="dev-box-details">
              <span className="dev-box-label">SECURE EMAIL TRANSMISSION</span>
              <strong className="dev-box-value email-value">mushtaq.alfaqih.ai@gmail.com</strong>
            </div>
            <div className="dev-box-actions">
              <a
                href="mailto:mushtaq.alfaqih.ai@gmail.com"
                className="dev-btn-action email-btn sci-fi-btn"
                title="إرسال رسالة بريد إلكتروني"
              >
                إرسال ✉️
              </a>
              <button
                className={`dev-btn-action copy-btn sci-fi-btn ${copiedField === 'email' ? 'copied' : ''}`}
                onClick={() => handleCopy('mushtaq.alfaqih.ai@gmail.com', 'email')}
              >
                {copiedField === 'email' ? '✓ تم النسخ' : '📋 نسخ'}
              </button>
            </div>
          </div>
        </div>

        {/* ── محرك المنظومة ومصفوفة التقنيات (Spaceship Engine Core Matrix) ── */}
        <div className="dev-skills-section sci-fi-matrix">
          <div className="dev-skills-header">
            <span className="matrix-icon">⚙️</span>
            <span className="dev-skills-title">TECH SPECIFICATIONS & RAG ENGINE MATRIX:</span>
            <span className="matrix-status">100% OPERATIONAL</span>
          </div>
          <div className="dev-skills-badges">
            <span className="dev-badge sci-fi-badge gold">⚖️ Yemeni Civil Law (2002m) RAG Core</span>
            <span className="dev-badge sci-fi-badge cyan">⚡ Warp Speed Search (&lt; 0.3s)</span>
            <span className="dev-badge sci-fi-badge purple">🧠 Google Gemini Flash Neural AI</span>
            <span className="dev-badge sci-fi-badge emerald">🛡️ Zero Hallucination Shield</span>
            <span className="dev-badge sci-fi-badge neon-blue">🛰️ ChromaDB Vector Telemetry</span>
            <span className="dev-badge sci-fi-badge orange">📡 Realtime SSE Hologram Stream</span>
          </div>
        </div>

        {/* ── تذييل وبصمة المطور ── */}
        <div className="dev-modal-footer sci-fi-footer">
          <div className="footer-hud-line"></div>
          <p>
            ✨ <strong>DESIGNED & ARCHITECTED IN SANAA</strong> • YEMENI CIVIL LAW DIGITAL DIWAN
          </p>
        </div>
      </div>
    </div>
  );
};

