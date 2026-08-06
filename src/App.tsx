import React, { useState, useEffect, useRef } from 'react';
import type {
  Message,
  SystemStats,
  SuggestionItem,
  SourceDocument,
  RagStats,
  SavedChat
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
import { DeveloperModal } from './components/DeveloperModal';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [stats, setStats] = useState<SystemStats>(DEFAULT_STATS);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>(DEFAULT_SUGGESTIONS);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [devModalOpen, setDevModalOpen] = useState(false);
  const [savedChats, setSavedChats] = useState<SavedChat[]>(() => {
    try {
      const raw = localStorage.getItem('yemeni_law_saved_chats');
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });
  const [activeChatId, setActiveChatId] = useState<string>(() => `chat_${Date.now()}`);
  const viewportRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (messages.length > 0) {
      const firstUserMsg = messages.find(m => m.role === 'user');
      const title = firstUserMsg
        ? (firstUserMsg.content.slice(0, 36) + (firstUserMsg.content.length > 36 ? '...' : ''))
        : 'استشارة قانونية جديدة';
      const dateStr = new Date().toLocaleDateString('ar-YE', { month: 'short', day: 'numeric' });

      setSavedChats(prev => {
        const existsIndex = prev.findIndex(c => c.id === activeChatId);
        let updated: SavedChat[];
        if (existsIndex >= 0) {
          updated = [...prev];
          updated[existsIndex] = { ...updated[existsIndex], title, messages };
        } else {
          const newChat: SavedChat = {
            id: activeChatId,
            title,
            date: dateStr,
            messages
          };
          updated = [newChat, ...prev];
        }
        try {
          localStorage.setItem('yemeni_law_saved_chats', JSON.stringify(updated));
        } catch {}
        return updated;
      });
    }
  }, [messages, activeChatId]);

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

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

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
      (sources: SourceDocument[], rag_stats?: RagStats) => {
        setMessages(prev =>
          prev.map(m => (m.id === assistantMsgId ? { ...m, sources, rag_stats } : m))
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
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
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
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      },
      controller.signal
    );
  };

  const handleReset = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setMessages([]);
    setActiveChatId(`chat_${Date.now()}`);
    setIsLoading(false);
  };

  const handleSelectSavedChat = (chat: SavedChat) => {
    if (isLoading) return;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setActiveChatId(chat.id);
    setMessages(chat.messages);
    setIsLoading(false);
  };

  const handleDeleteSavedChat = (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    setSavedChats(prev => {
      const updated = prev.filter(c => c.id !== chatId);
      try {
        localStorage.setItem('yemeni_law_saved_chats', JSON.stringify(updated));
      } catch {}
      return updated;
    });
    if (activeChatId === chatId) {
      handleReset();
    }
  };

  return (
    <div className="app-container">
      <TopBar
        stats={stats}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onReset={handleReset}
        onOpenDevModal={() => setDevModalOpen(true)}
      />

      <Sidebar
        stats={stats}
        isOpen={sidebarOpen}
        onReset={handleReset}
        savedChats={savedChats}
        activeChatId={activeChatId}
        onSelectSavedChat={handleSelectSavedChat}
        onDeleteSavedChat={handleDeleteSavedChat}
        onOpenDevModal={() => setDevModalOpen(true)}
      />

      <DeveloperModal
        isOpen={devModalOpen}
        onClose={() => setDevModalOpen(false)}
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
              messages.map((message, idx) => {
                const prevMsg = idx > 0 ? messages[idx - 1] : undefined;
                const userQuestion = prevMsg?.role === 'user' ? prevMsg.content : undefined;
                return (
                  <ChatMessageItem
                    key={message.id}
                    message={message}
                    userQuestion={userQuestion}
                    onSelectPrompt={handleSendPrompt}
                  />
                );
              })
            )}
          </div>
        </div>

        <ChatInput onSend={handleSendPrompt} disabled={isLoading} />
      </main>
    </div>
  );
};

export default App;
