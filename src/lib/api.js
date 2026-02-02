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

// Request interceptor (for auth tokens in future)
apiClient.interceptors.request.use(
    (config) => {
        // Add auth token here when implemented
        // config.headers.Authorization = `Bearer ${token}`;
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

export default api;
