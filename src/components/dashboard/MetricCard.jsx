/**
 * Enterprise Retail Intelligence System v3.0
 * METRIC CARD COMPONENT
 * 
 * Displays KPI metrics with trend indicators.
 * V3.0 Protocol: Uses COLOR_MAP for styling, no dynamic classes.
 */

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useMemo } from 'react';
import clsx from 'clsx';
import Card from '../ui/Card';
import { formatCurrency, formatCompactNumber, formatPercentage } from '../../lib/utils';
import { useLanguage } from '../../hooks/useLanguage';

const MetricCard = ({
    title,
    value,
    change,
    trend = 'neutral',
    format = 'number',
    icon: Icon,
    loading = false
}) => {
    const { t } = useLanguage();

    // Memoize formatted value for performance (V3.0 Standard)
    const formattedValue = useMemo(() => {
        if (loading) return '---';

        switch (format) {
            case 'currency':
                return formatCurrency(value);
            case 'compact':
                return formatCompactNumber(value);
            case 'percentage':
                return formatPercentage(value);
            default:
                return value.toLocaleString();
        }
    }, [value, format, loading]);

    // Determine trend icon and color
    const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

    const trendColorClass = clsx({
        'text-green-600 dark:text-green-400': trend === 'up',
        'text-red-600 dark:text-red-400': trend === 'down',
        'text-gray-600 dark:text-gray-400': trend === 'neutral'
    });

    const changeBgClass = clsx({
        'bg-green-100 dark:bg-green-900/20': trend === 'up',
        'bg-red-100 dark:bg-red-900/20': trend === 'down',
        'bg-gray-100 dark:bg-gray-900/20': trend === 'neutral'
    });

    return (
        <Card className="hover:shadow-xl">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    {/* Title */}
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                        {title}
                    </p>

                    {/* Value */}
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
                        {formattedValue}
                    </p>

                    {/* Change Indicator */}
                    {change !== undefined && change !== null && (
                        <div className="flex items-center gap-2">
                            <div className={clsx(
                                'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
                                changeBgClass,
                                trendColorClass
                            )}>
                                <TrendIcon className="w-3 h-3" />
                                <span>{Math.abs(change).toFixed(1)}%</span>
                            </div>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                {t('dashboard').vsLastPeriod}
                            </span>
                        </div>
                    )}
                </div>

                {/* Icon */}
                {Icon && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <Icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                )}
            </div>
        </Card>
    );
};

export default MetricCard;
