import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldOff } from 'lucide-react';

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen bg-bg-secondary flex items-center justify-center">
      <div className="text-center">
        <div className="w-20 h-20 bg-danger-light rounded-full flex items-center justify-center mx-auto mb-6">
          <ShieldOff size={36} className="text-danger" />
        </div>
        <h1 className="text-3xl font-bold text-text-primary mb-2">Access Denied</h1>
        <p className="text-text-secondary text-base mb-8 max-w-sm mx-auto">
          You don't have permission to view this page. Contact your administrator if you believe this is an error.
        </p>
        <div className="flex gap-3 justify-center">
          <Link
            to="/home"
            className="px-4 py-2 text-sm font-medium text-white bg-accent rounded-md hover:bg-accent-hover transition-colors"
          >
            Go to Home
          </Link>
          <Link
            to="/login"
            className="px-4 py-2 text-sm font-medium text-text-secondary bg-white border border-border rounded-md hover:bg-bg-secondary transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
