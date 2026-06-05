import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp, Calendar, Store, Package } from 'lucide-react';
import api from '../services/api';
import '../styles/sales.css';

const Sales = () => {
    const [selectedOutlet, setSelectedOutlet] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [selectedPeriod, setSelectedPeriod] = useState('30');

    // Queries
    const { data: outletsData } = useQuery({
        queryKey: ['outlets'],
        queryFn: () => api.get('/api/v1/outlets').then(r => r.data.data || []),
        staleTime: 30000
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
        staleTime: 30000
    });

    const { data: topProductsData } = useQuery({
        queryKey: ['topProducts', selectedOutlet, selectedPeriod],
        queryFn: () => {
            const params = new URLSearchParams();
            if (selectedOutlet) params.append('outlet_id', selectedOutlet);
            params.append('days', selectedPeriod);
            return api.get(`/api/v1/sales/top-products?${params}`).then(r => r.data.data || []);
        },
        staleTime: 30000
    });

    const { data: outletPerformanceData } = useQuery({
        queryKey: ['outletPerformance', selectedPeriod],
        queryFn: () => {
            const params = new URLSearchParams();
            params.append('days', selectedPeriod);
            return api.get(`/api/v1/sales/outlet-performance?${params}`).then(r => r.data.data || []);
        },
        staleTime: 30000
    });

    const { data: categorySalesData } = useQuery({
        queryKey: ['categorySales', selectedOutlet, selectedPeriod],
        queryFn: () => {
            const params = new URLSearchParams();
            if (selectedOutlet) params.append('outlet_id', selectedOutlet);
            params.append('days', selectedPeriod);
            return api.get(`/api/v1/sales/category-breakdown?${params}`).then(r => r.data.data || []);
        },
        staleTime: 30000
    });

    // Calculate summary stats
    const summaryStats = useMemo(() => {
        if (!salesData || salesData.length === 0) {
            return { totalRevenue: 0, avgDailySales: 0, totalTransactions: 0, conversionRate: 0 };
        }
        const totalRevenue = salesData.reduce((sum, item) => sum + (item.revenue || 0), 0);
        const avgDailySales = totalRevenue / salesData.length;
        const totalTransactions = salesData.reduce((sum, item) => sum + (item.transactions || 0), 0);
        const conversionRate = salesData.length > 0 ? (totalTransactions / (salesData.length * 100)) * 100 : 0;
        return { totalRevenue, avgDailySales, totalTransactions, conversionRate };
    }, [salesData]);

    // Get unique categories
    const categoriesList = useMemo(() => {
        if (!topProductsData) return [];
        const categories = [...new Set(topProductsData.map(p => p.category))].filter(Boolean);
        return categories;
    }, [topProductsData]);

    // Format currency
    const formatCurrency = (value) => {
        // eslint-disable-next-line no-undef
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(value || 0);
    };

    // Skeleton loader
    if (salesLoading) {
        return (
            <div className="sales-container">
                <div className="sales-header">
                    <h1 className="sales-title">Sales & Revenue</h1>
                </div>
                <div className="sales-filters">
                    <div className="skeleton-input"></div>
                    <div className="skeleton-input"></div>
                    <div className="skeleton-input"></div>
                </div>
                <div className="skeleton-cards"></div>
                <div className="skeleton-chart"></div>
            </div>
        );
    }

    return (
        <div className="sales-container">
            {/* Header */}
            <div className="sales-header">
                <div className="sales-title-group">
                    <h1 className="sales-title">Sales & Revenue</h1>
                    <TrendingUp size={24} className="sales-icon" />
                </div>
            </div>

            {/* Filters */}
            <div className="sales-filters">
                <select value={selectedOutlet} onChange={(e) => setSelectedOutlet(e.target.value)} className="filter-select">
                    <option value="">All Outlets</option>
                    {outletsData?.map(outlet => (
                        <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                    ))}
                </select>
                <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)} className="filter-select">
                    <option value="">All Categories</option>
                    {categoriesList.map(category => (
                        <option key={category} value={category}>{category}</option>
                    ))}
                </select>
                <select value={selectedPeriod} onChange={(e) => setSelectedPeriod(e.target.value)} className="filter-select">
                    <option value="7">Last 7 Days</option>
                    <option value="14">Last 14 Days</option>
                    <option value="30">Last 30 Days</option>
                    <option value="90">Last 90 Days</option>
                </select>
            </div>

            {/* Summary Stats */}
            <div className="sales-stats">
                <div className="stat-card">
                    <div className="stat-label">Total Revenue</div>
                    <div className="stat-value">{formatCurrency(summaryStats.totalRevenue)}</div>
                    <div className="stat-subtext">Last {selectedPeriod} days</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Avg Daily Sales</div>
                    <div className="stat-value">{formatCurrency(summaryStats.avgDailySales)}</div>
                    <div className="stat-subtext">Per day average</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Total Transactions</div>
                    <div className="stat-value">{(summaryStats.totalTransactions || 0).toLocaleString()}</div>
                    <div className="stat-subtext">Number of orders</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Avg Order Value</div>
                    <div className="stat-value">
                        {formatCurrency(summaryStats.totalTransactions > 0 ? summaryStats.totalRevenue / summaryStats.totalTransactions : 0)}
                    </div>
                    <div className="stat-subtext">Per transaction</div>
                </div>
            </div>

            {/* Sales Trend Chart */}
            <div className="chart-card">
                <h2 className="chart-title">Sales Trend</h2>
                <div className="chart-container">
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={salesData || []}>
                            <defs>
                                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                            <XAxis 
                                dataKey="date" 
                                tick={{ fontSize: 12 }} 
                                stroke="#6B7280"
                                tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            />
                            <YAxis 
                                tick={{ fontSize: 12 }} 
                                stroke="#6B7280"
                                tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`}
                            />
                            <Tooltip 
                                formatter={(value) => formatCurrency(value)}
                                labelFormatter={(label) => new Date(label).toLocaleDateString()}
                                contentStyle={{ backgroundColor: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                            />
                            <Area 
                                type="monotone" 
                                dataKey="revenue" 
                                stroke="#3B82F6" 
                                fillOpacity={1} 
                                fill="url(#colorRevenue)" 
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Top Products & Outlet Performance */}
            <div className="two-column-grid">
                {/* Top Products */}
                <div className="chart-card">
                    <h2 className="chart-title">Top Products</h2>
                    <div className="products-table">
                        <div className="table-header">
                            <div className="table-cell">Product</div>
                            <div className="table-cell">Sales</div>
                            <div className="table-cell">Revenue</div>
                        </div>
                        {(topProductsData || []).slice(0, 8).map((product, idx) => (
                            <div key={idx} className="table-row">
                                <div className="table-cell">
                                    <div className="product-name">{product.name}</div>
                                    <div className="product-category">{product.category}</div>
                                </div>
                                <div className="table-cell">{(product.quantity || 0).toLocaleString()} units</div>
                                <div className="table-cell">{formatCurrency(product.revenue)}</div>
                            </div>
                        ))}
                        {(!topProductsData || topProductsData.length === 0) && (
                            <div className="table-empty">No product data</div>
                        )}
                    </div>
                </div>

                {/* Outlet Performance */}
                <div className="chart-card">
                    <h2 className="chart-title">Outlet Performance</h2>
                    <div className="outlets-list">
                        {(outletPerformanceData || []).map((outlet, idx) => (
                            <div key={idx} className="outlet-item">
                                <div className="outlet-header">
                                    <div className="outlet-name">{outlet.name}</div>
                                    <div className="outlet-revenue">{formatCurrency(outlet.revenue)}</div>
                                </div>
                                <div className="outlet-bar-container">
                                    <div 
                                        className="outlet-bar"
                                        style={{
                                            width: `${((outlet.revenue || 0) / (Math.max(...(outletPerformanceData || []).map(o => o.revenue || 0)) || 1)) * 100}%`,
                                            backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#6D28D9', '#EC4899'][idx % 6]
                                        }}
                                    ></div>
                                </div>
                                <div className="outlet-stats">
                                    <span className="outlet-stat">↑ {outlet.growth}%</span>
                                    <span className="outlet-stat">{(outlet.transactions || 0).toLocaleString()} txn</span>
                                </div>
                            </div>
                        ))}
                        {(!outletPerformanceData || outletPerformanceData.length === 0) && (
                            <div className="outlets-empty">No outlet data</div>
                        )}
                    </div>
                </div>
            </div>

            {/* Category Breakdown */}
            <div className="chart-card">
                <h2 className="chart-title">Category Breakdown</h2>
                <div className="category-breakdown">
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie
                                    data={categorySalesData || []}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="revenue"
                                >
                                    {(categorySalesData || []).map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#6D28D9', '#EC4899'][index % 6]} />
                                    ))}
                                </Pie>
                                <Tooltip formatter={(value) => formatCurrency(value)} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="category-list">
                        {(categorySalesData || []).map((category, idx) => (
                            <div key={idx} className="category-item">
                                <div className="category-dot" style={{ backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#6D28D9', '#EC4899'][idx % 6] }}></div>
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
