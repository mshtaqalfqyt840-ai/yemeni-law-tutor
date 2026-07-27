import React from 'react';
import type { SystemStats } from '../types';

interface TopBarProps {
  stats: SystemStats;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  onReset: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  stats,
  sidebarOpen,
  onToggleSidebar,
  onReset
}) => {
  return (
    <header className="diwan-top-bar">
      <div className="top-bar-brand">
        <button
          onClick={onToggleSidebar}
          style={{
            background: sidebarOpen ? 'rgba(223, 176, 89, 0.2)' : 'transparent',
            border: 'none',
            color: '#dfb059',
            cursor: 'pointer',
            padding: '4px',
            display: 'flex',
            alignItems: 'center',
            borderRadius: '8px'
          }}

          title="تبديل الشريط الجانبي"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <div className="top-bar-logo-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
            <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
            <path d="M7 21h10"/>
            <path d="M12 3v18"/>
            <path d="M3 7h18"/>
          </svg>
        </div>

        <div className="top-bar-title-group">
          <h1>المعلّم <span>الذكي</span></h1>
          <small>الديوان الرقمي للقانون المدني اليمني (2002)</small>
        </div>
      </div>

      <div className="top-bar-actions">
        <div className="status-pill">
          <span className="status-dot" />
          <span>{stats.status} • {stats.total_docs.toLocaleString()} مادة</span>
        </div>
        <div className="ai-badge">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
          <span>معزّز بـ {stats.engine}</span>
        </div>
        <button
          onClick={onReset}
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            color: '#fca5a5',
            padding: '6px 12px',
            borderRadius: '10px',
            cursor: 'pointer',
            fontSize: '0.8rem',
            fontWeight: 700
          }}
          title="مسح المحادثة وبدء استشارة جديدة"
        >
          🗑️ جديد
        </button>
      </div>
    </header>
  );
};
