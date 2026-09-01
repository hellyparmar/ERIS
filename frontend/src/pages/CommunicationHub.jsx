import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../hooks/useApi';
import { useAuth } from '../contexts/AuthContext';
import { MessageSquare, Send, CheckCircle2, User as UserIcon, Clock } from 'lucide-react';
import { format } from 'date-fns';

export default function CommunicationHub() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const userId = user?.id || 1; // Fallback to 1 if not available
  const userType = 'staff';
  
  const [selectedThread, setSelectedThread] = useState(null);
  const [replyText, setReplyText] = useState('');

  // Fetch inbox threads (using /api/v1/messages/inbox)
  const { data: inboxData, isLoading: isLoadingInbox } = useQuery({
    queryKey: ['messages', 'inbox', userId],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/messages/inbox?user_type=${userType}&user_id=${userId}`);
      return data;
    },
    refetchInterval: 30000 // Poll every 30s
  });

  // Fetch thread messages
  const { data: threadMessages, isLoading: isLoadingThread } = useQuery({
    queryKey: ['messages', 'thread', selectedThread],
    queryFn: async () => {
      if (!selectedThread) return [];
      const { data } = await api.get(`/api/v1/messages/thread/${selectedThread}`);
      return data;
    },
    enabled: !!selectedThread,
    refetchInterval: 10000 // Poll faster when viewing thread
  });

  // Mark as read mutation
  const markAsRead = useMutation({
    mutationFn: async (messageId) => {
      const { data } = await api.post(`/api/v1/messages/${messageId}/mark-read`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', 'inbox'] });
      queryClient.invalidateQueries({ queryKey: ['messages', 'thread', selectedThread] });
    }
  });

  // Send message mutation
  const sendMessage = useMutation({
    mutationFn: async (payload) => {
      const { data } = await api.post('/api/v1/messages/send', payload);
      return data;
    },
    onSuccess: () => {
      setReplyText('');
      queryClient.invalidateQueries({ queryKey: ['messages', 'thread', selectedThread] });
      queryClient.invalidateQueries({ queryKey: ['messages', 'inbox'] });
    }
  });

  // Effect to mark messages as read when thread is opened
  useEffect(() => {
    if (threadMessages && threadMessages.length > 0) {
      threadMessages.forEach(msg => {
        if (!msg.read_at && msg.recipient_id === userId && msg.recipient_type === userType) {
          markAsRead.mutate(msg.id);
        }
      });
    }
  }, [threadMessages, userId, userType]);

  const handleSendReply = () => {
    if (!replyText.trim() || !threadMessages || threadMessages.length === 0) return;
    
    // Find recipient details from the thread (usually the other person)
    const firstMsg = threadMessages[0];
    const isWeSender = firstMsg.sender_id === userId && firstMsg.sender_type === userType;
    
    const recipientType = isWeSender ? firstMsg.recipient_type : firstMsg.sender_type;
    const recipientId = isWeSender ? firstMsg.recipient_id : firstMsg.sender_id;

    sendMessage.mutate({
      sender_type: userType,
      sender_id: userId,
      recipient_type: recipientType,
      recipient_id: recipientId,
      subject: firstMsg.subject || 'Re: Message',
      body: replyText,
      channel: firstMsg.channel || 'in_app',
      thread_id: selectedThread
    });
  };

  // Group inbox by thread
  const threads = [];
  const threadMap = new Map();
  if (inboxData) {
    inboxData.forEach(msg => {
      if (!threadMap.has(msg.thread_id)) {
        threadMap.set(msg.thread_id, msg);
        threads.push(msg);
      }
    });
  }

  return (
    <div className="h-[calc(100vh-64px)] flex p-6 gap-6 max-w-[1600px] mx-auto">
      {/* Sidebar / Inbox List */}
      <div className="w-1/3 bg-[var(--color-navy-deep)] border border-[rgba(255,255,255,0.06)] rounded-xl overflow-hidden flex flex-col">
        <div className="p-4 border-b border-[rgba(255,255,255,0.06)]">
          <h2 className="text-lg font-semibold text-[#f4f2ed] flex items-center gap-2">
            <MessageSquare size={18} className="text-[var(--color-amber)]" />
            Inbox
          </h2>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {isLoadingInbox ? (
            <div className="p-4 text-center text-[var(--color-navy-text)]">Loading messages...</div>
          ) : threads.length === 0 ? (
            <div className="p-8 text-center text-[var(--color-navy-text)] flex flex-col items-center">
              <MessageSquare size={32} className="mb-3 opacity-20" />
              <p>No messages in your inbox.</p>
            </div>
          ) : (
            <div className="divide-y divide-[rgba(255,255,255,0.04)]">
              {threads.map((thread) => {
                const isUnread = !thread.read_at && thread.recipient_id === userId && thread.recipient_type === userType;
                return (
                  <button
                    key={thread.thread_id}
                    onClick={() => setSelectedThread(thread.thread_id)}
                    className={`w-full text-left p-4 hover:bg-[var(--color-navy-hover)] transition-colors flex flex-col gap-1
                      ${selectedThread === thread.thread_id ? 'bg-[var(--color-navy-active)]' : ''}
                      ${isUnread ? 'bg-[var(--color-navy-dim)]' : ''}
                    `}
                  >
                    <div className="flex justify-between items-start w-full">
                      <span className={`text-sm truncate pr-2 ${isUnread ? 'font-semibold text-[#f4f2ed]' : 'font-medium text-[#d4d0c8]'}`}>
                        {thread.sender_type === userType && thread.sender_id === userId ? 'To: ' + thread.recipient_type : 'From: ' + thread.sender_type}
                      </span>
                      <span className="text-xs text-[var(--color-navy-text)] whitespace-nowrap shrink-0">
                        {format(new Date(thread.sent_at), 'MMM d, h:mm a')}
                      </span>
                    </div>
                    <div className={`text-sm truncate ${isUnread ? 'font-semibold text-[#f4f2ed]' : 'text-[#d4d0c8]'}`}>
                      {thread.subject}
                    </div>
                    <div className="text-xs text-[var(--color-navy-text)] truncate mt-1">
                      {thread.body}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Main Thread View */}
      <div className="flex-1 bg-[var(--color-navy-deep)] border border-[rgba(255,255,255,0.06)] rounded-xl overflow-hidden flex flex-col">
        {!selectedThread ? (
          <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-navy-text)] p-8">
            <MessageSquare size={48} className="mb-4 opacity-20" />
            <p className="text-lg font-medium">Select a conversation</p>
            <p className="text-sm mt-2">Choose a thread from the sidebar to view details and reply.</p>
          </div>
        ) : (
          <>
            {/* Thread Header */}
            <div className="p-4 border-b border-[rgba(255,255,255,0.06)] bg-[var(--color-navy-dim)]">
              <h2 className="text-base font-semibold text-[#f4f2ed]">
                {threadMessages?.[0]?.subject || 'Conversation'}
              </h2>
            </div>
            
            {/* Messages List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {isLoadingThread ? (
                <div className="text-center text-[var(--color-navy-text)] py-8">Loading thread...</div>
              ) : (
                threadMessages?.slice().reverse().map((msg) => {
                  const isMe = msg.sender_type === userType && msg.sender_id === userId;
                  
                  return (
                    <div key={msg.id} className={`flex flex-col max-w-[80%] ${isMe ? 'self-end ml-auto' : 'self-start mr-auto'}`}>
                      <div className="flex items-center gap-2 mb-1 px-1">
                        {!isMe && <UserIcon size={12} className="text-[var(--color-navy-text)]" />}
                        <span className="text-xs text-[var(--color-navy-text)] font-medium">
                          {isMe ? 'You' : msg.sender_type.toUpperCase()}
                        </span>
                        <span className="text-[10px] text-[var(--color-navy-muted)] ml-2 flex items-center gap-1">
                          <Clock size={10} />
                          {format(new Date(msg.sent_at), 'MMM d, h:mm a')}
                        </span>
                      </div>
                      
                      <div className={`p-3 rounded-2xl ${
                        isMe 
                          ? 'bg-[var(--color-amber)] text-amber-950 rounded-tr-sm' 
                          : 'bg-[var(--color-navy-dim)] border border-[rgba(255,255,255,0.04)] text-[#d4d0c8] rounded-tl-sm'
                      }`}>
                        <p className="text-sm whitespace-pre-wrap">{msg.body}</p>
                      </div>
                      
                      {isMe && msg.read_at && (
                        <div className="flex items-center justify-end gap-1 mt-1 px-1 text-[10px] text-emerald-500">
                          <CheckCircle2 size={10} /> Read
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
            
            {/* Reply Box */}
            <div className="p-4 border-t border-[rgba(255,255,255,0.06)] bg-[var(--color-navy-dim)]">
              <div className="relative">
                <textarea
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Type your reply here..."
                  className="w-full bg-[var(--color-navy-deep)] border border-[rgba(255,255,255,0.1)] rounded-xl py-3 px-4 pr-12 text-sm text-[#f4f2ed] focus:outline-none focus:border-[var(--color-amber)] resize-none"
                  rows={3}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendReply();
                    }
                  }}
                />
                <button
                  onClick={handleSendReply}
                  disabled={sendMessage.isPending || !replyText.trim()}
                  className="absolute bottom-3 right-3 p-2 bg-[var(--color-amber)] hover:bg-[var(--color-amber-hover)] disabled:opacity-50 disabled:cursor-not-allowed text-amber-950 rounded-lg transition-colors"
                >
                  <Send size={16} />
                </button>
              </div>
              <div className="text-xs text-[var(--color-navy-muted)] mt-2">
                Press Enter to send, Shift + Enter for new line.
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
