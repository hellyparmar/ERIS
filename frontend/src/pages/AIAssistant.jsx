import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Sparkles, ArrowUp, Trash2, Menu, X } from 'lucide-react';
import api from '../services/api';
import '../styles/aiassistant.css';

const AIAssistant = () => {
  // State management
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [mobileSessionsOpen, setMobileSessionsOpen] = useState(false);

  // Refs
  const textareaRef = useRef(null);
  const chatEndRef = useRef(null);

  // Quick action suggestions
  const suggestions = [
    "What are today's top selling products?",
    'Which products need reordering?',
    "Show me last week's revenue summary",
    "What's the sales forecast for next month?"
  ];

  // Generate UUID v4
  const generateUUID = useCallback(() => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }, []);

  // Initialize session on mount
  useEffect(() => {
    const newSessionId = generateUUID();
    setSessionId(newSessionId);

    // Load sessions from localStorage
    const savedSessions = localStorage.getItem('chatSessions');
    if (savedSessions) {
      try {
        setSessions(JSON.parse(savedSessions));
      } catch (e) {
        setSessions([]);
      }
    }
  }, [generateUUID]);

  // Fetch chat history for current session
  const { data: historyData } = useQuery({
    queryKey: ['chatHistory', sessionId],
    queryFn: async () => {
      if (!sessionId) return { messages: [] };
      try {
        const response = await api.get(`/api/v1/chat/history/${sessionId}`);
        return response.data;
      } catch (error) {
        console.error('Failed to load chat history:', error);
        return { messages: [] };
      }
    },
    enabled: !!sessionId,
    staleTime: Infinity,
  });

  // Load history into state when fetched
  useEffect(() => {
    if (historyData?.messages) {
      setMessages(historyData.messages);
    }
  }, [historyData]);

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message) => {
      const response = await api.post('/api/v1/chat/message', {
        session_id: sessionId,
        message: message,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setIsTyping(false);
      const assistantMessage = {
        id: data.response_id || Date.now().toString(),
        content: data.response || data.message,
        sender: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    },
    onError: (error) => {
      setIsTyping(false);
      const errorMessage = {
        id: Date.now().toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        sender: 'assistant',
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = Math.min(scrollHeight, 120) + 'px';
      textareaRef.current.style.overflowY = scrollHeight > 120 ? 'auto' : 'hidden';
    }
  }, [inputValue]);

  // Handle send message
  const handleSendMessage = useCallback(() => {
    const trimmedMessage = inputValue.trim();
    if (!trimmedMessage || isTyping) return;

    // Add user message to state
    const userMessage = {
      id: Date.now().toString(),
      content: trimmedMessage,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Update localStorage with new session if needed
    if (!sessions.some((s) => s.session_id === sessionId)) {
      const truncatedMessage = trimmedMessage.substring(0, 40) + (trimmedMessage.length > 40 ? '...' : '');
      const newSession = {
        session_id: sessionId,
        first_message: truncatedMessage,
        created_at: new Date(),
      };
      const updatedSessions = [newSession, ...sessions];
      setSessions(updatedSessions);
      localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
    }

    // Clear input
    setInputValue('');

    // Send message
    setIsTyping(true);
    sendMessageMutation.mutate(trimmedMessage);
  }, [inputValue, isTyping, sessionId, sessions, sendMessageMutation]);

  // Handle Enter key
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    },
    [handleSendMessage]
  );

  // Handle new chat
  const handleNewChat = useCallback(() => {
    const newSessionId = generateUUID();
    setSessionId(newSessionId);
    setMessages([]);
    setInputValue('');
    setIsTyping(false);
  }, [generateUUID]);

  // Handle load session
  const handleLoadSession = useCallback((selectedSessionId) => {
    setSessionId(selectedSessionId);
    setMessages([]);
    setInputValue('');
    setIsTyping(false);
  }, []);

  // Handle clear chat
  const handleClearChat = useCallback(() => {
    if (window.confirm('Clear all messages in this chat?')) {
      setMessages([]);
      setInputValue('');
      handleNewChat();
    }
  }, [handleNewChat]);

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion);
  };

  // Format timestamp
  const formatTime = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
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
    <div className="aiassistant-container">
      {/* Mobile Sessions Toggle Button */}
      <button 
        className="mobile-sessions-toggle md:hidden"
        onClick={() => setMobileSessionsOpen(!mobileSessionsOpen)}
        title={mobileSessionsOpen ? "Hide sessions" : "Show sessions"}
      >
        {mobileSessionsOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sessions Overlay for Mobile */}
      {mobileSessionsOpen && (
        <div className="mobile-sessions-overlay md:hidden" onClick={() => setMobileSessionsOpen(false)} />
      )}

      {/* Left Sidebar */}
      <div className={`aiassistant-sidebar ${mobileSessionsOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-title">
            <Sparkles size={20} />
            AI Assistant
          </div>
          <button className="new-chat-btn" onClick={handleNewChat} title="Start new conversation">
            <span className="new-chat-icon">+</span>
          </button>
        </div>

        <div className="sessions-list">
          {sessions.length === 0 ? (
            <div className="empty-sessions">
              <p>No previous chats</p>
              <p>Start a new conversation</p>
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.session_id}
                className={`session-item ${sessionId === session.session_id ? 'active' : ''}`}
                onClick={() => handleLoadSession(session.session_id)}
              >
                <div className="session-message">{session.first_message}</div>
                <div className="session-time">{formatSessionTime(session.created_at)}</div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right Chat Panel */}
      <div className="aiassistant-chat">
        {/* Header */}
        <div className="chat-header">
          <div className="header-left">
            <h2>Retail Intelligence Assistant</h2>
            <span className="powered-badge">Powered by Mistral AI</span>
          </div>
          <button className="clear-chat-btn" onClick={handleClearChat} title="Clear this chat">
            <Trash2 size={18} />
            Clear Chat
          </button>
        </div>

        {/* Messages Area */}
        <div className="messages-area">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <Sparkles size={48} />
              <h3>Welcome to AI Assistant</h3>
              <p>Ask questions about your retail business</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={msg.id} className={`message-container message-${msg.sender}`}>
                {msg.sender === 'assistant' && (
                  <div className="message-icon">
                    <Sparkles size={16} />
                  </div>
                )}
                <div className={`message-bubble ${msg.isError ? 'error' : ''}`}>
                  <p className="message-text">{msg.content}</p>
                  <span className="message-time">{formatTime(msg.timestamp)}</span>
                </div>
              </div>
            ))
          )}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="message-container message-assistant">
              <div className="message-icon">
                <Sparkles size={16} />
              </div>
              <div className="message-bubble typing-bubble">
                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-box">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about sales, inventory, forecasts…"
              className="message-input"
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isTyping}
              className="send-button"
              title="Send message (Shift+Enter for newline)"
            >
              <ArrowUp size={20} />
            </button>
          </div>

          {/* Suggestion Chips */}
          <div className="suggestions">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-chip"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;
