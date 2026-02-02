import React from 'react';

/**
 * Loading Skeleton Component
 * Provides a shimmer effect while content is loading
 */
export const LoadingSkeleton = ({ className = '', variant = 'default' }) => {
    const baseClasses = 'animate-pulse bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 bg-[length:200%_100%]';

    const variants = {
        default: 'h-4 rounded',
        text: 'h-4 rounded w-3/4',
        title: 'h-8 rounded w-1/2',
        circle: 'rounded-full',
        card: 'h-32 rounded-xl',
        avatar: 'h-12 w-12 rounded-full',
    };

    return (
        <div
            className={`${baseClasses} ${variants[variant]} ${className}`}
            style={{
                animation: 'shimmer 2s infinite',
            }}
        />
    );
};

/**
 * Card Skeleton
 */
export const CardSkeleton = () => (
    <div className="glass-card p-6 space-y-4">
        <LoadingSkeleton variant="title" />
        <LoadingSkeleton variant="text" />
        <LoadingSkeleton variant="text" className="w-1/2" />
        <LoadingSkeleton variant="card" />
    </div>
);

/**
 * Table Skeleton
 */
export const TableSkeleton = ({ rows = 5, cols = 4 }) => (
    <div className="space-y-3">
        {/* Header */}
        <div className="flex gap-4">
            {Array.from({ length: cols }).map((_, i) => (
                <LoadingSkeleton key={i} className="h-6 flex-1" />
            ))}
        </div>
        {/* Rows */}
        {Array.from({ length: rows }).map((_, rowIndex) => (
            <div key={rowIndex} className="flex gap-4">
                {Array.from({ length: cols }).map((_, colIndex) => (
                    <LoadingSkeleton key={colIndex} className="h-10 flex-1" />
                ))}
            </div>
        ))}
    </div>
);

/**
 * Dashboard Skeleton
 */
export const DashboardSkeleton = () => (
    <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="glass-card p-6 space-y-3">
                    <LoadingSkeleton className="h-4 w-24" />
                    <LoadingSkeleton variant="title" className="w-32" />
                    <LoadingSkeleton className="h-3 w-16" />
                </div>
            ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CardSkeleton />
            <CardSkeleton />
        </div>

        {/* Table */}
        <div className="glass-card p-6">
            <LoadingSkeleton variant="title" className="mb-4" />
            <TableSkeleton rows={5} cols={4} />
        </div>
    </div>
);

/**
 * List Skeleton
 */
export const ListSkeleton = ({ items = 5 }) => (
    <div className="space-y-4">
        {Array.from({ length: items }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 glass-card p-4">
                <LoadingSkeleton variant="avatar" />
                <div className="flex-1 space-y-2">
                    <LoadingSkeleton className="h-4 w-1/3" />
                    <LoadingSkeleton className="h-3 w-1/2" />
                </div>
            </div>
        ))}
    </div>
);

// Add shimmer animation to CSS
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
    @keyframes shimmer {
      0% {
        background-position: -200% 0;
      }
      100% {
        background-position: 200% 0;
      }
    }
  `;
    document.head.appendChild(style);
}

export default LoadingSkeleton;
