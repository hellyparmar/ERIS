/**
 * Enterprise Retail Intelligence System v3.0
 * UI COMPONENTS - BUTTON
 *
 * Reusable Button component with Theme-specific styling
 * Updated: No blue buttons, amber for dark theme, dark fill for light theme
 */

import clsx from 'clsx';

const Button = ({
    children,
    variant = 'primary',
    size = 'md',
    disabled = false,
    onClick,
    className = '',
    type = 'button',
    ...props
}) => {
    const baseStyles = 'font-medium rounded-lg transition-all duration-150 ease focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed';

    const getVariantStyles = () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

        if (isDark) {
            switch (variant) {
                case 'primary':
                    return 'bg-amber-500 hover:bg-amber-600 text-white border-none';
                case 'secondary':
                    return 'bg-transparent hover:bg-amber-500/10 text-amber-500 border border-amber-500';
                case 'success':
                    return 'bg-green-600 hover:bg-green-700 text-white border-none';
                case 'danger':
                    return 'bg-red-600 hover:bg-red-700 text-white border-none';
                case 'outline':
                    return 'border-2 border-amber-500 text-amber-500 hover:bg-amber-500/10';
                case 'ghost':
                    return 'text-gray-300 hover:bg-gray-800 hover:text-white';
                default:
                    return 'bg-amber-500 hover:bg-amber-600 text-white border-none';
            }
        } else {
            // Light theme
            switch (variant) {
                case 'primary':
                    return 'bg-gray-900 hover:bg-gray-800 text-white border-none';
                case 'secondary':
                    return 'bg-transparent hover:bg-gray-100 text-gray-900 border border-gray-900';
                case 'success':
                    return 'bg-green-600 hover:bg-green-700 text-white border-none';
                case 'danger':
                    return 'bg-red-600 hover:bg-red-700 text-white border-none';
                case 'outline':
                    return 'border-2 border-gray-900 text-gray-900 hover:bg-gray-50';
                case 'ghost':
                    return 'text-gray-700 hover:bg-gray-100 hover:text-gray-900';
                default:
                    return 'bg-gray-900 hover:bg-gray-800 text-white border-none';
            }
        }
    };

    const sizeStyles = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg'
    };

    return (
        <button
            type={type}
            disabled={disabled}
            onClick={onClick}
            className={clsx(
                baseStyles,
                getVariantStyles(),
                sizeStyles[size],
                className
            )}
            {...props}
        >
            {children}
        </button>
    );
};

export default Button;
