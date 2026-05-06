import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar,
} from 'recharts';
import { AlertTriangle, Shield, Activity, TrendingUp, ArrowRight } from 'lucide-react';
import SeverityBadge from '../common/SeverityBadge';
import LoadingSkeleton from '../common/LoadingSkeleton';
import { formatDate, formatAiScore } from '../../utils/formatters';
import { sampleOverview } from '../../utils/sampleData';

const PIE_COLORS = {
  critical: '#7C3AED',
  high: '#DC2626',
  medium: '#D97706',
  low: '#2563EB',
  info: '#94A3B8',
};

const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low'];

export default function OverviewTab({ overview: overviewData, loading, projectId }) {
  const navigate = useNavigate();
  const overview = overviewData || sampleOverview;

  const total = overview.total || (overview.critical + overview.high + overview.medium + overview.low);

  const pieData = SEVERITY_ORDER.map((sev) => ({
    name: sev.charAt(0).toUpperCase() + sev.slice(1),
    value: overview[sev] || 0,
    color: PIE_COLORS[sev],
  }));

  if (loading) {
    return <LoadingSkeleton type="kpi" cols={5} />;
  }

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          { key: 'total', label: 'Total', color: '#2563EB', icon: Activity },
          { key: 'critical', label: 'Critical', color: '#7C3AED', icon: Shield },
          { key: 'high', label: 'High', color: '#DC2626', icon: AlertTriangle },
          { key: 'medium', label: 'Medium', color: '#D97706', icon: AlertTriangle },
          { key: 'low', label: 'Low', color: '#2563EB', icon: TrendingUp },
        ].map(({ key, label, color, icon }) => (
          <div
            key={key}
            className="bg-white border border-border rounded-lg shadow-md p-4 border-l-4"
            style={{ borderLeftColor: color }}
          >
            <p className="text-xs font-medium text-text-muted mb-1">{label}</p>
            <p className="text-2xl font-bold text-text-primary">{(overview[key] || 0).toLocaleString()}</p>
            {key !== 'total' && total > 0 && (
              <p className="text-xs text-text-muted mt-1">
                {((overview[key] / total) * 100).toFixed(1)}% of total
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Line chart */}
        <div className="bg-white border border-border rounded-lg shadow-md p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Findings Over Time (30 days)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={overview.findings_over_time || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} tickFormatter={(d) => d.slice(5)} />
              <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="critical" stroke="#7C3AED" strokeWidth={2} dot={false} name="Critical" />
              <Line type="monotone" dataKey="high" stroke="#DC2626" strokeWidth={2} dot={false} name="High" />
              <Line type="monotone" dataKey="medium" stroke="#D97706" strokeWidth={2} dot={false} name="Medium" />
              <Line type="monotone" dataKey="low" stroke="#2563EB" strokeWidth={2} dot={false} name="Low" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Donut chart */}
        <div className="bg-white border border-border rounded-lg shadow-md p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Severity Distribution</h3>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={2}>
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip formatter={(value, name) => [value, name]} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-col gap-2">
              {pieData.map((d) => (
                <div key={d.name} className="flex items-center gap-2 text-sm">
                  <span className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: d.color }} />
                  <span className="text-text-secondary">{d.name}</span>
                  <span className="font-semibold text-text-primary ml-auto">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By scanner */}
        <div className="bg-white border border-border rounded-lg shadow-md p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Findings by Scanner</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={overview.by_scanner || []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <YAxis type="category" dataKey="scanner" tick={{ fontSize: 11, fill: '#475569' }} width={80} />
              <Tooltip />
              <Bar dataKey="count" fill="#2563EB" radius={[0, 4, 4, 0]} name="Findings" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* AI Score distribution */}
        <div className="bg-white border border-border rounded-lg shadow-md p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-4">AI Risk Score Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={overview.ai_score_distribution || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="range" tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <Tooltip />
              <Bar dataKey="count" fill="#7C3AED" radius={[4, 4, 0, 0]} name="Findings" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Critical */}
      <div className="bg-white border border-border rounded-lg shadow-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Recent Critical Findings</h3>
          <button
            onClick={() => navigate(`/projects/${projectId}/dashboard?tab=findings`)}
            className="text-xs text-accent hover:text-accent-hover font-medium flex items-center gap-1"
          >
            View all <ArrowRight size={12} />
          </button>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-bg-secondary">
              <th className="px-5 py-3 text-left text-xs font-semibold text-text-muted uppercase">Finding</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase">Severity</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase">Scanner</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase">AI Score</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase">Date</th>
            </tr>
          </thead>
          <tbody>
            {(overview.recent_critical || []).map((f) => (
              <tr key={f.id} className="border-b border-border hover:bg-accent-light transition-colors">
                <td className="px-5 py-3 font-medium text-text-primary max-w-xs truncate">{f.title}</td>
                <td className="px-4 py-3"><SeverityBadge severity={f.severity} /></td>
                <td className="px-4 py-3 text-text-secondary text-xs">{f.scanner}</td>
                <td className="px-4 py-3">
                  <span className={`font-semibold text-sm ${f.ai_score >= 7 ? 'text-danger' : f.ai_score >= 4 ? 'text-warning' : 'text-success'}`}>
                    {formatAiScore(f.ai_score)}
                  </span>
                </td>
                <td className="px-4 py-3 text-text-muted text-xs">{formatDate(f.date)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
