import React, { useState, useRef, useEffect } from 'react';
import { API_BASE } from '../../lib/api';
import { Bot, X, Send, Loader, Trash2 } from 'lucide-react';
import ChatMessage from '../ai/ChatMessage';
import VoiceInput from '../ai/VoiceInput';
import DatabaseResults from '../ai/DatabaseResults';
import { detectLanguage, formatMessageForAI, getSystemPrompt } from '../../lib/languageDetection';
import { sanitizeInput } from '../../utils/sanitize';
import { useToast } from '../ui/Toast';

const FloatingAIAssistant = () => {
    const { addToast } = useToast();
    const [isOpen, setIsOpen] = useState(false);
    const [showTooltip, setShowTooltip] = useState(false);

    // Load chat history from localStorage on mount
    const [messages, setMessages] = useState(() => {
        try {
            const savedMessages = localStorage.getItem('ai_chat_history_floating');
            return savedMessages ? JSON.parse(savedMessages) : [];
        } catch (error) {
            console.error('Failed to load chat history:', error);
            return [];
        }
    });

    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId] = useState(() => `floating_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    const [aiStatus, setAiStatus] = useState({ online: false, provider: 'Initializing...' });
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Check AI status
    useEffect(() => {
        const checkStatus = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/v1/ai/status`);
                if (res.ok) {
                    const data = await res.json();
                    setAiStatus({
                        online: data.status === 'online',
                        provider: data.primary_provider ? data.primary_provider.charAt(0).toUpperCase() + data.primary_provider.slice(1) : 'Unknown'
                    });
                }
            } catch (error) {
                console.error("AI Status Check Failed", error);
                setAiStatus({ online: false, provider: 'Offline' });
            }
        };
        checkStatus();
    }, []);

    // Save chat history to localStorage
    useEffect(() => {
        try {
            localStorage.setItem('ai_chat_history_floating', JSON.stringify(messages));
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
    }, [messages]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen) {
            inputRef.current?.focus();
        }
    }, [isOpen]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = sanitizeInput(inputValue.trim());
        const detectedLang = detectLanguage(userMessage);
        const formattedMessage = formatMessageForAI(userMessage, detectedLang);

        const newUserMessage = {
            id: Date.now(),
            ...formattedMessage,
            isUser: true
        };

        setMessages(prev => [...prev, newUserMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE}/api/v1/ai/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: formattedMessage,
                    session_id: sessionId,
                    system_prompt: getSystemPrompt(detectedLang)
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get AI response');
            }

            const data = await response.json();

            const aiMessage = {
                id: Date.now() + 1,
                text: data.message.text,
                language: data.message.language,
                script: data.message.script,
                timestamp: new Date().toISOString(),
                action: data.action,
                queryResult: data.query_result,  // NEW: Store database results
                isUser: false
            };

            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            // Fallback offline response
            setTimeout(() => {
                setMessages(prev => [...prev, {
                    id: Date.now() + 1,
                    text: "I am currently running in offline mode. I can help you with general questions about the system, but I cannot access real-time database insights at the moment.",
                    language: 'en',
                    script: 'native',
                    timestamp: new Date().toISOString(),
                    isUser: false
                }]);
            }, 500);
        } finally {
            setIsLoading(false);
        }
    };

    const handleVoiceTranscript = async (transcript) => {
        if (!transcript.trim()) return;

        const userMessage = sanitizeInput(transcript.trim());
        const detectedLang = detectLanguage(userMessage);
        const formattedMessage = formatMessageForAI(userMessage, detectedLang);

        const newUserMessage = {
            id: Date.now(),
            ...formattedMessage,
            isUser: true
        };

        setMessages(prev => [...prev, newUserMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE}/api/v1/ai/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: formattedMessage,
                    session_id: sessionId,
                    system_prompt: getSystemPrompt(detectedLang)
                })
            });

            if (response.ok) {
                const data = await response.json();
                const aiMessage = {
                    id: Date.now() + 1,
                    text: data.message.text,
                    language: data.message.language,
                    script: data.message.script,
                    timestamp: new Date().toISOString(),
                    action: data.action,
                    isUser: false
                };
                setMessages(prev => [...prev, aiMessage]);
            }
        } catch (error) {
            console.error('Voice input AI error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleClearChat = () => {
        if (window.confirm('Are you sure you want to clear the chat history?')) {
            setMessages([]);
            addToast("Chat history cleared", "info");
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <>
            {/* Chat Modal */}
            {isOpen && (
                <div className="fixed bottom-24 right-8 w-96 h-[500px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-violet-500 to-violet-600 text-white p-4 flex items-center justify-between shrink-0">
                        <div className="flex items-center gap-2">
                            <Bot className="w-5 h-5" />
                            <div>
                                <h3 className="font-bold text-lg">R-DIOS AI Assistant</h3>
                                <div className="flex items-center gap-1.5 mt-0.5">
                                    <span className={`w-1.5 h-1.5 rounded-full ${aiStatus.online ? 'bg-green-400' : 'bg-yellow-400'}`}></span>
                                    <span className="text-xs opacity-90">
                                        {aiStatus.online ? 'Online' : 'Offline'}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {messages.length > 0 && (
                                <button
                                    onClick={handleClearChat}
                                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                                    aria-label="Clear chat"
                                    title="Clear chat"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            )}
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                                aria-label="Close chat"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-800/50">
                        {messages.length === 0 ? (
                            <div className="h-full flex items-center justify-center text-center">
                                <div>
                                    <Bot className="w-12 h-12 mx-auto mb-3 text-violet-500" />
                                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                                        Welcome to AI Assistant
                                    </h4>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 max-w-xs">
                                        Ask me anything about your sales, inventory, or business insights!
                                    </p>
                                </div>
                            </div>
                        ) : (
                            messages.map(message => (
                                <ChatMessage
                                    key={message.id}
                                    message={message}
                                    isUser={message.isUser}
                                />
                            ))
                        )}
                        {isLoading && (
                            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                                <Loader className="w-4 h-4 animate-spin" />
                                <span className="text-sm">AI is thinking...</span>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <div className="p-3 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shrink-0">
                        <div className="flex gap-2 items-center">
                            <VoiceInput
                                onTranscript={handleVoiceTranscript}
                                language="en-US"
                            />
                            <div className="flex-1 flex items-center">
                                <input
                                    ref={inputRef}
                                    type="text"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Ask me anything..."
                                    disabled={isLoading}
                                    className="w-full px-4 py-2.5 bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent dark:text-white placeholder-slate-500 dark:placeholder-slate-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                />
                            </div>
                            <button
                                onClick={handleSendMessage}
                                disabled={!inputValue.trim() || isLoading}
                                className="p-2.5 bg-violet-500 text-white rounded-lg hover:bg-violet-600 active:bg-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0 flex items-center justify-center"
                                aria-label="Send message"
                                title="Send message (Enter)"
                            >
                                {isLoading ? (
                                    <Loader className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Send className="w-4 h-4" />
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Floating Button */}
            <div className="fixed bottom-8 right-8 z-40 group">
                {/* Tooltip */}
                {showTooltip && !isOpen && (
                    <div className="absolute bottom-full right-0 mb-3 px-3 py-2 bg-slate-900 text-white text-sm font-medium rounded-lg shadow-lg whitespace-nowrap">
                        AI Assistant
                        <div className="absolute top-full right-4 w-2 h-2 bg-slate-900 transform rotate-45"></div>
                    </div>
                )}

                {/* Button */}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    onMouseEnter={() => setShowTooltip(true)}
                    onMouseLeave={() => setShowTooltip(false)}
                    className="p-4 bg-gradient-to-br from-violet-500 to-violet-600 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-110 transition-all duration-200 flex items-center justify-center"
                    aria-label="AI Assistant"
                >
                    <Bot className="w-6 h-6" />
                </button>

                {/* Ambient glow effect */}
                <div className="absolute inset-0 bg-violet-400 rounded-full blur-lg opacity-0 group-hover:opacity-20 transition-opacity duration-200 pointer-events-none"></div>
            </div>
        </>
    );
};

export default FloatingAIAssistant;
