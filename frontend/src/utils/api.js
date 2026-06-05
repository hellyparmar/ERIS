import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const dispatchToast = (message, type = 'error', duration = 4000) => {
  if (typeof window !== 'undefined' && window.dispatchEvent) {
    window.dispatchEvent(new CustomEvent('global-toast', { detail: { message, type, duration } }));
  }
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('rdios-token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      dispatchToast('Network error. Check your connection.', 'error');
    } else if (error.response.status === 500) {
      dispatchToast('Server error. Please try again.', 'error');
    } else if (error.response.status === 403) {
      dispatchToast("You don't have permission to do this.", 'warning');
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('rdios-token');
      localStorage.removeItem('rdios-auth');
      localStorage.removeItem('rdios-user');

      window.dispatchEvent(new CustomEvent('auth-logout'));
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;
