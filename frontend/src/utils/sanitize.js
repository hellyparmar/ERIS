/**
 * Input Sanitization Utilities
 * Prevents XSS and injection attacks
 */

/**
 * Sanitize user input to prevent XSS attacks
 * @param {string} input - Raw user input
 * @returns {string} - Sanitized input
 */
export const sanitizeInput = (input) => {
    if (typeof input !== 'string') {
        return '';
    }

    return input
        // Remove HTML tags
        .replace(/<[^>]*>/g, '')
        // Remove script tags and content
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        // Remove javascript: protocol
        .replace(/javascript:/gi, '')
        // Remove on* event handlers
        .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
        // Trim whitespace
        .trim();
};

/**
 * Sanitize HTML content (for rich text)
 * @param {string} html - Raw HTML content
 * @returns {string} - Sanitized HTML
 */
export const sanitizeHTML = (html) => {
    if (typeof html !== 'string') {
        return '';
    }

    // Allowed tags
    const allowedTags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li'];

    // Remove dangerous tags
    let sanitized = html
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
        .replace(/<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi, '')
        .replace(/<embed[^>]*>/gi, '')
        .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '');

    return sanitized;
};

/**
 * Validate and sanitize email address
 * @param {string} email - Email address
 * @returns {string|null} - Sanitized email or null if invalid
 */
export const sanitizeEmail = (email) => {
    if (typeof email !== 'string') {
        return null;
    }

    const sanitized = email.trim().toLowerCase();

    // Basic email validation
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    return emailRegex.test(sanitized) ? sanitized : null;
};

/**
 * Sanitize URL to prevent javascript: and data: protocols
 * @param {string} url - URL string
 * @returns {string|null} - Sanitized URL or null if invalid
 */
export const sanitizeURL = (url) => {
    if (typeof url !== 'string') {
        return null;
    }

    const sanitized = url.trim();

    // Block dangerous protocols
    if (/^(javascript|data|vbscript):/i.test(sanitized)) {
        return null;
    }

    // Only allow http, https, and relative URLs
    if (!/^(https?:\/\/|\/)/i.test(sanitized)) {
        return null;
    }

    return sanitized;
};

/**
 * Sanitize number input
 * @param {any} input - Input value
 * @param {object} options - Validation options
 * @returns {number|null} - Sanitized number or null if invalid
 */
export const sanitizeNumber = (input, options = {}) => {
    const { min, max, integer = false } = options;

    const num = Number(input);

    if (isNaN(num) || !isFinite(num)) {
        return null;
    }

    if (integer && !Number.isInteger(num)) {
        return Math.floor(num);
    }

    if (min !== undefined && num < min) {
        return min;
    }

    if (max !== undefined && num > max) {
        return max;
    }

    return num;
};

/**
 * Sanitize SQL-like input (for search queries)
 * @param {string} input - Search query
 * @returns {string} - Sanitized query
 */
export const sanitizeSearchQuery = (input) => {
    if (typeof input !== 'string') {
        return '';
    }

    return input
        // Remove SQL keywords
        .replace(/(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)/gi, '')
        // Remove special SQL characters (single quote, semicolon)
        .replace(/[';]/g, '')
        // Remove SQL comment sequence
        .replace(/--/g, '')
        // Trim and limit length
        .trim()
        .substring(0, 200);
};

/**
 * Escape special characters for use in regex
 * @param {string} string - Input string
 * @returns {string} - Escaped string
 */
export const escapeRegex = (string) => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

/**
 * Sanitize file name
 * @param {string} filename - File name
 * @returns {string} - Sanitized filename
 */
export const sanitizeFilename = (filename) => {
    if (typeof filename !== 'string') {
        return 'file';
    }

    return filename
        // Remove path separators
        .replace(/[/\\]/g, '')
        // Remove dangerous characters
        .replace(/[<>:"|?*\x00-\x1f]/g, '')
        // Limit length
        .substring(0, 255)
        .trim() || 'file';
};

/**
 * Validate and sanitize JSON input
 * @param {string} jsonString - JSON string
 * @returns {object|null} - Parsed JSON or null if invalid
 */
export const sanitizeJSON = (jsonString) => {
    try {
        return JSON.parse(jsonString);
    } catch (error) {
        console.error('Invalid JSON:', error);
        return null;
    }
};

export default {
    sanitizeInput,
    sanitizeHTML,
    sanitizeEmail,
    sanitizeURL,
    sanitizeNumber,
    sanitizeSearchQuery,
    escapeRegex,
    sanitizeFilename,
    sanitizeJSON
};
