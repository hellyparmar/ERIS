import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../lib/api';
import { useAuthStore } from '../hooks/useAuthStore';

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
  const restoredRef = useRef(false);

  const logout = useCallback(async () => {
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('rdios-auth');
    localStorage.removeItem('rdios-user');
    localStorage.removeItem('rdios-token');

    useAuthStore.getState().logout();

    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }, []);

  const login = useCallback(async (username, password) => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await api.post('/api/v1/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token, user: userData } = response.data;

      localStorage.setItem('rdios-token', access_token);
      localStorage.setItem('rdios-auth', JSON.stringify({ access_token }));
      localStorage.setItem('rdios-user', JSON.stringify(userData));

      setToken(access_token);
      setUser(userData);
      useAuthStore.getState().setToken(access_token);
      useAuthStore.getState().setUser(userData);
      setIsAuthenticated(true);

      return { success: true, user: userData };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;

    const restoreSession = async () => {
      setIsLoading(true);
      try {
        const storedToken = localStorage.getItem('rdios-token');
        const storedUser = localStorage.getItem('rdios-user');

        if (storedToken && storedUser) {
          try {
            const response = await api.get('/api/v1/auth/me', {
              headers: {
                Authorization: `Bearer ${storedToken}`,
              },
            });

            setToken(storedToken);
            setUser(response.data);
            useAuthStore.getState().setToken(storedToken);
            useAuthStore.getState().setUser(response.data);
            setIsAuthenticated(true);
          } catch (error) {
            localStorage.removeItem('rdios-token');
            localStorage.removeItem('rdios-auth');
            localStorage.removeItem('rdios-user');
            setToken(null);
            setUser(null);
            useAuthStore.getState().logout();
            setIsAuthenticated(false);
          }
        }
      } catch (error) {
        console.error('Session restore error:', error);
        setToken(null);
        setUser(null);
        useAuthStore.getState().logout();
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  useEffect(() => {
    const interceptor = authAxios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          logout();
        }
        return Promise.reject(error);
      }
    );

    return () => {
      authAxios.interceptors.response.eject(interceptor);
    };
  }, [logout]);

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
