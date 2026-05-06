import React from 'react';

export default function KpiCard({ title, value, icon: Icon, trend, trendLabel, accentColor, subtitle }) {
  const trendPositive = trend && Number(trend) > 0;
  const trendNegative = trend && Number(trend) < 0;

  return (
    <div className="bg-white border border-border rounded-lg shadow-md p-6 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-text-secondary">{title}</span>
        {Icon && (
          <div
            className="w-9 h-9 rounded-md flex items-center justify-center"
            style={{ backgroundColor: accentColor ? `${accentColor}1A` : '#EFF6FF' }}
          >
            <Icon size={18} style={{ color: accentColor || '#2563EB' }} />
          </div>
        )}
      </div>
      <div className="flex items-end gap-3">
        <span className="text-3xl font-bold text-text-primary">{value}</span>
        {trend !== undefined && (
          <span
            className={`text-sm font-medium mb-1 ${
              trendPositive ? 'text-success' : trendNegative ? 'text-danger' : 'text-text-muted'
            }`}
          >
            {trendPositive ? '↑' : trendNegative ? '↓' : '—'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      {(trendLabel || subtitle) && (
        <p className="text-xs text-text-muted">{trendLabel || subtitle}</p>
      )}
    </div>
  );
}
