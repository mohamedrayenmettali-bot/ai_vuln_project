import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import AppLayout from './components/layout/AppLayout';
import PrivateRoute from './components/PrivateRoute';
import GlobalChatbot from './components/chatbot/GlobalChatbot';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import HomePage from './pages/home/HomePage';
import DashboardPage from './pages/dashboard/DashboardPage';
import NotificationsPage from './pages/notifications/NotificationsPage';
import ProfilePage from './pages/profile/ProfilePage';
import AdminPage from './pages/admin/AdminPage';
import UnauthorizedPage from './pages/errors/UnauthorizedPage';
import { ROLES } from './utils/constants';
import { useAuth } from './hooks/useAuth';

function PrivatePage({ children, allowedRoles }) {
  return (
    <PrivateRoute allowedRoles={allowedRoles}>
      <AppLayout>{children}</AppLayout>
    </PrivateRoute>
  );
}

function ChatbotWrapper() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return null;
  return <GlobalChatbot />;
}

export default function App() {
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            borderRadius: '8px',
            fontSize: '13px',
            fontFamily: 'Inter, sans-serif',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04)',
          },
        }}
      />

      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />

        <Route path="/home" element={<PrivatePage><HomePage /></PrivatePage>} />
        <Route path="/projects/:id/dashboard" element={<PrivatePage><DashboardPage /></PrivatePage>} />
        <Route path="/notifications" element={<PrivatePage><NotificationsPage /></PrivatePage>} />
        <Route path="/profile" element={<PrivatePage><ProfilePage /></PrivatePage>} />
        <Route path="/admin" element={<PrivatePage allowedRoles={[ROLES.ADMIN]}><AdminPage /></PrivatePage>} />
        <Route path="/admin/users" element={<PrivatePage allowedRoles={[ROLES.ADMIN]}><AdminPage /></PrivatePage>} />

        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>

      <ChatbotWrapper />
    </>
  );
}
