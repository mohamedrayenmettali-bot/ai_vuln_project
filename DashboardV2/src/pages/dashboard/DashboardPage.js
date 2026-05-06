import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Play, Download, ExternalLink, RefreshCw, ChevronRight } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useProject, useProjectOverview, useSyncFindings } from '../../hooks/useProjects';
import { canAccessTab } from '../../utils/roleGuards';
import { DASHBOARD_TABS } from '../../utils/constants';
import { formatRelative } from '../../utils/formatters';
import OverviewTab from '../../components/dashboard/OverviewTab';
import FindingsTab from '../../components/dashboard/FindingsTab';
import PipelineTab from '../../components/dashboard/PipelineTab';
import AiModelTab from '../../components/dashboard/AiModelTab';
import JiraTab from '../../components/dashboard/JiraTab';
import SettingsTab from '../../components/dashboard/SettingsTab';
import FindingDrawer from '../../components/dashboard/FindingDrawer';
import { sampleProjects } from '../../utils/sampleData';
import toast from 'react-hot-toast';

const TAB_LABELS = {
  [DASHBOARD_TABS.OVERVIEW]: 'Overview',
  [DASHBOARD_TABS.FINDINGS]: 'Findings',
  [DASHBOARD_TABS.PIPELINE]: 'Pipeline',
  [DASHBOARD_TABS.AI_MODEL]: 'AI Model',
  [DASHBOARD_TABS.JIRA]: 'Jira Tickets',
  [DASHBOARD_TABS.SETTINGS]: 'Settings',
};

export default function DashboardPage() {
  const { id } = useParams();
  const { role } = useAuth();
  const [activeTab, setActiveTab] = useState(DASHBOARD_TABS.OVERVIEW);
  const [selectedFinding, setSelectedFinding] = useState(null);

  const { data: project } = useProject(id);
  const { data: overview, isLoading: overviewLoading } = useProjectOverview(id);

  const displayProject = project || sampleProjects.find((p) => p.id === id) || sampleProjects[0];

  const visibleTabs = Object.values(DASHBOARD_TABS).filter((tab) => canAccessTab(role, tab));

  const { mutate: syncFindings, isPending: isSyncing } = useSyncFindings(id);

  const handleRunScan = () => toast.success('Security scan initiated for ' + displayProject.name);
  const handleExport = () => toast.success('PDF export started. You will be notified when ready.');
  const handleSync = () => {
    syncFindings();
  };

  const pipelineStatusMap = {
    passed: 'bg-success-light text-success',
    failed: 'bg-danger-light text-danger',
    running: 'bg-accent-light text-accent',
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-text-muted">
        <Link to="/home" className="hover:text-text-primary">Home</Link>
        <ChevronRight size={14} />
        <span>Projects</span>
        <ChevronRight size={14} />
        <span className="text-text-primary font-medium">{displayProject?.name || 'Dashboard'}</span>
      </nav>

      {/* Page header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-text-primary">{displayProject?.name || 'Project Dashboard'}</h1>
            {displayProject?.status && (
              <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${
                displayProject.status === 'active' ? 'bg-success-light text-success' : 'bg-bg-tertiary text-text-muted'
              }`}>
                {displayProject.status}
              </span>
            )}
          </div>
          <p className="text-sm text-text-muted">
            Last scan: <span className="text-text-secondary font-medium">{formatRelative(displayProject?.last_scan)}</span>
            {displayProject?.pipeline_status && (
              <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${pipelineStatusMap[displayProject.pipeline_status] || ''}`}>
                {displayProject.pipeline_status}
              </span>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { label: 'Run Scan', icon: Play, onClick: handleRunScan },
            { label: 'Export PDF', icon: Download, onClick: handleExport },
            { label: 'Open in Jira', icon: ExternalLink, onClick: () => {} },
            { label: isSyncing ? 'Syncing...' : 'Sync Findings', icon: RefreshCw, onClick: handleSync, disabled: isSyncing },
          ].map(({ label, icon: Icon, onClick, disabled }) => (
            <button
              key={label}
              onClick={onClick}
              disabled={disabled}
              className="flex items-center gap-2 h-9 px-3 text-sm font-medium text-text-secondary bg-white border border-border rounded-md hover:bg-bg-secondary transition-colors disabled:opacity-50"
            >
              <Icon size={14} className={disabled ? 'animate-spin' : ''} /> {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab nav */}
      <div className="border-b border-border">
        <nav className="flex gap-0">
          {visibleTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap -mb-px ${
                activeTab === tab
                  ? 'border-accent text-accent'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              }`}
            >
              {TAB_LABELS[tab]}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div>
        {activeTab === DASHBOARD_TABS.OVERVIEW && (
          <OverviewTab overview={overview} loading={overviewLoading} projectId={id} />
        )}
        {activeTab === DASHBOARD_TABS.FINDINGS && (
          <FindingsTab projectId={id} onSelectFinding={setSelectedFinding} />
        )}
        {activeTab === DASHBOARD_TABS.PIPELINE && <PipelineTab projectId={id} />}
        {activeTab === DASHBOARD_TABS.AI_MODEL && <AiModelTab />}
        {activeTab === DASHBOARD_TABS.JIRA && <JiraTab projectId={id} />}
        {activeTab === DASHBOARD_TABS.SETTINGS && <SettingsTab projectId={id} />}
      </div>

      {/* Finding drawer */}
      {selectedFinding && (
        <FindingDrawer finding={selectedFinding} onClose={() => setSelectedFinding(null)} />
      )}
    </div>
  );
}
