import React, { createContext, useState, useEffect, useCallback } from "react";
import { authApi } from "../api/auth.api";

export const AuthContext = createContext(null);

function clearSession() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_user");
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const hydrateSession = async () => {
      const storedToken = localStorage.getItem("auth_token");
      if (!storedToken) {
        if (!cancelled) setLoading(false);
        return;
      }

      try {
        const response = await authApi.me();
        if (cancelled) return;

        const userData = response.data;
        setToken(storedToken);
        setUser(userData);
        localStorage.setItem("auth_user", JSON.stringify(userData));
      } catch {
        clearSession();
        if (!cancelled) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    hydrateSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (credentials) => {
    const response = await authApi.login(credentials);
    const { access_token, user: userData } = response.data;
    localStorage.setItem("auth_token", access_token);
    const userObj = userData;
    localStorage.setItem("auth_user", JSON.stringify(userObj));
    setToken(access_token);
    setUser(userObj);
    return userObj;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setToken(null);
    setUser(null);
  }, []);

  const value = {
    user,
    token,
    role: user?.role || null,
    isAuthenticated: !!token && !!user,
    loading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
