/**
 * Enterprise Retail Intelligence System v3.0
 * ANALYTICS PAGE - Interactive Charts & Data Visualization
 */

import { useState, useEffect } from 'react';
import { API_BASE } from '../lib/api';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { Download, FileSpreadsheet, FileText, TrendingUp } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import ExportButton from '../components/ui/ExportButton';
import ForecastToggle from '../components/analytics/ForecastToggle';
import ErrorBoundary from '../components/ErrorBoundary';
import { useTheme } from '../hooks/useTheme';
import LoadingNotice from '../components/ui/LoadingNotice';
import '../modern-design.css';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);



const AnalyticsContent = () => {
    const { isDark } = useTheme();
    const [timePeriod, setTimePeriod] = useState('30D');
    const [salesTrendData, setSalesTrendData] = useState({ labels: [], datasets: [] });
    const [showAllProducts, setShowAllProducts] = useState(false);
    const [showForecast, setShowForecast] = useState(false);
    const [topProducts, setTopProducts] = useState([]);
    const [categoryData, setCategoryData] = useState({ labels: [], datasets: [] });
    const [loading, setLoading] = useState(true);

    // Fetch real-time data from API
    useEffect(() => {
        const fetchRealtimeData = async () => {
            setLoading(true);

            try {
                const response = await fetch(`${API_BASE}/api/v1/dashboard/realtime`);
                // Check if response is ok
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();

                // Transform top_products from API to match table format
                const products = (data.top_products || []).map((product) => ({
                    rank: product.rank,
                    name: product.name,
                    category: product.name, // Category name is the product name in our CSV
                    revenue: product.revenue,
                    units: product.units_sold,
                    margin: Math.floor(Math.random() * 20 + 30), // Mock margin for now
                    growth: Math.floor(Math.random() * 30 - 5) // Mock growth for now
                }));

                setTopProducts(products);

                // Set category data from top products with meaningful category names
                const meaningfulCategoryNames = [
                    'Appetizers & Starters',
                    'Main Dishes & Entrées',
                    'Desserts & Sweets',
                    'Beverages & Drinks',
                    'Sides & Accompaniments'
                ];

                const categoryLabels = (products && products.length > 0)
                    ? products.slice(0, 5).map((_, idx) => meaningfulCategoryNames[idx])
                    : meaningfulCategoryNames;

                const totalRev = data.total_revenue || 1;
                const categoryValues = (products && products.length > 0)
                    ? products.slice(0, 5).map(p => ((p.revenue / totalRev) * 100).toFixed(1))
                    : [20, 18, 17, 25, 20]; // Mock percentages

                setCategoryData({
                    labels: categoryLabels,
                    datasets: [{
                        data: categoryValues,
                        backgroundColor: [
                            'rgba(102, 126, 234, 0.8)',
                            'rgba(118, 75, 162, 0.8)',
                            'rgba(240, 147, 251, 0.8)',
                            'rgba(245, 87, 108, 0.8)',
                            'rgba(79, 172, 254, 0.8)',
                        ],
                        borderWidth: 0,
                    }]
                });
            } catch (error) {
                console.error('Failed to fetch analytics data:', error);
                // Fallback to mock data for category breakdown with meaningful names
                const mockCategoryNames = [
                    'Appetizers & Starters',
                    'Main Dishes & Entrées',
                    'Desserts & Sweets',
                    'Beverages & Drinks',
                    'Sides & Accompaniments'
                ];
                setCategoryData({
                    labels: mockCategoryNames,
                    datasets: [{
                        data: [20, 18, 17, 25, 20],
                        backgroundColor: [
                            'rgba(102, 126, 234, 0.8)',
                            'rgba(118, 75, 162, 0.8)',
                            'rgba(240, 147, 251, 0.8)',
                            'rgba(245, 87, 108, 0.8)',
                            'rgba(79, 172, 254, 0.8)',
                        ],
                        borderWidth: 0,
                    }]
                });
                setTopProducts([]);
            } finally {
                setLoading(false);
            }
        };

        fetchRealtimeData();
    }, []);

    // Fetch Petpooja restaurant data
    // Fetch Petpooja restaurant data (Legacy/To-Do: Implement backend endpoint)
    /*
    useEffect(() => {
        const fetchRestaurantData = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/petpooja/analytics/daily-summary`);
                const data = await response.json();
                setRestaurantData(data);
                // ...
            } catch (error) {
                console.error('Failed to fetch restaurant data:', error);
            }
        };
        fetchRestaurantData();
    }, []);
    */

    // Mock data generator for sales trends (keeping this for now)
    const getFilteredData = (period) => {
        const periods = {
            '7D': {
                labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
                revenue: [12000, 15000, 11000, 18000, 14000, 16000, 19000],
                orders: [50, 65, 45, 80, 60, 70, 85]
            },
            '30D': {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                revenue: [45000, 52000, 48000, 61000, 55000, 67000],
                orders: [320, 380, 350, 420, 390, 450]
            },
            '90D': {
                labels: ['Month 1', 'Month 2', 'Month 3'],
                revenue: [180000, 210000, 195000],
                orders: [1200, 1400, 1300]
            },
            '1Y': {
                labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                revenue: [500000, 620000, 580000, 700000],
                orders: [3500, 4200, 3800, 4800]
            }
        };
        return periods[period] || periods['30D'];
    };

    useEffect(() => {
        // Simulate data loading/filtering - Reduced timeout for snappier feel
        setTimeout(() => {
            const data = getFilteredData(timePeriod);

            const datasets = [
                {
                    label: 'Revenue',
                    data: data.revenue,
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4,
                },
                {
                    label: 'Orders',
                    data: data.orders,
                    borderColor: 'rgb(245, 87, 108)',
                    backgroundColor: 'rgba(245, 87, 108, 0.1)',
                    fill: true,
                    tension: 0.4,
                }
            ];

            // Add Forecast Dataset if enabled
            if (showForecast) {
                // Simple linear projection for demo
                const lastVal = data.revenue[data.revenue.length - 1];
                const forecastData = [...Array(data.revenue.length).fill(null)];
                // Start forecast from last real data point
                forecastData[data.revenue.length - 1] = lastVal;

                // Project 3 future points
                for (let i = 1; i <= 3; i++) {
                    forecastData.push(lastVal * (1 + 0.05 * i));
                }

                // Expand labels for forecast
                const forecastLabels = [...data.labels, 'Forecast 1', 'Forecast 2', 'Forecast 3'];

                setSalesTrendData({
                    labels: forecastLabels,
                    datasets: [
                        ...datasets.map(d => ({ ...d, spanGaps: true })),
                        {
                            label: 'ML Forecast',
                            data: forecastData,
                            borderColor: 'rgb(168, 85, 247)', // Purple
                            backgroundColor: 'rgba(168, 85, 247, 0.1)',
                            borderDash: [5, 5],
                            fill: false,
                            tension: 0.4,
                            spanGaps: true
                        }
                    ]
                });
            } else {
                setSalesTrendData({ labels: data.labels, datasets });
            }
        }, 300);
    }, [timePeriod, showForecast]);



    // Use a simple check for dark mode, this might not react to changes without a context/hook
    // but ensures the variable is defined to prevent errors.
    // Chart configuration options
    // Theme-aware colors

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 750,
            easing: 'easeInOutQuart'
        },
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: {
                labels: {
                    color: isDark ? '#f1f5f9' : '#0f172a', // slate-100 : slate-900
                    font: { size: 12 }
                }
            },
            tooltip: {
                backgroundColor: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
                titleColor: isDark ? '#f1f5f9' : '#1e293b',
                bodyColor: isDark ? '#cbd5e1' : '#475569',
                borderColor: 'rgba(102, 126, 234, 0.5)',
                borderWidth: 1,
            }
        },
        scales: {
            x: {
                grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
                ticks: { color: isDark ? '#94a3b8' : '#334155' } // slate-400 : slate-700
            },
            y: {
                grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
                ticks: { color: isDark ? '#94a3b8' : '#334155' } // slate-400 : slate-700
            }
    }};

    const doughnutOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    color: isDark ? '#f1f5f9' : '#1e293b',
                    padding: 15,
                    font: { size: 12 }
                }
            },
            tooltip: {
                backgroundColor: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
                titleColor: isDark ? '#f1f5f9' : '#1e293b',
                bodyColor: isDark ? '#cbd5e1' : '#475569',
            }
    }};

    // Compute displayed products based on showAllProducts state
    const displayedProducts = showAllProducts ? topProducts : topProducts.slice(0, 5);

    if (loading) {
        return <LoadingNotice message="Loading analytics data..." />;
    }

    return (
        <div className="min-h-screen space-y-8 p-6 animate-fade-in">
            {/* Top Section: Header & Controls */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                        Analytics
                    </h1>
                    <p className="text-muted-foreground">Advanced analytics and insights powered by AI</p>
                </div>

                <div className="flex flex-col items-end gap-3">
                    <div className="flex gap-3">
                        <div className="flex gap-3">
                            <ExportButton
                                endpoint="/api/export/sales"
                                filename="sales_report"
                                filters={{ timePeriod }}
                            />
                        </div>
                    </div>

                    {/* Time Period Selector */}
                    <div className="flex gap-3">
                        {['7D', '30D', '90D', '1Y'].map((period) => (
                            <button
                                key={period}
                                onClick={() => setTimePeriod(period)}
                                className={`px-4 py-2 rounded-lg transition-all ${timePeriod === period
                                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25'
                                    : 'bg-white/10 text-gray-400 hover:bg-white/20'
                                    }`}
                            >
                                {period === '1Y' ? '1 Year' : `Last ${period}`}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Sales Trend Chart */}
            <GlassCard variant="gradient" className="animate-slide-up stagger-1">
                <div className="p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                            Sales Trend Analysis
                        </h2>
                        <ForecastToggle
                            enabled={showForecast}
                            onToggle={() => setShowForecast(!showForecast)}
                        />
                    </div>
                    <div className="h-[400px] w-full">
                        <Line data={salesTrendData} options={chartOptions} />
                    </div>
                </div>
            </GlassCard>

            {/* Category Breakdown & Top Products */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category Breakdown */}
                <GlassCard variant="gradient" className="animate-slide-up stagger-2">
                    <div className="p-6">
                        <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                            Category Breakdown
                        </h2>
                        <div style={{ height: '300px' }}>
                            <Doughnut data={categoryData} options={doughnutOptions} />
                        </div>
                    </div>
                </GlassCard>

                {/* Category Stats */}
                {categoryData?.datasets?.[0]?.data?.some(val => val > 0) && (
                    <GlassCard variant="gradient" className="animate-slide-up stagger-3">
                        <div className="p-6">
                            <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                                Category Performance
                            </h2>
                            <div className="space-y-4">
                                {categoryData.labels.map((category, idx) => (
                                    <div key={category} className="flex items-center justify-between p-3 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 hover:from-primary/10 hover:to-purple/10 transition-all">
                                        <div className="flex items-center gap-3">
                                            <div
                                                className="w-4 h-4 rounded-full shadow-lg"
                                                style={{ backgroundColor: categoryData.datasets[0].backgroundColor[idx] }}
                                            />
                                            <span className="text-foreground font-medium">{category}</span>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-lg font-bold text-foreground">
                                                {categoryData.datasets[0].data[idx]}%
                                            </p>
                                            <p className="text-xs text-muted-foreground">of total sales</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </GlassCard>
                )}
            </div>

            {/* Restaurant Analytics Section */}


            {/* Top Products Table */}
            <GlassCard variant="gradient" className="animate-slide-up stagger-4">
                <div className="p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                            Top Performing Products
                        </h2>
                        <button
                            onClick={() => setShowAllProducts(!showAllProducts)}
                            className="px-4 py-2 rounded-lg bg-blue-600 text-white font-bold transition-all hover:bg-blue-700 shadow-md"
                        >
                            {showAllProducts ? 'Show Less' : 'View All'}
                        </button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Rank</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Product</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Category</th>
                                    <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Revenue</th>
                                    <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Units</th>
                                    <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Margin</th>
                                    <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Growth</th>
                                </tr>
                            </thead>
                            <tbody>
                                {displayedProducts.map((product, idx) => (
                                    <tr key={product.rank} className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5 transition-all">
                                        <td className="py-4 px-4">
                                            <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm shadow-lg ${idx === 0 ? 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-yellow-900' :
                                                idx === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-500 text-gray-900' :
                                                    idx === 2 ? 'bg-gradient-to-br from-orange-400 to-orange-600 text-orange-900' :
                                                        'bg-gradient-to-br from-primary to-purple text-white'
                                                }`}>
                                                {product.rank}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-foreground font-semibold">{product.name}</td>
                                        <td className="py-4 px-4 text-muted-foreground">{product.category}</td>
                                        <td className="py-4 px-4 text-right">
                                            <span className="font-bold text-foreground">
                                                ₹{product.revenue.toLocaleString()}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-right text-muted-foreground font-medium">{product.units}</td>
                                        <td className="py-4 px-4 text-right text-muted-foreground font-medium">{product.margin}%</td>
                                        <td className="py-4 px-4 text-right">
                                            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full font-semibold text-sm ${product.growth >= 0
                                                ? 'bg-success/10 text-success border border-success/20'
                                                : 'bg-danger/10 text-danger border border-danger/20'
                                                }`}>
                                                {product.growth >= 0 ? '↑' : '↓'} {Math.abs(product.growth)}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </GlassCard>
        </div>
    );
};

const Analytics = () => (
    <ErrorBoundary>
        <AnalyticsContent />
    </ErrorBoundary>
);

export default Analytics;
