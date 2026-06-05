import React from 'react';

/**
 * UnifiedCard Component - Enterprise Design System
 * Standardized card component for consistent UI across all pages
 * 
 * Features:
 * - Clean white background (dark: bg-card)
 * - Subtle border and shadow
 * - Fixed padding (p-6)
 * - Semantic color tokens for theme safety
 */
const UnifiedCard = ({
    children,
    title,
    subtitle,
    actions,
    className = "",
    animated = false,
    ...props
}) => {
    return (
        <div
            className={`bg-[var(--bg-surface)] border border-[var(--border-sm)] shadow-[var(--shadow-soft)] rounded-[var(--radius-lg)] p-6 ${className}`}
            {...props}
        >
            {(title || actions) && (
                <div className="flex items-center justify-between mb-4">
                    <div className="min-w-0 flex-1">
                        {title && (
                            <h3 className="text-lg font-semibold text-[var(--text-primary)] truncate">
                                {title}
                            </h3>
                        )}
                        {subtitle && (
                            <p className="text-sm text-[var(--text-muted)] mt-1 truncate">
                                {subtitle}
                            </p>
                        )}
                    </div>
                    {actions && (
                        <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                            {actions}
                        </div>
                    )}
                </div>
            )}
            <div className="text-[var(--text-primary)]">
                {children}
            </div>
        </div>
    );
};

export default UnifiedCard;
