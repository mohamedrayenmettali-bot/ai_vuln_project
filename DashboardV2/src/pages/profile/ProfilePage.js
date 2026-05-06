import React, { useState } from 'react';
import { Camera, Key, Shield } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { getRoleLabel } from '../../utils/formatters';
import { getRoleBadgeClass } from '../../utils/roleGuards';
import toast from 'react-hot-toast';

const TABS = ['Personal Info', 'Security', 'Preferences', 'API Keys'];

function PersonalInfoTab({ user }) {
  return (
    <form className="space-y-4 max-w-lg" onSubmit={(e) => { e.preventDefault(); toast.success('Profile updated.'); }}>
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="block text-sm font-medium text-text-primary mb-1.5">Full Name</label>
          <input defaultValue={user?.name} className="w-full h-10 px-3 border border-border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent" />
        </div>
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">Job Title</label>
          <input placeholder="Security Engineer" className="w-full h-10 px-3 border border-border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent" />
        </div>
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">Team</label>
          <input placeholder="Platform Security" className="w-full h-10 px-3 border border-border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent" />
        </div>
        <div className="col-span-2">
          <label className="block text-sm font-medium text-text-primary mb-1.5">Timezone</label>
          <select className="w-full h-10 px-3 border border-border rounded-md text-sm bg-white outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent">
            <option>UTC</option>
            <option>America/New_York</option>
            <option>Europe/London</option>
            <option>Asia/Singapore</option>
          </select>
        </div>
      </div>
      <button type="submit" className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-md transition-colors">
        Save Changes
      </button>
    </form>
  );
}

function SecurityTab() {
  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-4">Change Password</h3>
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); toast.success('Password updated successfully!'); }}>
          {['Current Password', 'New Password', 'Confirm New Password'].map((label) => (
            <div key={label}>
              <label className="block text-sm font-medium text-text-primary mb-1.5">{label}</label>
              <input type="password" className="w-full h-10 px-3 border border-border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent" />
            </div>
          ))}
          <button type="submit" className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-md transition-colors">Update Password</button>
        </form>
      </div>

      <div className="border-t border-border pt-6">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Two-Factor Authentication</h3>
        <div className="flex items-center justify-between bg-bg-secondary rounded-md p-4">
          <div>
            <p className="text-sm text-text-primary font-medium">TOTP Authenticator</p>
            <p className="text-xs text-text-muted">Use an authenticator app for extra security</p>
          </div>
          <button className="h-8 px-3 text-xs font-medium text-accent bg-accent-light hover:bg-blue-100 rounded-md">Enable</button>
        </div>
      </div>

      <div className="border-t border-border pt-6">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Active Sessions</h3>
        <div className="space-y-2">
          {[
            { device: 'Chrome on macOS', ip: '192.168.1.105', time: 'Active now', current: true },
            { device: 'Firefox on Ubuntu', ip: '10.0.0.42', time: '2 hours ago', current: false },
          ].map((s, i) => (
            <div key={i} className="flex items-center justify-between bg-bg-secondary rounded-md p-3">
              <div>
                <p className="text-sm text-text-primary font-medium">{s.device} {s.current && <span className="text-xs text-success ml-1">(current)</span>}</p>
                <p className="text-xs text-text-muted">{s.ip} · {s.time}</p>
              </div>
              {!s.current && <button className="text-xs text-danger hover:underline">Revoke</button>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PreferencesTab() {
  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3">Notification Preferences</h3>
        <div className="space-y-2">
          {[
            'New critical findings',
            'Pipeline failures',
            'Jira ticket updates',
            'AI model retrain complete',
            'Weekly security summary',
          ].map((item) => (
            <label key={item} className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4 accent-accent" />
              <span className="text-sm text-text-secondary">{item}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="border-t border-border pt-4">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Default Project on Login</h3>
        <select className="w-full h-10 px-3 border border-border rounded-md text-sm bg-white outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent">
          <option>— None —</option>
          <option>Core Banking API</option>
          <option>Payment Gateway Service</option>
          <option>Customer Portal Frontend</option>
        </select>
      </div>

      <button onClick={() => toast.success('Preferences saved!')} className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-md transition-colors">
        Save Preferences
      </button>
    </div>
  );
}

function ApiKeysTab() {
  const [keys] = useState([{ name: 'CI/CD Pipeline Token', created: '2024-01-01', lastUsed: '2024-01-15' }]);
  return (
    <div className="space-y-4 max-w-lg">
      <p className="text-sm text-text-secondary">
        Personal API tokens allow CI/CD pipelines to authenticate with SecureOps on your behalf.
      </p>
      <button onClick={() => toast.success('API token generated!')} className="flex items-center gap-2 h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-md transition-colors">
        <Key size={14} /> Generate New Token
      </button>
      {keys.length > 0 && (
        <div className="bg-white border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-bg-secondary">
                {['Name', 'Created', 'Last Used', ''].map((h) => (
                  <th key={h} className="px-4 py-2 text-left text-xs font-semibold text-text-muted">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {keys.map((k, i) => (
                <tr key={i} className="border-b border-border">
                  <td className="px-4 py-3 font-medium text-text-primary">{k.name}</td>
                  <td className="px-4 py-3 text-text-muted text-xs">{k.created}</td>
                  <td className="px-4 py-3 text-text-muted text-xs">{k.lastUsed}</td>
                  <td className="px-4 py-3"><button className="text-xs text-danger hover:underline">Revoke</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function ProfilePage() {
  const { user, role } = useAuth();
  const [activeTab, setActiveTab] = useState('Personal Info');

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text-primary">Profile</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left panel */}
        <div className="lg:col-span-1">
          <div className="bg-white border border-border rounded-lg shadow-md p-6 text-center">
            <div className="relative inline-block mb-4">
              <div className="w-20 h-20 rounded-full bg-accent text-white flex items-center justify-center text-3xl font-bold mx-auto">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <button className="absolute bottom-0 right-0 w-7 h-7 bg-white border border-border rounded-full flex items-center justify-center shadow-sm hover:bg-bg-secondary">
                <Camera size={13} className="text-text-muted" />
              </button>
            </div>
            <h2 className="text-base font-semibold text-text-primary">{user?.name || 'User'}</h2>
            <p className="text-sm text-text-muted mb-2">{user?.email}</p>
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${getRoleBadgeClass(role)}`}>{getRoleLabel(role)}</span>
            <div className="border-t border-border mt-4 pt-4 text-left space-y-2 text-xs text-text-muted">
              <p>Member since: <strong className="text-text-secondary">January 2024</strong></p>
              <p className="flex items-center gap-1 text-success"><Shield size={11} /> Connected to Jira</p>
            </div>
          </div>
        </div>

        {/* Right panel */}
        <div className="lg:col-span-3 bg-white border border-border rounded-lg shadow-md">
          <div className="flex border-b border-border px-6">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab ? 'border-accent text-accent' : 'border-transparent text-text-muted hover:text-text-primary'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
          <div className="p-6">
            {activeTab === 'Personal Info' && <PersonalInfoTab user={user} />}
            {activeTab === 'Security' && <SecurityTab />}
            {activeTab === 'Preferences' && <PreferencesTab />}
            {activeTab === 'API Keys' && <ApiKeysTab />}
          </div>
        </div>
      </div>
    </div>
  );
}
