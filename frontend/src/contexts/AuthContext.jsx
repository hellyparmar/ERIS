import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Initialize axios instance for auth requests
  const authAxios = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
  });

  // Logout function
  const logout = useCallback(async () => {
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('rdios-auth');
    localStorage.removeItem('rdios-user');
    localStorage.removeItem('rdios-token');
    
    // Redirect to login if not already there
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }, []);

  // Login function
  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);

      const response = await authAxios.post('/api/v1/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token, user: userData } = response.data;

      // Store in localStorage
      localStorage.setItem('rdios-token', access_token);
      localStorage.setItem('rdios-auth', JSON.stringify({ access_token }));
      localStorage.setItem('rdios-user', JSON.stringify(userData));

      // Update context
      setToken(access_token);
      setUser(userData);
      setIsAuthenticated(true);

      return { success: true, user: userData };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [authAxios]);

  // Restore session from localStorage on mount
  useEffect(() => {
    const restoreSession = async () => {
      setIsLoading(true);
      try {
        // Check localStorage for stored token
        const storedToken = localStorage.getItem('rdios-token');
        const storedUser = localStorage.getItem('rdios-user');

        if (storedToken && storedUser) {
          try {
            // Validate token by calling GET /api/v1/auth/me
            const response = await authAxios.get('/api/v1/auth/me', {
              headers: {
                Authorization: `Bearer ${storedToken}`,
              },
            });

            // Token is valid, restore session
            setToken(storedToken);
            setUser(response.data);
            setIsAuthenticated(true);
          } catch (error) {
            // Token is invalid or expired
            localStorage.removeItem('rdios-token');
            localStorage.removeItem('rdios-auth');
            localStorage.removeItem('rdios-user');
            setToken(null);
            setUser(null);
            setIsAuthenticated(false);
          }
        }
      } catch (error) {
        console.error('Session restore error:', error);
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, [authAxios]);

  // Listen for 401 errors across the app
  useEffect(() => {
    const interceptor = authAxios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Auto-logout on 401
          logout();
        }
        return Promise.reject(error);
      }
    );

    return () => {
      authAxios.interceptors.response.eject(interceptor);
    };
  }, [logout, authAxios]);

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
