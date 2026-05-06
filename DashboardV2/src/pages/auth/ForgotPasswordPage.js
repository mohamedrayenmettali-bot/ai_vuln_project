import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Shield, Mail, CheckCircle } from 'lucide-react';
import { authApi } from '../../api/auth.api';
import toast from 'react-hot-toast';

const schema = z.object({ email: z.string().email('Please enter a valid email') });

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (data) => {
    try {
      await authApi.forgotPassword(data.email);
      setSent(true);
    } catch {
      toast.error('Unable to send reset email. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-bg-secondary flex items-center justify-center p-4">
      <div className="bg-white border border-border rounded-lg shadow-md w-full max-w-sm p-8">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 bg-accent rounded-md flex items-center justify-center">
            <Shield size={16} className="text-white" />
          </div>
          <span className="font-bold text-text-primary">SecureOps</span>
        </div>

        {sent ? (
          <div className="text-center">
            <CheckCircle size={48} className="text-success mx-auto mb-3" />
            <h2 className="text-xl font-bold text-text-primary mb-2">Check your email</h2>
            <p className="text-text-secondary text-sm mb-6">
              We've sent password reset instructions to your email address.
            </p>
            <Link to="/login" className="text-sm text-accent font-medium hover:text-accent-hover">
              Back to Sign In
            </Link>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <div className="w-12 h-12 bg-accent-light rounded-full flex items-center justify-center mb-4">
                <Mail size={22} className="text-accent" />
              </div>
              <h2 className="text-xl font-bold text-text-primary mb-1">Forgot password?</h2>
              <p className="text-text-secondary text-sm">Enter your email and we'll send you a reset link.</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full h-10 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-md transition-colors disabled:opacity-60"
              >
                {isSubmitting ? 'Sending…' : 'Send Reset Link'}
              </button>
            </form>

            <p className="text-center text-sm text-text-muted mt-6">
              <Link to="/login" className="text-accent hover:text-accent-hover font-medium">← Back to Sign In</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
