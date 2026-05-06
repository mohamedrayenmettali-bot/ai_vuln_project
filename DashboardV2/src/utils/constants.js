export const ROLES = {
  DEVELOPER: 'developer',
  SCRUM_MASTER: 'scrum_master',
  SECURITY_ANALYST: 'security_analyst',
  DEVOPS_ENGINEER: 'devops_engineer',
  ADMIN: 'admin',
};

export const SEVERITY = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
  INFO: 'info',
};

export const SEVERITY_COLORS = {
  critical: { bg: 'bg-critical-light', text: 'text-critical', border: 'border-critical' },
  high: { bg: 'bg-danger-light', text: 'text-danger', border: 'border-danger' },
  medium: { bg: 'bg-warning-light', text: 'text-warning', border: 'border-warning' },
  low: { bg: 'bg-accent-light', text: 'text-accent', border: 'border-accent' },
  info: { bg: 'bg-bg-tertiary', text: 'text-text-muted', border: 'border-border' },
};

export const FINDING_STATUS = {
  OPEN: 'open',
  IN_PROGRESS: 'in_progress',
  ACCEPTED: 'accepted',
  CLOSED: 'closed',
};

export const FINDING_STATUS_COLORS = {
  open: { bg: 'bg-accent-light', text: 'text-accent' },
  in_progress: { bg: 'bg-warning-light', text: 'text-warning' },
  accepted: { bg: 'bg-bg-tertiary', text: 'text-text-muted' },
  closed: { bg: 'bg-success-light', text: 'text-success' },
};

export const PIPELINE_STATUS = {
  PASSED: 'passed',
  FAILED: 'failed',
  RUNNING: 'running',
  SKIPPED: 'skipped',
};

export const SCANNERS = ['SonarQube', 'OWASP ZAP', 'Trivy', 'Semgrep', 'Bandit'];

export const TECH_STACKS = ['React', 'Vue', 'Angular', 'Django', 'FastAPI', 'Spring Boot', 'Docker', 'Kubernetes', 'Node.js', 'PostgreSQL'];

export const PROJECT_STATUS = {
  ACTIVE: 'active',
  ARCHIVED: 'archived',
};

export const AI_SCORE_THRESHOLDS = {
  HIGH: 7,
  MEDIUM: 4,
};

export const DASHBOARD_TABS = {
  OVERVIEW: 'overview',
  FINDINGS: 'findings',
  PIPELINE: 'pipeline',
  AI_MODEL: 'ai_model',
  JIRA: 'jira',
  SETTINGS: 'settings',
};

export const TAB_ACCESS = {
  [DASHBOARD_TABS.OVERVIEW]: [ROLES.DEVELOPER, ROLES.SCRUM_MASTER, ROLES.SECURITY_ANALYST, ROLES.DEVOPS_ENGINEER, ROLES.ADMIN],
  [DASHBOARD_TABS.FINDINGS]: [ROLES.DEVELOPER, ROLES.SCRUM_MASTER, ROLES.SECURITY_ANALYST, ROLES.DEVOPS_ENGINEER, ROLES.ADMIN],
  [DASHBOARD_TABS.PIPELINE]: [ROLES.SECURITY_ANALYST, ROLES.DEVOPS_ENGINEER, ROLES.ADMIN],
  [DASHBOARD_TABS.AI_MODEL]: [ROLES.SECURITY_ANALYST, ROLES.ADMIN],
  [DASHBOARD_TABS.JIRA]: [ROLES.DEVELOPER, ROLES.SCRUM_MASTER, ROLES.SECURITY_ANALYST, ROLES.ADMIN],
  [DASHBOARD_TABS.SETTINGS]: [ROLES.SECURITY_ANALYST, ROLES.DEVOPS_ENGINEER, ROLES.ADMIN],
};

export const NOTIFICATION_TYPES = {
  FINDING: 'finding',
  PIPELINE: 'pipeline',
  JIRA: 'jira',
  SYSTEM: 'system',
};

export const PAGE_SIZE = 25;
