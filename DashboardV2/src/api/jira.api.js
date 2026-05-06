import api from './axios';

export const jiraApi = {
  getConfig: (projectId) => api.get(`/api/integrations/jira/config`, { params: { project_id: projectId } }),
  saveConfig: (data) => api.post('/api/integrations/jira/config', data),
  testConnection: (data) => api.post('/api/integrations/jira/test', data),
  createTicket: (data) => api.post('/api/integrations/jira/create-ticket', data),
  sync: (data) => api.post('/api/integrations/jira/sync', data),
  getTickets: (projectId, params) =>
    api.get(`/api/projects/${projectId}/jira-tickets`, { params }),
};
