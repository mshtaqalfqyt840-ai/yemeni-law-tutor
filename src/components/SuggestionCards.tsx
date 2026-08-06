import React from 'react';
import type { SuggestionItem } from '../types';

interface SuggestionCardsProps {
  suggestions: SuggestionItem[];
  onSelectPrompt: (prompt: string) => void;
}

export const SuggestionCards: React.FC<SuggestionCardsProps> = ({
  suggestions,
  onSelectPrompt
}) => {
  return (
    <div className="suggestions-wrapper">
      <div className="suggestions-title">
        <span style={{ color: 'var(--accent-gold)', display: 'flex' }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
          </svg>
        </span>
        <div>
          <span>نماذج أسئلة واستشارات قانونية شائعة للبدء</span>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 400, marginTop: '4px' }}>
            اختر أياً من الاستشارات والمواد القانونية الفورية أدناه للحصول على إجابة موثقة، أو اكتب سؤالك الخاص في شريط المحادثة
          </p>
        </div>
      </div>

      <div className="suggestions-grid">
        {suggestions.map((sug) => (
          <div
            key={sug.id}
            className={`suggestion-card ${sug.accent_class}`}
            onClick={() => onSelectPrompt(sug.prompt)}
          >
            <div className="sug-card-header">
              <div
                className="sug-icon-box"
                dangerouslySetInnerHTML={{ __html: sug.svg_icon }}
              />
              <span className="sug-badge">{sug.category}</span>
            </div>

            <h3 className="sug-title">{sug.title}</h3>
            <p className="sug-subtext">{sug.subtext}</p>

            <div className="sug-btn">
              <span>{sug.btn_label}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 5 12 12 19" />
              </svg>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
