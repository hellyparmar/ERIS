
import React, { useState } from 'react';
import { Send, Mic, Sparkles, X } from 'lucide-react';
import GlassCard from '../ui/GlassCard';

const RDIOSInsightPanel = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            isAi: true,
            text: "Hi, R-DIOS, can you please help me confirm if my stock levels and forecasting features meet my inventory and service?"
        },
        {
            id: 2,
            isAi: true,
            text: "Inventory levels look solid! Response, insights confirm no stockouts observed in current lines."
        },
        {
            id: 3,
            isAi: false,
            text: "When can you compute ROI in setup?"
        },
        {
            id: 4,
            isAi: true,
            text: "Here is an overview of how that, new custom response handling user data and can massively impact your count."
        }
    ]);

    return (

        <GlassCard className="h-full flex flex-col bg-card border-l border-border rounded-none md:rounded-l-2xl shadow-xl overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-border flex justify-between items-center bg-card/50 backdrop-blur-sm">
                <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-blue-500" />
                    <h3 className="font-bold text-card-foreground">R-DIOS AI Insight</h3>
                </div>
                <button className="text-muted-foreground hover:text-foreground transition-colors">
                    <X size={18} />
                </button>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted/30">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.isAi ? 'justify-start' : 'justify-end'}`}>
                        <div className={`flex gap-3 max-w-[85%] ${msg.isAi ? 'flex-row' : 'flex-row-reverse'}`}>

                            {/* Avatar */}
                            {msg.isAi ? (
                                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                                    <Sparkles className="w-4 h-4 text-white" />
                                </div>
                            ) : (
                                <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
                                    <span className="text-xs text-white font-bold">U</span>
                                </div>
                            )}

                            {/* Message Bubble */}
                            <div className={`p-3 rounded-2xl text-sm ${msg.isAi
                                ? 'bg-blue-500 text-white rounded-tl-none'
                                : 'bg-secondary text-secondary-foreground rounded-tr-none'
                                }`}>
                                {msg.text}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-border bg-card">
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Ask R-DIOS for insights..."
                        className="w-full pl-10 pr-12 py-3 bg-muted border-none rounded-xl text-sm focus:ring-2 focus:ring-blue-500 text-foreground placeholder-muted-foreground"
                    />
                    <Mic className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground cursor-pointer hover:text-blue-500" size={18} />

                    <button className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        <Send size={16} />
                    </button>
                </div>
            </div>
        </GlassCard>
    );
};

export default RDIOSInsightPanel;
