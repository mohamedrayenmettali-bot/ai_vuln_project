import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useLocation, matchPath } from 'react-router-dom';
import { MessageCircle, X, Send, Minimize2, Bot } from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import { useProject } from '../../hooks/useProjects';

const SUGGESTED_PROMPTS = [
  'What are my most critical vulnerabilities?',
  'Summarize today\'s new findings',
  'Explain CVSS scoring',
  'How do I fix SQL injection?',
];

function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center flex-shrink-0 mt-0.5">
          <Bot size={13} className="text-white" />
        </div>
      )}
      <div className={`max-w-[82%] px-3 py-2 rounded-lg text-sm leading-relaxed ${
        isUser ? 'bg-accent text-white rounded-tr-none' : 'bg-white border border-border text-text-primary rounded-tl-none shadow-sm'
      }`}>
        {message.content}
      </div>
    </div>
  );
}

export default function GlobalChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const location = useLocation();
  const projectMatch = matchPath('/projects/:id/dashboard', location.pathname);
  const projectId = projectMatch?.params?.id || null;
  const query = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const { data: project } = useProject(projectId);
  const chatContext = useMemo(
    () => ({
      route: location.pathname,
      project_id: projectId,
      projectId,
      project_name: project?.name || null,
      active_tab: query.get('tab') || null,
      finding_id: query.get('findingId') || query.get('finding_id') || null,
    }),
    [location.pathname, projectId, project?.name, query]
  );
  const { messages, isTyping, error, sendMessage, retry } = useChat(chatContext);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-accent hover:bg-accent-hover text-white rounded-full shadow-lg flex items-center justify-center transition-colors z-50"
        aria-label="Open AI Assistant"
      >
        {isOpen ? <X size={22} /> : <MessageCircle size={22} />}
      </button>

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[560px] bg-white border border-border rounded-lg shadow-lg flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-accent text-white">
            <div className="flex items-center gap-2">
              <Bot size={18} />
              <div>
                <p className="font-semibold text-sm">SecureAI Assistant</p>
                <p className="text-xs text-blue-200">GPT-4o · Security Expert</p>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-white/20 rounded">
              <Minimize2 size={15} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-bg-secondary">
            {messages.length === 0 ? (
              <div className="space-y-4">
                <p className="text-xs text-text-muted text-center">Hi! I'm your security assistant. How can I help?</p>
                <div className="space-y-2">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => sendMessage(prompt)}
                      disabled={isTyping}
                      className="w-full text-left px-3 py-2 bg-white border border-border rounded-md text-xs text-text-secondary hover:bg-accent-light hover:border-accent hover:text-accent transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => <ChatMessage key={i} message={m} />)
            )}
            {isTyping && (
              <div className="flex gap-2">
                <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                  <Bot size={13} className="text-white" />
                </div>
                <div className="bg-white border border-border rounded-lg rounded-tl-none px-3 py-2 flex gap-1 shadow-sm">
                  {[0, 1, 2].map((i) => (
                    <span key={i} className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            )}
            {error && (
              <div className="text-xs text-danger text-center">
                {error} <button onClick={retry} className="underline ml-1">Retry</button>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-border bg-white flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a security question…"
              rows={1}
              className="flex-1 resize-none border border-border rounded-md px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent text-text-primary"
              style={{ maxHeight: '80px' }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="self-end h-9 w-9 bg-accent hover:bg-accent-hover text-white rounded-md flex items-center justify-center disabled:opacity-50 transition-colors"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
