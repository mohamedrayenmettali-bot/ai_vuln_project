import React, { useState } from 'react';
import { Bell, AlertTriangle, Activity, Link, Settings, CheckCheck, Circle } from 'lucide-react';
import { formatRelative } from '../../utils/formatters';
import { sampleNotifications } from '../../utils/sampleData';
import EmptyState from '../../components/common/EmptyState';

const TYPE_CONFIG = {
  finding: { icon: AlertTriangle, color: 'text-danger', bg: 'bg-danger-light' },
  pipeline: { icon: Activity, color: 'text-accent', bg: 'bg-accent-light' },
  jira: { icon: Link, color: 'text-critical', bg: 'bg-critical-light' },
  system: { icon: Settings, color: 'text-text-secondary', bg: 'bg-bg-tertiary' },
};

const FILTERS = ['All', 'Unread', 'Findings', 'Pipeline', 'Jira', 'System'];

export default function NotificationsPage() {
  const [filter, setFilter] = useState('All');
  const [selected, setSelected] = useState(null);
  const [notifications, setNotifications] = useState(sampleNotifications);

  const filtered = notifications.filter((n) => {
    if (filter === 'Unread') return !n.read;
    if (filter === 'All') return true;
    return n.type === filter.toLowerCase();
  });

  const markRead = (id) => setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, read: true } : n));
  const markAllRead = () => setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));

  const selectedNotification = notifications.find((n) => n.id === selected);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text-primary">Notifications</h1>
        <button
          onClick={markAllRead}
          className="flex items-center gap-2 h-9 px-3 text-sm font-medium text-text-secondary bg-white border border-border rounded-md hover:bg-bg-secondary transition-colors"
        >
          <CheckCheck size={14} /> Mark All Read
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[600px]">
        {/* Left panel */}
        <div className="lg:col-span-1 flex flex-col bg-white border border-border rounded-lg shadow-md overflow-hidden">
          {/* Filter tabs */}
          <div className="flex gap-0 border-b border-border overflow-x-auto">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-2.5 text-xs font-medium whitespace-nowrap transition-colors ${
                  filter === f ? 'text-accent border-b-2 border-accent' : 'text-text-muted hover:text-text-primary'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-border">
            {filtered.length === 0 ? (
              <EmptyState icon={Bell} title="No notifications" message="You're all caught up!" />
            ) : (
              filtered.map((n) => {
                const config = TYPE_CONFIG[n.type] || TYPE_CONFIG.system;
                const Icon = config.icon;
                return (
                  <div
                    key={n.id}
                    onClick={() => { setSelected(n.id); markRead(n.id); }}
                    className={`flex items-start gap-3 p-4 cursor-pointer transition-colors ${selected === n.id ? 'bg-accent-light' : 'hover:bg-bg-secondary'}`}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${config.bg}`}>
                      <Icon size={14} className={config.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className={`text-sm font-medium truncate ${!n.read ? 'text-text-primary' : 'text-text-secondary'}`}>{n.title}</p>
                        {!n.read && <Circle size={8} className="text-accent fill-accent flex-shrink-0 mt-1.5" />}
                      </div>
                      <p className="text-xs text-text-muted truncate mt-0.5">{n.message}</p>
                      <p className="text-xs text-text-muted mt-1">{formatRelative(n.time)}</p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right panel */}
        <div className="lg:col-span-2 bg-white border border-border rounded-lg shadow-md">
          {selectedNotification ? (
            <div className="p-6">
              {(() => {
                const config = TYPE_CONFIG[selectedNotification.type] || TYPE_CONFIG.system;
                const Icon = config.icon;
                return (
                  <>
                    <div className="flex items-start gap-4 mb-6">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${config.bg}`}>
                        <Icon size={22} className={config.color} />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold text-text-primary">{selectedNotification.title}</h2>
                        <p className="text-xs text-text-muted mt-0.5">{formatRelative(selectedNotification.time)}</p>
                      </div>
                    </div>
                    <p className="text-text-secondary text-sm leading-relaxed mb-6">{selectedNotification.message}</p>
                    {selectedNotification.type === 'finding' && (
                      <div className="bg-danger-light border border-red-200 rounded-lg p-4">
                        <p className="text-sm font-semibold text-danger mb-2">Related Finding</p>
                        <p className="text-sm text-text-secondary">{selectedNotification.message}</p>
                        <button className="mt-3 text-sm font-medium text-danger hover:underline">View Finding →</button>
                      </div>
                    )}
                    {selectedNotification.type === 'pipeline' && (
                      <div className="bg-accent-light border border-blue-200 rounded-lg p-4">
                        <p className="text-sm font-semibold text-accent mb-2">Pipeline Run Summary</p>
                        <p className="text-sm text-text-secondary">{selectedNotification.message}</p>
                        <button className="mt-3 text-sm font-medium text-accent hover:underline">View Pipeline →</button>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <EmptyState icon={Bell} title="Select a notification" message="Click a notification to view its full details." />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
