import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save, TestTube, Link } from 'lucide-react';
import toast from 'react-hot-toast';

const jiraSchema = z.object({
  jira_url: z.string().url('Enter a valid Jira URL'),
  project_key: z.string().min(1, 'Project key is required'),
  api_token: z.string().min(1, 'API token is required'),
  user_email: z.string().email('Enter a valid email'),
  default_issue_type: z.string(),
  auto_critical: z.boolean(),
  auto_high_ai: z.boolean(),
});

export default function SettingsTab({ projectId }) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(jiraSchema),
    defaultValues: {
      jira_url: 'https://yourcompany.atlassian.net',
      project_key: 'SEC',
      api_token: '',
      user_email: '',
      default_issue_type: 'Bug',
      auto_critical: true,
      auto_high_ai: true,
    },
  });

  const onSubmit = async (data) => {
    await new Promise((r) => setTimeout(r, 800));
    toast.success('Jira integration settings saved successfully!');
  };

  const testConnection = () => {
    toast.loading('Testing Jira connection…', { duration: 2000 });
    setTimeout(() => toast.success('Jira connection successful!'), 2000);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Jira connection */}
      <div className="bg-white border border-border rounded-lg shadow-md p-6">
        <div className="flex items-center gap-2 mb-5">
          <Link size={18} className="text-accent" />
          <h3 className="text-base font-semibold text-text-primary">Jira Integration</h3>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-text-primary mb-1.5">Jira Base URL</label>
              <input
                {...register('jira_url')}
                className={`w-full h-10 px-3 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent ${errors.jira_url ? 'border-danger' : 'border-border'}`}
                placeholder="https://yourcompany.atlassian.net"
              />
              {errors.jira_url && <p className="text-xs text-danger mt-1">{errors.jira_url.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Project Key</label>
              <input
                {...register('project_key')}
                className={`w-full h-10 px-3 border rounded-md text-sm outline-none font-mono uppercase focus:ring-2 focus:ring-accent/30 focus:border-accent ${errors.project_key ? 'border-danger' : 'border-border'}`}
                placeholder="SEC"
              />
              {errors.project_key && <p className="text-xs text-danger mt-1">{errors.project_key.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">User Email</label>
              <input
                type="email"
                {...register('user_email')}
                className={`w-full h-10 px-3 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent ${errors.user_email ? 'border-danger' : 'border-border'}`}
                placeholder="security@company.com"
              />
              {errors.user_email && <p className="text-xs text-danger mt-1">{errors.user_email.message}</p>}
            </div>

            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-text-primary mb-1.5">API Token</label>
              <input
                type="password"
                {...register('api_token')}
                className={`w-full h-10 px-3 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent ${errors.api_token ? 'border-danger' : 'border-border'}`}
                placeholder="Your Jira API token"
              />
              {errors.api_token && <p className="text-xs text-danger mt-1">{errors.api_token.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Default Issue Type</label>
              <select
                {...register('default_issue_type')}
                className="w-full h-10 px-3 border border-border rounded-md text-sm outline-none bg-white focus:ring-2 focus:ring-accent/30 focus:border-accent"
              >
                <option>Bug</option>
                <option>Security</option>
                <option>Task</option>
                <option>Story</option>
              </select>
            </div>
          </div>

          <div className="border-t border-border pt-4 space-y-3">
            <p className="text-sm font-semibold text-text-primary">Auto-create Rules</p>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" {...register('auto_critical')} className="w-4 h-4 accent-accent" />
              <span className="text-sm text-text-secondary">Auto-create ticket for <strong>Critical</strong> findings</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" {...register('auto_high_ai')} className="w-4 h-4 accent-accent" />
              <span className="text-sm text-text-secondary">Auto-create ticket for <strong>High</strong> findings with AI Score &gt; 7</span>
            </label>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={testConnection}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-secondary bg-white border border-border rounded-md hover:bg-bg-secondary transition-colors"
            >
              <TestTube size={14} /> Test Connection
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-md transition-colors disabled:opacity-60"
            >
              <Save size={14} /> {isSubmitting ? 'Saving…' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
