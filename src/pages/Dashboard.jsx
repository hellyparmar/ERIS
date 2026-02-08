import React, { useState, useEffect, useRef } from 'react';
import {
    BarChart2,
    Users,
    Package,
    TrendingUp
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
import { DashboardSkeleton } from '../components/ui/LoadingSkeleton';
import TransactionsTable from '../components/dashboard/TransactionsTable';
import { useToast } from '../components/ui/Toast';

// Register Chart.js components
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
    const { addToast } = useToast();
    const [timeRange, setTimeRange] = useState('30D');
    const [realtimeData, setRealtimeData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(null);

    // Initial fetch on component mount
    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/v1/dashboard/realtime');
                const data = await res.json();
                setRealtimeData(data);
                setLastUpdate(new Date());
                setLoading(false);
            } catch (error) {
                console.error('Failed to fetch realtime data:', error);
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Format currency
    const formatCurrency = (value) => {
        if (!value) return '₹0';
        return `₹${(value / 100000).toFixed(2)}L`; // Convert to Lakhs
    };

    // Top Metrics Data
    const metricsData = realtimeData ? {
        revenue: {
            label: "Total Revenue",
            value: formatCurrency(realtimeData.total_revenue),
            change: "+6.5%",
            icon: BarChart2,
            colorClass: "bg-blue-500",
            textClass: "text-white",
            subtitle: `Today: ${formatCurrency(realtimeData.today_revenue)}`
        },
        orders: {
            label: "Total Orders",
            value: realtimeData.total_orders.toLocaleString(),
            change: "+12%",
            icon: Users,
            colorClass: "bg-cyan-500",
            textClass: "text-white",
            subtitle: `Active: ${realtimeData.active_orders}`
        },
        aov: {
            label: "Avg Order Value",
            value: `₹${realtimeData.avg_order_value.toLocaleString()}`,
            change: null,
            icon: Package,
            colorClass: "bg-purple-500",
            textClass: "text-white",
            subtitle: "Per transaction"
        },
        time: {
            label: "Time Multiplier",
            value: `${(realtimeData.time_multiplier * 100).toFixed(0)}%`,
            change: realtimeData.time_multiplier > 1 ? "Peak Hours" : "Off-Peak",
            icon: TrendingUp,
            colorClass: "bg-green-500",
            textClass: "text-white",
            subtitle: realtimeData.data_source || "Live"
        }
    } : {
        // Fallback object to prevent crashing if loading=false but data is null (e.g. error)
        revenue: { label: "Total Revenue", value: "₹0", change: null, icon: BarChart2, colorClass: "bg-blue-500", textClass: "text-white" },
        orders: { label: "Active Users", value: "0", change: null, icon: Users, colorClass: "bg-cyan-500", textClass: "text-white" },
        aov: { label: "Inventory Value", value: "₹0", change: null, icon: Package, colorClass: "bg-purple-500", textClass: "text-white" },
        time: { label: "Forecasted Growth", value: "0%", change: null, icon: TrendingUp, colorClass: "bg-green-500", textClass: "text-white" }
    };

    // Chart Data Generation
    const getChartData = (range) => {
        const baseData1 = [50, 120, 150, 140, 200, 220, 300, 280, 350, 320, 400, 450];
        const baseData2 = [40, 90, 110, 100, 160, 180, 220, 200, 260, 240, 310, 340];
        const baseData3 = [20, 40, 60, 50, 80, 100, 120, 110, 140, 130, 160, 180];

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

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        redraw: true,
        animation: { duration: 0 },
        plugins: {
            legend: {
                position: 'top',
                align: 'end',
                labels: { usePointStyle: true, boxWidth: 8, font: { size: 10 }, color: '#94a3b8' }
            },
            tooltip: {
                mode: 'index', intersect: false, backgroundColor: 'rgba(15, 23, 42, 0.9)', titleColor: '#f8fafc', bodyColor: '#cbd5e1', borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1
            }
        },
        scales: {
            y: {
                beginAtZero: true, grid: { color: 'rgba(200, 200, 200, 0.1)', borderDash: [5, 5] }, ticks: { callback: (value) => `$${value}`, font: { size: 10 }, color: '#94a3b8' }
            },
            x: {
                grid: { display: false }, ticks: { font: { size: 10 }, color: '#94a3b8' }
            }
        }
    };

    const renderMetricCard = (key, metric) => {
        const Icon = metric.icon;
        return (
            <div key={key} className="h-full">
                <GlassCard variant="gradient" className="h-full p-6 relative overflow-hidden group hover:ring-2 hover:ring-primary/50 transition-all cursor-move">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-purple/5 opacity-50"></div>
                    <div className="relative z-10 flex flex-col justify-between h-full">
                        <div className="flex justify-between items-start">
                            <div className="flex-1">
                                <p className="text-sm font-medium text-muted-foreground mb-1">{metric.label}</p>
                                <h3 className="text-2xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                                    {metric.value}
                                </h3>
                            </div>
                            <div className={`p-2 rounded-xl ${metric.colorClass} shadow-lg flex items-center justify-center`}>
                                <Icon className={`w-5 h-5 ${metric.textClass}`} strokeWidth={2.5} />
                            </div>
                        </div>
                        <div className="mt-2">
                            {metric.subtitle && (
                                <p className="text-xs text-muted-foreground truncate">{metric.subtitle}</p>
                            )}
                            {metric.change && (
                                <div className="flex items-center gap-1 mt-1">
                                    <span className="text-xs font-semibold text-success bg-success/10 px-1.5 py-0.5 rounded border border-success/20">
                                        ↑ {metric.change}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </GlassCard>
            </div>
        );
    };

    return (
        <div className="min-h-screen fade-in-up space-y-6">
            {/* Page Loading Overlay */}
            {loading && (
                <div className="fixed inset-0 bg-background/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="text-center space-y-4">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full animate-pulse">
                            <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
                        </div>
                        <div>
                            <p className="text-lg font-semibold text-foreground">Page is loading</p>
                            <p className="text-sm text-muted-foreground mt-1">Fetching real-time data...</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">Dashboard</h1>
                    <p className="text-muted-foreground">Real-time enterprise overview</p>
                </div>
            </div>


            {/* Metrics Grid - Fixed Layout */}
            {loading ? (
                <DashboardSkeleton />
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        {renderMetricCard('revenue', metricsData.revenue)}
                        {renderMetricCard('orders', metricsData.orders)}
                        {renderMetricCard('aov', metricsData.aov)}
                        {renderMetricCard('time', metricsData.time)}
                    </div>

                    <div className="space-y-6">
                        {/* Sales Chart */}
                        <GlassCard className="p-6 flex flex-col">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-bold text-foreground text-lg">Sales Performance</h3>
                                <div className="flex gap-2 p-1 bg-muted rounded-lg">
                                    {['7D', '30D', '90D'].map((range) => (
                                        <button
                                            key={range}
                                            onClick={() => setTimeRange(range)}
                                            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${timeRange === range
                                                ? 'bg-background text-primary shadow-sm'
                                                : 'text-muted-foreground hover:text-foreground'
                                                }`}
                                        >
                                            {range}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="w-full h-80">
                                <Line data={getChartData(timeRange)} options={chartOptions} />
                            </div>
                        </GlassCard>

                        {/* Transactions Table */}
                        <GlassCard className="overflow-hidden flex flex-col">
                            <div className="flex-1">
                                <TransactionsTable />
                            </div>
                        </GlassCard>
                    </div>
                </>
            )}
        </div >
    );
};

export default Dashboard;
