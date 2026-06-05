/**
 * Enterprise Retail Intelligence System v3.0
 * UI COMPONENTS - CARD
 * 
 * Reusable Card component with Dark Mode support
 * V3.0 UI Standard: Gradient Cards
 */

import clsx from 'clsx';

const Card = ({
    children,
    className = '',
    variant = 'default',
    gradient = false,
    onClick,
    ...props
}) => {
    const baseStyles = 'rounded-lg shadow-lg p-6 transition-base';

    const variantStyles = {
        default: 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700',
        glass: 'glass',
        gradient: 'gradient-card'
    };

    const selectedVariant = gradient ? 'gradient' : variant;

    return (
        <div
            className={clsx(
                baseStyles,
                variantStyles[selectedVariant],
                onClick && 'cursor-pointer hover:shadow-xl',
                className
            )}
            onClick={onClick}
            {...props}
        >
            {children}
        </div>
    );
};

export default Card;
