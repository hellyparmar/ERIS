import React from 'react';

/**
 * GradientButton - Clean button with theme-aware styling
 *
 * @param {object} props
 * @param {ReactNode} props.children - Button text/content
 * @param {string} props.variant - Button variant (primary, secondary)
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
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    const getButtonStyles = () => {
        if (isDark) {
            return variant === 'primary'
                ? 'bg-amber-500 hover:bg-amber-600 text-white border-none'
                : 'bg-transparent hover:bg-amber-500/10 text-amber-500 border border-amber-500';
        } else {
            return variant === 'primary'
                ? 'bg-gray-900 hover:bg-gray-800 text-white border-none'
                : 'bg-transparent hover:bg-gray-100 text-gray-900 border border-gray-900';
        }
    };

    const sizes = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-6 py-3 text-base',
        lg: 'px-8 py-4 text-lg',
    };

    return (
        <button
            className={`font-medium rounded-lg transition-all duration-150 ease focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed ${getButtonStyles()} ${sizes[size]} ${className}`}
            onClick={onClick}
            disabled={disabled}
            aria-disabled={disabled}
            type="button"
            {...props}
        >
            {icon && <span className="mr-2">{icon}</span>}
            {children}
        </button>
    );
};

export default GradientButton;
