import axios from 'axios';

const rawBaseUrl = process.env.REACT_APP_API_URL?.trim();
const BASE_URL = rawBaseUrl ? rawBaseUrl.replace(/\/+$/, '') : undefined;

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach Bearer token and adjust API path
api.interceptors.request.use(
  (config) => {
    // Rewrite /api/ to /api/v1/ to match backend router prefix
    if (config.url && config.url.startsWith('/api/')) {
      config.url = config.url.replace('/api/', '/api/v1/');
    }

    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — handle 401/403
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        window.location.href = '/login';
      } else if (error.response.status === 403) {
        window.location.href = '/unauthorized';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
