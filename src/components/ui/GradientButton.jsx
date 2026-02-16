import React from 'react';
import '../../modern-design.css';

/**
 * GradientButton - Animated button with gradient background
 * 
 * @param {object} props
 * @param {ReactNode} props.children - Button text/content
 * @param {string} props.variant - Gradient variant (primary, secondary, success, warning, danger)
 * @param {string} props.size - Button size (sm, md, lg)
 * @param {function} props.onClick - Click handler
 * @param {boolean} props.disabled - Disabled state
 * @param {ReactNode} props.icon - Optional icon
 */
const GradientButton = ({
    children,
    variant = 'primary',
    size = 'md',
    onClick,
    disabled = false,
    icon = null,
    className = '',
    ...props
}) => {
    const gradients = {
        primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        success: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        warning: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        danger: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)',
    };

    const sizes = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-6 py-3 text-base',
        lg: 'px-8 py-4 text-lg',
    };

    return (
        <button
            className={`gradient-button relative overflow-hidden shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40 border border-white/20 backdrop-blur-sm ${sizes[size]} ${className}`}
            style={{
                background: gradients[variant],
            }}
            onClick={onClick}
            disabled={disabled}
            aria-disabled={disabled}
            type="button"
            {...props}
        >
            <div className="absolute inset-0 bg-white/20 opacity-0 hover:opacity-100 transition-opacity duration-300" aria-hidden="true" />
            <div className="relative flex items-center justify-center gap-2 z-10 font-bold tracking-wide">
                {icon && <span className="icon" aria-hidden="true">{icon}</span>}
                <span>{children}</span>
            </div>
        </button>
    );
};

export default GradientButton;
