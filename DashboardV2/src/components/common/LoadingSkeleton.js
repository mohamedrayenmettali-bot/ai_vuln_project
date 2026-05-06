import React from 'react';

export default function LoadingSkeleton({ rows = 5, cols = 4, type = 'table' }) {
  if (type === 'card') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="bg-white border border-border rounded-lg p-6 animate-pulse">
            <div className="h-5 bg-bg-tertiary rounded w-2/3 mb-4" />
            <div className="h-3 bg-bg-tertiary rounded w-full mb-2" />
            <div className="h-3 bg-bg-tertiary rounded w-5/6 mb-4" />
            <div className="flex gap-2 mb-4">
              {Array.from({ length: 3 }).map((_, j) => (
                <div key={j} className="h-5 bg-bg-tertiary rounded w-16" />
              ))}
            </div>
            <div className="h-8 bg-bg-tertiary rounded w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'kpi') {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="bg-white border border-border rounded-lg p-6 animate-pulse">
            <div className="flex justify-between mb-3">
              <div className="h-4 bg-bg-tertiary rounded w-24" />
              <div className="h-9 w-9 bg-bg-tertiary rounded-md" />
            </div>
            <div className="h-8 bg-bg-tertiary rounded w-20 mb-2" />
            <div className="h-3 bg-bg-tertiary rounded w-32" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 py-3 border-b border-border">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className="h-4 bg-bg-tertiary rounded flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}
