import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

const IDLE_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

export function usePOSAuth() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [cashier, setCashier] = useState(null);
    const [loading, setLoading] = useState(true);

    // Check authentication on mount
    useEffect(() => {
        const token = localStorage.getItem('pos_token');
        const cashierData = localStorage.getItem('pos_cashier');
        const lastActivity = localStorage.getItem('pos_last_activity');

        if (token && cashierData && lastActivity) {
            const idleTime = Date.now() - parseInt(lastActivity);

            if (idleTime < IDLE_TIMEOUT_MS) {
                setIsAuthenticated(true);
                setCashier(JSON.parse(cashierData));
            } else {
                // Session expired due to inactivity
                logout();
            }
        }

        setLoading(false);
    }, []);

    // Track activity and refresh token
    const updateActivity = useCallback(async () => {
        const token = localStorage.getItem('pos_token');
        if (!token) return;

        localStorage.setItem('pos_last_activity', Date.now());

        // Refresh token every 5 minutes of activity
        const lastRefresh = localStorage.getItem('pos_last_refresh');
        const timeSinceRefresh = Date.now() - (parseInt(lastRefresh) || 0);

        if (timeSinceRefresh > 5 * 60 * 1000) {
            try {
                const response = await api.auth.refresh(token);
                const data = response.data;
                if (data?.access_token) {
                    localStorage.setItem('pos_token', data.access_token);
                    localStorage.setItem('pos_last_refresh', Date.now());
                }
            } catch (err) {
                console.error('Token refresh failed:', err);
            }
        }
    }, []);

    // Auto-logout on idle timeout
    useEffect(() => {
        if (!isAuthenticated) return;

        const checkIdle = setInterval(() => {
            const lastActivity = localStorage.getItem('pos_last_activity');
            const idleTime = Date.now() - parseInt(lastActivity);

            if (idleTime >= IDLE_TIMEOUT_MS) {
                logout();
            }
        }, 60000); // Check every minute

        return () => clearInterval(checkIdle);
    }, [isAuthenticated]);

    // Track user activity
    useEffect(() => {
        if (!isAuthenticated) return;

        const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];
        events.forEach(event => {
            window.addEventListener(event, updateActivity);
        });

        return () => {
            events.forEach(event => {
                window.removeEventListener(event, updateActivity);
            });
        };
    }, [isAuthenticated, updateActivity]);

    const logout = useCallback(async () => {
        const token = localStorage.getItem('pos_token');

        if (token) {
            try {
                await api.auth.logout({
                    headers: { 'Authorization': `Bearer ${token}` }
                });
            } catch (err) {
                console.error('Logout failed:', err);
            }
        }

        localStorage.removeItem('pos_token');
        localStorage.removeItem('pos_cashier');
        localStorage.removeItem('pos_last_activity');
        localStorage.removeItem('pos_last_refresh');

        setIsAuthenticated(false);
        setCashier(null);
    }, []);

    return {
        isAuthenticated,
        cashier,
        loading,
        logout,
        updateActivity
    };
}
