import React from 'react';
import type { Message } from '../types';
import { SourceCard } from './SourceCard';

interface ChatMessageItemProps {
  message: Message;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`message-row ${message.role}`}>
      <div className="avatar-box">
        {isUser ? '👤' : '⚖️'}
      </div>

      <div className="bubble-container">
        <div className="message-bubble">
          <div style={{ whiteSpace: 'pre-wrap' }}>
            {message.content}
            {message.isStreaming && <span className="streaming-cursor" />}
          </div>
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceCard sources={message.sources} />
        )}
      </div>
    </div>
  );
};
