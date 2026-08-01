import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../types';
import { SourceCard } from './SourceCard';
import { RagStatsCard } from './RagStatsCard';
import { exportConsultationAsPDF } from '../utils/pdfExport';

interface ChatMessageItemProps {
  message: Message;
  userQuestion?: string;
  onSelectPrompt?: (prompt: string) => void;
}

function cleanMarkdownForSpeech(text: string): string {
  if (!text) return '';
  return text
    .replace(/#+\s/g, '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`.*?`/g, '')
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
    .replace(/\n+/g, ' ')
    .trim();
}

function getFollowUpSuggestions(content: string): string[] {
  if (!content) return [];
  const text = content.toLowerCase();

  if (text.includes("عقد") || text.includes("بيع") || text.includes("شراء") || text.includes("تراضي")) {
    return [
      "ما هي شروط بطلان العقد في القانون اليمني؟",
      "هل يجوز الفسخ بالتراضي وكيف يتم؟",
      "ما هي التزامات البائع والمشتري عند التسليم؟"
    ];
  }
  if (text.includes("إرادة") || text.includes("غلط") || text.includes("تدليس") || text.includes("إكراه") || text.includes("استغلال")) {
    return [
      "ما الفرق بين الغلط والتدليس في القانون؟",
      "متى يسقط الحق في إبطال العقد بسبب الإكراه؟",
      "ما هي شروط تحقق الاستغلال أو الغبن؟"
    ];
  }
  if (text.includes("كفالة") || text.includes("ضمان") || text.includes("دين") || text.includes("دائن")) {
    return [
      "هل يجوز للكفيل الرجوع على المدين الأصلي؟",
      "ما هي حالات انقضاء الكفالة وبراءة الذمة؟",
      "ما هي شروط مطالبة الكفيل بالدين؟"
    ];
  }
  if (text.includes("أهلية") || text.includes("رشد") || text.includes("صغير") || text.includes("قاصر")) {
    return [
      "ما هي تصرفات الصبي المميز وغير المميز؟",
      "متى يبلغ الشخص سن الرشد القانوني في اليمن؟",
      "ما حكم تصرفات المجنون أو المعتوه؟"
    ];
  }
  if (text.includes("تعويض") || text.includes("ضرر") || text.includes("مسؤولية") || text.includes("خطأ")) {
    return [
      "ما هي أركان المسؤولية التقصيرية في القانون؟",
      "كيف يتم تقدير التعويض عن الضرر المادي والمعنوي؟",
      "هل يجوز الإعفاء من المسؤولية بالاتفاق؟"
    ];
  }

  return [
    "ما هي أركان العقد وشروط صحته وفقاً للقانون المدني؟",
    "اشرح لي المادة (138) من القانون المدني بالأمثلة",
    "ما هي عيوب الإرادة وأثرها القانوني في اليمن؟"
  ];
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message, userQuestion, onSelectPrompt }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const followUpSuggestions = (!isUser && !message.isStreaming && message.content.length > 5)
    ? getFollowUpSuggestions(message.content)
    : [];

  useEffect(() => {
    return () => {
      if (isSpeaking && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [isSpeaking]);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleToggleSpeech = () => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      alert('عذراً، متصفحك لا يدعم خاصية القراءة الصوتية (Web Speech API).');
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const textToSpeak = cleanMarkdownForSpeech(message.content);
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = 'ar-SA';
    utterance.rate = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const arabicVoice = voices.find(v => v.lang.startsWith('ar') || v.lang.includes('AR'));
    if (arabicVoice) {
      utterance.voice = arabicVoice;
    }

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className={`message-row ${message.role}`}>
      <div className="avatar-box">
        {isUser ? '👤' : '⚖️'}
      </div>

      <div className="bubble-container">
        {/* 1. المحتوى الأساسي للإجابة (يظهر أولاً وطوالي) */}
        <div className="message-bubble">
          {isUser ? (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          ) : (
            <div className="markdown-content">
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {message.isStreaming && <span className="streaming-cursor" />}
            </div>
          )}
        </div>

        {/* 2. إحصائيات RAG الفورية ومصادر القانون (تظهر بعد الإجابة وبشكل مضغوط/قابل للطي) */}
        {!isUser &&
          ((message.rag_stats && message.rag_stats.retrieved_count > 0) ||
            (message.sources && message.sources.length > 0)) && (
            <RagStatsCard
              stats={message.rag_stats}
              sourcesCount={message.sources?.length}
            />
          )}

        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceCard sources={message.sources} />
        )}

        {/* 3. شريط أدوات الرسالة (نسخ النص، استماع صوتي، وتصدير كتقرير PDF) */}
        {!isUser && !message.isStreaming && message.content.length > 5 && (
          <div className="message-actions-toolbar">
            <button
              type="button"
              className={`msg-action-btn copy-msg-btn ${copied ? 'copied' : ''}`}
              onClick={handleCopy}
              title="نسخ نص الإجابة القانونية"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              <span>{copied ? '✓ تم النسخ' : '📋 نسخ النص'}</span>
            </button>

            <button
              type="button"
              className={`msg-action-btn tts-msg-btn ${isSpeaking ? 'speaking' : ''}`}
              onClick={handleToggleSpeech}
              title={isSpeaking ? 'إيقاف القراءة الصوتية' : 'استماع صوتي للنص القانوني (Web Speech API)'}
            >
              {isSpeaking ? (
                <>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="6" y="4" width="4" height="16" rx="1"/>
                    <rect x="14" y="4" width="4" height="16" rx="1"/>
                  </svg>
                  <span>⏸️ إيقاف القراءة</span>
                </>
              ) : (
                <>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                  </svg>
                  <span>🔊 استماع صوتي</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="msg-action-btn pdf-export-btn"
              onClick={() => exportConsultationAsPDF(message, userQuestion)}
              title="تصدير هذه الاستشارة القانونية مع أسانيدها كملف PDF رسمي معتمد"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <path d="M12 18v-6"/>
                <path d="m9 15 3 3 3-3"/>
              </svg>
              <span>📄 تصدير كتقرير PDF رسمي</span>
            </button>
          </div>
        )}

        {/* 4. أسئلة واقتراحات ذات صلة في آخر المحادثة (ChatGPT Style Follow-ups) */}
        {!isUser && followUpSuggestions.length > 0 && onSelectPrompt && (
          <div className="message-followup-suggestions">
            <div className="followup-header">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
              </svg>
              <span>أسئلة واقتراحات ذات صلة بالموضوع:</span>
            </div>
            <div className="followup-pills-row">
              {followUpSuggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  className="followup-pill-btn"
                  onClick={() => onSelectPrompt(suggestion)}
                  type="button"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
