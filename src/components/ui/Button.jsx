/**
 * Enterprise Retail Intelligence System v3.0
 * UI COMPONENTS - BUTTON
 * 
 * Reusable Button component with Dark Mode support
 * V3.0 Standard: Uses COLOR_MAP for type-safe styling
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
    const baseStyles = 'font-medium rounded-lg transition-base focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const variantStyles = {
        primary: 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500',
        secondary: 'bg-gray-600 hover:bg-gray-700 text-white focus:ring-gray-500',
        success: 'bg-green-600 hover:bg-green-700 text-white focus:ring-green-500',
        danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
        outline: 'border-2 border-blue-600 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 focus:ring-blue-500',
        ghost: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 focus:ring-gray-500'
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
                variantStyles[variant],
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
