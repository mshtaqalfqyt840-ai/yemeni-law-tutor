import React, { useState, useEffect, useRef } from 'react';
import type {
  Message,
  SystemStats,
  SuggestionItem,
  SourceDocument
} from './types';
import {
  fetchStats,
  fetchSuggestions,
  streamChat,
  DEFAULT_STATS,
  DEFAULT_SUGGESTIONS
} from './services/api';
import { TopBar } from './components/TopBar';
import { Sidebar } from './components/Sidebar';
import { HeroBanner } from './components/HeroBanner';
import { SuggestionCards } from './components/SuggestionCards';
import { ChatMessageItem } from './components/ChatMessageItem';
import { ChatInput } from './components/ChatInput';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [stats, setStats] = useState<SystemStats>(DEFAULT_STATS);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>(DEFAULT_SUGGESTIONS);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchStats().then(setStats);
    fetchSuggestions().then(setSuggestions);
  }, []);

  useEffect(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendPrompt = (prompt: string) => {
    if (!prompt.trim() || isLoading) return;

    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `assistant_${Date.now() + 1}`;

    const newUserMsg: Message = {
      id: userMsgId,
      role: 'user',
      content: prompt,
      timestamp: new Date().toLocaleTimeString('ar-YE')
    };

    const emptyAssistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      sources: [],
      timestamp: new Date().toLocaleTimeString('ar-YE'),
      isStreaming: true
    };

    const updatedMessages = [...messages, newUserMsg, emptyAssistantMsg];
    setMessages(updatedMessages);
    setIsLoading(true);

    streamChat(
      prompt,
      messages,
      // onMetadata
      (sources: SourceDocument[]) => {
        setMessages(prev =>
          prev.map(m => (m.id === assistantMsgId ? { ...m, sources } : m))
        );
      },
      // onToken
      (token: string) => {
        setMessages(prev =>
          prev.map(m => (m.id === assistantMsgId ? { ...m, content: m.content + token } : m))
        );
      },
      // onDone
      () => {
        setMessages(prev =>
          prev.map(m => (m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
        );
        setIsLoading(false);
      },
      // onError
      (err: string) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantMsgId
              ? { ...m, content: m.content || `❌ حدث خطأ: ${err}`, isStreaming: false }
              : m
          )
        );
        setIsLoading(false);
      }
    );
  };

  const handleReset = () => {
    setMessages([]);
    setIsLoading(false);
  };

  return (
    <div className="app-container">
      <TopBar
        stats={stats}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onReset={handleReset}
      />

      <Sidebar
        stats={stats}
        isOpen={sidebarOpen}
        onSelectPrompt={handleSendPrompt}
        onReset={handleReset}
      />

      <main className="main-content">
        <div className="chat-viewport" ref={viewportRef}>
          <div className="chat-content-max">
            {messages.length === 0 ? (
              <>
                <HeroBanner />
                <SuggestionCards
                  suggestions={suggestions}
                  onSelectPrompt={handleSendPrompt}
                />
              </>
            ) : (
              messages.map((message) => (
                <ChatMessageItem key={message.id} message={message} />
              ))
            )}
          </div>
        </div>

        <ChatInput onSend={handleSendPrompt} disabled={isLoading} />
      </main>
    </div>
  );
};

export default App;
