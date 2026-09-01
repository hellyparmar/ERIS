import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

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
    return useFetch('dashboardKPIs', '/api/v1/analytics/dashboard/kpis', {
        staleTime: 2 * 60 * 1000, // 2 minutes
    });
};

// Revenue data
export const useRevenueData = (period = '30d') => {
    return useFetch(['revenue', period], `/api/v1/analytics/dashboard/revenue?period=${period}`, {
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
};

// Forecasts
export const useForecasts = (productId, horizon = 30) => {
    return useFetch(
        ['forecasts', productId, horizon],
        `/api/v1/forecasting/sales?product_id=${productId}&horizon=${horizon}`,
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


export default api;
