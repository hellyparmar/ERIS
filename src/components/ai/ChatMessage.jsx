import React from 'react';
import { motion } from 'framer-motion';
import { User, Bot } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import PurchaseOrderDraftCard from './PurchaseOrderDraftCard';

/**
 * ChatMessage Component
 * Displays individual chat messages with user/AI differentiation
 */
const ChatMessage = ({ message, isUser }) => {
    const { text, timestamp, language, script, action } = message;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-4`}
        >
            {/* Avatar */}
            <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${isUser
                ? 'bg-gradient-to-br from-blue-500 to-purple-600'
                : 'bg-gradient-to-br from-green-500 to-teal-600'
                }`}>
                {isUser ? (
                    <User className="w-5 h-5 text-white" />
                ) : (
                    <Bot className="w-5 h-5 text-white" />
                )}
            </div>

            {/* Message Content */}
            <div className={`flex-1 max-w-[70%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
                <div className={`rounded-2xl px-4 py-3 ${isUser
                    ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
                    }`}>
                    <p className="text-sm md:text-base whitespace-pre-wrap break-words">
                        {text}
                    </p>
                </div>

                {/* Agentic Action Cards */}
                {action && action.type === 'draft_po' && (
                    <div className="mt-2 w-full">
                        <PurchaseOrderDraftCard
                            actionData={action}
                            onConfirm={() => console.log('PO Confirmed', action)}
                            onCancel={() => console.log('PO Cancelled')}
                        />
                    </div>
                )}

                {/* Metadata */}
                <div className={`flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400 ${isUser ? 'flex-row-reverse' : 'flex-row'
                    }`}>
                    <span>
                        {timestamp ? formatDistanceToNow(new Date(timestamp), { addSuffix: true }) : 'Just now'}
                    </span>
                    {script === 'roman' && language !== 'en' && (
                        <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full text-xs">
                            Roman
                        </span>
                    )}
                </div>
            </div>
        </motion.div>
    );
};

export default ChatMessage;
