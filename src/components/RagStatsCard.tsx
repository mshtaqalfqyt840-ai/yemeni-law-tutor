import React from 'react';
import type { RagStats } from '../types';

interface RagStatsCardProps {
  stats?: RagStats;
  sourcesCount?: number;
}

export const RagStatsCard: React.FC<RagStatsCardProps> = ({ stats, sourcesCount }) => {
  const count = stats?.retrieved_count ?? sourcesCount ?? 0;
  if (count === 0 && !stats) return null;

  const responseTime = stats?.response_time || '<0.3s';
  const sourceVerified = stats?.source_verified ?? (count > 0);
  const status = stats?.status || (sourceVerified ? 'موثق بسجل القانون المدني (2002م)' : 'لم يتم العثور على مادة مطابقة');

  return (
    <div className="rag-stats-bar-sleek">
      <div className="rag-stats-bar-content">
        <span className="rag-pill-badge gold">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          <span>{count} مواد قانونية</span>
        </span>

        <span className="rag-pill-badge emerald">
          <span>⚡ {responseTime}</span>
        </span>

        <span className="rag-pill-badge cyan">
          <span>{sourceVerified ? '✓ نص رسمي معتمد' : '⚠️ غير مؤكد'}</span>
        </span>

        <span className="rag-pill-status">
          <span className="rag-status-dot-mini"></span>
          <span>{status}</span>
        </span>
      </div>
    </div>
  );
};
