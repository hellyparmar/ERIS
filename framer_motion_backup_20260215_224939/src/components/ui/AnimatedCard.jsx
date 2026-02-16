import React from 'react';
import { motion } from 'framer-motion';
import { cardHover } from '../../utils/animations';

/**
 * AnimatedCard Component
 * Card with hover animations and micro-interactions
 */
const AnimatedCard = ({
    children,
    className = '',
    onClick,
    ariaLabel,
    ...props
}) => {
    return (
        <motion.div
            className={`glass-card ${className}`}
            variants={cardHover}
            initial="rest"
            whileHover="hover"
            whileTap="tap"
            onClick={onClick}
            role={onClick ? 'button' : undefined}
            aria-label={ariaLabel}
            tabIndex={onClick ? 0 : undefined}
            onKeyDown={onClick ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onClick(e);
                }
            } : undefined}
            {...props}
        >
            {children}
        </motion.div>
    );
};

export default AnimatedCard;
