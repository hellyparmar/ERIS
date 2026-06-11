import { useState, useMemo, useEffect } from 'react';
import {
    Store, MapPin, TrendingUp, TrendingDown, DollarSign, Target, AlertTriangle, Star,
    ChevronDown, ChevronUp, Search
} from 'lucide-react';
import LoadingNotice from '../components/ui/LoadingNotice';
import mockStores, { getTopPerformingStores, calculateRegionalPerformance } from '../data/storeData';
import {
    getNetworkMetrics,
    getStoresNeedingAttention
} from '../utils/storeAnalytics';
import { Line, Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import '../styles/fresh-design.css';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const SortIcon = ({ field, sortBy, sortOrder }) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
};

const MiniSparkline = ({ data, color, isPositive }) => {
    const width = 60;
    const height = 24;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const points = data.map((val, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((val - min) / range) * height;
        return `${x},${y}`;
    }).join(' ');

    return (
        <svg width={width} height={height} className="overflow-visible">
            <path
                d={`M ${points}`}
                fill="none"
                stroke={isPositive ? '#10b981' : '#ef4444'}
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <circle
                cx={width}
                cy={height - ((data[data.length - 1] - min) / range) * height}
                r="2"
                fill={isPositive ? '#10b981' : '#ef4444'}
            />
        </svg>
    );
};

const Metric = ({ value, label, icon: Icon }) => (
    <div className="fresh-metric">
        {Icon && <Icon size={20} className="fresh-metric-icon" />}
        <div className="fresh-metric-value">{value}</div>
        <div className="fresh-metric-label">{label}</div>
    </div>
);

