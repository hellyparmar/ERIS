import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

/**
 * ForecastToggle Component
 * Toggle button for showing/hiding ML-predicted forecast data on charts
 */
const ForecastToggle = ({ enabled, onToggle, className = "" }) => {
    return (
        <button
            onClick={onToggle}
            className={`
                flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all
                ${enabled
                    ? 'bg-primary/10 border-primary text-primary'
                    : 'bg-transparent border-border/50 text-muted-foreground hover:bg-white/5'
                }
                ${className}
            `}
            aria-label={`${enabled ? 'Hide' : 'Show'} forecast`}
            title={`${enabled ? 'Hide' : 'Show'} ML-predicted forecast`}
        >
            <div
            >
                {enabled ? (
                    <TrendingUp className="w-4 h-4" />
                ) : (
                    <TrendingDown className="w-4 h-4" />
                )}
            </div>
            <span className="text-sm font-normal">
                {enabled ? 'Forecast ON' : 'Show Forecast'}
            </span>
            {enabled && (
                <div
                    className="w-2 h-2 rounded-full bg-primary animate-pulse"
                />
            )}
        </button>
    );
};

export default ForecastToggle;
