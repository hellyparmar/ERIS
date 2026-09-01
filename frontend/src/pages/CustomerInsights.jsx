import { useState, useEffect, useMemo } from 'react';
import {
    Users, TrendingUp, DollarSign, Target, Search,
    ChevronDown, ChevronUp, AlertTriangle, Crown, Heart,
    Zap, Clock, XCircle, UserX, Moon
} from 'lucide-react';
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
import SEO from '../components/SEO';

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
    return sortOrder === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />;
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
    const [growthTrend, setGrowthTrend] = useState([]);

    useEffect(() => {
        const fetchCustomers = async () => {
            setLoading(true);
            try {
                const summaryRes = await api.get('/api/v1/customers/stats');
                const stats = summaryRes.data.data;
                setApiSummary({
                    total_revenue: stats.total_lifetime_value,
                    total_customers: stats.total_customers,
                    segments: [
                        { segment: 'Champions', customer_count: stats.vip_customers, percentage: stats.total_customers ? Math.round((stats.vip_customers/stats.total_customers)*100) : 0, avg_lifetime_value: stats.average_lifetime_value * 1.5 },
                        { segment: 'Regular', customer_count: stats.regular_customers, percentage: stats.total_customers ? Math.round((stats.regular_customers/stats.total_customers)*100) : 0, avg_lifetime_value: stats.average_lifetime_value },
                        { segment: 'New', customer_count: stats.new_customers, percentage: stats.total_customers ? Math.round((stats.new_customers/stats.total_customers)*100) : 0, avg_lifetime_value: stats.average_lifetime_value * 0.5 }
                    ]
                });

                const customersRes = await api.get('/api/v1/customers?per_page=200');
                const processedCustomers = (customersRes.data.data?.customers || []).map(c => ({
                    ...c,
                    churnRisk: 15,
                    segment: c.segment || 'Regular',
                    totalSpent: c.lifetime_value || 0,
                    lastPurchaseDate: c.last_purchase_at || new Date().toISOString(),
                    rfmScore: { r: 3, f: 3, m: 3 }
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
        if (apiSummary) {
            const totalRevenue = apiSummary.total_revenue || 0;
            const customerCount = apiSummary.total_customers || 0;
            const avgSpend = (totalRevenue && customerCount > 0) ? totalRevenue / customerCount : 0;
            return {
                totalCustomers: customerCount,
                totalRevenue: totalRevenue,
                activeCustomers: customers.filter(c => (c.rfmScore?.r || 0) >= 3).length,
                retentionRate: 85,
                avgCustomerValue: avgSpend,
                avgOrderValue: 450,
                avgPurchasesPerCustomer: 3.5
            };
        }
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
        const map = {
            'Champions': { color: 'var(--c-brown)', background: 'var(--c-strip)' },
            'Whale': { color: 'var(--c-brown)', background: 'var(--c-strip)' },
            'Loyal': { color: 'var(--c-sage)', background: 'var(--c-strip)' },
            'Loyal Customers': { color: 'var(--c-sage)', background: 'var(--c-strip)' },
            'Potential Loyalist': { color: 'var(--c-sage)', background: 'var(--c-strip)' },
            'New': { color: 'var(--c-ink-muted)', background: 'var(--c-strip)' },
            'Recent Customers': { color: 'var(--c-ink-muted)', background: 'var(--c-strip)' },
            'At Risk': { color: 'var(--c-critical)', background: 'var(--c-strip)' },
            "Cant Lose": { color: 'var(--c-critical)', background: 'var(--c-strip)' },
            "Can't Lose Them": { color: 'var(--c-critical)', background: 'var(--c-strip)' },
            'Hibernating': { color: 'var(--c-ink-muted)', background: 'var(--c-strip)' },
            'Regular': { color: 'var(--c-ink-muted)', background: 'var(--c-strip)' }
        };
        return map[segment] || map['Regular'];
    };

    const filteredCustomers = useMemo(() => {
        let filtered = customers;

        if (selectedSegment !== 'all') {
            filtered = filtered.filter(c => c.segment === selectedSegment);
        }

        if (searchQuery) {
            filtered = filtered.filter(c =>
                c.name.toLowerCase().includes(searchQuery.toLowerCase())
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
            <div style={{ minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 13, color: 'var(--c-ink-muted)' }}>Analyzing customer profiles...</span>
            </div>
        );
    }

    return (
        <>
            <SEO title="Customer Insights" description="RFM Analysis and customer segmentation" />
            <style>{`
                .insight-row:hover {
                    background: var(--c-brown-glow) !important;
                }
            `}</style>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0, minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
                
                {/* Header Row */}
                <div style={{
                    padding: '16px 22px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-end',
                    borderBottom: '1px solid var(--c-border)',
                    background: 'var(--c-canvas)'
                }}>
                    <div>
                        <h1 className="page-title" >Customer Insights</h1>
                        <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>
                            Customer behavior and segmentation analysis
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <div style={{ position: 'relative' }}>
                            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-muted)' }} />
                            <input
                                placeholder="Search insights..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                style={{ paddingLeft: 30, fontSize: 12, width: 200 }}
                            />
                        </div>
                        {selectedSegment !== 'all' && (
                            <button className="action-btn" onClick={() => setSelectedSegment('all')}>
                                All Segments
                            </button>
                        )}
                    </div>
                </div>

                <div className="kpi-strip">
                    <div className="kpi-cell">
                        <div className="kpi-label">Total Customers</div>
                        <div className="kpi-value brown">{(metrics.totalCustomers ?? 0).toLocaleString()}</div>
                    </div>
                    <div className="kpi-cell">
                        <div className="kpi-label">Avg Spend</div>
                        <div className="kpi-value brown">₹{((metrics.avgCustomerValue || 0) / 1000).toFixed(1)}k</div>
                    </div>
                    <div className="kpi-cell">
                        <div className="kpi-label">Value At Risk</div>
                        <div className="kpi-value critical">₹{((customers.filter(c => c.segment === 'At Risk' || (c.churnRisk || 0) > 50).reduce((acc, c) => acc + (Number(c.totalSpent) || 0), 0)) / 100000).toFixed(2)}L</div>
                    </div>
                    <div className="kpi-cell">
                        <div className="kpi-label">Repeat Rate</div>
                        <div className="kpi-value sage">{customers.length > 0 ? Math.round((customers.filter(c => c.segment === 'Champions' || c.segment === 'Loyal').length / customers.length) * 100) : 0}%</div>
                    </div>
                </div>

                {/* AI Segments list (replacing card panels) */}
                <div style={{ padding: '22px', borderBottom: '1px solid var(--c-border)' }}>
                    <div className="zone-label" style={{ marginBottom: 12 }}>AI-Segment Profiles</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10 }}>
                        {apiSummary && apiSummary.segments.map((segmentData) => {
                            const segmentName = segmentData.segment;
                            const colors = getSegmentColor(segmentName);
                            const Icon = segmentIcons[segmentName] || Users;
                            const isSelected = selectedSegment === segmentName;

                            return (
                                <div
                                    key={segmentName}
                                    onClick={() => setSelectedSegment(isSelected ? 'all' : segmentName)}
                                    style={{
                                        cursor: 'pointer',
                                        padding: '12px',
                                        background: isSelected ? 'var(--c-brown-glow)' : 'var(--c-canvas-raised)',
                                        border: isSelected ? '1.5px solid var(--c-brown)' : '1px solid var(--c-border)'
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                        <span style={{ fontSize: '12px', fontWeight: 700, color: colors.color }}>{segmentName}</span>
                                        <Icon size={14} style={{ color: colors.color }} />
                                    </div>
                                    <div style={{ fontFamily: 'var(--f-mono)', fontSize: '18px', fontWeight: 700, color: 'var(--c-dark)' }}>
                                        {segmentData.customer_count ?? 0}
                                    </div>
                                    <div style={{ fontSize: '10px', color: 'var(--c-ink-muted)', marginTop: 4 }}>
                                        {segmentData.percentage ?? 0}% (Avg: ₹{((Number(segmentData.avg_lifetime_value) || 0) / 1000).toFixed(0)}k)
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Trends & Distribution charts */}
                <div className="two-col" style={{ borderBottom: '1px solid var(--c-border)' }}>
                    <div className="col-body">
                        <div className="zone-label">Acquisition Trend</div>
                        <div className="chart-inner" style={{ height: 220, marginTop: 12 }}>
                            {(!growthTrend || growthTrend.length === 0) ? (
                                <div className="empty-state" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <div className="empty-state-message">No customer data yet</div>
                                </div>
                            ) : (
                                <Line
                                    data={{
                                        labels: growthTrend.map(d => d.month),
                                        datasets: [{
                                            label: 'New Customers',
                                            data: growthTrend.map(d => d.newCustomers),
                                            borderColor: '#8B5E3C',
                                            backgroundColor: 'rgba(139,94,60,0.1)',
                                            fill: true,
                                            tension: 0.4
                                        }]
                                    }}
                                    options={{ responsive: true, maintainAspectRatio: false }}
                                />
                            )}
                        </div>
                    </div>
                    <div className="col-divider" />
                    <div className="col-body">
                        <div className="zone-label">Segment Distribution</div>
                        <div className="chart-inner" style={{ height: 220, marginTop: 12 }}>
                            {(!chartDistribution || Object.keys(chartDistribution).length === 0) ? (
                                <div className="empty-state" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 20px' }}>
                                    <div className="empty-state-message" style={{ whiteSpace: 'normal', lineHeight: '1.4' }}>No segment data yet — customers will appear here once sales are linked to customer records.</div>
                                </div>
                            ) : (
                                <Doughnut
                                    data={{
                                        labels: Object.keys(chartDistribution),
                                        datasets: [{
                                            data: Object.values(chartDistribution),
                                            backgroundColor: ['#8B5E3C', '#AEB784', '#091413', '#2C1F14', '#7A6A58']
                                        }]
                                    }}
                                    options={{ responsive: true, maintainAspectRatio: false }}
                                />
                            )}
                        </div>
                    </div>
                </div>

                {/* Detailed Table */}
                <div style={{ padding: '22px' }}>
                    <div className="zone-label" style={{ marginBottom: 12 }}>Customer Monitor</div>
                    <div style={{ overflowX: 'auto' }}>
                        <table className="eris-table" style={{ width: '100%' }}>
                            <thead>
                                <tr>
                                    <th onClick={() => handleSort('name')} style={{ cursor: 'pointer', textAlign: 'left' }}>Customer <SortIcon field="name" sortBy={sortBy} sortOrder={sortOrder} /></th>
                                    <th onClick={() => handleSort('segment')} style={{ cursor: 'pointer', textAlign: 'center' }}>AI Segment <SortIcon field="segment" sortBy={sortBy} sortOrder={sortOrder} /></th>
                                    <th onClick={() => handleSort('totalSpent')} style={{ cursor: 'pointer', textAlign: 'right' }}>LTV <SortIcon field="totalSpent" sortBy={sortBy} sortOrder={sortOrder} /></th>
                                    <th onClick={() => handleSort('lastPurchaseDate')} style={{ cursor: 'pointer', textAlign: 'right' }}>Last Active <SortIcon field="lastPurchaseDate" sortBy={sortBy} sortOrder={sortOrder} /></th>
                                    <th onClick={() => handleSort('churnRisk')} style={{ cursor: 'pointer', textAlign: 'right' }}>Churn Probability <SortIcon field="churnRisk" sortBy={sortBy} sortOrder={sortOrder} /></th>
                                </tr>
                            </thead>
                            <tbody>
                                {paginatedCustomers.map((customer) => (
                                    <tr key={customer.id} className="insight-row">
                                        <td>
                                            <div style={{ fontWeight: 700, color: '#1A1208' }}>{customer.name}</div>
                                        </td>
                                        <td style={{ textAlign: 'center' }}>
                                            <div className="badge active">{customer.segment}</div>
                                        </td>
                                        <td className="mono" style={{ textAlign: 'right', fontWeight: 600 }}>₹{(Number(customer.totalSpent) || 0).toLocaleString()}</td>
                                        <td className="mono" style={{ textAlign: 'right', color: 'var(--c-ink-muted)' }}>
                                            {customer.lastPurchaseDate ? new Date(customer.lastPurchaseDate).toLocaleDateString('en-IN') : 'N/A'}
                                        </td>
                                        <td className="mono" style={{ textAlign: 'right', fontWeight: 700, color: (customer.churnRisk ?? 0) > 50 ? 'var(--c-critical)' : 'var(--c-sage)' }}>
                                            {(customer.churnRisk ?? 0).toFixed(0)}%
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {totalPages > 1 && (
                        <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 16 }}>
                            <button className="action-btn" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>Prev</button>
                            <span style={{ fontSize: 12, alignSelf: 'center' }}>{currentPage} / {totalPages}</span>
                            <button className="action-btn" onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>Next</button>
                        </div>
                    )}
                </div>

            </div>
        </>
    );
};

export default CustomerInsights;
