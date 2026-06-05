import React from 'react';

/**
 * Standard Page Wrapper Component
 * Ensures consistent layout, spacing, and animations across all pages
 */
export const PageWrapper = ({ children, className = '' }) => (
    <div className={`min-h-screen space-y-6 fade-in ${className}`}>
        {children}
    </div>
);

/**
 * Standard Page Header Component
 * Ensures consistent header styling across all pages
 */
export const PageHeader = ({ 
    title, 
    description, 
    actions = null,
    animate = true 
}) => {
    const headerContent = (
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-1">
                    {title}
                </h1>
                <p className="text-muted-foreground text-sm">
                    {description}
                </p>
            </div>
            {actions && (
                <div className="flex flex-col items-end gap-3">
                    {actions}
                </div>
            )}
        </div>
    );

    return animate ? (
        <div
            }
            }
        >
            {headerContent}
        </div>
    ) : (
        headerContent
    );
};

export default PageWrapper;
