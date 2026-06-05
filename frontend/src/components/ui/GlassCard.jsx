import React from 'react';

/**
 * GlassCard - Clean card component without glassmorphism
 *
 * @param {object} props
 * @param {ReactNode} props.children - Card content
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.hover - Enable subtle hover effect (default: true)
 */
const GlassCard = ({
    children,
    className = '',
    hover = true,
    onClick,
    ...props
}) => {
    const baseClasses = 'bg-surface border-none rounded-lg shadow-soft transition-all duration-200 ease p-6';

    const hoverClasses = hover ? 'hover:shadow-medium' : '';

    return (
        <div
            className={`${baseClasses} ${hoverClasses} ${className}`}
            onClick={onClick}
            {...props}
        >
            {children}
        </div>
    );
};

export default GlassCard;
