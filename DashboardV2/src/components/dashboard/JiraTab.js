import React, { useState } from 'react';
import { ExternalLink, RefreshCw, Plus } from 'lucide-react';
import { formatRelative } from '../../utils/formatters';
import EmptyState from '../common/EmptyState';

const sampleTickets = [
  { id: 'SEC-142', summary: 'SQL Injection in authentication endpoint', finding: 'SQL Injection (f1)', priority: 'Critical', status: 'In Progress', assignee: 'Alice Chen', created: '2024-01-15T10:35:00Z', last_sync: '2024-01-15T10:40:00Z' },
  { id: 'SEC-141', summary: 'Hardcoded AWS credentials in config file', finding: 'AWS Credentials (f3)', priority: 'Critical', status: 'Open', assignee: 'Bob Kim', created: '2024-01-14T22:05:00Z', last_sync: '2024-01-15T08:00:00Z' },
  { id: 'SEC-139', summary: 'XSS vulnerability in user profile page', finding: 'XSS (f4)', priority: 'High', status: 'Done', assignee: 'Carol Wu', created: '2024-01-14T19:00:00Z', last_sync: '2024-01-15T07:30:00Z' },
];

const PRIORITY_COLORS = {
  Critical: 'bg-critical-light text-critical',
  High: 'bg-danger-light text-danger',
  Medium: 'bg-warning-light text-warning',
  Low: 'bg-accent-light text-accent',
};

const STATUS_COLORS = {
  Open: 'bg-accent-light text-accent',
  'In Progress': 'bg-warning-light text-warning',
  Done: 'bg-success-light text-success',
  Closed: 'bg-bg-tertiary text-text-muted',
};

export default function JiraTab({ projectId }) {
  const [selected, setSelected] = useState([]);
  const tickets = sampleTickets;

  const toggleSelect = (id) =>
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {selected.length > 0 && (
            <>
              <span className="text-sm text-text-secondary">{selected.length} selected</span>
              <button className="px-3 py-1.5 text-xs font-medium text-accent bg-accent-light rounded-md hover:bg-blue-100 flex items-center gap-1">
                <RefreshCw size={12} /> Sync Selected
              </button>
            </>
          )}
        </div>
        <button className="flex items-center gap-2 h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-md transition-colors">
          <Plus size={14} /> Create Batch Tickets
        </button>
      </div>

      {tickets.length === 0 ? (
        <EmptyState title="No Jira tickets linked" message="Link findings to Jira tickets to track remediation progress." />
      ) : (
        <div className="bg-white border border-border rounded-lg shadow-md overflow-hidden">
          <table className="w-full text-sm table-striped">
            <thead>
              <tr className="border-b border-border bg-bg-secondary">
                <th className="px-4 py-3 w-8">
                  <input type="checkbox" className="w-4 h-4" onChange={(e) => setSelected(e.target.checked ? tickets.map((t) => t.id) : [])} />
                </th>
                {['Ticket Key', 'Summary', 'Finding', 'Priority', 'Status', 'Assignee', 'Created', 'Last Sync', ''].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} className="border-b border-border hover:bg-accent-light transition-colors">
                  <td className="px-4 py-3">
                    <input type="checkbox" checked={selected.includes(t.id)} onChange={() => toggleSelect(t.id)} className="w-4 h-4" />
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs font-semibold text-accent hover:underline cursor-pointer flex items-center gap-1">
                      {t.id} <ExternalLink size={10} />
                    </span>
                  </td>
                  <td className="px-4 py-3 max-w-xs">
                    <p className="truncate text-text-primary font-medium text-sm">{t.summary}</p>
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs truncate max-w-32">{t.finding}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${PRIORITY_COLORS[t.priority] || ''}`}>{t.priority}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[t.status] || ''}`}>{t.status}</span>
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs">{t.assignee}</td>
                  <td className="px-4 py-3 text-text-muted text-xs">{formatRelative(t.created)}</td>
                  <td className="px-4 py-3 text-text-muted text-xs">{formatRelative(t.last_sync)}</td>
                  <td className="px-4 py-3">
                    <button className="text-xs text-accent hover:text-accent-hover flex items-center gap-1">
                      <RefreshCw size={11} /> Sync
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
