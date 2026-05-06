import { formatDistanceToNow, format, parseISO } from 'date-fns';

export function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr;
  }
}

export function formatDatetime(dateStr) {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy HH:mm');
  } catch {
    return dateStr;
  }
}

export function formatRelative(dateStr) {
  if (!dateStr) return '—';
  try {
    return formatDistanceToNow(parseISO(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
}

export function formatCvss(score) {
  if (score === null || score === undefined) return '—';
  return Number(score).toFixed(1);
}

export function formatEpss(value) {
  if (value === null || value === undefined) return '—';
  return `${(Number(value) * 100).toFixed(2)}%`;
}

export function formatAiScore(score) {
  if (score === null || score === undefined) return '—';
  return Number(score).toFixed(1);
}

export function formatNumber(n) {
  if (n === null || n === undefined) return '—';
  return Number(n).toLocaleString();
}

export function formatPercent(n) {
  if (n === null || n === undefined) return '—';
  return `${Number(n).toFixed(1)}%`;
}

export function truncate(str, maxLen = 80) {
  if (!str) return '';
  return str.length > maxLen ? `${str.slice(0, maxLen)}…` : str;
}

export function getAiScoreColor(score) {
  if (score >= 7) return 'text-danger';
  if (score >= 4) return 'text-warning';
  return 'text-success';
}

export function getAiScoreBg(score) {
  if (score >= 7) return 'bg-danger';
  if (score >= 4) return 'bg-warning';
  return 'bg-success';
}

export function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
}

export function getRoleLabel(role) {
  const map = {
    developer: 'Developer',
    scrum_master: 'Scrum Master',
    security_analyst: 'Security Analyst',
    devops_engineer: 'DevOps Engineer',
    admin: 'Admin',
  };
  return map[role] || capitalize(role);
}

export function getPipelineStatusColor(status) {
  const map = {
    passed: 'text-success bg-success-light',
    failed: 'text-danger bg-danger-light',
    running: 'text-accent bg-accent-light',
    skipped: 'text-text-muted bg-bg-tertiary',
  };
  return map[status] || 'text-text-muted bg-bg-tertiary';
}
