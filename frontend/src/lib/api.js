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

    // Authentication endpoints
    auth: {
        login: (data, config) => apiClient.post('/api/v1/auth/login', data, config),
        refresh: (refreshToken) => apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
        logout: (config) => apiClient.post('/api/v1/auth/logout', null, config),
        me: () => apiClient.get('/api/v1/auth/me'),
    },

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
            }),

        getRealtimeDashboard: () => apiClient.get('/api/v1/analytics/dashboard/realtime'),
        getSummary: () => apiClient.get('/api/v1/analytics/dashboard/summary'),
        getRevenueTrend: (params) => apiClient.get('/api/v1/analytics/dashboard/revenue-trend', { params }),
        getTopProducts: (params) => apiClient.get('/api/v1/analytics/dashboard/top-products', { params }),
        getOutletPerformance: () => apiClient.get('/api/v1/analytics/dashboard/outlet-performance'),
    },

    // Forecasting endpoints
    forecasting: {
        getSales: (params) => apiClient.get('/api/v1/forecasting/sales', { params }),
        getCausalAnalysis: (params) => apiClient.get('/api/v1/forecasting/causal-analysis', { params }),
        getAnomalyExplanation: (params) => apiClient.get('/api/v1/forecasting/anomaly-explanation', { params }),
        getInventoryDepletion: (params) => apiClient.get('/api/v1/forecasting/inventory-depletion', { params }),
    },

    // Causal analysis endpoints
    causal: {
        runCounterfactual: (scenario) => apiClient.post('/api/v1/causal/counterfactual', { scenario }),
    },

    // GST & Billing endpoints
    gst: {
        getGSTR1: (month, year) => apiClient.get('/api/v1/gst/gstr1', { params: { month, year } }),
        validateGSTR1: (month, year) => apiClient.get('/api/v1/gst/gstr1/validate', { params: { month, year } }),
        getInvoices: () => apiClient.get('/api/v1/gst/invoices'),
        createInvoice: (data) => apiClient.post('/api/v1/gst/invoices', data),
        payInvoice: (invoiceId) => apiClient.post(`/api/v1/gst/invoices/${invoiceId}/pay`),
        cancelInvoice: (invoiceId) => apiClient.patch(`/api/v1/gst/invoices/${invoiceId}/cancel`),
    },

    // Customer endpoints
    customers: {
        list: (params) => apiClient.get('/api/v1/customers', { params }),
        get: (id) => apiClient.get(`/api/v1/customers/${id}`),
        getStats: () => apiClient.get('/api/v1/customers/stats'),
        create: (data) => apiClient.post('/api/v1/customers/', data),
        getCreditBalance: (id) => apiClient.get(`/api/v1/customers/${id}/credit-balance`),
        updateCreditRating: (id, rating) => apiClient.patch(`/api/v1/customers/${id}/credit-rating`, null, { params: { rating } }),
    },

    // Inventory endpoints
    inventory: {
        list: (params) => apiClient.get('/api/v1/inventory', { params }),
        getSummary: () => apiClient.get('/api/v1/inventory/summary'),
        getLowStockAlerts: () => apiClient.get('/api/v1/inventory/alerts/low-stock'),
        getMovement: (id) => apiClient.get(`/api/v1/inventory/${id}/movement`),
        create: (data) => apiClient.post('/api/v1/inventory/create', data),
        update: (id, data) => apiClient.put(`/api/v1/inventory/${id}`, data),
        getCategories: () => apiClient.get('/api/v1/categories'),
    },

    // Reports & Export endpoints
    reports: {
        downloadSalesReport: (format = 'xlsx', days = 30) =>
            apiClient.get('/api/v1/reports/sales/download', { params: { format, days }, responseType: 'blob' }),
        downloadInventoryReport: (format = 'xlsx') =>
            apiClient.get('/api/v1/reports/inventory/download', { params: { format }, responseType: 'blob' }),
        exportSales: (data) => apiClient.post('/api/v1/reports/export/sales', data, { responseType: 'blob' }),
        exportInventory: (data) => apiClient.post('/api/v1/reports/export/inventory', data, { responseType: 'blob' }),
        exportInvoices: (data) => apiClient.post('/api/v1/reports/export/invoices', data, { responseType: 'blob' }),
        exportCustomers: (data) => apiClient.post('/api/v1/reports/export/customers', data, { responseType: 'blob' }),
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
    login: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await apiClient.post('/api/v1/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    },

    register: async (username, password, fullName) => {
        const response = await apiClient.post('/api/v1/auth/register', {
            username,
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
    },

    getUser: async () => {
        return apiClient.get('/api/v1/auth/me');
    }
};