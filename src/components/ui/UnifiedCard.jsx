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
            className={`bg-card/50 border-none shadow-2xl rounded-lg p-6 ${className}`}
            {...props}
        >
            {(title || actions) && (
                <div className="flex items-center justify-between mb-4">
                    <div className="min-w-0 flex-1">
                        {title && (
                            <h3 className="text-lg font-semibold text-foreground truncate">
                                {title}
                            </h3>
                        )}
                        {subtitle && (
                            <p className="text-sm text-muted-foreground mt-1 truncate">
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
            <div className="text-foreground">
                {children}
            </div>
        </div>
    );
};

export default UnifiedCard;
