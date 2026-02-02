/**
 * Enterprise Retail Intelligence System v3.0
 * UTILITY FUNCTIONS
 * 
 * Helper functions for formatting, calculations, and data transformations
 */

/**
 * Format currency with Indian Rupee symbol
 * @param {number} value - The numeric value to format
 * @param {string} locale - Locale code (default: 'en-IN')
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (value, locale = 'en-IN') => {
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
};

/**
 * Format large numbers with K, M, B suffixes
 * @param {number} value - The numeric value
 * @returns {string} Formatted string (e.g., "1.2M")
 */
export const formatCompactNumber = (value) => {
    if (value >= 1e9) {
        return (value / 1e9).toFixed(1) + 'B';
    }
    if (value >= 1e6) {
        return (value / 1e6).toFixed(1) + 'M';
    }
    if (value >= 1e3) {
        return (value / 1e3).toFixed(1) + 'K';
    }
    return value.toString();
};

/**
 * Format percentage with specified decimal places
 * @param {number} value - The percentage value
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, decimals = 1) => {
    return `${value.toFixed(decimals)}%`;
};

/**
 * Format date based on locale
 * @param {Date|string} date - Date to format
 * @param {string} locale - Locale code (default: 'en-IN')
 * @returns {string} Formatted date string
 */
export const formatDate = (date, locale = 'en-IN') => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(dateObj);
};

/**
 * Calculate percentage change between two values
 * @param {number} current - Current value
 * @param {number} previous - Previous value
 * @returns {number} Percentage change
 */
export const calculatePercentageChange = (current, previous) => {
    if (previous === 0) return 0;
    return ((current - previous) / previous) * 100;
};

/**
 * Calculate days until stockout based on current inventory and daily consumption
 * @param {number} currentStock - Current inventory level
 * @param {number} dailyConsumption - Average daily consumption rate
 * @returns {number} Days until stockout
 */
export const calculateDaysToStockout = (currentStock, dailyConsumption) => {
    if (dailyConsumption === 0) return Infinity;
    return Math.floor(currentStock / dailyConsumption);
};

/**
 * Debounce function for performance optimization
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
};

/**
 * Generate unique ID for components
 * @returns {string} Unique ID string
 */
export const generateId = () => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Clamp a value between min and max
 * @param {number} value - Value to clamp
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Clamped value
 */
export const clamp = (value, min, max) => {
    return Math.min(Math.max(value, min), max);
};

/**
 * Check if value is within threshold range
 * @param {number} value - Value to check
 * @param {number} target - Target value
 * @param {number} threshold - Threshold percentage
 * @returns {boolean} True if within threshold
 */
export const isWithinThreshold = (value, target, threshold) => {
    const deviation = Math.abs(value - target);
    return deviation <= (target * threshold / 100);
};
