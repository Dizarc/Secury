// Authentication context for managing user authentication state and actions

import React, { createContext, useContext, useState, useEffect } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../services/api";
import type { User } from "../types";

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Check if user is already authenticated on mount
    const checkAuth = () => {
      const authenticated = api.isAuthenticated();
      setIsAuthenticated(authenticated);
      setLoading(false);

      // TODO: Optionally fetch user profile from /api/me endpoint if it exists
      // For now, we just check if token exists
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      await api.login(email, password);
      setIsAuthenticated(true);
      // TODO: Fetch user profile after login if endpoint exists
      setUser({ id: "", email, full_name: null });
    } catch (error) {
      setIsAuthenticated(false);
      setUser(null);
      throw error;
    }
  };

  const logout = () => {
    api.logout();
    setIsAuthenticated(false);
    setUser(null);
  };

  const value: AuthContextType = {
    isAuthenticated,
    user,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

// Protected Route wrapper component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
