import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Shield, CheckCircle } from 'lucide-react';
import { authApi } from '../../api/auth.api';
import toast from 'react-hot-toast';

const schema = z.object({
  name: z.string().min(2, 'Full name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
  role: z.string().min(1, 'Please select a role'),
}).refine((d) => d.password === d.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

const ROLES = [
  { value: 'developer', label: 'Developer' },
  { value: 'scrum_master', label: 'Scrum Master' },
  { value: 'security_analyst', label: 'Security Analyst' },
  { value: 'devops_engineer', label: 'DevOps Engineer' },
  { value: 'admin', label: 'Admin' },
];

export default function RegisterPage() {
  const [showPw, setShowPw] = useState(false);
  const [success, setSuccess] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (data) => {
    try {
      await authApi.register(data);
      setSuccess(true);
      toast.success('Account created successfully!');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Registration failed. Please try again.');
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
        <div>
          <h1 className="text-3xl font-bold text-white leading-tight mb-3">
            Join the Platform
          </h1>
          <p className="text-blue-100 text-base">
            Create your account to access the enterprise DevSecOps vulnerability management platform.
          </p>
        </div>
        <p className="text-blue-200 text-xs">&copy; {new Date().getFullYear()} SecureOps.</p>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-text-primary">Create account</h2>
            <p className="text-text-secondary text-sm mt-1">Register for SecureOps access</p>
          </div>

          {success ? (
            <div className="flex flex-col items-center text-center gap-3 py-8">
              <CheckCircle size={48} className="text-success" />
              <h3 className="text-lg font-semibold text-text-primary">Account Created</h3>
              <p className="text-text-secondary text-sm">Your account is pending admin approval.</p>
              <Link to="/login" className="text-accent hover:text-accent-hover text-sm font-medium">Back to Login</Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">Full name</label>
                <input
                  {...register('name')}
                  className={`w-full h-10 px-3 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent ${errors.name ? 'border-danger' : 'border-border'}`}
                  placeholder="Jane Smith"
                />
                {errors.name && <p className="text-xs text-danger mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">Email address</label>
                <input
                  type="email"
                  {...register('email')}
                  className={`w-full h-10 px-3 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent ${errors.email ? 'border-danger' : 'border-border'}`}
                  placeholder="you@company.com"
                />
                {errors.email && <p className="text-xs text-danger mt-1">{errors.email.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">Role</label>
                <select
                  {...register('role')}
                  className={`w-full h-10 px-3 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent bg-white ${errors.role ? 'border-danger' : 'border-border'}`}
                >
                  <option value="">Select your role</option>
                  {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
                {errors.role && <p className="text-xs text-danger mt-1">{errors.role.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showPw ? 'text' : 'password'}
                    {...register('password')}
                    className={`w-full h-10 px-3 pr-10 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent ${errors.password ? 'border-danger' : 'border-border'}`}
                    placeholder="Min. 8 characters"
                  />
                  <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted">
                    {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                {errors.password && <p className="text-xs text-danger mt-1">{errors.password.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">Confirm password</label>
                <input
                  type="password"
                  {...register('confirmPassword')}
                  className={`w-full h-10 px-3 border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent ${errors.confirmPassword ? 'border-danger' : 'border-border'}`}
                  placeholder="Repeat your password"
                />
                {errors.confirmPassword && <p className="text-xs text-danger mt-1">{errors.confirmPassword.message}</p>}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full h-10 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-md transition-colors disabled:opacity-60"
              >
                {isSubmitting ? 'Creating account…' : 'Create Account'}
              </button>
            </form>
          )}

          <p className="text-center text-sm text-text-muted mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-accent hover:text-accent-hover font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
