import React, { useState } from 'react';
import { UserPlus, Edit2, UserX, Key, Eye, Cpu, Activity, Download } from 'lucide-react';
import { getRoleBadgeClass } from '../../utils/roleGuards';
import { getRoleLabel, formatRelative } from '../../utils/formatters';
import toast from 'react-hot-toast';

const TABS = ['Users', 'Integrations', 'System', 'Audit Log'];

const sampleUsers = [
  { id: 'u1', name: 'Alice Chen', email: 'alice@company.com', role: 'security_analyst', status: 'active', last_login: '2024-01-15T10:30:00Z' },
  { id: 'u2', name: 'Bob Kim', email: 'bob@company.com', role: 'developer', status: 'active', last_login: '2024-01-15T09:00:00Z' },
  { id: 'u3', name: 'Carol Wu', email: 'carol@company.com', role: 'scrum_master', status: 'active', last_login: '2024-01-14T18:00:00Z' },
  { id: 'u4', name: 'Dan Lee', email: 'dan@company.com', role: 'devops_engineer', status: 'active', last_login: '2024-01-14T12:00:00Z' },
  { id: 'u5', name: 'Eve Martinez', email: 'eve@company.com', role: 'developer', status: 'inactive', last_login: '2024-01-10T08:00:00Z' },
];

const sampleAuditLog = [
  { timestamp: '2024-01-15T10:35:00Z', user: 'Alice Chen', action: 'CREATE_FINDING', resource: 'Finding #312', ip: '192.168.1.105', details: 'SQL Injection detected' },
  { timestamp: '2024-01-15T09:00:00Z', user: 'System', action: 'PIPELINE_RUN', resource: 'Core Banking API #142', ip: '10.0.0.1', details: 'Automated scan triggered' },
  { timestamp: '2024-01-14T22:05:00Z', user: 'Alice Chen', action: 'CREATE_JIRA', resource: 'SEC-142', ip: '192.168.1.105', details: 'Ticket created from finding' },
  { timestamp: '2024-01-14T20:00:00Z', user: 'System', action: 'ML_RETRAIN', resource: 'AI Model v2.4.1', ip: '10.0.0.1', details: 'Model retrained on 48,320 samples' },
];

