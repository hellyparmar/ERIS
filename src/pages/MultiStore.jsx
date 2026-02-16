/**
 * Enterprise Retail Intelligence System v3.0
 * MULTI-STORE DASHBOARD - Store comparison and network performance
 */

import { useState, useMemo, useEffect } from 'react';
import {
    Store, MapPin, TrendingUp, TrendingDown, DollarSign, Target, AlertTriangle, Star,
    ChevronDown, ChevronUp, Search
} from 'lucide-react';
import UnifiedCard from '../components/ui/UnifiedCard';
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

// Register ChartJS components
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

// SortIcon component outside of render
const SortIcon = ({ field, sortBy, sortOrder }) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
};

// Mini Sparkline Component using SVG
const MiniSparkline = ({ data, color, isPositive }) => {
    const width = 60;
    const height = 24;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    // Generate path
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
                stroke={isPositive ? '#10b981' : '#ef4444'} // Semantic Green/Red
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            {/* End dot */}
            <circle
                cx={width}
                cy={height - ((data[data.length - 1] - min) / range) * height}
                r="2"
                fill={isPositive ? '#10b981' : '#ef4444'}
            />
        </svg>
    );
};

const MultiStore = () => {
    const [isLoading, setIsLoading] = useState(true);
    const [stores] = useState(mockStores);
    const [selectedRegion, setSelectedRegion] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('revenue');
    const [sortOrder, setSortOrder] = useState('desc');

    // Calculate metrics
    const networkMetrics = useMemo(() => getNetworkMetrics(stores), [stores]);
    const regionalPerformance = useMemo(() => calculateRegionalPerformance(stores), [stores]);
    const topStores = useMemo(() => getTopPerformingStores(stores, 5), [stores]);
    const storesNeedingAttention = useMemo(() => getStoresNeedingAttention(stores), [stores]);

    // Simulating initial data load
    useEffect(() => {
        const timer = setTimeout(() => setIsLoading(false), 2000);
        return () => clearTimeout(timer);
    }, []);

    // Filter and sort stores
    const filteredStores = useMemo(() => {
        let filtered = stores;

        // Filter by region
        if (selectedRegion !== 'all') {
            filtered = filtered.filter(s => s.location.region === selectedRegion);
        }

        // Filter by search
        if (searchQuery) {
            filtered = filtered.filter(s =>
                s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                s.location.city.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        // Sort
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
        if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
        if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
        return `₹${(value / 1000).toFixed(0)}k`;
    };

    return (
        <div className="min-h-screen space-y-8 p-6 animate-fade-in">
            {/* Header */}
            <div
            >
                <h1 className="text-4xl font-bold text-foreground mb-2">
                    Multi-Store Dashboard
                </h1>
                <p className="text-muted-foreground">
                    Monitor and compare performance across {networkMetrics.totalStores} retail locations
                </p>
            </div>

            {isLoading ? <LoadingNotice message="Loading store data..." /> : (
                <>
                    {/* Network Overview Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <UnifiedCard className="p-6 animate-slide-up stagger-1">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground mb-1">Total Stores</p>
                                    <p className="text-3xl font-bold text-foreground">{networkMetrics.totalStores}</p>
                                    <p className="text-xs text-gray-500 dark:text-muted-foreground mt-1">
                                        {networkMetrics.activeStores} Active
                                    </p>
                                </div>
                                <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20">
                                    <Store className="text-blue-500" size={24} />
                                </div>
                            </div>
                        </UnifiedCard>

                        <UnifiedCard className="p-6 animate-slide-up stagger-2">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground mb-1">Network Revenue</p>
                                    <p className="text-3xl font-bold text-foreground">
                                        {formatCurrency(networkMetrics.totalRevenue)}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-muted-foreground mt-1">
                                        Avg: {formatCurrency(networkMetrics.avgRevenue)}/store
                                    </p>
                                </div>
                                <div className="p-3 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20">
                                    <DollarSign className="text-green-500" size={24} />
                                </div>
                            </div>
                        </UnifiedCard>

                        <UnifiedCard className="p-6 animate-slide-up stagger-3">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground mb-1">Avg Growth</p>
                                    <p className="text-3xl font-bold text-foreground">
                                        {networkMetrics.avgGrowth >= 0 ? '+' : ''}{networkMetrics.avgGrowth}%
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-muted-foreground mt-1">Month over month</p>
                                </div>
                                <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                                    {networkMetrics.avgGrowth >= 0 ? (
                                        <TrendingUp className="text-success" size={24} />
                                    ) : (
                                        <TrendingDown className="text-danger" size={24} />
                                    )}
                                </div>
                            </div>
                        </UnifiedCard>

                        <UnifiedCard className="p-6 animate-slide-up stagger-4">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground mb-1">Satisfaction</p>
                                    <div className="flex items-center gap-2">
                                        <p className="text-3xl font-bold text-foreground">{networkMetrics.avgSatisfaction}</p>
                                        <Star className="text-yellow-500 fill-yellow-500" size={20} />
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-muted-foreground mt-1">Network average</p>
                                </div>
                                <div className="p-3 rounded-xl bg-gradient-to-br from-yellow-500/20 to-orange-500/20">
                                    <Target className="text-yellow-500" size={24} />
                                </div>
                            </div>
                        </UnifiedCard>
                    </div>

                    {/* Regional Performance */}
                    <UnifiedCard className="p-6 animate-slide-up stagger-1">
                        <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                            Regional Performance
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                            {regionalPerformance.map((region, idx) => (
                                <div
                                    key={region.region}
                                    onClick={() => setSelectedRegion(selectedRegion === region.region ? 'all' : region.region)}
                                    className={`p-4 rounded-xl border cursor-pointer transition-all hover:scale-105 ${selectedRegion === region.region
                                        ? 'bg-gradient-to-br from-primary/10 to-purple/10 border-primary/50 shadow-glow-primary'
                                        : 'bg-card border-border hover:border-primary/30'
                                        }`}
                                >
                                    <div className="flex items-center gap-2 mb-2">
                                        <MapPin size={16} className="text-primary" />
                                        <h3 className="font-semibold text-foreground">{region.region}</h3>
                                    </div>
                                    <p className="text-2xl font-bold text-foreground">
                                        {formatCurrency(region.totalRevenue)}
                                    </p>
                                    <div className="flex items-center justify-between mt-2 text-xs text-gray-500 dark:text-muted-foreground">
                                        <span>{region.storeCount} stores</span>
                                        <span className="text-foreground font-bold">
                                            {region.avgGrowth >= 0 ? '+' : ''}{region.avgGrowth}%
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </UnifiedCard>

                    {/* Top & Bottom Performers */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Top Performers */}
                        <UnifiedCard className="p-6 animate-slide-up stagger-2">
                            <div className="flex items-center gap-2 mb-4">
                                <TrendingUp className="text-success" size={20} />
                                <h2 className="text-xl font-bold text-foreground">Top Performers</h2>
                            </div>
                            <div className="space-y-3">
                                {topStores.map((store, idx) => (
                                    <div key={store.id} className="flex items-center justify-between p-3 rounded-lg bg-success/5 border border-success/20">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center text-white font-bold text-sm">
                                                #{idx + 1}
                                            </div>
                                            <div>
                                                <p className="font-semibold text-foreground">{store.name}</p>
                                                <p className="text-xs text-gray-500 dark:text-muted-foreground">{store.location.city}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold text-foreground">{formatCurrency(store.performance.monthlyRevenue)}</p>
                                            <p className="text-xs text-foreground font-semibold">{store.metrics.salesGrowth >= 0 ? '+' : ''}{store.metrics.salesGrowth}%</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </UnifiedCard>

                        {/* Needs Attention */}
                        <UnifiedCard className="p-6 animate-slide-up stagger-3">
                            <div className="flex items-center gap-2 mb-4">
                                <AlertTriangle className="text-warning" size={20} />
                                <h2 className="text-xl font-bold text-foreground">Needs Attention</h2>
                            </div>
                            <div className="space-y-3">
                                {storesNeedingAttention.slice(0, 5).map((store) => (
                                    <div key={store.id} className="flex items-center justify-between p-3 rounded-lg bg-warning/5 border border-warning/20">
                                        <div>
                                            <p className="font-semibold text-foreground">{store.name}</p>
                                            <div className="flex flex-wrap gap-1 mt-1">
                                                {store.issues.map((issue, idx) => (
                                                    <span key={idx} className="text-xs px-2 py-0.5 rounded-full bg-warning/20 text-warning">
                                                        {issue}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold text-foreground">{formatCurrency(store.performance.monthlyRevenue)}</p>
                                            <p className="text-xs text-foreground font-semibold">{store.metrics.salesGrowth}%</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </UnifiedCard>
                    </div>

                    {/* Store Analytics Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Store Performance Trends */}
                        <UnifiedCard className="p-6 animate-slide-up stagger-1">
                            <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                                Top Store Performance Trends
                            </h2>
                            <div className="h-64">
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
                                                'rgb(59, 130, 246)',
                                                'rgb(168, 85, 247)',
                                                'rgb(34, 197, 94)'
                                            ][idx],
                                            backgroundColor: [
                                                'rgba(59, 130, 246, 0.1)',
                                                'rgba(168, 85, 247, 0.1)',
                                                'rgba(34, 197, 94, 0.1)'
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
                                                    color: '#9ca3af',
                                                    padding: 10,
                                                    font: { size: 11 }
                                                }
                                            },
                                            tooltip: {
                                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                                padding: 12,
                                                titleColor: '#fff',
                                                bodyColor: '#fff',
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
                                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
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
                        </UnifiedCard>

                        {/* Store Type Distribution */}
                        <UnifiedCard className="p-6 animate-slide-up stagger-2">
                            <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                                Revenue by Store Type
                            </h2>
                            <div className="h-64">
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
                                                'rgba(251, 191, 36, 0.8)',
                                                'rgba(59, 130, 246, 0.8)',
                                                'rgba(34, 197, 94, 0.8)',
                                                'rgba(168, 85, 247, 0.8)'
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
                                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                                padding: 12,
                                                titleColor: '#fff',
                                                bodyColor: '#fff',
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
                        </UnifiedCard>
                    </div>

                    {/* Store Comparison Table */}
                    <UnifiedCard className="p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                                Store Comparison
                                {selectedRegion !== 'all' && (
                                    <span className="ml-2 text-sm font-normal text-muted-foreground">
                                        ({selectedRegion})
                                    </span>
                                )}
                            </h2>
                            <div className="flex items-center gap-4">
                                {selectedRegion !== 'all' && (
                                    <button
                                        onClick={() => setSelectedRegion('all')}
                                        className="px-4 py-2 rounded-lg bg-primary/20 text-primary text-sm font-medium hover:bg-primary/30 transition-colors"
                                    >
                                        Clear Filter
                                    </button>
                                )}
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                                    <input
                                        type="text"
                                        placeholder="Search stores..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="pl-10 pr-4 py-2 rounded-lg bg-card border border-border text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th
                                            onClick={() => handleSort('name')}
                                            className="text-left py-3 px-4 text-muted-foreground font-light text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                        >
                                            <div className="flex items-center gap-2">
                                                Store <SortIcon field="name" sortBy={sortBy} sortOrder={sortOrder} />
                                            </div>
                                        </th>
                                        <th className="text-center py-3 px-4 text-muted-foreground font-light text-sm uppercase tracking-wider">
                                            Trend
                                        </th>
                                        <th className="text-center py-3 px-4 text-muted-foreground font-light text-sm uppercase tracking-wider">
                                            Type
                                        </th>
                                        <th className="text-center py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                            Location
                                        </th>
                                        <th
                                            onClick={() => handleSort('revenue')}
                                            className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                Revenue <SortIcon field="revenue" sortBy={sortBy} sortOrder={sortOrder} />
                                            </div>
                                        </th>
                                        <th
                                            onClick={() => handleSort('growth')}
                                            className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                Growth <SortIcon field="growth" sortBy={sortBy} sortOrder={sortOrder} />
                                            </div>
                                        </th>
                                        <th
                                            onClick={() => handleSort('satisfaction')}
                                            className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                Rating <SortIcon field="satisfaction" sortBy={sortBy} sortOrder={sortOrder} />
                                            </div>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredStores.map((store, idx) => (
                                        <motion.tr
                                            key={store.id}
                                            className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5 transition-all"
                                        >
                                            <td className="py-3 px-4">
                                                <div>
                                                    <p className="font-semibold text-foreground">{store.name}</p>
                                                    <p className="text-xs text-muted-foreground">{store.id}</p>
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 flex justify-center">
                                                {/* Mock Sparkline Data - In real app, this comes from API */}
                                                <MiniSparkline
                                                    data={Array.from({ length: 10 }, () => 500 + Math.random() * 500)}
                                                    isPositive={store.metrics.salesGrowth >= 0}
                                                />
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${store.type === 'Flagship' ? 'bg-yellow-500/20 text-yellow-800 dark:text-yellow-300' :
                                                    store.type === 'Standard' ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' :
                                                        store.type === 'Express' ? 'bg-green-500/20 text-green-600 dark:text-green-400' :
                                                            'bg-purple-500/20 text-purple-600 dark:text-purple-400'
                                                    }`}>
                                                    {store.type}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <p className="text-sm text-foreground">{store.location.city}</p>
                                                <p className="text-xs text-muted-foreground">{store.location.region}</p>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <p className="font-bold text-foreground">
                                                    {formatCurrency(store.performance.monthlyRevenue)}
                                                </p>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <span className="font-semibold text-foreground">
                                                    {store.metrics.salesGrowth >= 0 ? '+' : ''}{store.metrics.salesGrowth}%
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <div className="flex items-center justify-end gap-1">
                                                    <Star className="text-yellow-500 fill-yellow-500" size={14} />
                                                    <span className="font-semibold text-foreground">{store.metrics.customerSatisfaction}</span>
                                                </div>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {filteredStores.length === 0 && (
                            <div className="text-center py-12 text-muted-foreground">
                                No stores found matching your criteria
                            </div>
                        )}
                    </UnifiedCard>
                </>
            )}
        </div>
    );
};

export default MultiStore;
