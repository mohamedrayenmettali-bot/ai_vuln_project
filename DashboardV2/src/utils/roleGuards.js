import { ROLES, TAB_ACCESS } from './constants';

export function hasRole(userRole, allowedRoles) {
  if (!allowedRoles || allowedRoles.length === 0) return true;
  return allowedRoles.includes(userRole);
}

export function isAdmin(role) {
  return role === ROLES.ADMIN;
}

export function isSecurityAnalyst(role) {
  return role === ROLES.SECURITY_ANALYST || role === ROLES.ADMIN;
}

export function isDevops(role) {
  return role === ROLES.DEVOPS_ENGINEER || role === ROLES.ADMIN;
}

export function canAccessTab(role, tab) {
  const allowed = TAB_ACCESS[tab];
  if (!allowed) return false;
  return allowed.includes(role);
}

export function getAccessibleTabs(role) {
  return Object.entries(TAB_ACCESS)
    .filter(([, roles]) => roles.includes(role))
    .map(([tab]) => tab);
}

export function canManageUsers(role) {
  return role === ROLES.ADMIN;
}

export function canViewAiModel(role) {
  return [ROLES.SECURITY_ANALYST, ROLES.ADMIN].includes(role);
}

export function canRetrainModel(role) {
  return [ROLES.SECURITY_ANALYST, ROLES.ADMIN].includes(role);
}

export function canCreateJiraTickets(role) {
  return [ROLES.SECURITY_ANALYST, ROLES.ADMIN, ROLES.DEVELOPER, ROLES.SCRUM_MASTER].includes(role);
}

export function canManageJiraSettings(role) {
  return [ROLES.SECURITY_ANALYST, ROLES.ADMIN].includes(role);
}

export function getRoleBadgeClass(role) {
  const map = {
    admin: 'bg-critical-light text-critical',
    security_analyst: 'bg-danger-light text-danger',
    devops_engineer: 'bg-accent-light text-accent',
    scrum_master: 'bg-warning-light text-warning',
    developer: 'bg-success-light text-success',
  };
  return map[role] || 'bg-bg-tertiary text-text-muted';
}
