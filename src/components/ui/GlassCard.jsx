import React from 'react';
import '../../modern-design.css';

/**
 * GlassCard - Premium glassmorphism card component
 * 
 * @param {object} props
 * @param {ReactNode} props.children - Card content
 * @param {string} props.className - Additional CSS classes
 * @param {string} props.variant - Card variant: 'default', 'gradient', 'elevated'
 * @param {boolean} props.animated - Enable entrance animation (default: true)
 * @param {boolean} props.hover - Enable hover effect (default: true)
 */
const GlassCard = ({
    children,
    className = '',
    variant = 'default',
    animated = true,
    hover = true,
    onClick,
    ...props
}) => {
    const getVariantClasses = () => {
        switch (variant) {
            case 'gradient':
                return 'gradient-card border-primary/20';
            case 'elevated':
                return 'shadow-glow-primary';
            default:
                return '';
        }
    };

    const cardStyle = {
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        background: 'var(--glass-bg)',
        boxShadow: 'var(--glass-shadow)',
    };

    const animationProps = animated ? {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.5 }
    } : {};

    const hoverProps = hover ? {
        whileHover: { y: -4, boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15)' }
    } : {};

    return (
        <div
            className={`glass-card ${getVariantClasses()} ${className}`}
            style={cardStyle}
            {...animationProps}
            {...hoverProps}
            onClick={onClick}
            {...props}
        >
            {children}
        </div>
    );
};

export default GlassCard;
