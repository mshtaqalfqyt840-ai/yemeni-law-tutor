import React, { useState } from 'react';
import type { SystemStats } from '../types';
import { saveApiKey } from '../services/api';

interface SidebarProps {
  stats: SystemStats;
  isOpen: boolean;
  onSelectPrompt: (prompt: string) => void;
  onReset: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  stats,
  isOpen,
  onSelectPrompt,
  onReset
}) => {
  const [apiKey, setApiKey] = useState('');
  const [keyStatus, setKeyStatus] = useState<{ success?: boolean; message?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;
    setIsSubmitting(true);
    const res = await saveApiKey(apiKey.trim());
    setKeyStatus(res);
    setIsSubmitting(false);
    if (res.success) {
      setApiKey('');
    }
  };

  const quickPills = ["138", "مادة (15)", "أركان العقد", "عيوب الإرادة", "الكفالة"];

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <h2 className="sidebar-brand-title">المعلّم <span>الذكي</span></h2>
        <p className="sidebar-brand-sub">
          الديوان الرقمي للقانون المدني اليمني<br />
          القرار الجمهوري رقم (14) لسنة 2002م
        </p>
      </div>

      {/* 🗝️ قسم مفتاح الذكاء الاصطناعي (Gemini API) */}
      <div className="sidebar-api-key-box" style={{
        background: 'rgba(13, 21, 38, 0.75)',
        border: '1px solid var(--border-glass)',
        borderRadius: '12px',
        padding: '12px 14px',
        margin: '10px 0'
      }}>
        <p className="sidebar-stats-title" style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          🔑 <span>مفتاح Gemini API</span>
        </p>
        <form onSubmit={handleSaveKey} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <input
            type="password"
            name="gemini-api-key"
            autoComplete="new-password"
            placeholder="AIzaSy... أو AQ..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid rgba(223, 176, 89, 0.3)',
              background: 'rgba(6, 11, 20, 0.8)',
              color: '#fff',
              fontSize: '0.85rem',
              outline: 'none'
            }}
          />
          <button
            type="submit"
            disabled={isSubmitting || !apiKey.trim()}
            style={{
              padding: '8px 12px',
              borderRadius: '8px',
              border: 'none',
              background: 'linear-gradient(135deg, #dfb059 0%, #b8860b 100%)',
              color: '#060b14',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: apiKey.trim() ? 'pointer' : 'not-allowed',
              opacity: apiKey.trim() ? 1 : 0.6
            }}
          >
            {isSubmitting ? 'جاري الحفظ...' : 'تفعيل المفتاح ✨'}
          </button>
        </form>
        {keyStatus.message && (
          <p style={{
            fontSize: '0.78rem',
            marginTop: '8px',
            color: keyStatus.success ? '#10b981' : '#f87171',
            lineHeight: 1.4
          }}>
            {keyStatus.message}
          </p>
        )}
        <a
          href="https://aistudio.google.com/app/apikey"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            fontSize: '0.75rem',
            color: 'var(--text-gold)',
            marginTop: '8px',
            textDecoration: 'underline'
          }}
        >
          💡 احصل على مفتاح مجاني من Google AI Studio
        </a>
      </div>

      <div>
        <p className="sidebar-stats-title">📊 إحصائيات وأداء النظام</p>
        <div className="sidebar-stats-grid" style={{ marginTop: '10px' }}>
          <div className="stat-card">
            <span className="stat-num">{stats.total_docs.toLocaleString()}</span>
            <span className="stat-lbl">مادة مفهرسة</span>
          </div>
          <div className="stat-card">
            <span className="stat-num">{stats.accuracy}</span>
            <span className="stat-lbl">دقة الإسناد</span>
          </div>
          <div className="stat-card">
            <span className="stat-num">{stats.response_time}</span>
            <span className="stat-lbl">سرعة الاسترجاع</span>
          </div>
          <div className="stat-card">
            <span className="stat-num">{stats.engine}</span>
            <span className="stat-lbl">المحرك الذكي</span>
          </div>
        </div>
      </div>

      <div className="sidebar-tip-card">
        <div className="tip-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M9 18h6" />
            <path d="M10 22h4" />
            <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14" />
          </svg>
          <span>تلميح التأصيل السريع</span>
        </div>
        <p>اكتب رقم المادة مباشرة أو اختر من الأزرار أدناه لاستحضار نصها القانوني وشرحها فوراً:</p>
        <div className="tip-pills">
          {quickPills.map((pill, idx) => (
            <button
              key={idx}
              className="tip-pill-btn"
              onClick={() => onSelectPrompt(pill)}
            >
              {pill}
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-footer">
        <button className="reset-chat-btn" onClick={onReset}>
          🗑️ مسح المحادثة والبدء من جديد
        </button>
      </div>
    </aside>
  );
};
