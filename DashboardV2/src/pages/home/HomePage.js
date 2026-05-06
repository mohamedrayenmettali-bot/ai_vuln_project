import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderOpen, AlertTriangle, Shield, Brain,
  Search, Filter, CheckCircle, XCircle, Loader,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useProjects } from '../../hooks/useProjects';
import KpiCard from '../../components/common/KpiCard';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import EmptyState from '../../components/common/EmptyState';
import { formatRelative, getRoleLabel } from '../../utils/formatters';
import { getRoleBadgeClass } from '../../utils/roleGuards';
import { sampleProjects } from '../../utils/sampleData';

const STACK_COLORS = {
  React: 'bg-blue-50 text-blue-600',
  Vue: 'bg-green-50 text-green-600',
  Angular: 'bg-red-50 text-red-600',
  Django: 'bg-green-50 text-green-700',
  FastAPI: 'bg-teal-50 text-teal-600',
  'Spring Boot': 'bg-lime-50 text-lime-700',
  Docker: 'bg-sky-50 text-sky-600',
  Kubernetes: 'bg-blue-50 text-blue-700',
  'Node.js': 'bg-emerald-50 text-emerald-700',
  PostgreSQL: 'bg-indigo-50 text-indigo-600',
  Redis: 'bg-red-50 text-red-600',
};

function PipelineStatusBadge({ status }) {
  const map = {
    passed: { label: 'Passed', icon: CheckCircle, cls: 'text-success bg-success-light' },
    failed: { label: 'Failed', icon: XCircle, cls: 'text-danger bg-danger-light' },
    running: { label: 'Running', icon: Loader, cls: 'text-accent bg-accent-light' },
    skipped: { label: 'Skipped', icon: null, cls: 'text-text-muted bg-bg-tertiary' },
  };
  const config = map[status] || map.skipped;
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${config.cls}`}>
      {Icon && <Icon size={11} className={status === 'running' ? 'animate-spin' : ''} />}
      {config.label}
    </span>
  );
}

function ProjectCard({ project }) {
  const navigate = useNavigate();
  const { findings_summary: fs } = project;

  return (
    <div
      className="bg-white border border-border rounded-lg shadow-md p-5 flex flex-col gap-3 cursor-pointer hover:border-accent transition-colors group"
      onClick={() => navigate(`/projects/${project.id}/dashboard`)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${project.status === 'active' ? 'bg-success' : 'bg-text-muted'}`} />
            <h3 className="font-semibold text-text-primary text-base group-hover:text-accent transition-colors truncate">
              {project.name}
            </h3>
          </div>
          <p className="text-xs text-text-muted mt-0.5 capitalize">{project.status}</p>
        </div>
        <PipelineStatusBadge status={project.pipeline_status} />
      </div>

      <p className="text-sm text-text-secondary leading-relaxed line-clamp-2">
        {project.description}
      </p>

      <div className="flex flex-wrap gap-1">
        {(project.tech_stack || []).map((tag) => (
          <span
            key={tag}
            className={`px-2 py-0.5 rounded text-xs font-medium ${STACK_COLORS[tag] || 'bg-bg-tertiary text-text-secondary'}`}
          >
            {tag}
          </span>
        ))}
      </div>

      <div className="text-xs text-text-muted">
        Last scan: <span className="text-text-secondary font-medium">{formatRelative(project.last_scan)}</span>
      </div>

      {fs && (
        <div className="flex gap-2 text-xs">
          {fs.critical > 0 && (
            <span className="bg-critical-light text-critical font-medium px-2 py-0.5 rounded">
              Critical: {fs.critical}
            </span>
          )}
          {fs.high > 0 && (
            <span className="bg-danger-light text-danger font-medium px-2 py-0.5 rounded">
              High: {fs.high}
            </span>
          )}
          {fs.medium > 0 && (
            <span className="bg-warning-light text-warning font-medium px-2 py-0.5 rounded">
              Med: {fs.medium}
            </span>
          )}
          {fs.low > 0 && (
            <span className="bg-accent-light text-accent font-medium px-2 py-0.5 rounded">
              Low: {fs.low}
            </span>
          )}
        </div>
      )}

      <button
        className="w-full h-9 text-sm font-medium text-accent border border-accent rounded-md hover:bg-accent-light transition-colors mt-1"
        onClick={(e) => {
          e.stopPropagation();
          navigate(`/projects/${project.id}/dashboard`);
        }}
      >
        View Dashboard →
      </button>
    </div>
  );
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export default function HomePage() {
  const { user, role } = useAuth();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { data: projectsData, isLoading, error } = useProjects();

  const projects = projectsData?.items || projectsData || sampleProjects;

  const filtered = useMemo(() => {
    return projects.filter((p) => {
      const matchesSearch =
        !search ||
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        (p.description || '').toLowerCase().includes(search.toLowerCase()) ||
        (p.tech_stack || []).some((t) => t.toLowerCase().includes(search.toLowerCase()));
      const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [projects, search, statusFilter]);

  const globalStats = useMemo(() => {
    const allFindings = projects.reduce(
      (acc, p) => {
        const fs = p.findings_summary || {};
        return {
          critical: acc.critical + (fs.critical || 0),
          high: acc.high + (fs.high || 0),
          medium: acc.medium + (fs.medium || 0),
          low: acc.low + (fs.low || 0),
        };
      },
      { critical: 0, high: 0, medium: 0, low: 0 }
    );
    return allFindings;
  }, [projects]);

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            {getGreeting()}, {user?.name?.split(' ')[0] || 'User'} 👋
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-text-secondary text-sm">Here's your security overview</p>
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${getRoleBadgeClass(role)}`}>
              {getRoleLabel(role)}
            </span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      {isLoading ? (
        <LoadingSkeleton type="kpi" cols={4} />
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Total Projects"
            value={projects.length}
            icon={FolderOpen}
            trend={12}
            trendLabel="vs last month"
            accentColor="#2563EB"
          />
          <KpiCard
            title="Open Findings"
            value={(globalStats.critical + globalStats.high + globalStats.medium + globalStats.low).toLocaleString()}
            icon={AlertTriangle}
            trend={-8}
            trendLabel="vs last week"
            accentColor="#DC2626"
          />
          <KpiCard
            title="Critical Unresolved"
            value={globalStats.critical}
            icon={Shield}
            trend={3}
            trendLabel="new this week"
            accentColor="#7C3AED"
          />
          <KpiCard
            title="Avg AI Risk Score"
            value="7.4"
            icon={Brain}
            trend={-5}
            trendLabel="improving"
            accentColor="#D97706"
          />
        </div>
      )}

      {/* Projects section */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <h2 className="text-lg font-semibold text-text-primary">Your Projects</h2>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white border border-border rounded-md px-3 h-9">
              <Search size={14} className="text-text-muted" />
              <input
                type="text"
                placeholder="Search projects…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="text-sm outline-none text-text-primary placeholder:text-text-muted bg-transparent w-48"
              />
            </div>
            <div className="flex items-center gap-2 bg-white border border-border rounded-md px-3 h-9">
              <Filter size={14} className="text-text-muted" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-sm outline-none text-text-primary bg-transparent"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>
        </div>

        {error && !projects.length ? (
          <EmptyState
            icon={AlertTriangle}
            title="Failed to load projects"
            message="Could not connect to the API. Showing sample data."
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={FolderOpen}
            title="No projects found"
            message="No projects match your search criteria. Try adjusting your filters."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
