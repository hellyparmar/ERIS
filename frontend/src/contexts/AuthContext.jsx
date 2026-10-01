import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api, apiClient } from '../lib/api';
import { normalizeUser } from '../lib/roles';

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
    localStorage.removeItem('eris-auth');
    localStorage.removeItem('eris-user');
    localStorage.removeItem('eris-token');

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

      const { access_token, refresh_token, user: rawUser } = response.data;
      const userData = normalizeUser(rawUser);

      localStorage.setItem('eris-token', access_token);
      localStorage.setItem('eris-auth', JSON.stringify({ access_token, refresh_token }));
      localStorage.setItem('eris-user', JSON.stringify(userData));

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
  }, []);

  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;

    const restoreSession = async () => {
      setIsLoading(true);
      try {
        const storedToken = localStorage.getItem('eris-token');
        const storedUser = localStorage.getItem('eris-user');

        if (storedToken && storedUser) {
          try {
            const response = await api.get('/api/v1/auth/me', {
              headers: {
                Authorization: `Bearer ${storedToken}`,
              },
            });

            setToken(storedToken);
            const userData = normalizeUser(response.data);
            setUser(userData);
            setIsAuthenticated(true);
          } catch (error) {
            localStorage.removeItem('eris-token');
            localStorage.removeItem('eris-auth');
            localStorage.removeItem('eris-user');
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
  }, []);

  useEffect(() => {
    const interceptor = apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          logout();
        }
        return Promise.reject(error);
      }
    );

    return () => {
      apiClient.interceptors.response.eject(interceptor);
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
