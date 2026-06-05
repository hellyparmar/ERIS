/**
 * Enterprise Retail Intelligence System v3.0
 * INVENTORY ALERTS COMPONENT
 * 
 * Displays critical and warning inventory alerts.
 * V3.0 Protocol: Uses COLOR_MAP for severity-based styling.
 */

import { AlertTriangle, Clock, Package, TrendingDown, TrendingUp } from 'lucide-react';
import { useMemo } from 'react';
import clsx from 'clsx';
import Card from '../ui/Card';
import { COLOR_MAP } from '../../lib/constants';
import { useLanguage } from '../../hooks/useLanguage';

const InventoryAlerts = ({ alerts = [], maxDisplay = 5 }) => {
    const { t } = useLanguage();

    // Memoize filtered alerts (V3.0 Performance Standard)
    const displayedAlerts = useMemo(() => {
        return alerts.slice(0, maxDisplay);
    }, [alerts, maxDisplay]);

    // Get severity styling using COLOR_MAP (V3.0 Protocol: NO dynamic classes)
    const getSeverityClasses = (severity) => {
        const colorConfig = COLOR_MAP[severity] || COLOR_MAP.neutral;
        return {
            bg: colorConfig.bgLight,
            border: colorConfig.border,
            text: colorConfig.text,
            darkText: colorConfig.darkText
        };
    };

    // Get icon for alert type
    const getAlertIcon = (type) => {
        switch (type) {
            case 'stockout':
                return AlertTriangle;
            case 'low_stock':
                return Package;
            case 'demand_spike':
                return TrendingUp;
            default:
                return Clock;
        }
    };

    if (!alerts || alerts.length === 0) {
        return (
            <Card>
                <h3 className="text-lg font-semibold text-foreground mb-4">
                    {t('dashboard').inventoryAlerts}
                </h3>
                <div className="text-center py-8">
                    <Package className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground">
                        No active alerts. All inventory levels are healthy!
                    </p>
                </div>
            </Card>
        );
    }

    return (
        <Card>
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground">
                    {t('dashboard').inventoryAlerts}
                </h3>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                    {alerts.length} {t('dashboard').total}
                </span>
            </div>

            <div className="space-y-3">
                {displayedAlerts.map((alert) => {
                    const severity = getSeverityClasses(alert.severity);
                    const AlertIcon = getAlertIcon(alert.type);

                    return (
                        <div
                            key={alert.id}
                            className={clsx(
                                'p-4 rounded-lg border-l-4 transition-base hover:shadow-md',
                                severity.bg,
                                severity.border
                            )}
                        >
                            <div className="flex items-start gap-3">
                                {/* Icon */}
                                <div className={clsx('flex-shrink-0', severity.text, severity.darkText)}>
                                    <AlertIcon className="w-5 h-5" />
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                    <p className={clsx('font-medium text-sm', severity.text, severity.darkText)}>
                                        {alert.message}
                                    </p>

                                    {alert.recommendation && (
                                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                            💡 {alert.recommendation}
                                        </p>
                                    )}

                                    {alert.daysToStockout !== undefined && (
                                        <div className="flex items-center gap-2 mt-2">
                                            <Clock className="w-3 h-3 text-gray-400" />
                                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                                {alert.daysToStockout} days remaining
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Severity Badge */}
                                <div className={clsx(
                                    'flex-shrink-0 px-2 py-1 rounded-full text-xs font-medium',
                                    COLOR_MAP[alert.severity].badge
                                )}>
                                    {alert.severity.toUpperCase()}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {alerts.length > maxDisplay && (
                <button className="w-full mt-4 text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium">
                    View all {alerts.length} alerts →
                </button>
            )}
        </Card>
    );
};

export default InventoryAlerts;
