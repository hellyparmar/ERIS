/** Shared Axios client for the ERIS FastAPI backend. */

import axios from 'axios';

// Create axios instance with base configuration
export const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Export base URL for direct fetch usage
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';


let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

export function clearAuthAndRedirect() {
    localStorage.removeItem('eris-auth');
    localStorage.removeItem('eris-user');
    localStorage.removeItem('eris-token');
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
    }
}

// Request interceptor (add auth tokens)
apiClient.interceptors.request.use(
    (config) => {
        const auth = localStorage.getItem('eris-auth');
        if (auth) {
            try {
                const { access_token } = JSON.parse(auth);
                if (access_token) {
                    config.headers.Authorization = `Bearer ${access_token}`;
                }
            } catch (e) {
                console.warn('Invalid auth token stored');
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor (handle 401 -> refresh once -> redirect)
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (!error.response || error.response.status !== 401 || !originalRequest) {
            return Promise.reject(error);
        }

        // Do not intercept login or refresh requests themselves to prevent loops
        if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
            return Promise.reject(error);
        }

        // If request was already retried, fail and redirect
        if (originalRequest._retry) {
            clearAuthAndRedirect();
            return Promise.reject(error);
        }

        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            })
                .then((token) => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return apiClient(originalRequest);
                })
                .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        const auth = localStorage.getItem('eris-auth');
        let refreshToken = null;
        if (auth) {
            try {
                const parsed = JSON.parse(auth);
                refreshToken = parsed.refresh_token;
            } catch (e) {
                // ignore
            }
        }

        if (!refreshToken) {
            isRefreshing = false;
            clearAuthAndRedirect();
            return Promise.reject(error);
        }

        try {
            const { data } = await axios.post(
                `${API_BASE}/api/v1/auth/refresh`,
                { refresh_token: refreshToken },
                { headers: { 'Content-Type': 'application/json' } }
            );

            const newAccessToken = data.access_token;
            const newRefreshToken = data.refresh_token || refreshToken;

            localStorage.setItem('eris-token', newAccessToken);
            localStorage.setItem(
                'eris-auth',
                JSON.stringify({ access_token: newAccessToken, refresh_token: newRefreshToken })
            );

            apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

            processQueue(null, newAccessToken);
            return apiClient(originalRequest);
        } catch (refreshError) {
            processQueue(refreshError, null);
            clearAuthAndRedirect();
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);

// API methods organized by domain
export const api = {
    get: (url, config) => apiClient.get(url, config),
    post: (url, data, config) => apiClient.post(url, data, config),
    put: (url, data, config) => apiClient.put(url, data, config),
    patch: (url, data, config) => apiClient.patch(url, data, config),
    delete: (url, config) => apiClient.delete(url, config),
};

export default api;
