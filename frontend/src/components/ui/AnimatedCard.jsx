import React from 'react';

/**
 * AnimatedCard Component
 * Clean card with subtle hover effect
 */
const AnimatedCard = ({
    children,
    className = '',
    onClick,
    ariaLabel,
    ...props
}) => {
    return (
        <div
            className={`bg-surface rounded-lg shadow-soft hover:shadow-medium transition-all duration-150 ease p-6 ${className}`}
            onClick={onClick}
            role={onClick ? 'button' : undefined}
            aria-label={ariaLabel}
            tabIndex={onClick ? 0 : undefined}
            onKeyDown={onClick ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onClick(e);
                }
            } : undefined}
            {...props}
        >
            {children}
        </div>
    );
};

export default AnimatedCard;
