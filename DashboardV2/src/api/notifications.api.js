import api from './axios';

export const notificationsApi = {
  getAll: (params) => api.get('/api/notifications', { params }),
  markRead: (id) => api.patch(`/api/notifications/${id}/read`),
  markAllRead: () => api.post('/api/notifications/mark-all-read'),
  getUnreadCount: () => api.get('/api/notifications/unread-count'),
};
