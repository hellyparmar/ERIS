/**
 * Enterprise Retail Intelligence System v3.0
 * CUSTOMER INSIGHTS - RFM Analysis & Customer Segmentation
 */

import { useState, useEffect, useMemo } from 'react';
import {
    Users, TrendingUp, DollarSign, Target, Search,
    ChevronDown, ChevronUp, AlertTriangle, Crown, Heart,
    Zap, Clock, XCircle, UserX, Moon
} from 'lucide-react';
import '../styles/fresh-design.css';
import api from '../lib/api';
import { getCustomerMetrics } from '../utils/customerAnalytics';
import { Line, Doughnut } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const SortIcon = ({ field, sortBy, sortOrder }) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
};

const CustomerInsights = () => {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedSegment, setSelectedSegment] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('totalSpent');
    const [sortOrder, setSortOrder] = useState('desc');
    const [currentPage, setCurrentPage] = useState(1);
    const customersPerPage = 10;

    const [apiSummary, setApiSummary] = useState(null);

    useEffect(() => {
        const fetchCustomers = async () => {
            setLoading(true);
            try {
                const summaryRes = await api.get('/api/analytics/customers/rfm/summary');
                setApiSummary(summaryRes.data);

                const customersRes = await api.get('/api/analytics/customers/rfm/customers?limit=200');

                const processedCustomers = customersRes.data.map(c => ({
                    ...c,
                    churnRisk: c.churn_risk_score > 1 ? c.churn_risk_score : c.churn_risk_score * 100,
                    segment: c.segment || 'Regular',
                    totalSpent: c.total_spent,
                    lastPurchaseDate: c.last_purchase_date,
                    rfmScore: {
                        r: c.rfm_scores.recency,
                        f: c.rfm_scores.frequency,
                        m: c.rfm_scores.monetary
                    }
                }));

                setCustomers(processedCustomers);
            } catch (error) {
                console.error("Failed to fetch customer insights:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchCustomers();
    }, []);

    const metrics = useMemo(() => {
        if (apiSummary) return {
            totalCustomers: apiSummary.total_customers,
            totalRevenue: apiSummary.total_revenue,
            activeCustomers: customers.filter(c => c.rfmScore.r >= 3).length,
            retentionRate: 85,
            avgCustomerValue: apiSummary.total_revenue / (apiSummary.total_customers || 1),
            avgOrderValue: 450,
            avgPurchasesPerCustomer: 3.5
        };
        return getCustomerMetrics(customers);
    }, [customers, apiSummary]);

    const chartDistribution = useMemo(() => {
        const dist = {};
        customers.forEach(c => {
            dist[c.segment] = (dist[c.segment] || 0) + 1;
        });

        if (Object.keys(dist).length === 0 && loading) {
            return {
                'Champions': 12,
                'Loyal': 28,
                'Potential Loyalist': 18,
                'New': 15,
                'Need Attention': 22,
                'At Risk': 25,
                'Regular': 35
            };
        }

        return dist;
    }, [customers, loading]);

    const growthTrend = useMemo(() => {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
        return months.map(m => ({
            month: m,
            newCustomers: Math.floor(Math.random() * 20) + 5
        }));
    }, []);

    const segmentIcons = {
        'Champions': Crown,
        'Loyal': Heart,
        'Loyal Customers': Heart,
        'Potential Loyalist': TrendingUp,
        'New': Zap,
        'Recent Customers': Zap,
        'Promising': Target,
        'Need Attention': AlertTriangle,
        'About to Sleep': Clock,
        'At Risk': AlertTriangle,
        "Cant Lose": XCircle,
        "Can't Lose Them": XCircle,
        'Hibernating': Moon,
        'Lost': UserX,
        'Whale': Crown
    };

    const getSegmentColor = (segment) => {
        const colors = {
            'Champions': { text: 'text-[var(--champions-text)]', bg: 'bg-[var(--champions-bg)]', border: 'border-[var(--champions-border)]' },
            'Whale': { text: 'text-[var(--champions-text)]', bg: 'bg-[var(--champions-bg)]', border: 'border-[var(--champions-border)]' },
            'Loyal': { text: 'text-[var(--loyal-text)]', bg: 'bg-[var(--loyal-bg)]', border: 'border-[var(--loyal-border)]' },
            'Loyal Customers': { text: 'text-[var(--loyal-text)]', bg: 'bg-[var(--loyal-bg)]', border: 'border-[var(--loyal-border)]' },
            'Potential Loyalist': { text: 'text-[var(--success-text)]', bg: 'bg-[var(--success-bg)]', border: 'border-[var(--success-border)]' },
            'New': { text: 'text-[var(--info-text)]', bg: 'bg-[var(--info-bg)]', border: 'border-[var(--info-border)]' },
            'Recent Customers': { text: 'text-[var(--info-text)]', bg: 'bg-[var(--info-bg)]', border: 'border-[var(--info-border)]' },
            'At Risk': { text: 'text-[var(--error-text)]', bg: 'bg-[var(--error-bg)]', border: 'border-[var(--error-border)]' },
            'Cant Lose': { text: 'text-[var(--warning-text)]', bg: 'bg-[var(--warning-bg)]', border: 'border-[var(--warning-border)]' },
            'Hibernating': { text: 'text-[var(--muted-text)]', bg: 'bg-[var(--muted-bg)]', border: 'border-[var(--muted-border)]' },
            'Regular': { text: 'text-[var(--muted-text)]', bg: 'bg-[var(--muted-bg)]', border: 'border-[var(--muted-border)]' }
        };
        return colors[segment] || colors['Regular'];
    };

    const filteredCustomers = useMemo(() => {
        let filtered = customers;

        if (selectedSegment !== 'all') {
            filtered = filtered.filter(c => c.segment === selectedSegment);
        }

        if (searchQuery) {
            filtered = filtered.filter(c =>
                c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                c.email?.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        filtered.sort((a, b) => {
            let aVal = a[sortBy];
            let bVal = b[sortBy];

            if (sortBy === 'lastPurchaseDate') {
                aVal = new Date(aVal || 0);
                bVal = new Date(bVal || 0);
            }

            if (sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });

        return filtered;
    }, [customers, selectedSegment, searchQuery, sortBy, sortOrder]);

    const totalPages = Math.ceil(filteredCustomers.length / customersPerPage);
    const paginatedCustomers = filteredCustomers.slice(
        (currentPage - 1) * customersPerPage,
        currentPage * customersPerPage
    );

    const handleSort = (field) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(field);
            setSortOrder('desc');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <div className="fresh-page">
            <div style={{ marginBottom: 32 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--text-muted)]" size={18} />
                            <input
                                type="text"
                                placeholder="Search customers..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 pr-4 py-2 bg-[var(--bg-muted)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                        {selectedSegment !== 'all' && (
                            <button
                                onClick={() => setSelectedSegment('all')}
                                className="fresh-btn"
                            >
                                Clear Filter
                            </button>
                        )}
                    </div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                    Customer behavior and segmentation analysis
                </p>
            </div>

            <div className="fresh-metrics">
                <div className="fresh-metric">
                    <div className="fresh-metric-value">{metrics.totalCustomers.toLocaleString()}</div>
                    <div className="fresh-metric-label">Total Customers</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">₹{(metrics.avgCustomerValue / 1000).toFixed(1)}k</div>
                    <div className="fresh-metric-label">Avg Spend</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">₹{(customers.filter(c => c.segment === 'At Risk' || c.churnRisk > 50).reduce((acc, c) => acc + c.totalSpent, 0) / 100000).toFixed(2)}L</div>
                    <div className="fresh-metric-label">At Risk</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">{customers.length > 0 ? Math.round((customers.filter(c => c.segment === 'Champions' || c.segment === 'Loyal').length / customers.length) * 100) : 0}%</div>
                    <div className="fresh-metric-label">Repeat Rate</div>
                </div>
            </div>

            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title">AI Segments</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {apiSummary && apiSummary.segments.map((segmentData) => {
                        const segmentName = segmentData.segment;
                        const colors = getSegmentColor(segmentName);
                        const Icon = segmentIcons[segmentName] || Users;
                        const isSelected = selectedSegment === segmentName;

                        return (
                            <div
                                key={segmentName}
                                onClick={() => setSelectedSegment(isSelected ? 'all' : segmentName)}
                                className={`p-4 cursor-pointer transition-all hover:scale-105 h-full flex flex-col justify-between rounded-xl border border-[var(--border)] ${isSelected ? 'ring-2 ring-[var(--accent)]' : ''}`}
                                style={{ backgroundColor: 'var(--bg-card)' }}
                            >
                                <div>
                                    <div className="flex items-start justify-between mb-3">
                                        <div className={`p-2 rounded-lg ${colors.bg}`}>
                                            <Icon className={colors.text} size={20} />
                                        </div>
                                        <span className="text-xs text-[var(--text-muted)]">{segmentData.percentage}%</span>
                                    </div>
                                    <h3 className={`font-semibold mb-1 ${colors.text}`}>{segmentName}</h3>
                                    <p className="text-2xl font-bold text-[var(--text-primary)] mb-2">{segmentData.customer_count}</p>
                                    <div className="text-xs text-[var(--text-muted)] mb-2">
                                        Avg: ₹{(segmentData.avg_lifetime_value / 1000).toFixed(0)}k
                                    </div>
                                </div>
                                <p className="text-xs text-[var(--text-muted)] line-clamp-2 mt-2">
                                    {apiSummary.segment_actions?.[segmentName] || "No action defined"}
                                </p>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="fresh-section">
                    <div className="fresh-section-header">
                        <span className="fresh-section-title">Customer Growth Trend</span>
                    </div>
                    <div className="h-64">
                        <Line
                            data={{
                                labels: growthTrend.map(d => d.month),
                                datasets: [{
                                    label: 'New Customers',
                                    data: growthTrend.map(d => d.newCustomers),
                                    borderColor: 'var(--accent)',
                                    backgroundColor: 'var(--accent-soft)',
                                    fill: true,
                                    tension: 0.4
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
                                        bodyColor: 'var(--text-secondary)'
                                    }
                                },
                                scales: {
                                    x: {
                                        grid: { color: 'rgba(255,255,255,0.04)' },
                                        ticks: { color: 'var(--text-muted)' }
                                    },
                                    y: {
                                        grid: { color: 'rgba(255,255,255,0.04)' },
                                        ticks: { color: 'var(--text-muted)' }
                                    }
                                }
                            }}
                        />
                    </div>
                </div>

                <div className="fresh-section">
                    <div className="fresh-section-header">
                        <span className="fresh-section-title">Segment Distribution</span>
                    </div>
                    <div className="h-64 flex items-center justify-center">
                        <Doughnut
                            data={{
                                labels: Object.keys(chartDistribution),
                                datasets: [{
                                    data: Object.values(chartDistribution),
                                    backgroundColor: [
                                        'var(--warning)',
                                        'var(--accent)',
                                        'var(--success)',
                                        'var(--info)',
                                        'var(--error)',
                                        'var(--warning)',
                                        'var(--error)',
                                        'var(--success)',
                                        'var(--text-muted)',
                                        'var(--text-secondary)',
                                        'var(--info)'
                                    ],
                                    borderWidth: 0
                                }]
                            }}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'right',
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
                                        bodyColor: 'var(--text-secondary)'
                                    }
                                }
                            }}
                        />
                    </div>
                    {loading && <p className="text-center text-sm text-gray-400 mt-2">Loading real data...</p>}
                </div>
            </div>

            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title">
                        Customer Monitor
                        {selectedSegment !== 'all' && (
                            <span className="ml-2 text-sm font-normal text-[var(--text-muted)]">
                                ({selectedSegment})
                            </span>
                        )}
                    </span>
                </div>

                <div className="overflow-x-auto">
                    <table className="fresh-table">
                        <thead>
                            <tr className="border-b border-[var(--border)]">
                                <th onClick={() => handleSort('name')} className="text-left py-3 px-4 text-xs font-medium text-[var(--text-faint)] uppercase tracking-wider cursor-pointer hover:text-[var(--text-primary)]">
                                    Customer <SortIcon field="name" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                                <th onClick={() => handleSort('segment')} className="text-left py-3 px-4 text-xs font-medium text-[var(--text-faint)] uppercase tracking-wider cursor-pointer hover:text-[var(--text-primary)]">
                                    AI Segment <SortIcon field="segment" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                                <th onClick={() => handleSort('totalSpent')} className="text-right py-3 px-4 text-xs font-medium text-[var(--text-faint)] uppercase tracking-wider cursor-pointer hover:text-[var(--text-primary)]">
                                    LTV <SortIcon field="totalSpent" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                                <th onClick={() => handleSort('lastPurchaseDate')} className="text-right py-3 px-4 text-xs font-medium text-[var(--text-faint)] uppercase tracking-wider cursor-pointer hover:text-[var(--text-primary)]">
                                    Last Active <SortIcon field="lastPurchaseDate" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                                <th onClick={() => handleSort('churnRisk')} className="text-left py-3 px-4 text-xs font-medium text-[var(--text-faint)] uppercase tracking-wider cursor-pointer hover:text-[var(--text-primary)] w-48">
                                    Churn Probability <SortIcon field="churnRisk" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {paginatedCustomers.map((customer) => {
                                const colors = getSegmentColor(customer.segment);
                                return (
                                    <tr
                                        key={customer.id}
                                        className="border-b border-[var(--border)] hover:bg-[var(--bg-muted)] transition-all"
                                    >
                                        <td className="py-4 px-4">
                                            <div>
                                                <p className="font-semibold text-[var(--text-primary)]">{customer.name}</p>
                                                <p className="text-xs text-[var(--text-muted)]">{customer.email}</p>
                                            </div>
                                        </td>
                                        <td className="py-4 px-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${colors.text} ${colors.border} ${colors.bg}`}>
                                                {customer.segment}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-right">
                                            <span className="font-bold text-[var(--text-primary)]">
                                                ₹{customer.totalSpent.toLocaleString()}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-right text-[var(--text-muted)] text-sm">
                                            {customer.lastPurchaseDate ? new Date(customer.lastPurchaseDate).toLocaleDateString('en-IN') : 'N/A'}
                                        </td>
                                        <td className="py-4 px-4">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex justify-between text-xs mb-1">
                                                    <span className={customer.churnRisk > 50 ? 'text-red-400 font-bold' : 'text-green-400'}>
                                                        {customer.churnRisk.toFixed(1)}%
                                                    </span>
                                                    <span className="text-[var(--text-muted)] text-[10px]">
                                                        {customer.churnRisk > 70 ? 'HIGH RISK' : customer.churnRisk > 30 ? 'MONITOR' : 'SAFE'}
                                                    </span>
                                                </div>
                                                <div className="w-full h-2 bg-[var(--bg-muted)] rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full transition-all ${customer.churnRisk >= 70 ? 'bg-red-500' :
                                                            customer.churnRisk >= 40 ? 'bg-orange-500' :
                                                                'bg-emerald-500'
                                                            }`}
                                                        style={{ width: `${Math.min(customer.churnRisk, 100)}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {totalPages > 1 && (
                    <div className="flex items-center justify-between mt-6 pt-4 border-t border-[var(--border)]">
                        <p className="text-sm text-[var(--text-muted)]">
                            Showing {((currentPage - 1) * customersPerPage) + 1} to {Math.min(currentPage * customersPerPage, filteredCustomers.length)} of {filteredCustomers.length} customers
                        </p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="fresh-btn disabled:cursor-not-allowed"
                            >
                                Previous
                            </button>
                            <span className="px-4 py-2 text-[var(--text-muted)]">
                                Page {currentPage} of {totalPages}
                            </span>
                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="fresh-btn disabled:cursor-not-allowed"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CustomerInsights;
