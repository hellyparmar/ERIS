/**
 * Enterprise Retail Intelligence System v3.0
 * CUSTOMER INSIGHTS - RFM Analysis & Customer Segmentation
 */

import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    Users, TrendingUp, DollarSign, Target, Search, Filter,
    ChevronDown, ChevronUp, AlertTriangle, Crown, Heart,
    Zap, Clock, XCircle, UserX, Moon
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import mockCustomers from '../data/customerData';
import { processCustomersWithRFM, getRFMDistribution, getSegmentColor, getSegmentAction } from '../utils/rfmAnalysis';
import { calculateLTV, predictChurnRisk, getCustomerMetrics, getCustomerGrowthTrend } from '../utils/customerAnalytics';
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
    const [selectedSegment, setSelectedSegment] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('totalSpent');
    const [sortOrder, setSortOrder] = useState('desc');
    const [currentPage, setCurrentPage] = useState(1);
    const customersPerPage = 10;

    // Process customers with RFM on mount
    useEffect(() => {
        const processedCustomers = processCustomersWithRFM(mockCustomers).map(customer => ({
            ...customer,
            lifetimeValue: calculateLTV(customer),
            predictedLTV: calculateLTV(customer),
            churnRisk: predictChurnRisk(customer)
        }));

        // Use setTimeout to avoid synchronous setState in effect
        const timer = setTimeout(() => {
            setCustomers(processedCustomers);
        }, 0);

        return () => clearTimeout(timer);
    }, []);

    // Calculate metrics
    const metrics = useMemo(() => getCustomerMetrics(customers), [customers]);
    const distribution = useMemo(() => getRFMDistribution(customers), [customers]);

    // Segment icons mapping
    const segmentIcons = {
        'Champions': Crown,
        'Loyal Customers': Heart,
        'Potential Loyalists': TrendingUp,
        'Recent Customers': Zap,
        'Promising': Target,
        'Need Attention': AlertTriangle,
        'About to Sleep': Clock,
        'At Risk': AlertTriangle,
        "Can't Lose Them": XCircle,
        'Hibernating': Moon,
        'Lost': UserX
    };

    // Filter and sort customers
    const filteredCustomers = useMemo(() => {
        let filtered = customers;

        // Filter by segment
        if (selectedSegment !== 'all') {
            filtered = filtered.filter(c => c.segment === selectedSegment);
        }

        // Filter by search
        if (searchQuery) {
            filtered = filtered.filter(c =>
                c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                c.email.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        // Sort
        filtered.sort((a, b) => {
            let aVal = a[sortBy];
            let bVal = b[sortBy];

            if (sortBy === 'lastPurchaseDate') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
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

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                    Customer Insights
                </h1>
                <p className="text-muted-foreground">
                    RFM Analysis, Lifetime Value, and Churn Prediction
                </p>
            </motion.div>

            {/* Overview Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-1">
                    <div className="flex items-center justify-between mb-2">
                        <Users className="text-primary" size={24} />
                        <span className="text-xs text-muted-foreground">Total</span>
                    </div>
                    <p className="text-3xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                        {metrics.totalCustomers}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">Customers</p>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-2">
                    <div className="flex items-center justify-between mb-2">
                        <TrendingUp className="text-success" size={24} />
                        <span className="text-xs text-muted-foreground">Active</span>
                    </div>
                    <p className="text-3xl font-bold bg-gradient-to-r from-success to-green-600 bg-clip-text text-transparent">
                        {metrics.activeCustomers}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                        {metrics.retentionRate}% Retention
                    </p>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-3">
                    <div className="flex items-center justify-between mb-2">
                        <DollarSign className="text-warning" size={24} />
                        <span className="text-xs text-muted-foreground">Revenue</span>
                    </div>
                    <p className="text-3xl font-bold bg-gradient-to-r from-warning to-orange-600 bg-clip-text text-transparent">
                        ₹{(metrics.totalRevenue / 100000).toFixed(1)}L
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                        Avg: ₹{(metrics.avgCustomerValue / 1000).toFixed(0)}k
                    </p>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-4">
                    <div className="flex items-center justify-between mb-2">
                        <Target className="text-purple-500" size={24} />
                        <span className="text-xs text-muted-foreground">AOV</span>
                    </div>
                    <p className="text-3xl font-bold bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
                        ₹{(metrics.avgOrderValue / 1000).toFixed(1)}k
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                        {metrics.avgPurchasesPerCustomer} orders/customer
                    </p>
                </GlassCard>
            </div>

            {/* RFM Segments Grid */}
            <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                    Customer Segments
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {Object.entries(distribution).map(([segment, data], idx) => {
                        const colors = getSegmentColor(segment);
                        const Icon = segmentIcons[segment] || Users;
                        const isSelected = selectedSegment === segment;

                        return (
                            <motion.div
                                key={segment}
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: idx * 0.05 }}
                            >
                                <GlassCard
                                    variant="gradient"
                                    onClick={() => setSelectedSegment(isSelected ? 'all' : segment)}
                                    className={`p-4 cursor-pointer transition-all hover:scale-105 ${isSelected ? `ring-2 ${colors.glow}` : ''
                                        } ${colors.glow}`}
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <div className={`p-2 rounded-lg bg-gradient-to-br ${colors.bg} bg-opacity-20`}>
                                            <Icon className={colors.text} size={20} />
                                        </div>
                                        <span className="text-xs text-muted-foreground">{data.percentage}%</span>
                                    </div>
                                    <h3 className={`font-semibold mb-1 ${colors.text}`}>{segment}</h3>
                                    <p className="text-2xl font-bold text-foreground mb-2">{data.count}</p>
                                    <div className="text-xs text-muted-foreground mb-2">
                                        Avg: ₹{(data.avgValue / 1000).toFixed(0)}k
                                    </div>
                                    <p className="text-xs text-muted-foreground line-clamp-2">
                                        {getSegmentAction(segment)}
                                    </p>
                                </GlassCard>
                            </motion.div>
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
                                labels: getCustomerGrowthTrend(customers).map(d => d.month),
                                datasets: [{
                                    label: 'New Customers',
                                    data: getCustomerGrowthTrend(customers).map(d => d.newCustomers),
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
                                labels: Object.keys(distribution),
                                datasets: [{
                                    data: Object.values(distribution).map(d => d.count),
                                    backgroundColor: [
                                        'rgba(251, 191, 36, 0.8)',  // Champions - gold
                                        'rgba(59, 130, 246, 0.8)',  // Loyal - blue
                                        'rgba(34, 197, 94, 0.8)',   // Potential - green
                                        'rgba(6, 182, 212, 0.8)',   // Recent - cyan
                                        'rgba(168, 85, 247, 0.8)',  // Need Attention - purple
                                        'rgba(249, 115, 22, 0.8)',  // About to Sleep - orange
                                        'rgba(239, 68, 68, 0.8)',   // At Risk - red
                                        'rgba(236, 72, 153, 0.8)',  // Can't Lose - pink
                                        'rgba(156, 163, 175, 0.8)', // Hibernating - gray
                                        'rgba(100, 116, 139, 0.8)', // Lost - slate
                                        'rgba(20, 184, 166, 0.8)'   // Promising - teal
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
                </GlassCard>
            </div>

            {/* Customer Table */}
            <GlassCard variant="gradient" className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                        Customer List
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
                                <th
                                    onClick={() => handleSort('name')}
                                    className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        Customer <SortIcon field="name" sortBy={sortBy} sortOrder={sortOrder} />
                                    </div>
                                </th>
                                <th className="text-center py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    RFM Score
                                </th>
                                <th
                                    onClick={() => handleSort('segment')}
                                    className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        Segment <SortIcon field="segment" sortBy={sortBy} sortOrder={sortOrder} />
                                    </div>
                                </th>
                                <th
                                    onClick={() => handleSort('totalSpent')}
                                    className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                >
                                    <div className="flex items-center justify-end gap-2">
                                        Total Spent <SortIcon field="totalSpent" sortBy={sortBy} sortOrder={sortOrder} />
                                    </div>
                                </th>
                                <th
                                    onClick={() => handleSort('lastPurchaseDate')}
                                    className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                >
                                    <div className="flex items-center justify-end gap-2">
                                        Last Purchase <SortIcon field="lastPurchaseDate" sortBy={sortBy} sortOrder={sortOrder} />
                                    </div>
                                </th>
                                <th
                                    onClick={() => handleSort('churnRisk')}
                                    className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors"
                                >
                                    <div className="flex items-center justify-end gap-2">
                                        Churn Risk <SortIcon field="churnRisk" sortBy={sortBy} sortOrder={sortOrder} />
                                    </div>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {paginatedCustomers.map((customer, idx) => {
                                const colors = getSegmentColor(customer.segment);
                                return (
                                    <motion.tr
                                        key={customer.id}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: idx * 0.02 }}
                                        className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5 transition-all"
                                    >
                                        <td className="py-4 px-4">
                                            <div>
                                                <p className="font-semibold text-foreground">{customer.name}</p>
                                                <p className="text-xs text-muted-foreground">{customer.email}</p>
                                            </div>
                                        </td>
                                        <td className="py-4 px-4">
                                            <div className="flex items-center justify-center gap-1">
                                                <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded font-semibold">
                                                    R:{customer.rfmScore.r}
                                                </span>
                                                <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded font-semibold">
                                                    F:{customer.rfmScore.f}
                                                </span>
                                                <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded font-semibold">
                                                    M:{customer.rfmScore.m}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="py-4 px-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${colors.text} ${colors.border} bg-gradient-to-r ${colors.bg} bg-opacity-10`}>
                                                {customer.segment}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-right">
                                            <span className="font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                                                ₹{customer.totalSpent.toLocaleString()}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-right text-muted-foreground text-sm">
                                            {new Date(customer.lastPurchaseDate).toLocaleDateString('en-IN')}
                                        </td>
                                        <td className="py-4 px-4">
                                            <div className="flex items-center justify-end gap-2">
                                                <div className="w-24 h-2 bg-muted/30 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full transition-all ${customer.churnRisk >= 70 ? 'bg-danger' :
                                                            customer.churnRisk >= 40 ? 'bg-warning' :
                                                                'bg-success'
                                                            }`}
                                                        style={{ width: `${customer.churnRisk}%` }}
                                                    />
                                                </div>
                                                <span className={`text-xs font-semibold ${customer.churnRisk >= 70 ? 'text-danger' :
                                                    customer.churnRisk >= 40 ? 'text-warning' :
                                                        'text-success'
                                                    }`}>
                                                    {customer.churnRisk}%
                                                </span>
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
                                className="px-4 py-2 bg-muted/30 hover:bg-muted/50 rounded-lg text-foreground transition-all border border-border disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Previous
                            </button>
                            <span className="px-4 py-2 text-muted-foreground">
                                Page {currentPage} of {totalPages}
                            </span>
                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="px-4 py-2 bg-muted/30 hover:bg-muted/50 rounded-lg text-foreground transition-all border border-border disabled:opacity-50 disabled:cursor-not-allowed"
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
