import api from './axios';

export const adminApi = {
  getUsers: (params) => api.get('/api/admin/users', { params }),
  updateUser: (id, data) => api.put(`/api/admin/users/${id}`, data),
  deactivateUser: (id) => api.patch(`/api/admin/users/${id}/deactivate`),
  resetPassword: (id) => api.post(`/api/admin/users/${id}/reset-password`),
  inviteUser: (data) => api.post('/api/admin/users/invite', data),
  getIntegrations: () => api.get('/api/admin/integrations'),
  getSystemInfo: () => api.get('/api/admin/system'),
  retrainAll: () => api.post('/api/ml/retrain'),
  getRetrainStatus: () => api.get('/api/ml/retrain/status'),
  refreshEpss: () => api.post('/api/admin/epss/refresh'),
  getAuditLog: (params) => api.get('/api/admin/audit-log', { params }),
  exportAuditLog: () => api.get('/api/admin/audit-log/export', { responseType: 'blob' }),
};