const MultiStore = () => {
    const [isLoading, setIsLoading] = useState(true);
    const [stores] = useState(mockStores);
    const [selectedRegion, setSelectedRegion] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('revenue');
    const [sortOrder, setSortOrder] = useState('desc');

    const networkMetrics = useMemo(() => getNetworkMetrics(stores), [stores]);
    const regionalPerformance = useMemo(() => calculateRegionalPerformance(stores), [stores]);
    const topStores = useMemo(() => getTopPerformingStores(stores, 5), [stores]);
    const storesNeedingAttention = useMemo(() => getStoresNeedingAttention(stores), [stores]);

    useEffect(() => {
        const timer = setTimeout(() => setIsLoading(false), 2000);
        return () => clearTimeout(timer);
    }, []);

    const filteredStores = useMemo(() => {
        let filtered = stores;

        if (selectedRegion !== 'all') {
            filtered = filtered.filter(s => s.location.region === selectedRegion);
        }

        if (searchQuery) {
            filtered = filtered.filter(s =>
                s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                s.location.city.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        filtered = [...filtered].sort((a, b) => {
            let aVal, bVal;
            switch (sortBy) {
                case 'revenue':
                    aVal = a.performance.monthlyRevenue;
                    bVal = b.performance.monthlyRevenue;
                    break;
                case 'growth':
                    aVal = a.metrics.salesGrowth;
                    bVal = b.metrics.salesGrowth;
                    break;
                case 'satisfaction':
                    aVal = a.metrics.customerSatisfaction;
                    bVal = b.metrics.customerSatisfaction;
                    break;
                case 'name':
                    return sortOrder === 'asc'
                        ? a.name.localeCompare(b.name)
                        : b.name.localeCompare(a.name);
                default:
                    aVal = a.performance.monthlyRevenue;
                    bVal = b.performance.monthlyRevenue;
            }
            return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
        });

        return filtered;
    }, [stores, selectedRegion, searchQuery, sortBy, sortOrder]);

    const handleSort = (field) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(field);
            setSortOrder('desc');
        }
    };

    const formatCurrency = (value) => {
        if (value >= 10000000) return `\u20B9${(value / 10000000).toFixed(1)}Cr`;
        if (value >= 100000) return `\u20B9${(value / 100000).toFixed(1)}L`;
        return `\u20B9${(value / 1000).toFixed(0)}k`;
    };

    return (
        <div className="fresh-page">
            <div style={{ marginBottom: 32 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    <div className="fresh-pills">
                        <button
                            className={`fresh-pill ${selectedRegion === 'all' ? 'active' : ''}`}
                            onClick={() => setSelectedRegion('all')}
                        >
                            All
                        </button>
                        {regionalPerformance.map(r => (
                            <button
                                key={r.region}
                                className={`fresh-pill ${selectedRegion === r.region ? 'active' : ''}`}
                                onClick={() => setSelectedRegion(selectedRegion === r.region ? 'all' : r.region)}
                            >
                                {r.region}
                            </button>
                        ))}
                    </div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                    Network-wide performance and comparison
                </p>
            </div>

            {isLoading ? <LoadingNotice message="Loading store data..." /> : (
                <>
                    <div className="fresh-metrics">
                        <Metric value={String(networkMetrics.totalStores)} label="Total Stores" icon={Store} />
                        <Metric value={formatCurrency(networkMetrics.totalRevenue)} label="Network Revenue" icon={DollarSign} />
                        <Metric
                            value={`${networkMetrics.avgGrowth >= 0 ? '+' : ''}${networkMetrics.avgGrowth}%`}
                            label="Avg Growth"
                            icon={networkMetrics.avgGrowth >= 0 ? TrendingUp : TrendingDown}
                        />
                        <Metric value={String(networkMetrics.avgSatisfaction)} label="Satisfaction" icon={Target} />
                    </div>

                    <div className="fresh-section">
                        <div className="fresh-section-header">
                            <span className="fresh-section-title">Regional Performance</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                            {regionalPerformance.map((region) => (
                                <div
                                    key={region.region}
                                    onClick={() => setSelectedRegion(selectedRegion === region.region ? 'all' : region.region)}
                                    className={`p-4 rounded-xl border cursor-pointer transition-all hover:scale-105 ${
                                        selectedRegion === region.region
                                            ? 'bg-[var(--bg-muted)] border-[var(--text-primary)]/50'
                                            : 'bg-[var(--bg-card)] border-[var(--border)] hover:border-[var(--text-primary)]/30'
                                    }`}
                                >
                                    <div className="flex items-center gap-2 mb-2">
                                        <MapPin size={16} className="text-[var(--text-primary)]" />
                                        <h3 className="font-semibold text-[var(--text-primary)]">{region.region}</h3>
                                    </div>
                                    <p className="text-2xl font-bold text-[var(--text-primary)]">
                                        {formatCurrency(region.totalRevenue)}
                                    </p>
                                    <div className="flex items-center justify-between mt-2 text-xs text-[var(--text-muted)]">
                                        <span>{region.storeCount} stores</span>
                                        <span className="text-[var(--text-primary)] font-bold">
                                            {region.avgGrowth >= 0 ? '+' : ''}{region.avgGrowth}%
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="fresh-section">
                            <div className="fresh-section-header">
                                <TrendingUp size={18} style={{ color: 'var(--success)' }} />
                                <span className="fresh-section-title">Top Performers</span>
                            </div>
                            <div className="fresh-list">
                                {topStores.map((store, idx) => (
                                    <div key={store.id} className="fresh-list-item">
                                        <div className="fresh-list-left">
                                            <span className="fresh-badge yellow" style={{ width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 12 }}>
                                                #{idx + 1}
                                            </span>
                                            <div>
                                                <span className="fresh-list-label">{store.name}</span>
                                                <span style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)' }}>{store.location.city}</span>
                                            </div>
                                        </div>
                                        <div className="fresh-list-right">
                                            <span className="fresh-list-value">{formatCurrency(store.performance.monthlyRevenue)}</span>
                                            <span style={{ fontSize: 11, color: 'var(--text-primary)', fontWeight: 600 }}>{store.metrics.salesGrowth >= 0 ? '+' : ''}{store.metrics.salesGrowth}%</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="fresh-section">
                            <div className="fresh-section-header">
                                <AlertTriangle size={18} style={{ color: 'var(--warning)' }} />
                                <span className="fresh-section-title">Needs Attention</span>
                            </div>
                            <div className="fresh-list">
                                {storesNeedingAttention.slice(0, 5).map((store) => (
                                    <div key={store.id} className="fresh-list-item">
                                        <div>
                                            <span className="fresh-list-label">{store.name}</span>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                                                {store.issues.map((issue, idx) => (
                                                    <span key={idx} className="fresh-badge yellow">{issue}</span>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="fresh-list-right">
                                            <span className="fresh-list-value">{formatCurrency(store.performance.monthlyRevenue)}</span>
                                            <span style={{ fontSize: 11, color: 'var(--text-primary)', fontWeight: 600 }}>{store.metrics.salesGrowth}%</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="fresh-section">
                            <div className="fresh-section-header">
                                <span className="fresh-section-title">Top Store Performance Trends</span>
                            </div>
                            <div style={{ height: 256 }}>
                                <Line
                                    data={{
                                        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                                        datasets: topStores.slice(0, 3).map((store, idx) => ({
                                            label: store.name,
                                            data: Array.from({ length: 6 }, (_, i) => {
                                                const base = store.performance.monthlyRevenue;
                                                const variation = (Math.sin(i / 2) * 0.1 + 1);
                                                return Math.floor(base * variation);
                                            }),
                                            borderColor: [
                                                'var(--accent)',
                                                'var(--info)',
                                                'var(--success)'
                                            ][idx],
                                            backgroundColor: [
                                                'var(--accent-soft)',
                                                'var(--info-soft)',
                                                'var(--success-soft)'
                                            ][idx],
                                            tension: 0.4,
                                            fill: true
                                        }))
                                    }}
                                    options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: {
                                            legend: {
                                                position: 'top',
                                                labels: {
                                                    color: 'var(--text-muted)',
                                                    padding: 10,
                                                    font: { size: 11 }
                                                }
                                            },
                                            tooltip: {
                                                backgroundColor: 'var(--bg-card)',
                                                padding: 12,
                                                titleColor: 'var(--text-primary)',
                                                bodyColor: 'var(--text-secondary)',
                                                callbacks: {
                                                    label: (context) => {
                                                        const value = context.parsed.y;
                                                        return `${context.dataset.label}: ${formatCurrency(value)}`;
                                                    }
                                                }
                                            }
                                        },
                                        scales: {
                                            x: {
                                                grid: { color: 'rgba(255,255,255,0.04)' },
                                                ticks: { color: 'var(--text-muted)' }
                                            },
                                            y: {
                                                grid: { color: 'rgba(255,255,255,0.04)' },
                                                ticks: {
                                                    color: 'var(--text-muted)',
                                                    callback: (value) => formatCurrency(value)
                                                }
                                            }
                                        }
                                    }}
                                />
                            </div>
                        </div>

                        <div className="fresh-section">
                            <div className="fresh-section-header">
                                <span className="fresh-section-title">Revenue by Store Type</span>
                            </div>
                            <div style={{ height: 256 }}>
                                <Bar
                                    data={{
                                        labels: ['Flagship', 'Standard', 'Express', 'Outlet'],
                                        datasets: [{
                                            label: 'Total Revenue',
                                            data: ['Flagship', 'Standard', 'Express', 'Outlet'].map(type => {
                                                return stores
                                                    .filter(s => s.type === type)
                                                    .reduce((sum, s) => sum + s.performance.monthlyRevenue, 0);
                                            }),
                                            backgroundColor: [
                                                'var(--warning)',
                                                'var(--accent)',
                                                'var(--success)',
                                                'var(--info)'
                                            ],
                                            borderWidth: 0
                                        }]
                                    }}
                                    options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: {
                                            legend: { display: false },
                                            tooltip: {
                                                backgroundColor: 'var(--bg-card)',
                                                padding: 12,
                                                titleColor: 'var(--text-primary)',
                                                bodyColor: 'var(--text-secondary)',
                                                callbacks: {
                                                    label: (context) => {
                                                        const value = context.parsed.y;
                                                        const count = stores.filter(s => s.type === context.label).length;
                                                        return [
                                                            `Revenue: ${formatCurrency(value)}`,
                                                            `Stores: ${count}`
                                                        ];
                                                    }
                                                }
                                            }
                                        },
                                        scales: {
                                            x: {
                                                grid: { display: false },
                                                ticks: { color: '#9ca3af' }
                                            },
                                            y: {
                                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                                ticks: {
                                                    color: '#9ca3af',
                                                    callback: (value) => formatCurrency(value)
                                                }
                                            }
                                        }
                                    }}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="fresh-section">
                        <div className="fresh-section-header">
                            <span className="fresh-section-title">
                                Store Comparison
                                {selectedRegion !== 'all' && (
                                    <span style={{ marginLeft: 8, fontSize: 13, fontWeight: 400, color: 'var(--text-muted)' }}>
                                        ({selectedRegion})
                                    </span>
                                )}
                            </span>
                            <div style={{ position: 'relative' }}>
                                <Search className="absolute" style={{ left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} size={18} />
                                <input
                                    type="text"
                                    placeholder="Search stores..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{
                                        paddingLeft: 36,
                                        paddingRight: 16,
                                        paddingTop: 8,
                                        paddingBottom: 8,
                                        borderRadius: 8,
                                        background: 'var(--bg-card)',
                                        border: '1px solid var(--border)',
                                        color: 'var(--text-primary)',
                                        fontSize: 13,
                                        outline: 'none',
                                        width: 200
                                    }}
                                />
                            </div>
                        </div>
                        <table className="fresh-table">
                            <thead>
                                <tr>
                                    <th
                                        onClick={() => handleSort('name')}
                                        style={{ cursor: 'pointer', textAlign: 'left' }}
                                    >
                                        <div className="flex items-center gap-2">
                                            Store <SortIcon field="name" sortBy={sortBy} sortOrder={sortOrder} />
                                        </div>
                                    </th>
                                    <th style={{ textAlign: 'center' }}>Trend</th>
                                    <th style={{ textAlign: 'center' }}>Type</th>
                                    <th style={{ textAlign: 'center' }}>Location</th>
                                    <th
                                        onClick={() => handleSort('revenue')}
                                        className="num"
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <div className="flex items-center justify-end gap-2">
                                            Revenue <SortIcon field="revenue" sortBy={sortBy} sortOrder={sortOrder} />
                                        </div>
                                    </th>
                                    <th
                                        onClick={() => handleSort('growth')}
                                        className="num"
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <div className="flex items-center justify-end gap-2">
                                            Growth <SortIcon field="growth" sortBy={sortBy} sortOrder={sortOrder} />
                                        </div>
                                    </th>
                                    <th
                                        onClick={() => handleSort('satisfaction')}
                                        className="num"
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <div className="flex items-center justify-end gap-2">
                                            Rating <SortIcon field="satisfaction" sortBy={sortBy} sortOrder={sortOrder} />
                                        </div>
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredStores.map((store) => (
                                    <tr key={store.id}>
                                        <td>
                                            <div>
                                                <p className="font-semibold text-[var(--text-primary)]">{store.name}</p>
                                                <p className="text-xs text-[var(--text-muted)]">{store.id}</p>
                                            </div>
                                        </td>
                                        <td style={{ textAlign: 'center' }}>
                                            <MiniSparkline
                                                data={Array.from({ length: 10 }, () => 500 + Math.random() * 500)}
                                                isPositive={store.metrics.salesGrowth >= 0}
                                            />
                                        </td>
                                        <td style={{ textAlign: 'center' }}>
                                            {(() => {
                                                const badgeStyle = {
                                                    Flagship: { bg: 'rgba(250, 204, 21, 0.2)', color: '#facc15' },
                                                    Standard: { bg: 'rgba(96, 165, 250, 0.2)', color: '#93c5fd' },
                                                    Express: { bg: 'rgba(74, 222, 128, 0.2)', color: '#4ade80' },
                                                    Outlet: { bg: 'rgba(192, 132, 252, 0.2)', color: '#c084fc' }
                                                }[store.type] || { bg: 'rgba(255,255,255,0.1)', color: 'var(--text-primary)' };
                                                return (
                                                    <span className="fresh-badge" style={{ background: badgeStyle.bg, color: badgeStyle.color }}>
                                                        {store.type}
                                                    </span>
                                                );
                                            })()}
                                        </td>
                                        <td style={{ textAlign: 'center' }}>
                                            <p className="text-sm text-[var(--text-primary)]">{store.location.city}</p>
                                            <p className="text-xs text-[var(--text-muted)]">{store.location.region}</p>
                                        </td>
                                        <td className="num" style={{ fontWeight: 600 }}>
                                            {formatCurrency(store.performance.monthlyRevenue)}
                                        </td>
                                        <td className="num" style={{ fontWeight: 600 }}>
                                            {store.metrics.salesGrowth >= 0 ? '+' : ''}{store.metrics.salesGrowth}%
                                        </td>
                                        <td className="num">
                                            <div className="flex items-center justify-end gap-1">
                                                <Star className="text-yellow-500 fill-yellow-500" size={14} />
                                                <span className="font-semibold text-[var(--text-primary)]">{store.metrics.customerSatisfaction}</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        {filteredStores.length === 0 && (
                            <div className="text-center py-12 text-[var(--text-muted)]">
                                No stores found matching your criteria
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default MultiStore;
