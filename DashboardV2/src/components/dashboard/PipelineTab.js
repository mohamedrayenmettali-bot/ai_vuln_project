import React, { useState } from 'react';
import { ChevronDown, CheckCircle, XCircle, Loader, AlertCircle, Clock } from 'lucide-react';
import { formatRelative } from '../../utils/formatters';
import { samplePipeline } from '../../utils/sampleData';

function StatusIcon({ status }) {
  if (status === 'passed') return <CheckCircle size={14} className="text-success" />;
  if (status === 'failed') return <XCircle size={14} className="text-danger" />;
  if (status === 'running') return <Loader size={14} className="text-accent animate-spin" />;
  return <AlertCircle size={14} className="text-text-muted" />;
}

function StatusBadge({ status }) {
  const map = {
    passed: 'bg-success-light text-success',
    failed: 'bg-danger-light text-danger',
    running: 'bg-accent-light text-accent',
    skipped: 'bg-bg-tertiary text-text-muted',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${map[status] || map.skipped}`}>
      {status}
    </span>
  );
}

function SummaryCard({ type, data }) {
  const colors = {
    sast: { bg: 'bg-critical-light', text: 'text-critical', label: 'SAST Scan' },
    dast: { bg: 'bg-danger-light', text: 'text-danger', label: 'DAST Scan' },
    sca: { bg: 'bg-accent-light', text: 'text-accent', label: 'SCA / Dependencies' },
    secrets: { bg: 'bg-success-light', text: 'text-success', label: 'Secrets Scan' },
  };
  const config = colors[type] || {};
  return (
    <div className="bg-white border border-border rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-text-primary">{config.label}</p>
        <StatusBadge status={data?.status} />
      </div>
      <div className="flex items-end gap-3">
        <div>
          <p className="text-2xl font-bold text-text-primary">{data?.new_findings ?? 0}</p>
          <p className="text-xs text-text-muted">New findings</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-semibold text-text-secondary">{data?.total ?? 0}</p>
          <p className="text-xs text-text-muted">Total</p>
        </div>
      </div>
    </div>
  );
}

export default function PipelineTab({ projectId }) {
  const [expandedRun, setExpandedRun] = useState(null);
  const pipeline = samplePipeline;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(pipeline.summary).map(([type, data]) => (
          <SummaryCard key={type} type={type} data={data} />
        ))}
      </div>

      {/* Runs table */}
      <div className="bg-white border border-border rounded-lg shadow-md overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Pipeline Runs</h3>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-bg-secondary">
              {['Run #', 'Triggered By', 'Branch', 'Status', 'Duration', 'Date', ''].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pipeline.runs.map((run) => (
              <React.Fragment key={run.id}>
                <tr className="border-b border-border hover:bg-bg-secondary transition-colors">
                  <td className="px-4 py-3 font-mono text-sm font-semibold text-text-primary">#{run.run_number}</td>
                  <td className="px-4 py-3 text-text-secondary">{run.triggered_by}</td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs bg-bg-tertiary px-2 py-1 rounded">{run.branch}</span>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={run.status} /></td>
                  <td className="px-4 py-3 text-text-secondary text-xs">
                    <span className="flex items-center gap-1"><Clock size={12} />{run.duration}</span>
                  </td>
                  <td className="px-4 py-3 text-text-muted text-xs">{formatRelative(run.date)}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setExpandedRun(expandedRun === run.id ? null : run.id)}
                      className="flex items-center gap-1 text-xs text-accent hover:text-accent-hover font-medium"
                    >
                      Details
                      <ChevronDown size={12} className={`transition-transform ${expandedRun === run.id ? 'rotate-180' : ''}`} />
                    </button>
                  </td>
                </tr>
                {expandedRun === run.id && (
                  <tr>
                    <td colSpan={7} className="bg-bg-secondary border-b border-border">
                      <div className="px-6 py-4">
                        <p className="text-xs font-semibold text-text-muted uppercase mb-3">Scanner Results</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                          {run.scanners.map((s) => (
                            <div key={s.name} className="bg-white border border-border rounded-md p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-text-primary">{s.name}</span>
                                <StatusIcon status={s.status} />
                              </div>
                              <div className="text-xs text-text-muted space-y-0.5">
                                <p>Findings: <span className="font-semibold text-text-primary">{s.findings}</span></p>
                                <p>Duration: <span className="text-text-secondary">{s.duration}</span></p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
