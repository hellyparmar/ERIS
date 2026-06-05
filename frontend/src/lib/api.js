/**
 * Enterprise Retail Intelligence System v3.0
 * API CLIENT
 * 
 * Axios-based HTTP client for FastAPI backend communication.
 * V3.0 Protocol: Centralized API calls with error handling.
 */

import axios from 'axios';

// Create axios instance with base configuration
const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Export base URL for direct fetch usage
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';


// Request interceptor (add auth tokens)
apiClient.interceptors.request.use(
    (config) => {
        const auth = localStorage.getItem('rdios-auth');
        if (auth) {
            try {
                const { access_token } = JSON.parse(auth);
                if (access_token && access_token !== 'demo-token') {
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

// Response interceptor (for error handling)
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

// API methods organized by domain
export const api = {
    // Generic HTTP methods
    get: (url, config) => apiClient.get(url, config),
    post: (url, data, config) => apiClient.post(url, data, config),
    put: (url, data, config) => apiClient.put(url, data, config),
    delete: (url, config) => apiClient.delete(url, config),

    // System endpoints
    health: () => apiClient.get('/health'),

    // Analytics endpoints
    analytics: {
        getMetrics: () => apiClient.get('/api/v1/analytics/metrics'),

        getAlerts: (severity = 'all') =>
            apiClient.get('/api/v1/analytics/alerts', {
                params: { severity }
            }),

        getChartData: (days = 30, forecastDays = 15) =>
            apiClient.get('/api/v1/analytics/chart-data', {
                params: { days, forecast_days: forecastDays }
            })
    },

    // Prediction endpoints
    predictions: {
        predictSales: (data) =>
            apiClient.post('/api/v1/predict/sales', data),

        predictStockout: (data) =>
            apiClient.post('/api/v1/predict/stockout', data)
    },

    // Data management endpoints
    data: {
        uploadSales: (file) => {
            const formData = new FormData();
            formData.append('file', file);
            return apiClient.post('/api/v1/data/upload/sales', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        },

        uploadInventory: (file) => {
            const formData = new FormData();
            formData.append('file', file);
            return apiClient.post('/api/v1/data/upload/inventory', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        },

        getSources: () => apiClient.get('/api/v1/data/sources')
    },

    // Model management endpoints
    models: {
        list: () => apiClient.get('/api/v1/models/list'),

        retrain: (data) => apiClient.post('/api/v1/models/retrain', data),

        getStatus: (jobId) => apiClient.get(`/api/v1/models/status/${jobId}`)
    }
};

// Export utility functions for data export
export const exportToCSV = async (data, filename = 'export.csv') => {
    const csvContent = convertToCSV(data);
    downloadFile(csvContent, filename, 'text/csv');
};

export const exportToExcel = async (data, filename = 'export.xlsx') => {
    // For now, export as CSV (Excel can open CSV files)
    // TODO: Implement proper XLSX generation using a library like xlsx
    const csvContent = convertToCSV(data);
    downloadFile(csvContent, filename.replace('.xlsx', '.csv'), 'text/csv');
};

export const exportToPDF = async (data, filename = 'export.pdf') => {
    // TODO: Implement PDF generation
    console.warn('PDF export not yet implemented. Exporting as CSV instead.');
    const csvContent = convertToCSV(data);
    downloadFile(csvContent, filename.replace('.pdf', '.csv'), 'text/csv');
};

// Helper function to convert array of objects to CSV
const convertToCSV = (data) => {
    if (!data || data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];

    for (const row of data) {
        const values = headers.map(header => {
            const value = row[header];
            // Escape quotes and wrap in quotes if contains comma
            const escaped = String(value).replace(/"/g, '""');
            return escaped.includes(',') ? `"${escaped}"` : escaped;
        });
        csvRows.push(values.join(','));
    }

    return csvRows.join('\n');
};

// Helper function to trigger file download
const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
};

export default api;
// Authentication API
export const authAPI = {
    login: async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        const response = await apiClient.post('/api/v1/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    },

    register: async (email, password, fullName) => {
        const response = await apiClient.post('/api/v1/auth/register', {
            email,
            password,
            full_name: fullName
        });
        return response.data;
    },

    refreshToken: async () => {
        const auth = localStorage.getItem('rdios-auth');
        if (!auth) throw new Error('No refresh token available');
        
        const { refresh_token } = JSON.parse(auth);
        const response = await apiClient.post('/api/v1/auth/refresh', {
            refresh_token
        });
        return response.data;
    },

    logout: () => {
        localStorage.removeItem('rdios-auth');
        localStorage.removeItem('rdios-user');
    }
};