function UsersTab() {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-sm text-text-muted">{sampleUsers.length} users registered</p>
        <button onClick={() => toast.success('Invite modal would open here.')} className="flex items-center gap-2 h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-md transition-colors">
          <UserPlus size={14} /> Invite User
        </button>
      </div>
      <div className="bg-white border border-border rounded-lg shadow-md overflow-hidden">
        <table className="w-full text-sm table-striped">
          <thead>
            <tr className="border-b border-border bg-bg-secondary">
              {['User', 'Role', 'Status', 'Last Login', 'Actions'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sampleUsers.map((u) => (
              <tr key={u.id} className="border-b border-border">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center text-sm font-semibold flex-shrink-0">
                      {u.name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-text-primary">{u.name}</p>
                      <p className="text-xs text-text-muted">{u.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRoleBadgeClass(u.role)}`}>{getRoleLabel(u.role)}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${u.status === 'active' ? 'bg-success-light text-success' : 'bg-bg-tertiary text-text-muted'}`}>
                    {u.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-text-muted text-xs">{formatRelative(u.last_login)}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <button onClick={() => toast.success(`Edit ${u.name}`)} className="p-1.5 text-text-muted hover:text-accent rounded" title="Edit role"><Edit2 size={13} /></button>
                    <button onClick={() => toast.success(`Deactivate ${u.name}`)} className="p-1.5 text-text-muted hover:text-danger rounded" title="Deactivate"><UserX size={13} /></button>
                    <button onClick={() => toast.success(`Reset password for ${u.name}`)} className="p-1.5 text-text-muted hover:text-warning rounded" title="Reset password"><Key size={13} /></button>
                    <button onClick={() => toast.success(`Impersonating ${u.name}`)} className="p-1.5 text-text-muted hover:text-critical rounded" title="Impersonate"><Eye size={13} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function IntegrationsTab() {
  const integrations = [
    { name: 'Jira', status: 'connected', icon: '🔗' },
    { name: 'Slack', status: 'not_connected', icon: '💬' },
    { name: 'SonarQube', status: 'connected', icon: '🔍' },
    { name: 'GitHub', status: 'connected', icon: '🐙' },
    { name: 'GitLab', status: 'not_connected', icon: '🦊' },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {integrations.map((intg) => (
        <div key={intg.name} className="bg-white border border-border rounded-lg shadow-md p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{intg.icon}</span>
            <div>
              <p className="font-semibold text-text-primary text-sm">{intg.name}</p>
              <span className={`text-xs font-medium ${intg.status === 'connected' ? 'text-success' : 'text-text-muted'}`}>
                {intg.status === 'connected' ? '● Connected' : '○ Not connected'}
              </span>
            </div>
          </div>
          <button
            onClick={() => toast.success(`${intg.name} ${intg.status === 'connected' ? 'settings' : 'connect'} clicked`)}
            className={`h-8 px-3 text-xs font-medium rounded-md transition-colors ${
              intg.status === 'connected'
                ? 'text-text-secondary bg-bg-secondary border border-border hover:bg-bg-tertiary'
                : 'text-white bg-accent hover:bg-accent-hover'
            }`}
          >
            {intg.status === 'connected' ? 'Configure' : 'Connect'}
          </button>
        </div>
      ))}
    </div>
  );
}

function SystemTab() {
  return (
    <div className="space-y-6 max-w-2xl">
      <div className="bg-white border border-border rounded-lg shadow-md p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Cpu size={16} className="text-critical" /> ML Model</h3>
        <div className="grid grid-cols-3 gap-4 text-sm mb-4">
          <div><p className="text-xs text-text-muted">Version</p><p className="font-mono font-semibold text-text-primary">v2.4.1</p></div>
          <div><p className="text-xs text-text-muted">Global Accuracy</p><p className="font-semibold text-success">94.2%</p></div>
          <div><p className="text-xs text-text-muted">Dataset Size</p><p className="font-semibold text-text-primary">48,320</p></div>
        </div>
        <button onClick={() => toast.success('Retraining all models...')} className="h-9 px-4 text-sm font-medium text-white bg-critical hover:bg-purple-700 rounded-md transition-colors">
          Retrain All Models
        </button>
      </div>

      <div className="bg-white border border-border rounded-lg shadow-md p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Activity size={16} className="text-accent" /> EPSS Data</h3>
        <p className="text-sm text-text-muted mb-3">Last updated: <strong className="text-text-secondary">2024-01-15 02:00 UTC</strong></p>
        <button onClick={() => toast.success('Refreshing EPSS data...')} className="h-9 px-4 text-sm font-medium text-accent bg-accent-light hover:bg-blue-100 rounded-md transition-colors">
          Refresh EPSS Data
        </button>
      </div>

      <div className="bg-white border border-border rounded-lg shadow-md p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-4">Celery Workers</h3>
        <div className="space-y-2">
          {[
            { name: 'scan_worker', status: 'running' },
            { name: 'ml_worker', status: 'running' },
            { name: 'jira_worker', status: 'running' },
            { name: 'epss_worker', status: 'stopped' },
          ].map((w) => (
            <div key={w.name} className="flex items-center justify-between py-2 border-b border-border last:border-0">
              <span className="font-mono text-sm text-text-secondary">{w.name}</span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${w.status === 'running' ? 'bg-success-light text-success' : 'bg-danger-light text-danger'}`}>
                {w.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AuditLogTab() {
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => toast.success('Exporting audit log...')} className="flex items-center gap-2 h-9 px-3 text-sm font-medium text-text-secondary bg-white border border-border rounded-md hover:bg-bg-secondary transition-colors">
          <Download size={14} /> Export CSV
        </button>
      </div>
      <div className="bg-white border border-border rounded-lg shadow-md overflow-hidden">
        <table className="w-full text-sm table-striped">
          <thead>
            <tr className="border-b border-border bg-bg-secondary">
              {['Timestamp', 'User', 'Action', 'Resource', 'IP Address', 'Details'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sampleAuditLog.map((entry, i) => (
              <tr key={i} className="border-b border-border">
                <td className="px-4 py-3 text-xs text-text-muted font-mono">{formatRelative(entry.timestamp)}</td>
                <td className="px-4 py-3 text-text-secondary text-sm">{entry.user}</td>
                <td className="px-4 py-3"><span className="font-mono text-xs bg-bg-tertiary px-2 py-0.5 rounded">{entry.action}</span></td>
                <td className="px-4 py-3 text-text-secondary text-xs">{entry.resource}</td>
                <td className="px-4 py-3 font-mono text-xs text-text-muted">{entry.ip}</td>
                <td className="px-4 py-3 text-text-secondary text-xs max-w-xs truncate">{entry.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('Users');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Admin Panel</h1>
        <p className="text-sm text-text-muted mt-1">Manage users, integrations, and system settings</p>
      </div>

      <div className="flex gap-0 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab ? 'border-accent text-accent' : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div>
        {activeTab === 'Users' && <UsersTab />}
        {activeTab === 'Integrations' && <IntegrationsTab />}
        {activeTab === 'System' && <SystemTab />}
        {activeTab === 'Audit Log' && <AuditLogTab />}
      </div>
    </div>
  );
}
