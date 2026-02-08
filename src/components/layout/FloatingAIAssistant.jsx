import { Sparkles, X, Send, Mic } from 'lucide-react';
import { useState } from 'react';

const FloatingAIAssistant = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [showTooltip, setShowTooltip] = useState(false);
    const [messages, setMessages] = useState([
        {
            id: 1,
            isAi: true,
            text: "Hi! I'm your R-DIOS AI Assistant. How can I help you today?"
        }
    ]);
    const [inputValue, setInputValue] = useState('');

    const handleSendMessage = () => {
        if (inputValue.trim()) {
            // Add user message
            setMessages([...messages, {
                id: messages.length + 1,
                isAi: false,
                text: inputValue
            }]);

            // Simulate AI response after a brief delay
            setTimeout(() => {
                setMessages(prev => [...prev, {
                    id: prev.length + 1,
                    isAi: true,
                    text: "I'm processing your request. This is a demo response. In production, this will connect to your AI backend."
                }]);
            }, 500);

            setInputValue('');
        }
    };

    return (
        <>
            {/* Chat Modal */}
            {isOpen && (
                <div className="fixed bottom-24 right-8 w-96 h-96 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-violet-500 to-violet-600 text-white p-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5" />
                            <h3 className="font-bold text-lg">R-DIOS AI Assistant</h3>
                        </div>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="p-1 hover:bg-white/20 rounded-lg transition-colors"
                            aria-label="Close chat"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-800/50">
                        {messages.map((msg) => (
                            <div key={msg.id} className={`flex ${msg.isAi ? 'justify-start' : 'justify-end'}`}>
                                <div className={`max-w-xs px-4 py-2 rounded-lg ${
                                    msg.isAi
                                        ? 'bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-slate-100'
                                        : 'bg-violet-500 text-white'
                                }`}>
                                    <p className="text-sm">{msg.text}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Input */}
                    <div className="p-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 space-y-3">
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                                placeholder="Ask me anything..."
                                className="flex-1 px-3 py-2 bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                            />
                            <button
                                onClick={handleSendMessage}
                                className="p-2 bg-violet-500 text-white rounded-lg hover:bg-violet-600 transition-colors"
                                aria-label="Send message"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="flex items-center justify-center">
                            <button className="p-1.5 text-slate-400 hover:text-violet-500 transition-colors">
                                <Mic className="w-4 h-4" />
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
                    <Sparkles className="w-6 h-6" />
                </button>

                {/* Ambient glow effect */}
                <div className="absolute inset-0 bg-violet-400 rounded-full blur-lg opacity-0 group-hover:opacity-20 transition-opacity duration-200"></div>
            </div>
        </>
    );
};

export default FloatingAIAssistant;
