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
import GlassCard from '../components/ui/GlassCard';
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

// Register ChartJS components
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

// SortIcon component outside of render
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

    // State for API-fetched summary
    const [apiSummary, setApiSummary] = useState(null);

    // Fetch customers from API
    useEffect(() => {
        const fetchCustomers = async () => {
            setLoading(true);
            try {
                // Fetch summary first
                const summaryRes = await api.get('/api/analytics/customers/rfm/summary');
                setApiSummary(summaryRes.data);

                // Fetch customer list (limit 200 for performance for now)
                const customersRes = await api.get('/api/analytics/customers/rfm/customers?limit=200');

                // Process fetched customers
                const processedCustomers = customersRes.data.map(c => ({
                    ...c,
                    // Ensure churnRisk is 0-100 for display (backend sends 0.0-1.0)
                    churnRisk: c.churn_risk_score > 1 ? c.churn_risk_score : c.churn_risk_score * 100,
                    // Use stored segment or fallback
                    segment: c.segment || 'Regular',
                    // Map snake_case to camelCase where needed by UI
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

    // Calculate metrics locally if API summary fails, or use API summary
    const metrics = useMemo(() => {
        if (apiSummary) return {
            totalCustomers: apiSummary.total_customers,
            totalRevenue: apiSummary.total_revenue,
            activeCustomers: customers.filter(c => c.rfmScore.r >= 3).length, // Rough approximation
            retentionRate: 85, // Placeholder or fetch from backend
            avgCustomerValue: apiSummary.total_revenue / (apiSummary.total_customers || 1),
            avgOrderValue: 450, // Placeholder
            avgPurchasesPerCustomer: 3.5
        };
        return getCustomerMetrics(customers);
    }, [customers, apiSummary]);

    // Calculate Distribution for Charts locally from fetched customers
    const chartDistribution = useMemo(() => {
        const dist = {};
        customers.forEach(c => {
            dist[c.segment] = (dist[c.segment] || 0) + 1;
        });
        
        // Provide mock data while loading if no customers are available
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

    // Calculate Growth Trend (Mocked or derived from real dates)
    const growthTrend = useMemo(() => {
        // Group customers by creation date or first purchase date (using lastPurchaseDate as proxy if needed, or better yet, fetch this)
        // For now, we'll mock a realistic trend based on customer volume
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
        return months.map(m => ({
            month: m,
            newCustomers: Math.floor(Math.random() * 20) + 5 // Placeholder
        }));
    }, []);


    // Segment icons mapping
    const segmentIcons = {
        'Champions': Crown,
        'Loyal': Heart, // Mapped from backend 'Loyal'
        'Loyal Customers': Heart,
        'Potential Loyalist': TrendingUp,
        'New': Zap, // Mapped from backend 'New'
        'Recent Customers': Zap,
        'Promising': Target,
        'Need Attention': AlertTriangle,
        'About to Sleep': Clock,
        'At Risk': AlertTriangle,
        "Cant Lose": XCircle,
        "Can't Lose Them": XCircle,
        'Hibernating': Moon,
        'Lost': UserX,
        'Whale': Crown // Integrated Synthetic Data Segment
    };

    const getSegmentColor = (segment) => {
        const colors = {
            'Champions': { text: 'text-amber-400', bg: 'from-amber-400 to-yellow-600', border: 'border-amber-400/50', glow: 'shadow-amber-400/20' },
            'Whale': { text: 'text-amber-400', bg: 'from-amber-400 to-yellow-600', border: 'border-amber-400/50', glow: 'shadow-amber-400/20' },
            'Loyal': { text: 'text-blue-400', bg: 'from-blue-400 to-blue-600', border: 'border-blue-400/50', glow: 'shadow-blue-400/20' },
            'Loyal Customers': { text: 'text-blue-400', bg: 'from-blue-400 to-blue-600', border: 'border-blue-400/50', glow: 'shadow-blue-400/20' },
            'Potential Loyalist': { text: 'text-green-400', bg: 'from-green-400 to-emerald-600', border: 'border-green-400/50', glow: 'shadow-green-400/20' },
            'New': { text: 'text-cyan-400', bg: 'from-cyan-400 to-cyan-600', border: 'border-cyan-400/50', glow: 'shadow-cyan-400/20' },
            'Recent Customers': { text: 'text-cyan-400', bg: 'from-cyan-400 to-cyan-600', border: 'border-cyan-400/50', glow: 'shadow-cyan-400/20' },
            'At Risk': { text: 'text-red-400', bg: 'from-red-400 to-red-600', border: 'border-red-400/50', glow: 'shadow-red-400/20' },
            'Cant Lose': { text: 'text-pink-400', bg: 'from-pink-400 to-rose-600', border: 'border-pink-400/50', glow: 'shadow-pink-400/20' },
            'Hibernating': { text: 'text-gray-400', bg: 'from-gray-400 to-gray-600', border: 'border-gray-400/50', glow: 'shadow-gray-400/20' },
            'Regular': { text: 'text-slate-400', bg: 'from-slate-400 to-slate-600', border: 'border-slate-400/50', glow: 'shadow-slate-400/20' }
        };
        return colors[segment] || colors['Regular'];
    };

    // Filter and sort customers
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

    // Pagination
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
        <div className="min-h-screen space-y-8 animate-fade-in p-6">
            {/* Header */}
            <div
            >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                    Customer Insights
                </h1>
                <p className="text-muted-foreground">
                    Deep Learning Churn Predictions & Segmentation
                </p>
            </div>

            {/* Overview Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-1">
                    <div className="flex items-center justify-between mb-2">
                        <Users className="text-primary" size={24} />
                        <span className="text-xs text-muted-foreground">Total Database</span>
                    </div>
                    <p className="text-3xl font-bold text-foreground">
                        {metrics.totalCustomers.toLocaleString()}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">Active Profiles</p>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-2">
                    <div className="flex items-center justify-between mb-2">
                        <DollarSign className="text-success" size={24} />
                        <span className="text-xs text-muted-foreground">Revenue Impact</span>
                    </div>
                    <p className="text-3xl font-bold text-foreground">
                        ₹{(metrics.totalRevenue / 100000).toFixed(2)}L
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                        Lifetime Value
                    </p>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-3">
                    <div className="flex items-center justify-between mb-2">
                        <AlertTriangle className="text-warning" size={24} />
                        <span className="text-xs text-muted-foreground">Revenue at Risk</span>
                    </div>
                    <p className="text-3xl font-bold text-foreground">
                        {/* Calculate rudimentary 'At Risk' revenue */}
                        ₹{(customers.filter(c => c.segment === 'At Risk' || c.churnRisk > 50).reduce((acc, c) => acc + c.totalSpent, 0) / 100000).toFixed(2)}L
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                        High Churn Probability
                    </p>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-4">
                    <div className="flex items-center justify-between mb-2">
                        <Target className="text-purple-500" size={24} />
                        <span className="text-xs text-muted-foreground">Retention</span>
                    </div>
                    <p className="text-3xl font-bold text-foreground">
                        {customers.length > 0 ? Math.round((customers.filter(c => c.segment === 'Champions' || c.segment === 'Loyal').length / customers.length) * 100) : 0}%
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                        Loyal & Champions
                    </p>
                </GlassCard>
            </div>

            {/* RFM Segments Grid */}
            <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                    AI Segments
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {apiSummary && apiSummary.segments.map((segmentData, idx) => {
                        const segmentName = segmentData.segment;
                        const colors = getSegmentColor(segmentName);
                        const Icon = segmentIcons[segmentName] || Users;
                        const isSelected = selectedSegment === segmentName;

                        return (
                            <div
                                key={segmentName}
                                className="h-full"
                            >
                                <GlassCard
                                    variant="gradient"
                                    onClick={() => setSelectedSegment(isSelected ? 'all' : segmentName)}
                                    className={`p-4 cursor-pointer transition-all hover:scale-105 h-full flex flex-col justify-between ${isSelected ? `ring-2 ${colors.glow}` : ''
                                        } ${colors.glow}`}
                                >
                                    <div>
                                        <div className="flex items-start justify-between mb-3">
                                            <div className={`p-2 rounded-lg bg-gradient-to-br ${colors.bg} bg-opacity-20`}>
                                                <Icon className={colors.text} size={20} />
                                            </div>
                                            <span className="text-xs text-muted-foreground">{segmentData.percentage}%</span>
                                        </div>
                                        <h3 className={`font-semibold mb-1 ${colors.text}`}>{segmentName}</h3>
                                        <p className="text-2xl font-bold text-foreground mb-2">{segmentData.customer_count}</p>
                                        <div className="text-xs text-muted-foreground mb-2">
                                            Avg: ₹{(segmentData.avg_lifetime_value / 1000).toFixed(0)}k
                                        </div>
                                    </div>
                                    <p className="text-xs text-muted-foreground line-clamp-2 mt-2">
                                        {/* Use backend summary action or fallback */}
                                        {apiSummary.segment_actions?.[segmentName] || "No action defined"}
                                    </p>
                                </GlassCard>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Analytics Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Customer Growth Trend */}
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-1">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                        Customer Growth Trend
                    </h2>
                    <div className="h-64">
                        <Line
                            data={{
                                labels: growthTrend.map(d => d.month),
                                datasets: [{
                                    label: 'New Customers',
                                    data: growthTrend.map(d => d.newCustomers),
                                    borderColor: 'rgb(59, 130, 246)',
                                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
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
                                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                        padding: 12,
                                        titleColor: '#fff',
                                        bodyColor: '#fff'
                                    }
                                },
                                scales: {
                                    x: {
                                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                        ticks: { color: '#9ca3af' }
                                    },
                                    y: {
                                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                        ticks: { color: '#9ca3af' }
                                    }
                                }
                            }}
                        />
                    </div>
                </GlassCard>

                {/* Segment Distribution */}
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-2">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                        Segment Distribution
                    </h2>
                    <div className="h-64 flex items-center justify-center">
                        <Doughnut
                            data={{
                                labels: Object.keys(chartDistribution),
                                datasets: [{
                                    data: Object.values(chartDistribution),
                                    backgroundColor: [
                                        'rgba(251, 191, 36, 0.8)',  // Champions
                                        'rgba(59, 130, 246, 0.8)',  // Loyal
                                        'rgba(34, 197, 94, 0.8)',   // Potential
                                        'rgba(6, 182, 212, 0.8)',   // Recent
                                        'rgba(168, 85, 247, 0.8)',  // Need Attention
                                        'rgba(249, 115, 22, 0.8)',  // About to Sleep
                                        'rgba(239, 68, 68, 0.8)',   // At Risk
                                        'rgba(236, 72, 153, 0.8)',  // Can't Lose
                                        'rgba(156, 163, 175, 0.8)', // Hibernating
                                        'rgba(100, 116, 139, 0.8)', // Lost
                                        'rgba(20, 184, 166, 0.8)'   // Promising
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
                                            color: '#9ca3af',
                                            padding: 10,
                                            font: { size: 11 }
                                        }
                                    },
                                    tooltip: {
                                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                        padding: 12,
                                        titleColor: '#fff',
                                        bodyColor: '#fff'
                                    }
                                }
                            }}
                        />
                    </div>
                    {loading && <p className="text-center text-sm text-gray-400 mt-2">Loading real data...</p>}
                </GlassCard>
            </div>

            {/* Customer Table */}
            <GlassCard variant="gradient" className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                        Customer Monitor
                        {selectedSegment !== 'all' && (
                            <span className="ml-2 text-sm font-normal text-muted-foreground">
                                ({selectedSegment})
                            </span>
                        )}
                    </h2>
                    <div className="flex gap-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={18} />
                            <input
                                type="text"
                                placeholder="Search customers..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 pr-4 py-2 bg-muted/30 border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                        {selectedSegment !== 'all' && (
                            <button
                                onClick={() => setSelectedSegment('all')}
                                className="px-4 py-2 bg-muted/30 hover:bg-muted/50 rounded-lg text-foreground transition-all border border-border"
                            >
                                Clear Filter
                            </button>
                        )}
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-border">
                                <th onClick={() => handleSort('name')} className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase cursor-pointer hover:text-foreground">
                                    Customer <SortIcon field="name" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                                <th onClick={() => handleSort('segment')} className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase cursor-pointer hover:text-foreground">
                                    AI Segment <SortIcon field="segment" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                                <th onClick={() => handleSort('totalSpent')} className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase cursor-pointer hover:text-foreground">
                                    LTV <SortIcon field="totalSpent" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                                <th onClick={() => handleSort('lastPurchaseDate')} className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase cursor-pointer hover:text-foreground">
                                    Last Active <SortIcon field="lastPurchaseDate" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                                <th onClick={() => handleSort('churnRisk')} className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase cursor-pointer hover:text-foreground w-48">
                                    Churn Probability <SortIcon field="churnRisk" sortBy={sortBy} sortOrder={sortOrder} />
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {paginatedCustomers.map((customer, idx) => {
                                const colors = getSegmentColor(customer.segment);
                                return (
                                    <motion.tr
                                        key={customer.id}
                                        className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5 transition-all"
                                    >
                                        <td className="py-4 px-4">
                                            <div>
                                                <p className="font-semibold text-foreground">{customer.name}</p>
                                                <p className="text-xs text-muted-foreground">{customer.email}</p>
                                            </div>
                                        </td>
                                        <td className="py-4 px-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${colors.text} ${colors.border} ${colors.bg} bg-opacity-20`}>
                                                {customer.segment}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-right">
                                            <span className="font-bold text-foreground">
                                                ₹{customer.totalSpent.toLocaleString()}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-right text-muted-foreground text-sm">
                                            {customer.lastPurchaseDate ? new Date(customer.lastPurchaseDate).toLocaleDateString('en-IN') : 'N/A'}
                                        </td>
                                        <td className="py-4 px-4">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex justify-between text-xs mb-1">
                                                    <span className={customer.churnRisk > 50 ? 'text-red-400 font-bold' : 'text-green-400'}>
                                                        {customer.churnRisk.toFixed(1)}%
                                                    </span>
                                                    <span className="text-muted-foreground text-[10px]">
                                                        {customer.churnRisk > 70 ? 'HIGH RISK' : customer.churnRisk > 30 ? 'MONITOR' : 'SAFE'}
                                                    </span>
                                                </div>
                                                <div className="w-full h-2 bg-muted/30 rounded-full overflow-hidden">
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
                                    </motion.tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between mt-6 pt-4 border-t border-border">
                        <p className="text-sm text-muted-foreground">
                            Showing {((currentPage - 1) * customersPerPage) + 1} to {Math.min(currentPage * customersPerPage, filteredCustomers.length)} of {filteredCustomers.length} customers
                        </p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="px-4 py-2 bg-muted/30 hover:bg-muted/50 rounded-lg text-foreground transition-all border border-border disabled:cursor-not-allowed"
                            >
                                Previous
                            </button>
                            <span className="px-4 py-2 text-muted-foreground">
                                Page {currentPage} of {totalPages}
                            </span>
                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="px-4 py-2 bg-muted/30 hover:bg-muted/50 rounded-lg text-foreground transition-all border border-border disabled:cursor-not-allowed"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </GlassCard>
        </div>
    );
};

export default CustomerInsights;
