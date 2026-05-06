import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home, Bell, User,
  Users, Activity, Settings,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';
import { getRoleLabel } from '../../utils/formatters';
import { getRoleBadgeClass } from '../../utils/roleGuards';

const navItems = [
  { to: '/home', icon: Home, label: 'Home', roles: null },
  { to: '/notifications', icon: Bell, label: 'Notifications', roles: null },
  { to: '/profile', icon: User, label: 'Profile', roles: null },
];

const adminItems = [
  { to: '/admin', icon: Settings, label: 'Admin Panel', roles: [ROLES.ADMIN] },
  { to: '/admin/users', icon: Users, label: 'Users', roles: [ROLES.ADMIN] },
];

function SidebarLink({ to, icon: Icon, label, end = false }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? 'bg-accent-light text-accent border-l-2 border-accent pl-[10px]'
            : 'text-text-secondary hover:bg-bg-secondary hover:text-text-primary'
        }`
      }
    >
      <Icon size={17} />
      {label}
    </NavLink>
  );
}

export default function Sidebar() {
  const { user, role } = useAuth();

  return (
    <aside className="w-60 bg-white border-r border-border flex flex-col flex-shrink-0 h-full">
      <div className="px-4 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center text-sm font-semibold flex-shrink-0">
            {user?.name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div className="overflow-hidden">
            <p className="text-sm font-medium text-text-primary truncate">{user?.name}</p>
            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${getRoleBadgeClass(role)}`}>
              {getRoleLabel(role)}
            </span>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 flex flex-col gap-1 overflow-y-auto">
        <p className="text-xs font-semibold text-text-muted uppercase tracking-wider px-3 mb-2">Navigation</p>
        {navItems.map((item) => (
          <SidebarLink key={item.to} {...item} end={item.to === '/home'} />
        ))}

        {role === ROLES.ADMIN && (
          <>
            <div className="border-t border-border my-3" />
            <p className="text-xs font-semibold text-text-muted uppercase tracking-wider px-3 mb-2">Administration</p>
            {adminItems.map((item) => (
              <SidebarLink key={item.to} {...item} end={item.to === '/admin'} />
            ))}
          </>
        )}
      </nav>

      <div className="px-3 py-3 border-t border-border">
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <Activity size={13} />
          <span>System: Operational</span>
        </div>
      </div>
    </aside>
  );
}
