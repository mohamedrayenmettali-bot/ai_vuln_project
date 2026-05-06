import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Shield, Lock, Search, AlertCircle, BarChart2 } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
  remember: z.boolean().optional(),
});

function FeatureItem({ icon: Icon, title, description }) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-md bg-white/20 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Icon size={16} className="text-white" />
      </div>
      <div>
        <p className="font-semibold text-white text-sm">{title}</p>
        <p className="text-blue-100 text-xs mt-0.5">{description}</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showPw, setShowPw] = useState(false);
  const [authError, setAuthError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (data) => {
    setAuthError('');
    try {
      await login({ email: data.email, password: data.password });
      navigate('/home');
    } catch (err) {
      setAuthError(
        err?.response?.data?.detail ||
          err?.response?.data?.message ||
          'Invalid credentials. Please try again.'
      );
    }
  };

  return (
    <div className="flex min-h-screen">
      <div className="hidden lg:flex lg:w-[45%] bg-gradient-to-br from-accent to-accent-hover flex-col justify-between p-12">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <Shield size={22} className="text-white" />
          </div>
          <span className="text-xl font-bold text-white">SecureOps</span>
        </div>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-white leading-tight mb-3">
              Enterprise DevSecOps<br />Vulnerability Platform
            </h1>
            <p className="text-blue-100 text-base leading-relaxed">
              Unified security intelligence for engineering and security teams.
            </p>
          </div>
          <div className="space-y-4">
            <FeatureItem icon={Search} title="AI-Powered Risk Scoring" description="ML models rank findings by real exploitability, not just CVSS." />
            <FeatureItem icon={BarChart2} title="Full Pipeline Visibility" description="Track SAST, DAST, SCA, and secret scanning results in one place." />
            <FeatureItem icon={Lock} title="Jira Auto-Ticketing" description="Critical findings automatically create Jira issues with AI descriptions." />
          </div>
        </div>
        <p className="text-blue-200 text-xs">&copy; {new Date().getFullYear()} SecureOps. Enterprise Edition.</p>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <div className="flex items-center gap-2 lg:hidden mb-6">
              <div className="w-8 h-8 bg-accent rounded-md flex items-center justify-center">
                <Shield size={16} className="text-white" />
              </div>
              <span className="font-bold text-text-primary">SecureOps</span>
            </div>
            <h2 className="text-2xl font-bold text-text-primary">Welcome back</h2>
            <p className="text-text-secondary text-sm mt-1">Sign in to your security dashboard</p>
          </div>

          {authError && (
            <div className="flex items-center gap-2 bg-danger-light border border-red-200 text-danger rounded-md px-4 py-3 mb-4 text-sm">
              <AlertCircle size={16} className="flex-shrink-0" />
              {authError}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Email address</label>
              <input
                type="email"
                {...register('email')}
                className={`w-full h-10 px-3 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all ${errors.email ? 'border-danger' : 'border-border'}`}
                placeholder="you@company.com"
              />
              {errors.email && <p className="text-xs text-danger mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  {...register('password')}
                  className={`w-full h-10 px-3 pr-10 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all ${errors.password ? 'border-danger' : 'border-border'}`}
                  placeholder="••••••••"
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary">
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="text-xs text-danger mt-1">{errors.password.message}</p>}
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" {...register('remember')} className="w-4 h-4 accent-accent" />
                <span className="text-sm text-text-secondary">Remember me</span>
              </label>
              <Link to="/forgot-password" className="text-sm text-accent hover:text-accent-hover font-medium">Forgot password?</Link>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full h-10 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-md transition-colors disabled:opacity-60"
            >
              {isSubmitting ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <p className="text-center text-sm text-text-muted mt-6">
            Need an account?{' '}
            <Link to="/register" className="text-accent hover:text-accent-hover font-medium">Contact your admin</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
