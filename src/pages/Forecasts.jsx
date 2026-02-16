/**
 * Enterprise Retail Intelligence System v3.0
 * FORECASTS PAGE - AI-Powered Demand Predictions
 */

import { useState, useEffect } from 'react';
import { API_BASE } from '../lib/api';
import { TrendingUp, TrendingDown, Target, Brain, Zap, AlertCircle, CheckCircle, ArrowUp, ArrowDown, Info, Package, Truck } from 'lucide-react';
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
import { Line } from 'react-chartjs-2';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import ActionButton from '../components/ui/ActionButton';
import { useTheme } from '../hooks/useTheme';
import '../modern-design.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const Forecasts = () => {
    const { isDark } = useTheme();
    const [timeHorizon, setTimeHorizon] = useState(30);
    const [growthRate, setGrowthRate] = useState(0); // For What-If Analysis
    const [loading, setLoading] = useState(false);
    const [apiData, setApiData] = useState(null);

    useEffect(() => {
        fetchForecast();
    }, [timeHorizon, growthRate]);

    const fetchForecast = async () => {
        setLoading(true);
        try {
            // Use existing /api/forecasting/forecast endpoint
            const response = await fetch(`${API_BASE}/api/forecasting/forecast/1/1?days=${timeHorizon}&growth_rate=${growthRate / 100}`, {
                method: 'GET'
            });
            const data = await response.json();
            setApiData(data);
        } catch (error) {
            console.warn("Backend unavailable, using mock data", error);
            // Mock Fallback Data
            const today = new Date();
            const mockForecast = Array.from({ length: timeHorizon }, (_, i) => {
                const date = new Date(today);
                date.setDate(date.getDate() + i);
                const baseValue = 5000 + (i * 100) + (growthRate * 50);
                const noise = Math.random() * 500;
                return {
                    date: date.toISOString().split('T')[0],
                    value: baseValue + noise,
                    lower_bound: baseValue - 200,
                    upper_bound: baseValue + 700 + noise
                };
            });

            setApiData({
                forecast: mockForecast,
                impact: {
                    projected_margin: 154000 * (1 + growthRate / 100),
                    warehouse_utilization: 4500,
                    shipping_risk: "Low"
                }
            });
        } finally {
            setLoading(false);
        }
    };

    // Model metrics
    const modelMetrics = {
        accuracy: 94.0,
        rmse: 1.9,
        mae: 1.4,
        mape: 3.2,
        lastUpdated: '2 hours ago',
        trainingData: '12 months'
    };

    const getChartData = () => {
        if (!apiData || !apiData.forecast || !Array.isArray(apiData.forecast)) {
            console.log('Chart data not ready:', { apiData, hasForecast: apiData?.forecast, isArray: Array.isArray(apiData?.forecast) });
            return { labels: [], datasets: [] };
        }

        const labels = apiData.forecast.map(f => f.date);
        const values = apiData.forecast.map(f => f.value);
        const lower = apiData.forecast.map(f => f.lower_bound);
        const upper = apiData.forecast.map(f => f.upper_bound);

        const chartData = {
            labels,
            datasets: [
                {
                    label: 'Forecast',
                    data: values,
                    borderColor: 'rgb(244, 114, 182)', // Pink color to match legend
                    backgroundColor: 'rgba(244, 114, 182, 0.1)',
                    borderDash: [5, 5], // Dashed line to match legend
                    fill: false,
                    tension: 0.4,
                    borderWidth: 2,
                },
                {
                    label: 'Lower Confidence (95%)',
                    data: lower,
                    borderColor: 'rgba(244, 114, 182, 0.3)',
                    backgroundColor: 'rgba(244, 114, 182, 0.1)',
                    pointRadius: 0,
                    fill: '+1', // Fill to next dataset
                    borderWidth: 1,
                },
                {
                    label: 'Upper Confidence (95%)',
                    data: upper,
                    borderColor: 'rgba(244, 114, 182, 0.3)',
                    backgroundColor: isDark ? 'rgba(244, 114, 182, 0.15)' : 'rgba(244, 114, 182, 0.1)',
                    pointRadius: 0,
                    fill: false,
                    borderWidth: 1,
                }
            ]
        };

        console.log('Chart data prepared:', { labels: labels.length, values: values.length, chartData });
        return chartData;
    };

    const forecastData = getChartData();

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        },
        plugins: {
            legend: {
                labels: {
                    color: isDark ? '#f1f5f9' : '#1e293b',
                    font: { size: 12 },
                    filter: (item) => item.text !== 'Upper Confidence (95%)' && item.text !== 'Lower Confidence (95%)'
                }
            },
            tooltip: {
                backgroundColor: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
                titleColor: isDark ? '#f1f5f9' : '#1e293b',
                bodyColor: isDark ? '#cbd5e1' : '#475569',
            }
        },
        scales: {
            x: {
                grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
                ticks: {
                    color: isDark ? '#94a3b8' : '#64748b',
                    maxTicksLimit: 8,
                    callback: function (val) {
                        // Format date to "MMM D" e.g. "May 8"
                        const date = new Date(this.getLabelForValue(val));
                        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    }
            },
            y: {
                grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
                ticks: {
                    color: isDark ? '#94a3b8' : '#64748b',
                    callback: (value) => {
                        if (value >= 1000) {
                            return '₹' + (value / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
                        }
                        return '₹' + value;
                    }
            }
                }
            }
    }};

    // Key insights
    const insights = [
        {
            icon: <TrendingUp className="text-blue-400" size={24} />,
            title: 'Upward Trend Detected',
            description: 'Sales projected to increase by 12.4% over next 30 days',
            keyDrivers: ['Feb Promotion Period (+8%)', 'Pre-Holiday Inventory Rush', 'Competitor Stock-out'],
            type: 'positive'
        },
        {
            icon: <AlertCircle className="text-yellow-400" size={24} />,
            title: 'Seasonal Pattern',
            description: 'Peak expected on Day 15 - prepare 15% extra stock',
            keyDrivers: ['Valentine\'s Day (Feb 14)', 'Historical Purchase Cycle', 'Regional Event Traffic'],
            type: 'warning'
        },
        {
            icon: <Zap className="text-purple-400" size={24} />,
            title: 'High Demand Products',
            description: 'Fresh Paneer: +25% demand, Coca Cola 300ml: +18%',
            keyDrivers: ['Price Reduction (-8%)', 'High Inventory Levels (+40%)', 'Promotional Cross-sells'],
            type: 'info'
        }
    ];

    // Recommendations
    const recommendations = [
        {
            category: 'Stock Planning',
            action: 'Increase inventory by 18% for top 5 products',
            impact: 'High',
            priority: 'Urgent',
            savings: '₹45,000'
        },
        {
            category: 'Pricing',
            action: 'Adjust pricing strategy for seasonal items',
            impact: 'Medium',
            priority: 'Medium',
            savings: '₹22,000'
        },
        {
            category: 'Promotion',
            action: 'Launch promotion on Day 12-14 to capitalize on peak',
            impact: 'High',
            priority: 'High',
            savings: '₹38,000'
        },
        {
            category: 'Supplier Alert',
            action: 'Contact suppliers for Basmati Rice restock',
            impact: 'Critical',
            priority: 'Urgent',
            savings: '₹67,000'
        }
    ];

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'Urgent': return 'bg-red-500/20 border-red-500/30 text-red-400';
            case 'High': return 'bg-orange-500/20 border-orange-500/30 text-orange-400';
            case 'Medium': return 'bg-yellow-500/20 border-yellow-500/30 text-yellow-400';
            default: return 'bg-blue-500/20 border-blue-500/30 text-blue-400';
        }
    };

    return (
        <div className="min-h-screen space-y-8 p-6 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                    AI-Powered Forecasts
                </h1>
                <p className="text-muted-foreground">Machine learning demand predictions with confidence intervals</p>
            </div>

            {/* Model Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-1">
                    <div className="text-center">
                        <Brain className="mx-auto mb-3 text-purple-400" size={32} />
                        <p className="text-muted-foreground text-sm mb-2">Model Accuracy</p>
                        <div className="relative w-24 h-24 mx-auto">
                            <svg className="transform -rotate-90 w-24 h-24">
                                <circle cx="48" cy="48" r="40" stroke="rgba(255,255,255,0.1)" strokeWidth="8" fill="none" />
                                <circle
                                    cx="48" cy="48" r="40"
                                    stroke="url(#gradient)"
                                    strokeWidth="8"
                                    fill="none"
                                    strokeDasharray={`${2 * Math.PI * 40}`}
                                    strokeDashoffset={`${2 * Math.PI * 40 * (1 - modelMetrics.accuracy / 100)}`}
                                    strokeLinecap="round"
                                />
                                <defs>
                                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stopColor="#667eea" />
                                        <stop offset="100%" stopColor="#764ba2" />
                                    </linearGradient>
                                </defs>
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center z-10">
                                <span className="text-2xl font-bold text-foreground">{modelMetrics.accuracy}%</span>
                            </div>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 relative group overflow-visible animate-slide-up stagger-2">
                    <div className="absolute top-4 right-4 group/info z-10">
                        <div className="text-gray-400 opacity-50 hover:opacity-100 cursor-help">
                            <Info size={16} />
                        </div>
                        <div className="invisible group-hover/info:visible absolute right-0 top-6 w-48 p-2 bg-gray-900 border border-gray-700 text-white text-xs rounded shadow-lg z-50">
                            <strong>RMSE (Root Mean Square Error)</strong>: Lower is better. Measures the average magnitude of the error.
                        </div>
                    </div>
                    <Target className="mb-3 text-blue-400" size={28} />
                    <p className="text-gray-400 text-sm mb-2">RMSE</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{modelMetrics.rmse}K</p>
                    <p className="text-xs text-gray-500">Root Mean Square Error</p>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 relative group overflow-visible animate-slide-up stagger-3">
                    <div className="absolute top-4 right-4 group/info z-10">
                        <div className="text-gray-400 opacity-50 hover:opacity-100 cursor-help">
                            <Info size={16} />
                        </div>
                        <div className="invisible group-hover/info:visible absolute right-0 top-6 w-48 p-2 bg-gray-900 border border-gray-700 text-white text-xs rounded shadow-lg z-50">
                            <strong>MAE (Mean Absolute Error)</strong>: Average absolute difference between predicted and actual values.
                        </div>
                    </div>
                    <CheckCircle className="mb-3 text-green-400" size={28} />
                    <p className="text-gray-400 text-sm mb-2">MAE</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{modelMetrics.mae}K</p>
                    <p className="text-xs text-gray-500">Mean Absolute Error</p>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 relative group overflow-visible animate-slide-up stagger-4">
                    <div className="absolute top-4 right-4 group/info z-10">
                        <div className="text-gray-400 opacity-50 hover:opacity-100 cursor-help">
                            <Info size={16} />
                        </div>
                        <div className="invisible group-hover/info:visible absolute right-0 top-6 w-48 p-2 bg-gray-900 border border-gray-700 text-white text-xs rounded shadow-lg z-50">
                            <strong>MAPE</strong>: Mean Absolute Percentage Error. Accuracy as a percentage. Lower is better.
                        </div>
                    </div>
                    <Zap className="mb-3 text-yellow-400" size={28} />
                    <p className="text-gray-400 text-sm mb-2">MAPE</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{modelMetrics.mape}%</p>
                    <p className="text-xs text-gray-500">Mean Abs Percentage Error</p>
                </GlassCard>
            </div>

            {/* Forecast Chart */}
            <GlassCard variant="gradient" className="animate-slide-up stagger-5">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-1">
                                Demand Forecast with Confidence Intervals
                            </h2>
                            <p className="text-muted-foreground text-sm">Updated {modelMetrics.lastUpdated} • Trained on {modelMetrics.trainingData} of data</p>
                        </div>
                        <div className="flex gap-2">
                            {[7, 14, 30, 90].map((days) => (
                                <button
                                    key={days}
                                    onClick={() => setTimeHorizon(days)}
                                    className={`px-4 py-2 rounded-lg transition font-medium ${timeHorizon === days
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/20'
                                        }`}
                                >
                                    {days}D
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* What-If Analysis Control */}
                    <div className="mb-6 p-4 bg-white/5 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <Zap className="text-yellow-400" size={20} />
                                <span className="font-bold text-gray-900 dark:text-white">"What-If" Analysis Engine</span>
                            </div>
                            <span className="text-sm text-gray-500">Simulate market changes</span>
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[100px]">Growth Impact:</span>
                            <input
                                type="range"
                                min="-50"
                                max="50"
                                value={growthRate}
                                onChange={(e) => setGrowthRate(parseInt(e.target.value))}
                                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                            />
                            <span className={`text-sm font-bold w-16 text-right ${growthRate > 0 ? 'text-green-500' : growthRate < 0 ? 'text-red-500' : 'text-gray-500'}`}>
                                {growthRate > 0 ? '+' : ''}{growthRate}%
                            </span>
                        </div>
                        <p className="text-xs text-gray-400 mt-2 text-center">
                            Adjusting this simulates price changes, marketing campaigns, or competitor actions.
                        </p>
                    </div>

                    <div style={{ height: '400px' }} className="relative">
                        {loading && (
                            <div className="absolute inset-0 flex items-center justify-center bg-gray-900/50 backdrop-blur-sm z-10 rounded-lg">
                                <div className="text-white font-bold animate-pulse">Running Prophet Model...</div>
                            </div>
                        )}
                        <Line data={forecastData} options={chartOptions} />
                    </div>

                    <div className="mt-4 flex items-center justify-center gap-6 text-sm">
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-0.5 bg-blue-400"></div>
                            <span className="text-gray-400">Historical</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-0.5 border-t-2 border-dashed border-pink-400"></div>
                            <span className="text-gray-400">Forecast</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 bg-pink-400/20 border border-pink-400/30"></div>
                            <span className="text-gray-400">95% Confidence</span>
                        </div>
                    </div>
                </div>
            </GlassCard>

            {/* Strategic Impact Analysis (Prescriptive Analytics) */}
            {apiData && apiData.impact && (
                <GlassCard className="mt-8 border-t-4 border-t-purple-500">
                    <div className="p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-3 bg-purple-500/10 rounded-lg">
                                <Brain className="text-purple-500 w-6 h-6" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Strategic Impact Analysis</h2>
                                <p className="text-sm text-gray-500">AI-projected business implications based on current simulation</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* Margin Impact */}
                            <div className="bg-gray-50 dark:bg-white/5 rounded-xl p-5 border border-gray-100 dark:border-white/10">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-gray-500 text-sm font-medium">Projected Margin</span>
                                    {growthRate >= 0 ?
                                        <TrendingUp className="text-green-500 w-5 h-5" /> :
                                        <TrendingDown className="text-red-500 w-5 h-5" />
                                    }
                                </div>
                                <div className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                                    ₹{(apiData.impact.projected_margin / 100000).toFixed(2)} Lakhs
                                </div>
                                <div className="text-xs text-green-600 dark:text-green-400 font-medium">
                                    {growthRate > 0 ? `+${growthRate}% vs Baseline` : 'Baseline Scenario'}
                                </div>
                            </div>

                            {/* Warehousing */}
                            <div className="bg-gray-50 dark:bg-white/5 rounded-xl p-5 border border-gray-100 dark:border-white/10">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-gray-500 text-sm font-medium">Warehouse Space</span>
                                    <Package className="text-blue-500 w-5 h-5" />
                                </div>
                                <div className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                                    {apiData.impact.warehouse_utilization.toLocaleString()} sq.ft
                                </div>
                                <div className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                                    Utilization Forecast
                                </div>
                            </div>

                            {/* Shipping Risk */}
                            <div className={`rounded-xl p-5 border ${apiData.impact.shipping_risk.includes("High") ? 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900/30' :
                                apiData.impact.shipping_risk.includes("Medium") ? 'bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-900/30' :
                                    'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900/30'
                                }`}>
                                <div className="flex justify-between items-start mb-2">
                                    <span className={`text-sm font-medium ${apiData.impact.shipping_risk.includes("High") ? 'text-red-700 dark:text-red-400' :
                                        apiData.impact.shipping_risk.includes("Medium") ? 'text-yellow-700 dark:text-yellow-400' :
                                            'text-green-700 dark:text-green-400'
                                        }`}>Logistics Risk</span>
                                    <Truck className={`w-5 h-5 ${apiData.impact.shipping_risk.includes("High") ? 'text-red-600 dark:text-red-500' :
                                        apiData.impact.shipping_risk.includes("Medium") ? 'text-yellow-600 dark:text-yellow-500' :
                                            'text-green-600 dark:text-green-500'
                                        }`} />
                                </div>
                                <div className={`text-xl font-bold mb-1 ${apiData.impact.shipping_risk.includes("High") ? 'text-red-800 dark:text-red-300' :
                                    apiData.impact.shipping_risk.includes("Medium") ? 'text-yellow-800 dark:text-yellow-300' :
                                        'text-green-800 dark:text-green-300'
                                    }`}>
                                    {apiData.impact.shipping_risk}
                                </div>
                                <div className={`text-xs font-medium ${apiData.impact.shipping_risk.includes("High") ? 'text-red-700 dark:text-red-400' :
                                    apiData.impact.shipping_risk.includes("Medium") ? 'text-yellow-700 dark:text-yellow-400' :
                                        'text-green-700 dark:text-green-400'
                                    }`}>
                                    Based on daily volume spikes
                                </div>
                            </div>
                        </div>
                    </div>
                </GlassCard>
            )}

            {/* Key Insights */}
            <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                    Key Insights
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {insights.map((insight, idx) => (
                        <div key={idx}>
                            <GlassCard variant="gradient" className="p-6 h-full hover:shadow-glow-primary transition-all">
                                <div className="flex items-start gap-4 h-full">
                                    <div className="p-3 rounded-lg bg-gray-100 dark:bg-white/5 dark:bg-black/20 flex-shrink-0">
                                        {insight.icon}
                                    </div>
                                    <div className="flex-1 flex flex-col h-full">
                                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{insight.title}</h3>
                                        <p className="text-gray-400 text-sm mb-3 flex-1">{insight.description}</p>
                                        <div className="mt-auto pt-3 border-t border-gray-200 dark:border-gray-700">
                                            <p className="text-xs font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-2">Key Drivers (Why?)</p>
                                            <div className="flex flex-wrap gap-2">
                                                {insight.keyDrivers.map((driver) => (
                                                    <span key={driver} className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800/50 text-slate-800 dark:text-slate-200 text-xs rounded-md border border-slate-300 dark:border-slate-700 font-semibold">
                                                        {driver}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </GlassCard>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recommendations */}
            <GlassCard variant="gradient" className="animate-slide-up">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                            AI-Powered Recommendations
                        </h2>
                        <button className="btn-enterprise btn-enterprise-destructive text-sm">
                            Retrain Model
                        </button>
                    </div>

                    <div className="space-y-4">
                        {recommendations.map((rec, idx) => (
                            <div
                                key={idx}
                                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-white/5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 transition"
                            >
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="text-xs font-semibold text-gray-500 uppercase">{rec.category}</span>
                                        <span className={`px-2 py-1 rounded text-xs font-semibold border ${getPriorityColor(rec.priority)}`}>
                                            {rec.priority}
                                        </span>
                                    </div>
                                    <p className="text-gray-900 dark:text-white font-medium mb-1">{rec.action}</p>
                                    <p className="text-sm text-gray-400">Potential savings: {rec.savings}</p>
                                </div>
                                <div className="flex gap-3">
                                    <button
                                        onClick={() => { }}
                                        className="btn-enterprise btn-enterprise-success text-sm"
                                    >
                                        Accept
                                    </button>
                                    <button
                                        onClick={() => { }}
                                        className="btn-enterprise btn-enterprise-destructive text-sm"
                                    >
                                        Dismiss
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </GlassCard >
        </div >
    );
};

export default Forecasts;
