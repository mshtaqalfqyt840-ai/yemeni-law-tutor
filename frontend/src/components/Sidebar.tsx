import React from 'react';
import type { SystemStats } from '../types';

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
