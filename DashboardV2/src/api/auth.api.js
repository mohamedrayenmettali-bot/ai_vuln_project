import api from './axios';

export const authApi = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  register: (data) => api.post('/api/auth/register', data),
  forgotPassword: (email) => api.post('/api/auth/forgot-password', { email }),
  me: () => api.get('/api/auth/me'),
};
