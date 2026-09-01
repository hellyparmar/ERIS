import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Send, Trash2, Bot, User as UserIcon } from 'lucide-react';
import api from '../lib/api';
import SEO from '../components/SEO';

const AIAssistant = () => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessions, setSessions] = useState([]);

  const textareaRef = useRef(null);
  const chatEndRef = useRef(null);

  const suggestions = [
    "What are today's top selling products?",
    'Which products need reordering?',
    "Show me last week's revenue summary",
    "What's the sales forecast for next month?",
  ];

  const generateUUID = useCallback(() => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }, []);

  useEffect(() => {
    const newSessionId = generateUUID();
    setSessionId(newSessionId);
    const savedSessions = localStorage.getItem('chatSessions');
    if (savedSessions) {
      try { setSessions(JSON.parse(savedSessions)); }
      catch (e) { setSessions([]); }
    }
  }, [generateUUID]);

  const { data: historyData } = useQuery({
    queryKey: ['chatHistory', sessionId],
    queryFn: async () => {
      if (!sessionId) return { messages: [] };
      try {
        const response = await api.get(`/api/v1/ai/history/${sessionId}`);
        return response.data;
      } catch (error) {
        console.error('Failed to load chat history:', error);
        return { messages: [] };
      }
    },
    enabled: !!sessionId,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (historyData?.messages) setMessages(historyData.messages);
  }, [historyData]);

  const sendMessageMutation = useMutation({
    mutationFn: async (message) => {
      const response = await api.post('/api/v1/ai/chat', {
        session_id: sessionId, 
        message: { text: message, language: 'en', script: 'native' },
      });
      return response.data;
    },
    onSuccess: (data) => {
      setIsTyping(false);
      setMessages((prev) => [...prev, {
        id: data.response_id || Date.now().toString(),
        content: data.message?.text || data.response || data.message,
        sender: 'assistant',
        timestamp: new Date(),
      }]);
    },
    onError: () => {
      setIsTyping(false);
      setMessages((prev) => [...prev, {
        id: Date.now().toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        sender: 'assistant', timestamp: new Date(), isError: true,
      }]);
    },
  });

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const sh = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = Math.min(sh, 120) + 'px';
      textareaRef.current.style.overflowY = sh > 120 ? 'auto' : 'hidden';
    }
  }, [inputValue]);

  const handleSendMessage = useCallback(() => {
    const trimmed = inputValue.trim();
    if (!trimmed || isTyping) return;
    setMessages((prev) => [...prev, {
      id: Date.now().toString(), content: trimmed, sender: 'user', timestamp: new Date(),
    }]);
    if (!sessions.some((s) => s.session_id === sessionId)) {
      const truncated = trimmed.substring(0, 40) + (trimmed.length > 40 ? '...' : '');
      const updated = [{ session_id: sessionId, first_message: truncated, created_at: new Date() }, ...sessions];
      setSessions(updated);
      localStorage.setItem('chatSessions', JSON.stringify(updated));
    }
    setInputValue('');
    setIsTyping(true);
    sendMessageMutation.mutate(trimmed);
  }, [inputValue, isTyping, sessionId, sessions, sendMessageMutation]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }
  }, [handleSendMessage]);

  const handleNewChat = useCallback(() => {
    setSessionId(generateUUID()); setMessages([]); setInputValue(''); setIsTyping(false);
  }, [generateUUID]);

  const handleLoadSession = useCallback((id) => {
    setSessionId(id); setMessages([]); setInputValue(''); setIsTyping(false);
  }, []);

  const handleClearChat = useCallback(() => {
    if (window.confirm('Clear all messages in this chat?')) { setMessages([]); setInputValue(''); handleNewChat(); }
  }, [handleNewChat]);

  const handleSuggestionClick = (suggestion) => setInputValue(suggestion);

  const formatTime = (date) => {
    if (!date) return '';
    return new Date(date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
  };

  const formatSessionTime = (date) => {
    if (!date) return '';
    const d = new Date(date);
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <>
      <SEO title="AI Assistant" description="Talk to retail intelligence assistant" />
      <div style={{ display: 'flex', height: 'calc(100vh - 175px)', border: '1px solid var(--c-border)', borderRadius: 'var(--r-lg)', overflow: 'hidden', gap: 0, position: 'relative', background: 'var(--c-canvas)' }}>
        {/* Left Panel - Conversation list */}
        <div style={{
          width: 260, flexShrink: 0, display: 'flex', flexDirection: 'column',
          borderRight: '1px solid #D4C9B8', background: '#F0EBE0',
          overflow: 'hidden',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px', borderBottom: '1px solid #D4C9B8' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600, color: 'var(--c-brown)', letterSpacing: '1px', textTransform: 'uppercase' }}>
              Chats
            </div>
            <button className="action-btn" onClick={handleNewChat} style={{ padding: '4px 10px' }}>
              New Chat
            </button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {sessions.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 24, fontSize: 13, color: 'var(--c-ink-muted)' }}>
                <p>No previous chats</p>
              </div>
            ) : (
              sessions.map((session) => (
                <button key={session.session_id}
                  onClick={() => handleLoadSession(session.session_id)}
                  style={{
                    width: '100%', textAlign: 'left', padding: '12px 16px',
                    background: sessionId === session.session_id ? '#FFFFFF' : 'transparent',
                    border: 'none',
                    borderLeft: sessionId === session.session_id ? '2px solid #8B5E3C' : '2px solid transparent',
                    cursor: 'pointer', marginBottom: 2, transition: 'background 0.12s',
                  }}>
                  <div style={{ fontSize: 12, color: '#1A1208', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {session.first_message}
                  </div>
                  <div style={{ fontSize: 10, color: '#9A8F82', marginTop: 2 }}>
                    {formatSessionTime(session.created_at)}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right Panel - Chat area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#FFFFFF', overflow: 'hidden' }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 24px', borderBottom: '1px solid var(--c-border)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--c-dark)', margin: 0 }}>Retail Intelligence Assistant</h2>
              <div className="badge active" style={{ fontSize: 10 }}>Mistral AI</div>
            </div>
            <button className="action-btn" onClick={handleClearChat}>
              <Trash2 size={13} style={{ marginRight: 4 }} /> Clear
            </button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
            {messages.length === 0 ? (
              <div className="empty-state" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingTop: 80, textAlign: 'center' }}>
                <div style={{ width: 64, height: 64, borderRadius: 'var(--radius)', background: 'rgba(139,94,60,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--c-brown)', marginBottom: 20 }}>
                  <Bot size={28} />
                </div>
                <div className="empty-state-title" style={{ marginBottom: 8 }}>Welcome to AI Assistant</div>
                <p style={{ color: 'var(--c-ink-muted)', fontSize: '13px', margin: 0 }}>Ask questions about your retail business, sales trends, and inventory levels.</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} style={{ display: 'flex', gap: 10, marginBottom: 16, justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                  {msg.sender === 'assistant' && (
                    <div style={{ width: 28, height: 28, borderRadius: 'var(--radius)', background: 'var(--c-strip)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--c-brown)', flexShrink: 0 }}>
                      <Bot size={14} />
                    </div>
                  )}
                  <div style={{
                    maxWidth: '70%', padding: '12px 16px',
                    background: msg.sender === 'user' ? '#222831' : '#F0EBE0',
                    color: msg.sender === 'user' ? '#F3E4C9' : '#1A1208',
                    borderRadius: msg.sender === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                  }}>
                    <p style={{ fontSize: 14, color: msg.isError ? 'var(--c-critical)' : 'inherit', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </p>
                    <span style={{ fontSize: 10, color: msg.sender === 'user' ? 'rgba(243,228,201,0.6)' : 'var(--c-ink-muted)', marginTop: 6, display: 'block', textAlign: 'right' }}>
                      {formatTime(msg.timestamp)}
                    </span>
                  </div>
                  {msg.sender === 'user' && (
                    <div style={{ width: 28, height: 28, borderRadius: 'var(--radius)', background: 'var(--c-strip)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--c-brown)', flexShrink: 0 }}>
                      <UserIcon size={14} />
                    </div>
                  )}
                </div>
              ))
            )}

            {isTyping && (
              <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
                <div style={{ width: 28, height: 28, borderRadius: 'var(--radius)', background: 'var(--c-strip)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--c-brown)', flexShrink: 0 }}>
                  <Bot size={14} />
                </div>
                <div style={{ padding: '12px 16px', background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', borderRadius: 'var(--radius)' }}>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {[0, 1, 2].map(i => (
                      <span key={i} style={{
                        width: 6, height: 6, borderRadius: '50%', background: 'var(--c-ink-muted)',
                        display: 'inline-block',
                      }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          <div style={{ padding: '16px 24px', borderTop: '1px solid #D4C9B8', background: '#FDFAF4' }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <textarea ref={textareaRef} value={inputValue} onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown} placeholder="Ask about sales, inventory, forecasts…" rows={1}
                style={{ flex: 1, minHeight: 42, resize: 'none', padding: '10px 14px', fontSize: 14 }} />
              <button onClick={handleSendMessage} disabled={!inputValue.trim() || isTyping}
                className="action-btn primary" style={{ height: 42, width: 42, padding: 0, flexShrink: 0, justifyContent: 'center' }}>
                <Send size={16} />
              </button>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {suggestions.map((suggestion, index) => (
                <button key={index} onClick={() => handleSuggestionClick(suggestion)}
                  className="action-btn"
                  style={{ fontSize: 12, padding: '4px 10px' }}>
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AIAssistant;
