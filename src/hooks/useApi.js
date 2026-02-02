import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with defaults
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Generic fetch hook with caching
export const useFetch = (key, url, options = {}) => {
    return useQuery({
        queryKey: Array.isArray(key) ? key : [key],
        queryFn: async () => {
            const { data } = await api.get(url);
            return data;
        },
        ...options,
    });
};

// Dashboard KPIs
export const useDashboardKPIs = () => {
    return useFetch('dashboardKPIs', '/api/v1/dashboard/kpis', {
        staleTime: 2 * 60 * 1000, // 2 minutes
    });
};

// Revenue data
export const useRevenueData = (period = '30d') => {
    return useFetch(['revenue', period], `/api/v1/dashboard/revenue?period=${period}`, {
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
};

// Forecasts
export const useForecasts = (productId, horizon = 30) => {
    return useFetch(
        ['forecasts', productId, horizon],
        `/api/v1/forecasts/${productId}?horizon=${horizon}`,
        {
            staleTime: 10 * 60 * 1000, // 10 minutes
            enabled: !!productId, // Only fetch if productId exists
        }
    );
};

// Inventory
export const useInventory = (filters = {}) => {
    const queryString = new URLSearchParams(filters).toString();
    return useFetch(
        ['inventory', filters],
        `/api/v1/inventory${queryString ? `?${queryString}` : ''}`,
        {
            staleTime: 3 * 60 * 1000, // 3 minutes
        }
    );
};

// Analytics
export const useAnalytics = (dateRange) => {
    return useFetch(
        ['analytics', dateRange],
        `/api/v1/analytics?start=${dateRange.start}&end=${dateRange.end}`,
        {
            staleTime: 5 * 60 * 1000,
        }
    );
};

// AI Assistant Query
export const useAIQuery = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (query) => {
            const { data } = await api.post('/api/v1/ai/query', { query });
            return data;
        },
        onSuccess: () => {
            // Invalidate relevant queries after AI query
            queryClient.invalidateQueries({ queryKey: ['analytics'] });
        },
    });
};

// Customer Insights
export const useCustomerInsights = () => {
    return useFetch('customerInsights', '/api/v1/customers/insights', {
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
};

// Multi-store data
export const useMultiStoreData = () => {
    return useFetch('multiStore', '/api/v1/stores/summary', {
        staleTime: 5 * 60 * 1000,
    });
};

// Employees
export const useEmployees = () => {
    return useFetch('employees', '/api/v1/employees', {
        staleTime: 5 * 60 * 1000,
    });
};

// Returns
export const useReturns = (status) => {
    return useFetch(
        ['returns', status],
        `/api/v1/returns${status ? `?status=${status}` : ''}`,
        {
            staleTime: 2 * 60 * 1000,
        }
    );
};

// Suppliers
export const useSuppliers = () => {
    return useFetch('suppliers', '/api/v1/suppliers', {
        staleTime: 10 * 60 * 1000,
    });
};

// Promotions
export const usePromotions = () => {
    return useFetch('promotions', '/api/v1/promotions', {
        staleTime: 5 * 60 * 1000,
    });
};

// Monitoring
export const useMonitoring = () => {
    return useFetch('monitoring', '/api/v1/monitoring/costs', {
        staleTime: 1 * 60 * 1000, // 1 minute for real-time monitoring
        refetchInterval: 60000, // Auto-refetch every minute
    });
};

export default api;
