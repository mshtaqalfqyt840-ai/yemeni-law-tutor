import React from 'react';
import type { SystemStats, SavedChat } from '../types';

interface SidebarProps {
  stats: SystemStats;
  isOpen: boolean;
  onReset: () => void;
  savedChats: SavedChat[];
  activeChatId: string;
  onSelectSavedChat: (chat: SavedChat) => void;
  onDeleteSavedChat: (e: React.MouseEvent, chatId: string) => void;
  onOpenDevModal?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  stats,
  isOpen,
  onReset,
  savedChats,
  activeChatId,
  onSelectSavedChat,
  onDeleteSavedChat,
  onOpenDevModal
}) => {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      {/* ── رأس القائمة مع زر محادثة جديدة على طريقة ChatGPT ── */}
      <div className="sidebar-header-chatgpt">
        <button className="new-chat-btn-chatgpt" onClick={onReset}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>محادثة جديدة</span>
        </button>
      </div>

      {/* ── قائمة المحادثات المحفوظة (سجل الاستشارات) ── */}
      <div className="sidebar-topics-list">
        <div className="sidebar-section-label">
          <span>المحادثات المحفوظة</span>
          {savedChats.length > 0 && <span className="saved-badge-count">{savedChats.length}</span>}
        </div>

        {savedChats.length === 0 ? (
          <div className="sidebar-empty-history">
            <span className="empty-icon">💬</span>
            <p className="empty-text">لا توجد محادثات محفوظة بعد.</p>
            <small className="empty-sub">ابدأ استشارتك ليتم حفظها تلقائياً</small>
          </div>
        ) : (
          savedChats.map((chat) => {
            const isActive = chat.id === activeChatId;
            return (
              <div
                key={chat.id}
                className={`sidebar-saved-chat-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectSavedChat(chat)}
              >
                <div className="saved-chat-content">
                  <span className="saved-chat-icon">💬</span>
                  <div className="saved-chat-text">
                    <span className="saved-chat-title" title={chat.title}>
                      {chat.title}
                    </span>
                    <span className="saved-chat-date">{chat.date}</span>
                  </div>
                </div>

                <button
                  className="saved-chat-delete-btn"
                  onClick={(e) => onDeleteSavedChat(e, chat.id)}
                  title="حذف هذه المحادثة"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* ── تذييل القائمة الجانبية (حالة المحرك ومصادر القانون) ── */}
      <div className="sidebar-footer-chatgpt">
        {onOpenDevModal && (
          <button
            className="sidebar-dev-btn"
            onClick={onOpenDevModal}
            title="عرض بطاقة المطور مشتاق الفقية"
          >
            <span>👨‍💻 خيار المطور • مشتاق الفقية</span>
          </button>
        )}
        <div className="sidebar-status-pill">
          <span className="status-dot"></span>
          <span>متصل • القانون المدني (2002م)</span>
        </div>
        <div className="sidebar-stats-compact">
          <div className="stat-row">
            <span>المواد المفهرسة:</span>
            <strong>{stats.total_docs.toLocaleString()} مادة</strong>
          </div>
          <div className="stat-row">
            <span>دقة الإسناد:</span>
            <strong>{stats.accuracy} (100% RAG)</strong>
          </div>
          <div className="stat-row">
            <span>المحرك الذكي:</span>
            <strong>Gemini Flash</strong>
          </div>
        </div>
      </div>
    </aside>
  );
};
