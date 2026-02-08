import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader, Sparkles, Trash2 } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import ChatMessage from '../components/ai/ChatMessage';
// QuickActions removed
import VoiceInput from '../components/ai/VoiceInput';
import { detectLanguage, formatMessageForAI, getSystemPrompt } from '../lib/languageDetection';
import { useToast } from '../components/ui/Toast';
import { sanitizeInput } from '../utils/sanitize';

/**
 * AI Assistant Page
 * Multilingual chat interface with auto-detection and script support
 */
const AIAssistant = () => {
    const { addToast } = useToast();
    // Load chat history from localStorage on mount
    const [messages, setMessages] = useState(() => {
        try {
            const savedMessages = localStorage.getItem('ai_chat_history');
            return savedMessages ? JSON.parse(savedMessages) : [];
        } catch (error) {
            console.error('Failed to load chat history:', error);
            return [];
        }
    });
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedLanguage] = useState('en');
    const [scriptMode] = useState('native');
    const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const [aiStatus, setAiStatus] = useState({ online: false, provider: 'Initializing...' });

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/v1/ai/status');
                if (res.ok) {
                    const data = await res.json();
                    setAiStatus({
                        online: data.status === 'online',
                        provider: data.primary_provider ? data.primary_provider.charAt(0).toUpperCase() + data.primary_provider.slice(1) : 'Unknown',
                        details: data.providers
                    });
                }
            } catch (error) {
                console.error("AI Status Check Failed", error);
                setAiStatus({ online: false, provider: 'Offline (Connection Error)' });
            }
        };
        checkStatus();
    }, []);

    // Save chat history to localStorage whenever messages change
    useEffect(() => {
        try {
            localStorage.setItem('ai_chat_history', JSON.stringify(messages));
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
    }, [messages]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        // Scroll to top of PAGE on mount and route change
        // Use setTimeout to ensure it runs after React Router navigation
        const timer = setTimeout(() => {
            window.scrollTo({ top: 0, behavior: 'instant' });
        }, 0);
        inputRef.current?.focus();
        return () => clearTimeout(timer);
    }, []);

    const handleSendMessage = async () => {
        if (!inputText.trim() || isLoading) return;

        const userMessage = sanitizeInput(inputText.trim());
        const detectedLang = detectLanguage(userMessage);
        const formattedMessage = formatMessageForAI(userMessage, detectedLang);

        const newUserMessage = {
            id: Date.now(),
            ...formattedMessage,
            isUser: true
        };

        setMessages(prev => [...prev, newUserMessage]);
        setInputText('');
        setIsLoading(true);

        try {
            // Call actual Gemini API (Route handles multi-provider)
            const response = await fetch('http://localhost:8000/api/v1/ai/chat', {
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
                timestamp: new Date().toISOString(), // Use current time for accurate display
                action: data.action, // Include agentic action if present
                isUser: false
            };

            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            // Mock response fallback
            setTimeout(() => {
                setMessages(prev => [...prev, {
                    id: Date.now() + 1,
                    text: "I am currently running in offline mode. I can help you with general questions about the system, but I cannot access real-time database insights at the moment.",
                    language: selectedLanguage,
                    script: scriptMode,
                    timestamp: new Date().toISOString(),
                    isUser: false
                }]);
            }, 1000);
        } finally {
            setIsLoading(false);
        }
    };



    const handleClearChat = async () => {
        if (window.confirm('Are you sure you want to clear the chat history?')) {
            try {
                await fetch(`http://localhost:8000/api/v1/ai/history/${sessionId}`, {
                    method: 'DELETE'
                });
                setMessages([]);
            } catch (error) {
                console.error('Error clearing chat:', error);
                addToast("Chat history cleared (Local)", "info");
                setMessages([]);
            }
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className="h-full flex flex-col overflow-hidden fade-in-up">
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between shrink-0 mb-6"
            >
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent mb-2 flex items-center gap-3">
                        AI Assistant
                    </h1>
                    <p className="text-muted-foreground">
                        Intelligent multilingual assistant for retail insights
                    </p>
                    <div className={`mt-2 inline-flex items-center gap-2 px-2 py-1 rounded-md border ${aiStatus.online
                        ? 'bg-green-500/10 border-green-500/20'
                        : 'bg-yellow-500/10 border-yellow-500/20'
                        }`}>
                        <span className={`w-2 h-2 rounded-full ${aiStatus.online ? 'bg-green-500' : 'bg-yellow-500'
                            }`}></span>
                        <span className={`text-xs font-mono ${aiStatus.online ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'
                            }`}>
                            {aiStatus.online ? 'AI Online' : 'Offline Mode'}
                        </span>
                    </div>
                </div>
                {messages.length > 0 && (
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleClearChat}
                        className="flex items-center gap-2 px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                    >
                        <Trash2 className="w-4 h-4" />
                        Clear Chat
                    </motion.button>
                )}
            </motion.div>

            <div className="flex-1 min-h-0 flex flex-col">
                <GlassCard className="flex-1 flex flex-col p-0 overflow-hidden h-full">
                    <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
                        <AnimatePresence>
                            {messages.length === 0 ? (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="h-full flex items-center justify-center text-center"
                                >
                                    <div>
                                        <Sparkles className="w-16 h-16 mx-auto mb-4 text-blue-500 dark:text-blue-400" />
                                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                                            Welcome to AI Assistant
                                        </h3>
                                        <p className="text-gray-600 dark:text-gray-400 max-w-md">
                                            Ask me anything about your sales, inventory, forecasts, or business insights!
                                        </p>
                                    </div>
                                </motion.div>
                            ) : (
                                (messages || []).map(message => (
                                    <ChatMessage
                                        key={message.id}
                                        message={message}
                                        isUser={message.isUser}
                                    />
                                ))
                            )}
                        </AnimatePresence>
                        {isLoading && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="flex items-center gap-2 text-gray-500 dark:text-gray-400"
                            >
                                <Loader className="w-4 h-4 animate-spin" />
                                <span className="text-sm">AI is thinking...</span>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="border-t border-border p-4 space-y-3 shrink-0">
                        <div className="flex gap-2">
                            <VoiceInput
                                onTranscript={(transcript) => {
                                    setInputText(transcript);
                                    // Auto-send after voice input completes
                                    setTimeout(() => {
                                        if (transcript.trim()) {
                                            // Trigger send by simulating the message send
                                            const userMessage = sanitizeInput(transcript.trim());
                                            const detectedLang = detectLanguage(userMessage);
                                            const formattedMessage = formatMessageForAI(userMessage, detectedLang);

                                            const newUserMessage = {
                                                id: Date.now(),
                                                ...formattedMessage,
                                                isUser: true
                                            };

                                            setMessages(prev => [...prev, newUserMessage]);
                                            setInputText('');
                                            setIsLoading(true);

                                            // Call AI service
                                            (async () => {
                                                try {
                                                    const response = await fetch('http://localhost:8000/api/v1/ai/chat', {
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
                                            })();
                                        }
                                    }, 500);
                                }}
                                language={selectedLanguage === 'en' ? 'en-US' : `${selectedLanguage}-IN`}
                            />
                            <div className="flex-1 relative">
                                <Sparkles className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={20} />
                                <textarea
                                    ref={inputRef}
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Ask me anything..."
                                    className="w-full pl-10 pr-4 py-3 bg-transparent border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary transition resize-none h-[52px]"
                                    rows="1"
                                />
                            </div>

                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={handleSendMessage}
                                disabled={!inputText.trim() || isLoading}
                                className="px-6 py-3 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shrink-0"
                            >
                                {isLoading ? (
                                    <Loader className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Send className="w-5 h-5" />
                                )}
                            </motion.button>
                        </div>
                    </div>
                </GlassCard>
            </div>
        </div>
    );
};

export default AIAssistant;
