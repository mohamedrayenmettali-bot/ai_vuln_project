import React, { useState, Fragment } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, Transition } from '@headlessui/react';
import {
  Search, Bell, ChevronDown, User, Settings, LogOut,
  Shield, RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useUnreadCount } from '../../hooks/useNotifications';
import { getRoleLabel } from '../../utils/formatters';

export default function Navbar({ onSearch }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState('');
  const { data: unreadData } = useUnreadCount();
  const unreadCount = unreadData?.count || 0;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-border sticky top-0 z-40 flex items-center px-6 gap-4">
      <Link to="/home" className="flex items-center gap-2 flex-shrink-0 mr-4">
        <div className="w-8 h-8 bg-accent rounded-md flex items-center justify-center">
          <Shield size={16} className="text-white" />
        </div>
        <span className="font-bold text-text-primary text-base hidden sm:block">SecureOps</span>
      </Link>

      <div className="flex-1 max-w-xs hidden md:flex items-center gap-2 bg-bg-secondary border border-border rounded-md px-3">
        <Search size={15} className="text-text-muted flex-shrink-0" />
        <input
          type="text"
          placeholder="Search projects, findings…"
          className="bg-transparent text-sm text-text-primary placeholder:text-text-muted outline-none w-full py-2"
          value={searchValue}
          onChange={(e) => {
            setSearchValue(e.target.value);
            onSearch && onSearch(e.target.value);
          }}
        />
      </div>

      <div className="ml-auto flex items-center gap-3">
        <Link to="/notifications" className="relative p-2 rounded-md hover:bg-bg-secondary text-text-secondary">
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 min-w-[16px] h-4 bg-danger text-white text-[10px] font-bold rounded-full flex items-center justify-center px-0.5">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Link>

        <div className="flex items-center gap-1 text-xs text-text-muted border-l border-border pl-3 hidden sm:flex">
          <RefreshCw size={12} />
          <span>Jira synced 5m ago</span>
        </div>

        <Menu as="div" className="relative">
          <Menu.Button className="flex items-center gap-2 p-1.5 rounded-md hover:bg-bg-secondary">
            <div className="w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center text-sm font-semibold">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="hidden md:flex flex-col items-start">
              <span className="text-sm font-medium text-text-primary leading-tight">{user?.name || 'User'}</span>
              <span className="text-xs text-text-muted">{getRoleLabel(user?.role)}</span>
            </div>
            <ChevronDown size={14} className="text-text-muted hidden md:block" />
          </Menu.Button>
          <Transition
            as={Fragment}
            enter="transition ease-out duration-100"
            enterFrom="transform opacity-0 scale-95"
            enterTo="transform opacity-100 scale-100"
            leave="transition ease-in duration-75"
            leaveFrom="transform opacity-100 scale-100"
            leaveTo="transform opacity-0 scale-95"
          >
            <Menu.Items className="absolute right-0 mt-2 w-52 bg-white border border-border rounded-lg shadow-lg py-1 z-50 origin-top-right">
              <div className="px-3 py-2 border-b border-border">
                <p className="text-sm font-medium text-text-primary">{user?.name}</p>
                <p className="text-xs text-text-muted">{user?.email}</p>
              </div>
              <Menu.Item>
                {({ active }) => (
                  <Link
                    to="/profile"
                    className={`flex items-center gap-2 px-3 py-2 text-sm ${active ? 'bg-bg-secondary' : ''} text-text-secondary`}
                  >
                    <User size={15} /> Profile
                  </Link>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <Link
                    to="/profile"
                    className={`flex items-center gap-2 px-3 py-2 text-sm ${active ? 'bg-bg-secondary' : ''} text-text-secondary`}
                  >
                    <Settings size={15} /> Settings
                  </Link>
                )}
              </Menu.Item>
              <div className="border-t border-border mt-1 pt-1">
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={handleLogout}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-sm ${active ? 'bg-bg-secondary' : ''} text-danger`}
                    >
                      <LogOut size={15} /> Logout
                    </button>
                  )}
                </Menu.Item>
              </div>
            </Menu.Items>
          </Transition>
        </Menu>
      </div>
    </header>
  );
}
