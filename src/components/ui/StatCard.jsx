import React from 'react';
import CountUp from 'react-countup';
import GlassCard from './GlassCard';
import '../../modern-design.css';

/**
 * StatCard - Animated metric display card
 * 
 * @param {object} props
 * @param {string} props.title - Card title
 * @param {number} props.value - Numeric value to display
 * @param {number} props.change - Percentage change (optional)
 * @param {ReactNode} props.icon - Icon component
 * @param {string} props.gradient - Gradient variant
 * @param {string} props.prefix - Value prefix (e.g., '₹', '$')
 * @param {string} props.suffix - Value suffix (e.g., 'K', 'M')
 */
const StatCard = ({
    title,
    value,
    change = null,
    icon,
    gradient = 'primary',
    prefix = '',
    suffix = '',
    decimals = 0,
    sparklineData = null,
}) => {
    const gradients = {
        primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        success: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        warning: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    };

    const isPositive = change >= 0;

    return (
        <GlassCard className="stat-card p-5">
            <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                    <p className="text-muted-foreground text-sm mb-2 font-medium truncate" title={title}>{title}</p>
                    <div className="animated-number text-2xl lg:text-3xl font-bold text-foreground break-words mb-3">
                        <CountUp
                            end={value}
                            duration={2}
                            separator=","
                            decimals={decimals}
                            prefix={prefix}
                            suffix={suffix}
                        />
                    </div>

                    {change !== null && (
                        <div className={`trend-indicator flex items-center flex-wrap gap-1 text-sm ${isPositive ? 'trend-up' : 'trend-down'}`}>
                            <span className={`flex items-center font-bold ${isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                                {isPositive ? '↑' : '↓'} {Math.abs(change)}%
                            </span>
                            <span className="text-muted-foreground text-xs whitespace-nowrap">vs last period</span>
                        </div>
                    )}
                </div>

                <div
                    className="icon-container p-4 rounded-xl flex-shrink-0 flex items-center justify-center"
                    style={{ background: gradients[gradient] }}
                >
                    {icon}
                </div>
            </div>

            {sparklineData && (
                <div className="mt-4 h-12">
                    {/* Simple sparkline - can be enhanced with chart library */}
                    <svg width="100%" height="100%" className="sparkline">
                        <polyline
                            fill="none"
                            stroke="url(#gradient)"
                            strokeWidth="2"
                            points={sparklineData.map((val, i) =>
                                `${(i / (sparklineData.length - 1)) * 100},${100 - (val / Math.max(...sparklineData)) * 100}`
                            ).join(' ')}
                        />
                        <defs>
                            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#667eea" />
                                <stop offset="100%" stopColor="#764ba2" />
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
            )}
        </GlassCard>
    );
};

export default StatCard;
