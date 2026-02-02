import { QueryClient } from '@tanstack/react-query';

// Create a client with optimized defaults
export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            // Cache data for 5 minutes
            staleTime: 5 * 60 * 1000,
            // Keep unused data in cache for 10 minutes
            gcTime: 10 * 60 * 1000,
            // Retry failed requests 3 times
            retry: 3,
            // Retry with exponential backoff
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
            // Refetch on window focus for fresh data
            refetchOnWindowFocus: true,
            // Don't refetch on mount if data is fresh
            refetchOnMount: false,
            // Refetch on reconnect
            refetchOnReconnect: true,
        },
        mutations: {
            // Retry mutations once
            retry: 1,
        },
    },
});

// Prefetch common queries
export const prefetchDashboardData = () => {
    queryClient.prefetchQuery({
        queryKey: ['dashboard', 'kpis'],
        queryFn: () => fetch('/api/v1/dashboard/kpis').then(res => res.json()),
    });

    queryClient.prefetchQuery({
        queryKey: ['dashboard', 'revenue'],
        queryFn: () => fetch('/api/v1/dashboard/revenue').then(res => res.json()),
    });
};

export default queryClient;
