import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

/**
 * ForecastToggle Component
 * Toggle button for showing/hiding ML-predicted forecast data on charts
 */
const ForecastToggle = ({ enabled, onToggle, className = "" }) => {
    return (
        <motion.button
            onClick={onToggle}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={`
                flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all
                ${enabled
                    ? 'bg-primary/10 border-primary text-primary'
                    : 'bg-muted border-border text-muted-foreground hover:bg-muted/80'
                }
                ${className}
            `}
            aria-label={`${enabled ? 'Hide' : 'Show'} forecast`}
            title={`${enabled ? 'Hide' : 'Show'} ML-predicted forecast`}
        >
            <motion.div
                animate={{ rotate: enabled ? 0 : 180 }}
                transition={{ duration: 0.3 }}
            >
                {enabled ? (
                    <TrendingUp className="w-4 h-4" />
                ) : (
                    <TrendingDown className="w-4 h-4" />
                )}
            </motion.div>
            <span className="text-sm font-medium">
                {enabled ? 'Forecast ON' : 'Show Forecast'}
            </span>
            {enabled && (
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-2 h-2 rounded-full bg-primary animate-pulse"
                />
            )}
        </motion.button>
    );
};

export default ForecastToggle;
