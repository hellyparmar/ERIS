/**
 * Enterprise Retail Intelligence System v3.0
 * ANALYTICS PAGE - Interactive Charts & Data Visualization
 */

import { useState, useEffect } from 'react';
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
import { useTheme } from '../hooks/useTheme';
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



const Analytics = () => {
    const { isDark } = useTheme();
    const [timePeriod, setTimePeriod] = useState('30D');
    const [salesTrendData, setSalesTrendData] = useState({ labels: [], datasets: [] });
    const [showAllProducts, setShowAllProducts] = useState(false);
    const [showForecast, setShowForecast] = useState(false);
    const [topProducts, setTopProducts] = useState([]);
    const [categoryData, setCategoryData] = useState({ labels: [], datasets: [] });
    const [restaurantData, setRestaurantData] = useState(null);
    const [revenueComparisonData, setRevenueComparisonData] = useState({ labels: [], datasets: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch real-time data from API
    useEffect(() => {
        const fetchRealtimeData = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await fetch('http://localhost:8000/api/v1/dashboard/realtime');
                // Check if response is ok
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();

                // Transform top_products from API to match table format
                const products = data.top_products.map((product) => ({
                    rank: product.rank,
                    name: product.name,
                    category: product.name, // Category name is the product name in our CSV
                    revenue: product.revenue,
                    units: product.units_sold,
                    margin: Math.floor(Math.random() * 20 + 30), // Mock margin for now
                    growth: Math.floor(Math.random() * 30 - 5) // Mock growth for now
                }));

                setTopProducts(products);

                // Set category data from top products
                const categoryLabels = products.slice(0, 5).map(p => p.name);
                const categoryValues = products.slice(0, 5).map(p => Math.floor((p.revenue / data.total_revenue) * 100));

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
                // Fallback to empty data
                setTopProducts([]);
            }
        };

        fetchRealtimeData();
    }, []);

    // Fetch Petpooja restaurant data
    useEffect(() => {
        const fetchRestaurantData = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/petpooja/analytics/daily-summary');
                const data = await response.json();
                setRestaurantData(data);

                // Create revenue comparison chart data
                const retailResponse = await fetch('http://localhost:8000/api/v1/dashboard/realtime');
                const retailData = await retailResponse.json();

                setRevenueComparisonData({
                    labels: ['Retail', 'Restaurant'],
                    datasets: [{
                        label: 'Today\'s Revenue',
                        data: [
                            retailData.today_revenue / 100000, // Convert to Lakhs
                            data.total_revenue / 100000
                        ],
                        backgroundColor: [
                            'rgba(102, 126, 234, 0.8)',
                            'rgba(245, 158, 11, 0.8)', // Amber for restaurant
                        ],
                        borderWidth: 0,
                    }]
                });
            } catch (error) {
                console.error('Failed to fetch restaurant data:', error);
            }
        };

        fetchRestaurantData();
    }, []);

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
                    color: isDark ? '#f1f5f9' : '#1e293b',
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
                ticks: { color: isDark ? '#94a3b8' : '#64748b' }
            },
            y: {
                grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
                ticks: { color: isDark ? '#94a3b8' : '#64748b' }
            }
        }
    };

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
        }
    };

    // Compute displayed products based on showAllProducts state
    const displayedProducts = showAllProducts ? topProducts : topProducts.slice(0, 5);

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
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
                    <div style={{ height: '350px' }}>
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
                                        <p className="text-lg font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                                            {categoryData.datasets[0].data[idx]}%
                                        </p>
                                        <p className="text-xs text-muted-foreground">of total sales</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* Restaurant Analytics Section */}
            {restaurantData && (
                <>
                    <div className="mt-8">
                        <h2 className="text-2xl font-bold gradient-text mb-4">🍽️ Store Operations Analytics</h2>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Revenue Comparison */}
                        <GlassCard>
                            <div className="p-6">
                                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Revenue Comparison</h2>
                                <div style={{ height: '300px' }}>
                                    <Bar data={revenueComparisonData} options={{
                                        ...chartOptions,
                                        plugins: {
                                            ...chartOptions.plugins,
                                            legend: { display: false }
                                        },
                                        scales: {
                                            ...chartOptions.scales,
                                            y: {
                                                ...chartOptions.scales.y,
                                                title: {
                                                    display: true,
                                                    text: 'Revenue (₹ Lakhs)',
                                                    color: isDark ? '#94a3b8' : '#64748b'
                                                }
                                            }
                                        }
                                    }} />
                                </div>
                                <div className="mt-4 grid grid-cols-2 gap-4">
                                    <div className="text-center">
                                        <p className="text-sm text-gray-500">Retail</p>
                                        <p className="text-2xl font-bold text-blue-600">₹{(revenueComparisonData.datasets[0]?.data[0] || 0).toFixed(2)}L</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-sm text-gray-500">Restaurant</p>
                                        <p className="text-2xl font-bold text-amber-600">₹{(revenueComparisonData.datasets[0]?.data[1] || 0).toFixed(2)}L</p>
                                    </div>
                                </div>
                            </div>
                        </GlassCard>

                        {/* Order Type Breakdown */}
                        <GlassCard>
                            <div className="p-6">
                                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Order Type Distribution</h2>
                                <div style={{ height: '300px' }}>
                                    <Doughnut data={{
                                        labels: Object.keys(restaurantData.order_type_breakdown || {}),
                                        datasets: [{
                                            data: Object.values(restaurantData.order_type_breakdown || {}).map(v => v.count),
                                            backgroundColor: [
                                                'rgba(59, 130, 246, 0.8)', // Blue for Dine-in
                                                'rgba(34, 197, 94, 0.8)', // Green for Takeaway
                                                'rgba(168, 85, 247, 0.8)', // Purple for Delivery
                                            ],
                                            borderWidth: 0,
                                        }]
                                    }} options={doughnutOptions} />
                                </div>
                            </div>
                        </GlassCard>

                        {/* Payment Method Breakdown */}
                        <GlassCard>
                            <div className="p-6">
                                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Payment Methods</h2>
                                <div className="space-y-3">
                                    {Object.entries(restaurantData.payment_method_breakdown || {}).map(([method, data]) => (
                                        <div key={method} className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-3 h-3 rounded-full ${method === 'Cash' ? 'bg-green-500' :
                                                    method === 'Card' ? 'bg-blue-500' :
                                                        method === 'UPI' ? 'bg-purple-500' :
                                                            'bg-amber-500'
                                                    }`} />
                                                <span className="text-gray-300">{method}</span>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-gray-900 dark:text-white font-semibold">{data.count}</p>
                                                <p className="text-xs text-gray-500">₹{data.amount.toLocaleString()}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </GlassCard>

                        {/* Restaurant Summary Stats */}
                        <GlassCard>
                            <div className="p-6">
                                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Restaurant Summary</h2>
                                <div className="space-y-4">
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Total Orders</span>
                                        <span className="font-bold text-gray-900 dark:text-white">{restaurantData.total_orders}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Total Revenue</span>
                                        <span className="font-bold text-gray-900 dark:text-white">₹{restaurantData.total_revenue.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">GST Collected</span>
                                        <span className="font-bold text-gray-900 dark:text-white">₹{restaurantData.total_gst_collected.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Avg Order Value</span>
                                        <span className="font-bold text-gray-900 dark:text-white">₹{restaurantData.average_order_value.toFixed(2)}</span>
                                    </div>
                                    <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                                        <p className="text-sm text-gray-500 mb-2">Peak Hours</p>
                                        <div className="flex gap-2">
                                            <span className="px-3 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full text-sm">
                                                {restaurantData.peak_hours.lunch}
                                            </span>
                                            <span className="px-3 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full text-sm">
                                                {restaurantData.peak_hours.dinner}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </GlassCard>
                    </div>
                </>
            )}

            {/* Top Products Table */}
            <GlassCard variant="gradient" className="animate-slide-up stagger-4">
                <div className="p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                            Top Performing Products
                        </h2>
                        <button
                            onClick={() => setShowAllProducts(!showAllProducts)}
                            className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary/20 to-purple/20 hover:from-primary/30 hover:to-purple/30 text-primary font-medium transition-all border border-primary/30"
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
                                            <span className="font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
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

export default Analytics;
