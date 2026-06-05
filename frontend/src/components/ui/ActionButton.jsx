import React from 'react';

/**
 * ActionButton Component - Enterprise Design System
 * Standardized button with semantic color tokens for theme safety
 * 
 * Variants:
 * - primary: Solid blue/black for Add, Save, Export
 * - destructive: Light red background with red text for Delete, Dismiss
 * - secondary: White background with border for Edit, Cancel
 * - accept: Green for approval actions (legacy support)
 * - outline: High contrast outline (legacy support)
 */
const ActionButton = ({
    children,
    onClick,
    variant = 'primary',
    size = 'md',
    className = '',
    icon: Icon,
    disabled = false,
    ...props
}) => {

    const variants = {
        primary: "bg-primary hover:bg-primary/90 text-white shadow-sm",
        destructive: "bg-destructive/10 hover:bg-destructive/20 text-destructive border border-destructive/20",
        secondary: "bg-background hover:bg-muted text-foreground border border-border",
        accept: "bg-green-600 hover:bg-green-700 text-white shadow-sm",
        dismiss: "bg-primary hover:bg-primary/90 text-white shadow-sm",
        outline: "bg-background hover:bg-muted text-foreground border border-border"
    };

    const sizes = {
        sm: "px-3 py-1.5 text-xs",
        md: "px-4 py-2 text-sm",
        lg: "px-6 py-3 text-base"
    };

    const baseClass = "rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2 whitespace-nowrap flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed";

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`${baseClass} ${variants[variant] || variants.primary} ${sizes[size]} ${className}`}
            {...props}
        >
            {Icon && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 20 : 18} />}
            {children}
        </button>
    );
};

export default ActionButton;
