import React from 'react';
import '../../modern-design.css';

/**
 * Skeleton Loader - Professional placeholder for loading states
 * @param {string} className - Additional classes (width/height)
 */
const Skeleton = ({ className = "h-4 w-full" }) => {
    return (
        <div
            className={`shimmer bg-gray-200 dark:bg-gray-700 rounded ${className}`}
            role="status"
            aria-label="Loading..."
        />
    );
};

export default Skeleton;
