import React from 'react';
import { SEVERITY_COLORS } from '../../utils/constants';
import { capitalize } from '../../utils/formatters';

const SEVERITY_ICONS = {
  critical: '●',
  high: '▲',
  medium: '◆',
  low: '▼',
  info: '○',
};

export default function SeverityBadge({ severity, size = 'sm' }) {
  const s = (severity || 'info').toLowerCase();
  const colors = SEVERITY_COLORS[s] || SEVERITY_COLORS.info;
  const sizeClass = size === 'lg' ? 'px-3 py-1 text-sm' : 'px-2 py-0.5 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded ${sizeClass} ${colors.bg} ${colors.text}`}
    >
      <span className="text-xs">{SEVERITY_ICONS[s]}</span>
      {capitalize(s)}
    </span>
  );
}
