import api from './axios';

export const llmApi = {
  chat: (messages, context = {}, config = {}) =>
    api.post('/api/llm/chat', { messages, context }, config),
};
