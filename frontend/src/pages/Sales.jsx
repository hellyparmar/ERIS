import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Calendar } from 'lucide-react';
import api from '../services/api';
import '../styles/sales.css';

const CHART_COLORS = ['#f59e0b', '#22c55e', '#3b82f6', '#ef4444', '#a855f7'];
const tooltipStyle = { background: '#0f0f0f', border: '1px solid #2a2a2a', borderRadius: 6, fontSize: 12, color: '#e8e8e8', boxShadow: '0 4px 16px rgba(0,0,0,0.6)' };

const Sales = () => {
    const [selectedOutlet, setSelectedOutlet] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [selectedPeriod, setSelectedPeriod] = useState('30');

    const { data: outletsData } = useQuery({
        queryKey: ['outlets'],
        queryFn: () => api.get('/api/v1/outlets').then(r => r.data.data || []),
    });

    const { data: salesData, isLoading: salesLoading } = useQuery({
        queryKey: ['sales', selectedOutlet, selectedCategory, selectedPeriod],
        queryFn: () => {
            const params = new URLSearchParams();
            if (selectedOutlet) params.append('outlet_id', selectedOutlet);
            if (selectedCategory) params.append('category', selectedCategory);
            params.append('days', selectedPeriod);
            return api.get(`/api/v1/sales/trend?${params}`).then(r => r.data.data || []);
        },
    });

    const { data: topProductsData } = useQuery({
        queryKey: ['topProducts', selectedOutlet, selectedPeriod],
        queryFn: () => {
            const params = new URLSearchParams();
            if (selectedOutlet) params.append('outlet_id', selectedOutlet);
            params.append('days', selectedPeriod);
            return api.get(`/api/v1/sales/top-products?${params}`).then(r => r.data.data || []);
        },
    });

    const { data: outletPerformanceData } = useQuery({
        queryKey: ['outletPerformance', selectedPeriod],
        queryFn: () => {
            const params = new URLSearchParams();
            params.append('days', selectedPeriod);
            return api.get(`/api/v1/sales/outlet-performance?${params}`).then(r => r.data.data || []);
        },
    });

    const { data: categorySalesData } = useQuery({
        queryKey: ['categorySales', selectedOutlet, selectedPeriod],
        queryFn: () => {
            const params = new URLSearchParams();
            if (selectedOutlet) params.append('outlet_id', selectedOutlet);
            params.append('days', selectedPeriod);
            return api.get(`/api/v1/sales/category-breakdown?${params}`).then(r => r.data.data || []);
        },
    });

    const summaryStats = useMemo(() => {
        if (!salesData || salesData.length === 0) {
            return { totalRevenue: 0, avgDailySales: 0, totalTransactions: 0, conversionRate: 0 };
        }
        const totalRevenue = salesData.reduce((sum, item) => sum + (item.revenue || 0), 0);
        const avgDailySales = totalRevenue / salesData.length;
        const totalTransactions = salesData.reduce((sum, item) => sum + (item.transactions || 0), 0);
        return { totalRevenue, avgDailySales, totalTransactions };
    }, [salesData]);

    const categoriesList = useMemo(() => {
        if (!topProductsData) return [];
        return [...new Set(topProductsData.map(p => p.category))].filter(Boolean);
    }, [topProductsData]);

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);
    };

    return (
        <div className="sales-container">
            <div className="sales-header-inner">
                <div>
                    <p className="page-subtitle">Track your sales performance across outlets</p>
                </div>
            </div>

            <div className="sales-filters">
                <select value={selectedOutlet} onChange={(e) => setSelectedOutlet(e.target.value)}>
                    <option value="">All Outlets</option>
                    {outletsData?.map(outlet => (
                        <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                    ))}
                </select>
                <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
                    <option value="">All Categories</option>
                    {categoriesList.map(category => (
                        <option key={category} value={category}>{category}</option>
                    ))}
                </select>
                <select value={selectedPeriod} onChange={(e) => setSelectedPeriod(e.target.value)}>
                    <option value="7">Last 7 Days</option>
                    <option value="14">Last 14 Days</option>
                    <option value="30">Last 30 Days</option>
                    <option value="90">Last 90 Days</option>
                </select>
            </div>

            {/* Stats — terminal metric grid */}
            <div className="terminal-grid">
                <div className="terminal-metric span-2" style={{ borderLeft: '3px solid #f59e0b' }}>
                    <div className="terminal-label">Total Revenue</div>
                    <div className="terminal-value">{formatCurrency(summaryStats.totalRevenue)}</div>
                    <span style={{ fontSize: 11, color: '#525252' }}>Last {selectedPeriod} days</span>
                </div>
                <div className="terminal-metric">
                    <div className="terminal-label">Avg Daily Sales</div>
                    <div className="terminal-value">{formatCurrency(summaryStats.avgDailySales)}</div>
                    <span style={{ fontSize: 11, color: '#525252' }}>Per day average</span>
                </div>
                <div className="terminal-metric">
                    <div className="terminal-label">Total Transactions</div>
                    <div className="terminal-value">{(summaryStats.totalTransactions || 0).toLocaleString()}</div>
                    <span style={{ fontSize: 11, color: '#525252' }}>Number of orders</span>
                </div>
            </div>

            {/* Sales Trend */}
            <div className="terminal-section" style={{ borderLeft: '3px solid #f59e0b' }}>
                <div className="terminal-title">Sales Trend</div>
                <div style={{ marginTop: 12 }}>
                    <ResponsiveContainer width="100%" height={260}>
                        <AreaChart data={salesData || []}>
                            <defs>
                                <linearGradient id="salesRevenue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                            <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#525252' }} stroke="#525252" tickFormatter={(d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                            <YAxis tick={{ fontSize: 11, fill: '#525252' }} stroke="#525252" tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                            <Tooltip formatter={(v) => formatCurrency(v)} labelFormatter={(l) => new Date(l).toLocaleDateString()} contentStyle={tooltipStyle} />
                            <Area type="monotone" dataKey="revenue" stroke="#f59e0b" fillOpacity={1} fill="url(#salesRevenue)" strokeWidth={1.5} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Two-col: Products + Outlets */}
            <div className="terminal-two">
                <div className="terminal-section" style={{ borderLeft: '3px solid #f59e0b' }}>
                    <div className="terminal-title">Top Products</div>
                    <div className="products-table" style={{ marginTop: 12 }}>
                        <div className="table-header">
                            <div>Product</div>
                            <div>Sales</div>
                            <div>Revenue</div>
                        </div>
                        {(topProductsData || []).slice(0, 8).map((product, idx) => (
                            <div key={idx} className="table-row">
                                <div>
                                    <div className="product-name">{product.name}</div>
                                    <div className="product-category">{product.category}</div>
                                </div>
                                <div>{(product.quantity || 0).toLocaleString()} units</div>
                                <div>{formatCurrency(product.revenue)}</div>
                            </div>
                        ))}
                        {(!topProductsData || topProductsData.length === 0) && (
                            <div className="table-empty">No product data</div>
                        )}
                    </div>
                </div>

                <div className="terminal-section" style={{ borderLeft: '3px solid #f59e0b' }}>
                    <div className="terminal-title">Outlet Performance</div>
                    <div className="outlets-list" style={{ marginTop: 12 }}>
                        {(outletPerformanceData || []).map((outlet, idx) => {
                            const maxRevenue = Math.max(...(outletPerformanceData || []).map(o => o.revenue || 0)) || 1;
                            return (
                                <div key={idx} className="outlet-item">
                                    <div className="outlet-header">
                                        <div className="outlet-name">{outlet.name}</div>
                                        <div className="outlet-revenue">{formatCurrency(outlet.revenue)}</div>
                                    </div>
                                    <div className="outlet-bar-container">
                                        <div className="outlet-bar" style={{ width: `${((outlet.revenue || 0) / maxRevenue) * 100}%`, background: CHART_COLORS[idx % CHART_COLORS.length] }} />
                                    </div>
                                    <div className="outlet-stats">
                                        <span>↑ {outlet.growth}%</span>
                                        <span>{(outlet.transactions || 0).toLocaleString()} txn</span>
                                    </div>
                                </div>
                            );
                        })}
                        {(!outletPerformanceData || outletPerformanceData.length === 0) && (
                            <div className="outlets-empty">No outlet data</div>
                        )}
                    </div>
                </div>
            </div>

            {/* Category Breakdown */}
            <div className="terminal-section" style={{ borderLeft: '3px solid #f59e0b' }}>
                <div className="terminal-title">Category Breakdown</div>
                <div className="category-breakdown" style={{ marginTop: 12 }}>
                    <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                            <Pie data={categorySalesData || []} cx="50%" cy="50%" labelLine={false} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} outerRadius={80} dataKey="revenue">
                                {(categorySalesData || []).map((_, index) => (
                                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip formatter={(value) => formatCurrency(value)} contentStyle={tooltipStyle} />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="category-list">
                        {(categorySalesData || []).map((category, idx) => (
                            <div key={idx} className="category-item">
                                <div className="category-dot" style={{ background: CHART_COLORS[idx % CHART_COLORS.length] }} />
                                <div className="category-info">
                                    <div className="category-name">{category.name}</div>
                                    <div className="category-value">{formatCurrency(category.revenue)}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sales;
