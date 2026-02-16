/**
 * Enterprise Retail Intelligence System v3.0
 * SALES CHART COMPONENT
 * 
 * Time-series visualization with Recharts.
 * V3.0 Standard: Uses ResponsiveContainer, memoized data processing.
 */

import { useMemo } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import Card from '../ui/Card';
import { formatCurrency, formatCompactNumber } from '../../lib/utils';
import { CHART_COLORS } from '../../lib/constants';

const SalesChart = ({ data, title = "Sales Trend & Forecast", height = 300 }) => {
    // Memoize chart data formatting (V3.0 Performance Standard)
    const chartData = useMemo(() => {
        if (!data || data.length === 0) return [];

        return data.map(d => ({
            date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            actual: d.actual || null,
            predicted: d.predicted || null,
            lowerBound: d.lowerBound || null,
            upperBound: d.upperBound || null
        }));
    }, [data]);

    // Custom tooltip
    const CustomTooltip = ({ active, payload }) => {
        if (!active || !payload || payload.length === 0) return null;

        const data = payload[0].payload;

        return (
            <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
                <p className="text-sm font-medium text-foreground mb-2">
                    {data.date}
                </p>
                {data.actual && (
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CHART_COLORS.primary }} />
                        <span className="text-xs text-muted-foreground">Actual:</span>
                        <span className="text-xs font-medium text-foreground">
                            {formatCompactNumber(data.actual)}
                        </span>
                    </div>
                )}
                {data.predicted && (
                    <>
                        <div className="flex items-center gap-2 mb-1">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CHART_COLORS.secondary }} />
                            <span className="text-xs text-muted-foreground">Predicted:</span>
                            <span className="text-xs font-medium text-foreground">
                                {formatCompactNumber(data.predicted)}
                            </span>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                            Range: {formatCompactNumber(data.lowerBound)} - {formatCompactNumber(data.upperBound)}
                        </div>
                    </>
                )}
            </div>
        );
    };

    return (
        <Card>
            <h3 className="text-lg font-semibold text-foreground mb-4">
                {title}
            </h3>

            <ResponsiveContainer width="100%" height={height}>
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={CHART_COLORS.secondary} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={CHART_COLORS.secondary} stopOpacity={0} />
                        </linearGradient>
                    </defs>

                    <CartesianGrid
                        strokeDasharray="3 3"
                        stroke={CHART_COLORS.grid}
                        opacity={0.1}
                    />

                    <XAxis
                        dataKey="date"
                        stroke="#9CA3AF"
                        style={{ fontSize: '12px' }}
                        tick={{ fill: '#9CA3AF' }}
                    />

                    <YAxis
                        stroke="#9CA3AF"
                        style={{ fontSize: '12px' }}
                        tick={{ fill: '#9CA3AF' }}
                        tickFormatter={(value) => formatCompactNumber(value)}
                    />

                    <Tooltip content={<CustomTooltip />} />

                    <Legend
                        wrapperStyle={{ fontSize: '12px' }}
                        iconType="circle"
                    />

                    {/* Actual Sales Area */}
                    <Area
                        type="monotone"
                        dataKey="actual"
                        stroke={CHART_COLORS.primary}
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorActual)"
                        name="Actual Sales"
                    />

                    {/* Predicted Sales Area */}
                    <Area
                        type="monotone"
                        dataKey="predicted"
                        stroke={CHART_COLORS.secondary}
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        fillOpacity={1}
                        fill="url(#colorPredicted)"
                        name="Forecast"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </Card>
    );
};

export default SalesChart;
