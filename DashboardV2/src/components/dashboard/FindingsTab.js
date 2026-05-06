import React, { useState } from 'react';
import { Search, Download, MoreVertical, ChevronDown } from 'lucide-react';
import SeverityBadge from '../common/SeverityBadge';
import EmptyState from '../common/EmptyState';
import { formatDate, formatCvss, formatEpss, formatAiScore, capitalize } from '../../utils/formatters';
import { FINDING_STATUS_COLORS } from '../../utils/constants';
import { sampleFindings } from '../../utils/sampleData';

function AiScoreBar({ score }) {
  const color = score >= 7 ? 'bg-danger' : score >= 4 ? 'bg-warning' : 'bg-success';
  const textColor = score >= 7 ? 'text-danger' : score >= 4 ? 'text-warning' : 'text-success';
  return (
    <div className="flex items-center gap-2">
      <span className={`text-sm font-semibold ${textColor} w-8`}>{formatAiScore(score)}</span>
      <div className="flex-1 h-1.5 bg-bg-tertiary rounded-full overflow-hidden w-16">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${(score / 10) * 100}%` }} />
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = FINDING_STATUS_COLORS[status] || { bg: 'bg-bg-tertiary', text: 'text-text-muted' };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text}`}>
      {status === 'in_progress' ? 'In Progress' : capitalize(status)}
    </span>
  );
}

const SEVERITY_OPTIONS = ['', 'critical', 'high', 'medium', 'low', 'info'];
const STATUS_OPTIONS = ['', 'open', 'in_progress', 'accepted', 'closed'];
const SCANNER_OPTIONS = ['', 'SonarQube', 'OWASP ZAP', 'Trivy', 'Semgrep', 'Bandit'];

export default function FindingsTab({ projectId, onSelectFinding }) {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [scannerFilter, setScannerFilter] = useState('');

  // Use sample data — in production this would use useFindings hook
  const findings = sampleFindings.items;
  const filtered = findings.filter((f) => {
    const matchSearch = !search || f.title.toLowerCase().includes(search.toLowerCase()) || (f.cve_id || '').toLowerCase().includes(search.toLowerCase());
    const matchSev = !severityFilter || f.severity === severityFilter;
    const matchStatus = !statusFilter || f.status === statusFilter;
    const matchScanner = !scannerFilter || f.scanner === scannerFilter;
    return matchSearch && matchSev && matchStatus && matchScanner;
  });

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2 bg-white border border-border rounded-md px-3 h-9 flex-1 min-w-48">
          <Search size={14} className="text-text-muted flex-shrink-0" />
          <input
            type="text"
            placeholder="Search by title, CVE ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="text-sm outline-none bg-transparent text-text-primary placeholder:text-text-muted w-full"
          />
        </div>

        {[
          { value: severityFilter, setter: setSeverityFilter, options: SEVERITY_OPTIONS, placeholder: 'Severity' },
          { value: scannerFilter, setter: setScannerFilter, options: SCANNER_OPTIONS, placeholder: 'Scanner' },
          { value: statusFilter, setter: setStatusFilter, options: STATUS_OPTIONS, placeholder: 'Status' },
        ].map((f, i) => (
          <div key={i} className="relative">
            <select
              value={f.value}
              onChange={(e) => f.setter(e.target.value)}
              className="appearance-none bg-white border border-border rounded-md px-3 h-9 pr-8 text-sm text-text-secondary outline-none cursor-pointer"
            >
              <option value="">{f.placeholder}: All</option>
              {f.options.filter(Boolean).map((o) => (
                <option key={o} value={o}>{o === 'in_progress' ? 'In Progress' : capitalize(o)}</option>
              ))}
            </select>
            <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
          </div>
        ))}

        <div className="ml-auto flex items-center gap-2 text-xs text-text-muted">
          Showing <strong className="text-text-primary">{filtered.length}</strong> of{' '}
          <strong className="text-text-primary">{sampleFindings.total}</strong> findings
        </div>

        <button className="flex items-center gap-2 h-9 px-3 text-sm font-medium text-text-secondary bg-white border border-border rounded-md hover:bg-bg-secondary transition-colors">
          <Download size={14} />
          Export
        </button>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <EmptyState title="No findings match your filters" message="Try adjusting your search or filter criteria." />
      ) : (
        <div className="bg-white border border-border rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm table-striped">
              <thead>
                <tr className="border-b border-border-strong bg-bg-secondary sticky top-0">
                  {['#', 'Title', 'Severity', 'Scanner', 'CVSS', 'AI Score', 'EPSS', 'Status', 'Assigned', 'Date', 'Actions'].map((col) => (
                    <th key={col} className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((f, idx) => (
                  <tr
                    key={f.id}
                    className="border-b border-border cursor-pointer hover:bg-accent-light transition-colors"
                    onClick={() => onSelectFinding && onSelectFinding(f)}
                  >
                    <td className="px-4 py-3 text-text-muted font-mono text-xs">{idx + 1}</td>
                    <td className="px-4 py-3">
                      <div className="max-w-xs">
                        <p className="font-medium text-text-primary truncate text-sm">{f.title}</p>
                        {f.cve_id && (
                          <span className="font-mono text-xs text-text-muted">{f.cve_id}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3"><SeverityBadge severity={f.severity} /></td>
                    <td className="px-4 py-3 text-text-secondary text-xs whitespace-nowrap">{f.scanner}</td>
                    <td className="px-4 py-3 font-mono text-sm text-text-primary">{formatCvss(f.cvss)}</td>
                    <td className="px-4 py-3"><AiScoreBar score={f.ai_score} /></td>
                    <td className="px-4 py-3 font-mono text-xs text-text-secondary">{formatEpss(f.epss)}</td>
                    <td className="px-4 py-3"><StatusBadge status={f.status} /></td>
                    <td className="px-4 py-3 text-text-secondary text-xs whitespace-nowrap">{f.assigned || '—'}</td>
                    <td className="px-4 py-3 text-text-muted text-xs whitespace-nowrap">{formatDate(f.date)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        <button
                          className="px-2 py-1 text-xs font-medium text-accent bg-accent-light rounded hover:bg-blue-100 transition-colors"
                          onClick={() => onSelectFinding && onSelectFinding(f)}
                        >
                          View
                        </button>
                        <button className="p-1 text-text-muted hover:text-text-primary rounded">
                          <MoreVertical size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
