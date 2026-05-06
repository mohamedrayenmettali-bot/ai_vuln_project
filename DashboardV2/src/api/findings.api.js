import api from './axios';

export const findingsApi = {
  getAll: (projectId, params) =>
    api.get(`/api/projects/${projectId}/findings`, { params }),
  getById: (id) => api.get(`/api/findings/${id}`),
  updateStatus: (id, status) => api.patch(`/api/findings/${id}/status`, { status }),
  assign: (id, userId) => api.patch(`/api/findings/${id}/assign`, { user_id: userId }),
  submitFeedback: (id, data) => api.post(`/api/findings/${id}/feedback`, data),
  getHistory: (id) => api.get(`/api/findings/${id}/history`),
  getAiAnalysis: (id) => api.get(`/api/findings/${id}/ai-analysis`),
  exportCsv: (projectId, params) =>
    api.get(`/api/projects/${projectId}/findings/export/csv`, {
      params,
      responseType: 'blob',
    }),
};
