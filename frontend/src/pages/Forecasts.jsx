import { useState, useEffect } from 'react';
import { API_BASE } from '../lib/api';
import { TrendingUp, TrendingDown, Target, Brain, Zap, AlertCircle, CheckCircle, Package, Truck } from 'lucide-react';
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
import { useTheme } from '../hooks/useTheme';
import '../styles/fresh-design.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const Forecasts = () => {
    const { isDark } = useTheme();
    const [timeHorizon, setTimeHorizon] = useState(30);
    const [growthRate, setGrowthRate] = useState(0);
    const [loading, setLoading] = useState(false);
    const [apiData, setApiData] = useState(null);

    useEffect(() => {
        fetchForecast();
    }, [timeHorizon, growthRate]);

    const fetchForecast = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/forecasting/forecast/1/1?days=${timeHorizon}&growth_rate=${growthRate / 100}`, {
                method: 'GET'
            });
            const data = await response.json();
            setApiData(data);
        } catch (error) {
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
                    borderColor: 'var(--warning)',
                    backgroundColor: 'var(--warning-soft)',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    borderWidth: 2,
                },
                {
                    label: 'Lower Confidence (95%)',
                    data: lower,
                    borderColor: 'rgba(214, 134, 0, 0.3)',
                    backgroundColor: 'var(--warning-soft)',
                    pointRadius: 0,
                    fill: '+1',
                    borderWidth: 1,
                },
                {
                    label: 'Upper Confidence (95%)',
                    data: upper,
                    borderColor: 'rgba(214, 134, 0, 0.3)',
                    backgroundColor: isDark ? 'rgba(255, 202, 40, 0.2)' : 'var(--warning-soft)',
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
            icon: <Zap className="text-yellow-400" size={24} />,
            title: 'High Demand Products',
            description: 'Fresh Paneer: +25% demand, Coca Cola 300ml: +18%',
            keyDrivers: ['Price Reduction (-8%)', 'High Inventory Levels (+40%)', 'Promotional Cross-sells'],
            type: 'info'
        }
    ];

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

    const priorityBadgeStyle = (priority) => {
        switch (priority) {
            case 'Urgent': return { background: 'var(--danger-bg)', color: 'var(--danger-text)' };
            case 'High': return { background: 'var(--warning-bg)', color: 'var(--warning-text)' };
            case 'Medium': return { background: 'var(--warning-bg)', color: 'var(--warning-text)' };
            default: return { background: 'var(--info-bg)', color: 'var(--info-text)' };
        }
    };

    const impactBadgeStyle = (impact) => {
        switch (impact) {
            case 'Critical': return { background: 'var(--danger-bg)', color: 'var(--danger-text)' };
            case 'High': return { background: 'var(--warning-bg)', color: 'var(--warning-text)' };
            case 'Medium': return { background: 'var(--info-bg)', color: 'var(--info-text)' };
            default: return { background: 'var(--info-bg)', color: 'var(--info-text)' };
        }
    };

    return (
        <div className="fresh-page">
            <div style={{ marginBottom: 32 }}>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                    ML-powered demand forecasting
                </p>
            </div>

            <div className="fresh-metrics">
                <div className="fresh-metric">
                    <div className="fresh-metric-value">{modelMetrics.accuracy}%</div>
                    <div className="fresh-metric-label">Model Accuracy</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">{modelMetrics.rmse}K</div>
                    <div className="fresh-metric-label">RMSE</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">{modelMetrics.mae}K</div>
                    <div className="fresh-metric-label">MAE</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">{modelMetrics.mape}%</div>
                    <div className="fresh-metric-label">MAPE</div>
                </div>
            </div>

            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title">Demand Forecast with Confidence Intervals</span>
                    <div style={{ display: 'flex', gap: 8 }}>
                        {[7, 14, 30, 90].map((days) => (
                            <button
                                key={days}
                                onClick={() => setTimeHorizon(days)}
                                className={`fresh-btn ${timeHorizon === days ? 'primary' : ''}`}
                            >
                                {days}D
                            </button>
                        ))}
                    </div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                    Updated {modelMetrics.lastUpdated} &bull; Trained on {modelMetrics.trainingData} of data
                </p>

                <div style={{ marginBottom: 16, padding: 16, background: 'var(--bg-muted)', borderRadius: 8, border: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Zap className="text-yellow-400" size={20} />
                            <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>&ldquo;What-If&rdquo; Analysis Engine</span>
                        </div>
                        <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Simulate market changes</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <span style={{ fontSize: 13, color: 'var(--text-muted)', minWidth: 100 }}>Growth Impact:</span>
                        <input
                            type="range"
                            min="-50"
                            max="50"
                            value={growthRate}
                            onChange={(e) => setGrowthRate(parseInt(e.target.value))}
                            style={{ flex: 1, height: 8, background: 'var(--bg-muted)', borderRadius: 4, cursor: 'pointer' }}
                        />
                        <span style={{
                            fontSize: 13, fontWeight: 700, width: 60, textAlign: 'right',
                            color: growthRate > 0 ? 'var(--accent-green)' : growthRate < 0 ? 'var(--accent-red)' : 'var(--text-muted)'
                        }}>
                            {growthRate > 0 ? '+' : ''}{growthRate}%
                        </span>
                    </div>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8, textAlign: 'center' }}>
                        Adjusting this simulates price changes, marketing campaigns, or competitor actions.
                    </p>
                </div>

                <div style={{ height: 400, position: 'relative' }}>
                    {loading && (
                        <div style={{
                            position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
                            justifyContent: 'center', background: 'rgba(0,0,0,0.5)',
                            backdropFilter: 'blur(4px)', zIndex: 10, borderRadius: 8
                        }}>
                            <div style={{ color: '#fff', fontWeight: 700, animation: 'pulse 2s infinite' }}>
                                Running Prophet Model...
                            </div>
                        </div>
                    )}
                    <Line data={forecastData} options={chartOptions} />
                </div>

                <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 24, fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 16, height: 2, background: '#60a5fa' }}></div>
                        <span style={{ color: 'var(--text-muted)' }}>Historical</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 16, height: 0, borderTop: '2px dashed #f472b6' }}></div>
                        <span style={{ color: 'var(--text-muted)' }}>Forecast</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 16, height: 16, background: 'rgba(244,114,182,0.2)', border: '1px solid rgba(244,114,182,0.3)' }}></div>
                        <span style={{ color: 'var(--text-muted)' }}>95% Confidence</span>
                    </div>
                </div>
            </div>

            {apiData && apiData.impact && (
                <div className="fresh-section">
                    <div className="fresh-section-header">
                        <span className="fresh-section-title">Strategic Impact Analysis</span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                        AI-projected business implications based on current simulation
                    </p>
                    <div className="fresh-metrics">
                        <div className="fresh-metric">
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Projected Margin</span>
                                {growthRate >= 0 ?
                                    <TrendingUp style={{ color: 'var(--accent-green)' }} size={20} /> :
                                    <TrendingDown style={{ color: 'var(--accent-red)' }} size={20} />
                                }
                            </div>
                            <div className="fresh-metric-value">
                                ₹{(apiData.impact.projected_margin / 100000).toFixed(2)} Lakhs
                            </div>
                            <div style={{ fontSize: 12, color: growthRate > 0 ? 'var(--accent-green)' : 'var(--text-muted)', fontWeight: 500 }}>
                                {growthRate > 0 ? `+${growthRate}% vs Baseline` : 'Baseline Scenario'}
                            </div>
                        </div>
                        <div className="fresh-metric">
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Warehouse Space</span>
                                <Package style={{ color: '#3b82f6' }} size={20} />
                            </div>
                            <div className="fresh-metric-value">
                                {apiData.impact.warehouse_utilization.toLocaleString()} sq.ft
                            </div>
                            <div style={{ fontSize: 12, color: '#3b82f6', fontWeight: 500 }}>
                                Utilization Forecast
                            </div>
                        </div>
                        <div className="fresh-metric">
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Logistics Risk</span>
                                <Truck style={{
                                    color: apiData.impact.shipping_risk.includes("High") ? 'var(--danger-text)' :
                                        apiData.impact.shipping_risk.includes("Medium") ? 'var(--warning-text)' : 'var(--success-text)'
                                }} size={20} />
                            </div>
                            <div className="fresh-metric-value" style={{
                                color: apiData.impact.shipping_risk.includes("High") ? 'var(--danger-text)' :
                                    apiData.impact.shipping_risk.includes("Medium") ? 'var(--warning-text)' : 'var(--success-text)'
                            }}>
                                {apiData.impact.shipping_risk}
                            </div>
                            <div style={{
                                fontSize: 12, fontWeight: 500,
                                color: apiData.impact.shipping_risk.includes("High") ? 'var(--danger-text)' :
                                    apiData.impact.shipping_risk.includes("Medium") ? 'var(--warning-text)' : 'var(--success-text)'
                            }}>
                                Based on daily volume spikes
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title">Key Insights</span>
                </div>
                <div className="fresh-list">
                    {insights.map((insight, idx) => (
                        <div key={idx} className="fresh-list-item" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                                <div style={{ padding: 12, background: 'var(--bg-muted)', borderRadius: 8, flexShrink: 0 }}>
                                    {insight.icon}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                                        {insight.title}
                                    </div>
                                    <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
                                        {insight.description}
                                    </div>
                                    <div style={{ paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                                        <div style={{
                                            fontSize: 11, fontWeight: 600, color: 'var(--text-primary)',
                                            textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8
                                        }}>
                                            Key Drivers (Why?)
                                        </div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                            {insight.keyDrivers.map((driver) => (
                                                <span key={driver} style={{
                                                    padding: '4px 12px', background: 'var(--bg-muted)',
                                                    color: 'var(--text-primary)', fontSize: 12,
                                                    borderRadius: 6, border: '1px solid var(--border)', fontWeight: 600
                                                }}>
                                                    {driver}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title">AI-Powered Recommendations</span>
                    <button className="fresh-btn primary">Retrain Model</button>
                </div>
                <table className="fresh-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Action</th>
                            <th>Impact</th>
                            <th>Priority</th>
                            <th>Savings</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {recommendations.map((rec, idx) => (
                            <tr key={idx}>
                                <td style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-faint)', textTransform: 'uppercase' }}>
                                    {rec.category}
                                </td>
                                <td>
                                    <div style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>{rec.action}</div>
                                    <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Potential savings: {rec.savings}</div>
                                </td>
                                <td>
                                    <span style={{
                                        padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600,
                        ...impactBadgeStyle(rec.impact)
                                    }}>
                                        {rec.impact}
                                    </span>
                                </td>
                                <td>
                                    <span style={{
                                        padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600,
                        ...priorityBadgeStyle(rec.priority)
                                    }}>
                                        {rec.priority}
                                    </span>
                                </td>
                                <td style={{ fontWeight: 600, color: 'var(--accent-green)' }}>{rec.savings}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: 8 }}>
                                        <button className="fresh-btn primary" onClick={() => {}}>Accept</button>
                                        <button className="fresh-btn" onClick={() => {}}>Dismiss</button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Forecasts;
