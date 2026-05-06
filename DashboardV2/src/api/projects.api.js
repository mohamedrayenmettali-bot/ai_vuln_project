import api from './axios';

export const projectsApi = {
  getAll: (params) => api.get('/api/projects/', { params }),
  getById: (id) => api.get(`/api/projects/${id}`),
  getOverview: (id) => api.get(`/api/projects/${id}/overview`),
  getPipeline: (id) => api.get(`/api/projects/${id}/pipeline`),
  getJiraTickets: (id, params) => api.get(`/api/projects/${id}/jira-tickets`, { params }),
  create: (data) => api.post('/api/projects/', data),
  update: (id, data) => api.put(`/api/projects/${id}`, data),
  delete: (id) => api.delete(`/api/projects/${id}`),
  runScan: (id) => api.post(`/api/projects/${id}/scan`),
  exportPdf: (id) => api.get(`/api/projects/${id}/export/pdf`, { responseType: 'blob' }),
  syncFindings: (id) => api.post(`/api/projects/${id}/sync`),
  getSettings: (id) => api.get(`/api/projects/${id}/settings`),
  updateSettings: (id, data) => api.put(`/api/projects/${id}/settings`, data),
};
