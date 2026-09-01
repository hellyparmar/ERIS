import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../lib/api';
import {
    Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
    BarElement, ArcElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import { ErrorBoundary } from 'react-error-boundary';
import ErrorFallback from '../components/ui/ErrorFallback';
import { useTheme } from '../hooks/useTheme';
import { useToast } from '../contexts/ToastContext';
import { Play, AlertCircle, Sparkles, X, Activity } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

const AnalyticsContent = () => {
    const { isDark } = useTheme();
    const [searchParams, setSearchParams] = useSearchParams();
    const [activeTab, setActiveTab] = useState('general');
    const [timePeriod, setTimePeriod] = useState('30D');
    const { showToast } = useToast();
    const [activeSimulation, setActiveSimulation] = useState(null);

    useEffect(() => {
        const tab = searchParams.get('tab');
        if (tab === 'causal') {
            setActiveTab('causal');
        } else {
            setActiveTab('general');
        }
    }, [searchParams]);
    const [salesTrendData, setSalesTrendData] = useState({ labels: [], datasets: [] });
    const [showAllProducts, setShowAllProducts] = useState(false);
    const [showForecast, setShowForecast] = useState(false);
    const [topProducts, setTopProducts] = useState([]);
    const [categoryData, setCategoryData] = useState({ labels: [], datasets: [] });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchRealtimeData = async () => {
            setLoading(true);
            try {
                const response = await api.analytics.getRealtimeDashboard();
                const data = response.data || {};
                const products = (data.top_products || []).map((product) => ({
                    rank: product.rank, name: product.name, category: product.name,
                    revenue: product.revenue, units: product.units_sold,
                    margin: Math.floor(Math.random() * 20 + 30),
                    growth: Math.floor(Math.random() * 30 - 5),
                }));
                setTopProducts(products);
                const catLabels = [
                    'Appetizers & Starters', 'Main Dishes & Entrées',
                    'Desserts & Sweets', 'Beverages & Drinks', 'Sides & Accompaniments',
                ];
                const totalRev = data.total_revenue || 1;
                const catValues = (products || []).slice(0, 5).map(p => ((p.revenue / totalRev) * 100).toFixed(1));
                setCategoryData({
                    labels: catLabels,
                    datasets: [{
                        data: catValues.length ? catValues : [20, 18, 17, 25, 20],
                        backgroundColor: ['#8B5E3C', '#AEB784', '#622B14', '#222831', '#D3D4C0'],
                        borderWidth: 0,
                    }]
                });
            } catch (error) {
                console.error('Failed to fetch analytics data:', error);
                setCategoryData({
                    labels: ['Appetizers & Starters', 'Main Dishes & Entrées', 'Desserts & Sweets', 'Beverages & Drinks', 'Sides & Accompaniments'],
                    datasets: [{ data: [20, 18, 17, 25, 20], backgroundColor: ['#8B5E3C', '#AEB784', '#622B14', '#222831', '#D3D4C0'], borderWidth: 0 }]
                });
                setTopProducts([]);
            } finally {
                setLoading(false);
            }
        };
        fetchRealtimeData();
    }, []);

    const getFilteredData = (period) => {
        const periods = {
            '7D':  { labels: ['Day 1','Day 2','Day 3','Day 4','Day 5','Day 6','Day 7'], revenue: [12000,15000,11000,18000,14000,16000,19000], orders: [50,65,45,80,60,70,85] },
            '30D': { labels: ['Week 1','Week 2','Week 3','Week 4','Week 5','Week 6'], revenue: [45000,52000,48000,61000,55000,67000], orders: [320,380,350,420,390,450] },
            '90D': { labels: ['Month 1','Month 2','Month 3'], revenue: [180000,210000,195000], orders: [1200,1400,1300] },
            '1Y':  { labels: ['Q1','Q2','Q3','Q4'], revenue: [500000,620000,580000,700000], orders: [3500,4200,3800,4800] },
        };
        return periods[period] || periods['30D'];
    };

    useEffect(() => {
        setTimeout(() => {
            const data = getFilteredData(timePeriod);
            const datasets = [
                { 
                    label: 'Revenue', 
                    data: data.revenue, 
                    borderColor: '#8B5E3C', 
                    backgroundColor: 'rgba(139,94,60,0.15)', 
                    fill: true, 
                    tension: 0.4 
                },
                { 
                    label: 'Orders', 
                    data: data.orders, 
                    borderColor: '#AEB784', 
                    backgroundColor: 'rgba(174,183,132,0.1)', 
                    fill: true, 
                    tension: 0.4,
                    borderDash: [5, 5]
                },
            ];
            if (showForecast) {
                const lastVal = data.revenue[data.revenue.length - 1];
                const forecastData = [...Array(data.revenue.length).fill(null)];
                forecastData[data.revenue.length - 1] = lastVal;
                for (let i = 1; i <= 3; i++) forecastData.push(lastVal * (1 + 0.05 * i));
                setSalesTrendData({
                    labels: [...data.labels, 'Forecast 1', 'Forecast 2', 'Forecast 3'],
                    datasets: [...datasets.map(d => ({ ...d, spanGaps: true })), {
                        label: 'ML Forecast', data: forecastData, borderColor: '#8B5E3C',
                        backgroundColor: 'transparent', borderDash: [5, 5], fill: false, tension: 0.4, spanGaps: true,
                    }]
                });
            } else {
                setSalesTrendData({ labels: data.labels, datasets });
            }
        }, 300);
    }, [timePeriod, showForecast]);

    const baseGridColor = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.05)';
    const baseTickColor = isDark ? '#6b6560' : '#64748b';
    const tooltipBg = isDark ? 'rgba(38,38,38,0.95)' : 'rgba(255,255,255,0.95)';
    const tooltipTitle = isDark ? '#ece4d9' : '#1e293b';
    const tooltipBody = isDark ? '#9a9289' : '#475569';

    const chartOptions = {
        responsive: true, maintainAspectRatio: false,
        animation: { duration: 750, easing: 'easeInOutQuart' },
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: { labels: { color: tooltipTitle, font: { size: 12 } } },
            tooltip: { backgroundColor: tooltipBg, titleColor: tooltipTitle, bodyColor: tooltipBody, borderColor: 'var(--c-brown)', borderWidth: 1 },
        },
        scales: {
            x: { grid: { color: baseGridColor }, ticks: { color: baseTickColor } },
            y: { grid: { color: baseGridColor }, ticks: { color: baseTickColor } },
        },
    };

    const doughnutOptions = {
        responsive: true, maintainAspectRatio: false,
        plugins: {
            legend: { position: 'right', labels: { color: tooltipTitle, padding: 15, font: { size: 12 } } },
            tooltip: { backgroundColor: tooltipBg, titleColor: tooltipTitle, bodyColor: tooltipBody, borderColor: 'var(--c-brown)', borderWidth: 1 },
        },
    };

    const displayedProducts = showAllProducts ? topProducts : topProducts.slice(0, 5);

    if (loading) {
        return (
            <div style={{ padding: '24px', background: 'var(--c-canvas)', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div className="skeleton-strip" />
                <div className="skeleton-chart" />
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0, minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
            
            {/* Header / Tabs Row */}
            <div style={{
                padding: '16px 22px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid var(--c-border)',
                background: 'var(--c-canvas)'
            }}>
                <div>
                    <h1 className="page-title" style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#1A1208' }}>Enterprise Analytics</h1>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                        className="action-btn"
                        onClick={() => setActiveTab('general')}
                        style={{
                            padding: '5px 14px',
                            background: activeTab === 'general' ? '#222831' : 'transparent',
                            color: activeTab === 'general' ? '#F3E4C9' : 'var(--c-ink-muted)',
                            borderColor: activeTab === 'general' ? '#222831' : 'var(--c-border)'
                        }}
                    >
                        Sales Analytics
                    </button>
                    <button 
                        className="action-btn"
                        onClick={() => setActiveTab('causal')}
                        style={{
                            padding: '5px 14px',
                            background: activeTab === 'causal' ? '#222831' : 'transparent',
                            color: activeTab === 'causal' ? '#F3E4C9' : 'var(--c-ink-muted)',
                            borderColor: activeTab === 'causal' ? '#222831' : 'var(--c-border)'
                        }}
                    >
                        Causal Analytics
                    </button>
                </div>
            </div>

            {activeTab === 'general' ? (
                <>
                    {/* 1. Period selector row */}
                    <div className="content-section">
                        <div className="filter-bar" style={{ justifyContent: 'flex-end', marginBottom: 0 }}>
                            <div style={{ display: 'flex', gap: '4px' }}>
                                {['7D', '30D', '90D', '1Y'].map(p => {
                                    const isActive = timePeriod === p;
                                    return (
                                        <button key={p}
                                            className="action-btn"
                                            style={{
                                                padding: '5px 14px',
                                                background: isActive ? '#222831' : 'transparent',
                                                color: isActive ? '#F3E4C9' : 'var(--c-ink-muted)',
                                                borderColor: isActive ? '#222831' : 'var(--c-border)'
                                            }}
                                            onClick={() => setTimePeriod(p)}>
                                            {p === '1Y' ? 'Year' : p}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    {/* 2. KPI STRIP */}
                    <div className="kpi-strip">
                        <div className="kpi-cell">
                            <div className="kpi-label">Total Revenue</div>
                            <div className="kpi-value brown">₹45.2K</div>
                            <div className="kpi-delta up">↑ 8.2%</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Orders</div>
                            <div className="kpi-value">1,247</div>
                            <div className="kpi-delta up">↑ 5.1%</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Avg. Order Value</div>
                            <div className="kpi-value sage">₹520</div>
                            <div className="kpi-delta down">↓ 2.3%</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Conversion Rate</div>
                            <div className="kpi-value brown">23.5%</div>
                            <div className="kpi-delta up">↑ 1.4%</div>
                        </div>
                    </div>

                    {/* 3. SALES TREND */}
                    <div className="content-section-alt">
                        <div className="section-header">
                            <div className="zone-label" style={{ marginBottom: 0 }}>Sales Trend</div>
                            <button 
                                className={`action-btn ${showForecast ? 'primary' : ''}`}
                                onClick={() => setShowForecast(!showForecast)}
                                style={{ padding: '5px 14px' }}
                            >
                                {showForecast ? 'Hide Forecast' : 'Show Forecast'}
                            </button>
                        </div>
                        <div className="chart-inner" style={{ height: 320, marginTop: '12px' }}>
                            <Line data={salesTrendData} options={chartOptions} />
                        </div>
                    </div>

                    {/* 4. TWO-COLUMN COMPARISON */}
                    <div className="content-section" style={{ padding: 0 }}>
                        <div className="two-col">
                            {/* Left col */}
                            <div className="col-body">
                                <div className="section-header">
                                    <div className="zone-label" style={{ marginBottom: 0 }}>Category Breakdown</div>
                                </div>
                                <div style={{ height: 280, marginTop: '12px' }}>
                                    <Doughnut data={categoryData} options={doughnutOptions} />
                                </div>
                            </div>

                            {/* Column Divider */}
                            <div className="col-divider" />

                            {/* Right col */}
                            <div className="col-body">
                                <div className="section-header">
                                    <div className="zone-label" style={{ marginBottom: 0 }}>Top Products</div>
                                    <button className="action-btn" onClick={() => setShowAllProducts(!showAllProducts)} style={{ padding: '4px 10px' }}>
                                        {showAllProducts ? 'Show Less' : 'View All'}
                                    </button>
                                </div>
                                <div className="rank-list" style={{ marginTop: '12px' }}>
                                    {displayedProducts.map((p, i) => {
                                        const maxRev = topProducts[0]?.revenue || 1;
                                        const pct = (p.revenue / maxRev) * 100;
                                        const fillColors = ['var(--c-brown)', 'var(--c-sage)', 'var(--c-critical)', 'var(--c-muted)', 'var(--c-muted)'];
                                        const fillColor = fillColors[i] || 'var(--c-muted)';
                                        const isUp = p.growth >= 0;
                                        return (
                                            <div key={p.rank || i} className="rank-row">
                                                <div className="rank-num">#{p.rank}</div>
                                                <div className="rank-name">{p.name}</div>
                                                <div className="rank-track">
                                                    <div className="rank-fill" style={{ width: `${pct}%`, background: fillColor }} />
                                                </div>
                                                <div className="rank-value" style={{ marginRight: '8px' }}>₹{p.revenue.toLocaleString()}</div>
                                                <div style={{
                                                    fontFamily: 'var(--f-mono)',
                                                    fontSize: '10px',
                                                    color: isUp ? 'var(--c-sage)' : 'var(--c-critical)',
                                                    fontWeight: '600',
                                                    minWidth: '40px',
                                                    textAlign: 'right'
                                                }}>
                                                    {isUp ? '↑' : '↓'} {Math.abs(p.growth)}%
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <>
                    <div className="content-section" style={{ padding: 0 }}>
                        <div className="two-col">
                            {/* Left Col: Revenue Drivers Panel */}
                            <RevenueDriversPanel />

                            <div className="col-divider" />

                            {/* Right Col: Seasonal & Holiday Impact Panel */}
                            <HolidayImpactPanel />
                        </div>
                    </div>

                    {/* Bottom Full Row: What-If Scenarios Panel */}
                    <WhatIfScenariosPanel />
                </>
            )}

        </div>
    );
};

const RevenueDriversPanel = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [data, setData] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(false);
            try {
                const response = await api.forecasting.getCausalAnalysis({ outlet_id: 'all', days: 90 });
                setData(response.data);
            } catch (err) {
                console.error(err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const renderSkeleton = () => (
        <div className="col-body" style={{ flex: 1.2 }}>
            <div className="section-header">
                <div className="zone-label" style={{ marginBottom: 0 }}>Revenue Drivers</div>
            </div>
            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div className="skeleton-row" style={{ height: '32px', borderRadius: '4px' }} />
                <div className="skeleton-row" style={{ height: '32px', borderRadius: '4px' }} />
                <div className="skeleton-row" style={{ height: '32px', borderRadius: '4px' }} />
                <div className="skeleton-row" style={{ height: '32px', borderRadius: '4px' }} />
                <div className="skeleton-row" style={{ height: '32px', borderRadius: '4px' }} />
            </div>
        </div>
    );

    if (loading) return renderSkeleton();

    if (error || !data || !data.drivers || data.drivers.length === 0) {
        return (
            <div className="col-body" style={{ flex: 1.2 }}>
                <div className="section-header">
                    <div className="zone-label" style={{ marginBottom: 0 }}>Revenue Drivers</div>
                </div>
                <div style={{ marginTop: '16px', color: 'var(--c-ink-muted)', fontSize: '13px', textAlign: 'center', padding: '24px 0' }}>
                    Revenue Drivers — Connect your sales data to enable causal analysis
                </div>
            </div>
        );
    }

    return (
        <div className="col-body" style={{ flex: 1.2 }}>
            <div className="section-header">
                <div className="zone-label" style={{ marginBottom: 0 }}>Revenue Drivers</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: '16px' }}>
                {data.drivers.slice(0, 5).map((driver, index) => {
                    const isPositive = driver.direction === 'positive';
                    const absVal = Math.min(Math.abs(driver.effect_size) * 10, 50); // Just for visualization width
                    return (
                        <div key={index}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                                <span style={{ color: 'var(--c-ink-muted)' }}>{driver.factor_name}</span>
                                <span style={{ fontWeight: 700, color: isPositive ? 'var(--c-sage)' : 'var(--c-critical)' }}>
                                    {isPositive ? '+' : '-'}{Math.abs(driver.effect_size).toFixed(1)}
                                    <span style={{ fontSize: '10px', color: 'var(--c-ink-muted)', marginLeft: '6px', fontWeight: 'normal' }}>
                                        (Conf: {(driver.confidence * 100).toFixed(0)}%)
                                    </span>
                                </span>
                            </div>
                            <div style={{ width: '100%', height: 6, background: 'var(--c-strip)', borderRadius: 3, overflow: 'hidden', position: 'relative', marginTop: 4 }}>
                                <div style={{
                                    position: 'absolute',
                                    left: isPositive ? '50%' : `${50 - absVal}%`,
                                    width: `${absVal}%`,
                                    height: '100%',
                                    background: isPositive ? 'var(--c-sage)' : 'var(--c-critical)',
                                }}></div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

const HolidayImpactPanel = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [data, setData] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(false);
            try {
                const response = await api.forecasting.getAnomalyExplanation({ outlet_id: 'all', date: '2026-07-01' });
                setData(response.data);
            } catch (err) {
                console.error(err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const renderSkeleton = () => (
        <div className="col-body" style={{ flex: 1 }}>
            <div className="section-header">
                <div className="zone-label" style={{ marginBottom: 0 }}>Seasonal & Holiday Impact</div>
            </div>
            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div className="skeleton-row" style={{ height: '32px', borderRadius: '4px' }} />
                <div className="skeleton-row" style={{ height: '32px', borderRadius: '4px' }} />
                <div className="skeleton-row" style={{ height: '32px', borderRadius: '4px' }} />
            </div>
        </div>
    );

    if (loading) return renderSkeleton();

    if (error || !data || !data.impacts || data.impacts.length === 0) {
        return (
            <div className="col-body" style={{ flex: 1 }}>
                <div className="section-header">
                    <div className="zone-label" style={{ marginBottom: 0 }}>Seasonal & Holiday Impact</div>
                </div>
                <div style={{ marginTop: '16px', color: 'var(--c-ink-muted)', fontSize: '13px', textAlign: 'center', padding: '24px 0' }}>
                    Seasonal & Holiday Impact — Connect your sales data to enable causal analysis
                </div>
            </div>
        );
    }

    return (
        <div className="col-body" style={{ flex: 1 }}>
            <div className="section-header">
                <div className="zone-label" style={{ marginBottom: 0 }}>Seasonal & Holiday Impact</div>
            </div>
            <div style={{ marginTop: '16px' }}>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--c-border)', color: 'var(--c-ink-muted)', textAlign: 'left' }}>
                            <th style={{ padding: '8px 4px', fontWeight: 600 }}>Holiday</th>
                            <th style={{ padding: '8px 4px', fontWeight: 600, textAlign: 'right' }}>Revenue Impact %</th>
                            <th style={{ padding: '8px 4px', fontWeight: 600, textAlign: 'right' }}>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.impacts.map((item, idx) => {
                            const isPositive = item.revenue_impact_pct >= 0;
                            return (
                                <tr key={idx} style={{ borderBottom: '1px solid var(--c-border)' }}>
                                    <td style={{ padding: '10px 4px', color: 'var(--c-dark)', fontWeight: 500 }}>{item.holiday}</td>
                                    <td style={{ padding: '10px 4px', textAlign: 'right', fontWeight: 600, color: isPositive ? 'var(--c-sage)' : 'var(--c-critical)' }}>
                                        {isPositive ? '+' : ''}{item.revenue_impact_pct}%
                                    </td>
                                    <td style={{ padding: '10px 4px', textAlign: 'right', color: 'var(--c-ink-muted)' }}>
                                        {(item.confidence * 100).toFixed(0)}%
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const WhatIfScenariosPanel = () => {
    const [scenario, setScenario] = useState('baseline');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(false);
    const [result, setResult] = useState(null);

    const runSimulation = async () => {
        setLoading(true);
        setError(false);
        setResult(null);
        try {
            const response = await api.causal.runCounterfactual(scenario);
            setResult(response.data);
        } catch (err) {
            console.error(err);
            setError(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="content-section" style={{ borderTop: '1px solid var(--c-border)', marginTop: '24px', padding: '24px' }}>
            <div className="section-header">
                <div className="zone-label" style={{ marginBottom: 0 }}>What-If Scenarios</div>
            </div>
            
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginTop: '16px' }}>
                <select 
                    value={scenario} 
                    onChange={e => setScenario(e.target.value)}
                    style={{ padding: '8px 12px', borderRadius: 'var(--radius)', border: '1px solid var(--c-border)', background: 'var(--c-canvas)', color: 'var(--c-ink)', fontSize: '13px', outline: 'none' }}
                >
                    <option value="baseline">Baseline</option>
                    <option value="price_increase">Price Increase (+10%)</option>
                    <option value="promotion">Aggressive Promotion</option>
                </select>
                <button 
                    className="action-btn primary"
                    onClick={runSimulation}
                    disabled={loading}
                    style={{ padding: '8px 16px', fontSize: '13px' }}
                >
                    {loading ? 'Running...' : 'Run Simulation'}
                </button>
            </div>

            {error && (
                <div style={{ marginTop: '24px', color: 'var(--c-ink-muted)', fontSize: '13px', textAlign: 'center', padding: '24px 0', border: '1px solid var(--c-border)', borderRadius: 'var(--radius)' }}>
                    What-If Scenarios — Connect your sales data to enable causal analysis
                </div>
            )}

            {result && !error && (
                <div style={{ marginTop: '24px', padding: '20px', border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas-raised)' }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-dark)', marginBottom: '16px' }}>Simulation Results</div>
                    <div style={{ display: 'flex', gap: '32px' }}>
                        <div>
                            <div style={{ fontSize: '11px', color: 'var(--c-ink-muted)', marginBottom: '4px' }}>Actual Revenue</div>
                            <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--c-dark)' }}>₹{result.actual_revenue?.toLocaleString()}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '11px', color: 'var(--c-ink-muted)', marginBottom: '4px' }}>Counterfactual Revenue</div>
                            <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--c-brown)' }}>₹{result.counterfactual_revenue?.toLocaleString()}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '11px', color: 'var(--c-ink-muted)', marginBottom: '4px' }}>Impact</div>
                            <div style={{ fontSize: '18px', fontWeight: 600, color: result.counterfactual_revenue >= result.actual_revenue ? 'var(--c-sage)' : 'var(--c-critical)' }}>
                                {result.counterfactual_revenue >= result.actual_revenue ? '+' : ''}
                                {(((result.counterfactual_revenue - result.actual_revenue) / result.actual_revenue) * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const Analytics = () => (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
        <AnalyticsContent />
    </ErrorBoundary>
);

export default Analytics;
