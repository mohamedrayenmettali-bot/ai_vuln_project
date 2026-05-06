import { useState, useCallback, useEffect, useRef } from 'react';
import { llmApi } from '../api/llm.api';

export function useChat(initialContext = {}) {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const contextRef = useRef(initialContext);

  useEffect(() => {
    contextRef.current = initialContext;
  }, [initialContext]);

  const sendMessage = useCallback(
    async (content, retrying = false) => {
      const trimmed = content.trim();
      if (!trimmed || isTyping) return;

      const userMsg = { role: 'user', content: trimmed };
      const historyForRequest = [...messages, userMsg].slice(-10);

      setMessages((prev) => [...prev, userMsg]);
      setIsTyping(true);
      setError(null);
      try {
        const response = await llmApi.chat(historyForRequest, contextRef.current, { timeout: 30000 });
        const reply = response.data.reply || '';
        setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
      } catch (err) {
        setError('Failed to get a response. Please try again.');
        if (!retrying) {
          setMessages((prev) => prev.slice(0, -1));
        }
      } finally {
        setIsTyping(false);
      }
    },
    [messages, isTyping]
  );

  const retry = useCallback(() => {
    const lastUser = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUser) {
      setMessages((prev) => prev.filter((m) => m !== lastUser));
      sendMessage(lastUser.content, true);
    }
  }, [messages, sendMessage]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isTyping, error, sendMessage, retry, clearHistory };
}
