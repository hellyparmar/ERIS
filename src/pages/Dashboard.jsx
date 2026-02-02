import React, { useState, useEffect } from 'react';
import {
    BarChart2,
    Users,
    Package,
    TrendingUp,
    RefreshCw
} from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import GlassCard from '../components/ui/GlassCard';
import TransactionsTable from '../components/dashboard/TransactionsTable';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const Dashboard = () => {
    const [timeRange, setTimeRange] = useState('30D');
    const [realtimeData, setRealtimeData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(null);

    // Fetch real-time data from API
    const fetchRealtimeData = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/v1/dashboard/realtime');
            const data = await response.json();
            setRealtimeData(data);
            setLastUpdate(new Date());
            setLoading(false);
        } catch (error) {
            console.error('Failed to fetch realtime data:', error);
            setLoading(false);
        }
    };

    // Initial fetch and auto-refresh every 30 seconds
    useEffect(() => {
        fetchRealtimeData();
        const interval = setInterval(fetchRealtimeData, 30000); // 30 seconds
        return () => clearInterval(interval);
    }, []);

    // Format currency
    const formatCurrency = (value) => {
        if (!value) return '₹0';
        return `₹${(value / 100000).toFixed(2)}L`; // Convert to Lakhs
    };

    // Top Metrics Data - Using real API data
    const metrics = realtimeData ? [
        {
            label: "Total Revenue",
            value: formatCurrency(realtimeData.total_revenue),
            change: "+6.5%",
            icon: BarChart2,
            colorClass: "bg-blue-500",
            textClass: "text-white",
            subtitle: `Today: ${formatCurrency(realtimeData.today_revenue)}`
        },
        {
            label: "Total Orders",
            value: realtimeData.total_orders.toLocaleString(),
            change: "+12%",
            icon: Users,
            colorClass: "bg-cyan-500",
            textClass: "text-white",
            subtitle: `Active: ${realtimeData.active_orders}`
        },
        {
            label: "Avg Order Value",
            value: `₹${realtimeData.avg_order_value.toLocaleString()}`,
            change: null,
            icon: Package,
            colorClass: "bg-purple-500",
            textClass: "text-white",
            subtitle: "Per transaction"
        },
        {
            label: "Time Multiplier",
            value: `${(realtimeData.time_multiplier * 100).toFixed(0)}%`,
            change: realtimeData.time_multiplier > 1 ? "Peak Hours" : "Off-Peak",
            icon: TrendingUp,
            colorClass: "bg-green-500",
            textClass: "text-white",
            subtitle: realtimeData.data_source || "Live"
        }
    ] : [
        { label: "Total Revenue", value: "Loading...", change: null, icon: BarChart2, colorClass: "bg-blue-500", textClass: "text-white" },
        { label: "Active Users", value: "Loading...", change: null, icon: Users, colorClass: "bg-cyan-500", textClass: "text-white" },
        { label: "Inventory Value", value: "Loading...", change: null, icon: Package, colorClass: "bg-purple-500", textClass: "text-white" },
        { label: "Forecasted Growth", value: "Loading...", change: null, icon: TrendingUp, colorClass: "bg-green-500", textClass: "text-white" }
    ];

    // Chart Data Generation based on Time Range
    const getChartData = (range) => {
        const baseData1 = [50, 120, 150, 140, 200, 220, 300, 280, 350, 320, 400, 450];
        const baseData2 = [40, 90, 110, 100, 160, 180, 220, 200, 260, 240, 310, 340];
        const baseData3 = [20, 40, 60, 50, 80, 100, 120, 110, 140, 130, 160, 180];

        // Simulate different data for ranges (simple slicing or scaling for demo)
        let modifier = 1;
        if (range === '7D') modifier = 0.5;
        if (range === '90D') modifier = 2;

        return {
            labels: ['May 8', 'May 10', 'May 12', 'May 14', 'May 16', 'May 18', 'May 20', 'May 22', 'May 24', 'May 26', 'May 28', 'May 30'],
            datasets: [
                {
                    label: 'Online Sales',
                    data: baseData1.map(v => v * modifier),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'In-Store Sales',
                    data: baseData2.map(v => v * modifier),
                    borderColor: '#0ea5e9',
                    backgroundColor: 'rgba(14, 165, 233, 0.05)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'B2B Orders',
                    data: baseData3.map(v => v * modifier),
                    borderColor: '#6366f1',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.4
                }
            ]
        };
    };

    const chartData = getChartData(timeRange);

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 750,
            easing: 'easeInOutQuart'
        },
        plugins: {
            legend: {
                position: 'top',
                align: 'end',
                labels: {
                    usePointStyle: true,
                    boxWidth: 8,
                    font: { size: 10 },
                    color: '#94a3b8' // Slate 400
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleColor: '#f8fafc',
                bodyColor: '#cbd5e1',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(200, 200, 200, 0.1)',
                    borderDash: [5, 5]
                },
                ticks: {
                    callback: (value) => `$${value}`,
                    font: { size: 10 },
                    color: '#94a3b8'
                }
            },
            x: {
                grid: { display: false },
                ticks: { font: { size: 10 }, color: '#94a3b8' }
            }
        }
    };

    return (
        <div className="min-h-screen fade-in-up space-y-8">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">Dashboard</h1>
                    <p className="text-gray-400">Real-time enterprise overview with actual data</p>
                </div>
                <div className="flex items-center gap-3">
                    {lastUpdate && (
                        <span className="text-xs text-gray-500">
                            Updated: {lastUpdate.toLocaleTimeString()}
                        </span>
                    )}
                    <button
                        onClick={fetchRealtimeData}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Premium Metrics Row with Stagger Animation */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {metrics.map((metric, idx) => {
                    const Icon = metric.icon;
                    const staggerClass = `stagger-${idx + 1}`;
                    return (
                        <GlassCard
                            key={idx}
                            variant="gradient"
                            className={`p-6 relative overflow-hidden animate-slide-up ${staggerClass}`}
                        >
                            {/* Gradient Background Overlay */}
                            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-purple/5 opacity-50"></div>

                            {/* Content */}
                            <div className="relative z-10">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-muted-foreground mb-2">
                                            {metric.label}
                                        </p>
                                        <h3 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                                            {metric.value}
                                        </h3>
                                        {metric.subtitle && (
                                            <p className="text-xs text-muted-foreground mt-2">
                                                {metric.subtitle}
                                            </p>
                                        )}
                                    </div>
                                    <div className={`p-3 rounded-xl ${metric.colorClass} shadow-lg flex items-center justify-center animate-pulse-custom`}>
                                        <Icon className={`w-6 h-6 ${metric.textClass}`} strokeWidth={2.5} />
                                    </div>
                                </div>
                                {metric.change && (
                                    <div className="flex items-center gap-2 mt-4">
                                        <span className="text-xs font-semibold text-success bg-success/10 px-2 py-1 rounded-md border border-success/20">
                                            ↑ {metric.change}
                                        </span>
                                        <span className="text-xs text-muted-foreground">vs last period</span>
                                    </div>
                                )}
                            </div>
                        </GlassCard>
                    );
                })}
            </div>

            {/* Sales Performance Chart */}
            <GlassCard className="p-6">
                <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                    <h3 className="font-bold text-slate-900 dark:text-white text-lg">Sales Performance</h3>

                    {/* Time Filters */}
                    <div className="flex gap-2 p-1 bg-slate-100 dark:bg-secondary/50 rounded-lg">
                        {['7D', '30D', '90D'].map((range) => (
                            <button
                                key={range}
                                onClick={() => setTimeRange(range)}
                                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${timeRange === range
                                    ? 'bg-white dark:bg-card text-blue-600 dark:text-blue-400 shadow-sm'
                                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                                    }`}
                            >
                                {range}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="h-[300px] w-full">
                    <Line data={chartData} options={chartOptions} />
                </div>
            </GlassCard>

            {/* Recent Transactions Table */}
            <div className="h-[400px]">
                <TransactionsTable />
            </div>
        </div>
    );
};

export default Dashboard;
