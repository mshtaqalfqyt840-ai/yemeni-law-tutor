import React, { useState } from 'react';
import type { SourceDocument } from '../types';

interface SourceCardProps {
  sources: SourceDocument[];
}

export const SourceCard: React.FC<SourceCardProps> = ({ sources }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="source-accordion">
      <div className="source-header" onClick={() => setIsOpen(!isOpen)}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>📜 السجل القانوني والمصادر الرسمية المعتمدة ({sources.length} مراجع)</span>
        </span>
        <span style={{ fontSize: '1rem' }}>
          {isOpen ? '▲' : '▼'}
        </span>
      </div>

      {isOpen && (
        <div className="source-body">
          {sources.map((doc, idx) => {
            const artNum = doc.metadata?.article_number || '؟';
            const book = doc.metadata?.book || '';
            return (
              <div key={idx} className="source-card">
                <div className="source-meta-bar" style={{ justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="art-badge">مادة ({artNum})</span>
                    {book && <span className="book-badge">• {book}</span>}
                  </div>
                  <button
                    onClick={() => handleCopy(doc.content, idx)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      color: '#cbd5e1',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      fontWeight: 700
                    }}
                  >
                    {copiedIdx === idx ? '✔️ تم النسخ' : '📋 نسخ النص'}
                  </button>
                </div>
                <div className="source-quote">{doc.content}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
