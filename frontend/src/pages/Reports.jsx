import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Download, Calendar, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '../utils/api';
import { useToast } from '../contexts/ToastContext';
import DataTable from '../components/ui/DataTable';
import StatCard from '../components/StatCard';

const Reports = () => {
    const { showToast } = useToast();
    
    // Sales Report State
    const [salesDateFrom, setSalesDateFrom] = useState(() => {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        return d.toISOString().split('T')[0];
    });
    const [salesDateTo, setSalesDateTo] = useState(() => new Date().toISOString().split('T')[0]);
    const [salesOutlet, setSalesOutlet] = useState('');
    
    // Inventory Report State
    const [inventoryDate, setInventoryDate] = useState(() => new Date().toISOString().split('T')[0]);
    const [inventoryOutlet, setInventoryOutlet] = useState('');
    
    // GST Report State
    const [gstMonth, setGstMonth] = useState(new Date().getMonth() + 1);
    const [gstYear, setGstYear] = useState(new Date().getFullYear());
    const [gstOutlet, setGstOutlet] = useState('');
    
    // Performance Report State
    const [performancePeriod, setPerformancePeriod] = useState('this-month');
    
    // Active Tab
    const [activeTab, setActiveTab] = useState('sales');

    // API Queries
    const { data: outletsData = [] } = useQuery({
        queryKey: ['outlets'],
        queryFn: async () => {
            const response = await api.get('/api/v1/outlets');
            return response.data.data || [];
        },
        staleTime: 10 * 60 * 1000
    });

    const { data: salesData } = useQuery({
        queryKey: ['sales-report', salesDateFrom, salesDateTo, salesOutlet],
        queryFn: async () => {
            const params = new URLSearchParams();
            params.append('from', salesDateFrom);
            params.append('to', salesDateTo);
            if (salesOutlet) params.append('outlet_id', salesOutlet);
            const response = await api.get(`/api/v1/sales/report?${params}`);
            return response.data.data || {};
        },
        enabled: !!salesDateFrom && !!salesDateTo && activeTab === 'sales',
        staleTime: 5 * 60 * 1000
    });

    const { data: inventoryData } = useQuery({
        queryKey: ['inventory-report', inventoryDate, inventoryOutlet],
        queryFn: async () => {
            const params = new URLSearchParams();
            params.append('date', inventoryDate);
            if (inventoryOutlet) params.append('outlet_id', inventoryOutlet);
            const response = await api.get(`/api/v1/inventory/report?${params}`);
            return response.data.data || {};
        },
        enabled: !!inventoryDate && activeTab === 'inventory',
        staleTime: 5 * 60 * 1000
    });

    const { data: gstr1Data } = useQuery({
        queryKey: ['gstr1-report', gstMonth, gstYear, gstOutlet],
        queryFn: async () => {
            const params = new URLSearchParams();
            params.append('month', gstMonth);
            params.append('year', gstYear);
            if (gstOutlet) params.append('outlet_id', gstOutlet);
            const response = await api.get(`/api/v1/gst/gstr1?${params}`);
            return response.data.data || {};
        },
        enabled: activeTab === 'gst',
        staleTime: 10 * 60 * 1000
    });

    const { data: gstr3bData } = useQuery({
        queryKey: ['gstr3b-report', gstMonth, gstYear, gstOutlet],
        queryFn: async () => {
            const params = new URLSearchParams();
            params.append('month', gstMonth);
            params.append('year', gstYear);
            if (gstOutlet) params.append('outlet_id', gstOutlet);
            const response = await api.get(`/api/v1/gst/gstr3b?${params}`);
            return response.data.data || {};
        },
        enabled: activeTab === 'gst',
        staleTime: 10 * 60 * 1000
    });

    const { data: performanceData } = useQuery({
        queryKey: ['performance-report', performancePeriod],
        queryFn: async () => {
            const params = new URLSearchParams();
            params.append('period', performancePeriod);
            const response = await api.get(`/api/v1/analytics/performance?${params}`);
            return response.data.data || {};
        },
        enabled: activeTab === 'performance',
        staleTime: 10 * 60 * 1000
    });

    const { data: modelPerformanceData } = useQuery({
        queryKey: ['model-performance', performancePeriod],
        queryFn: async () => {
            const response = await api.get('/api/v1/analytics/model-performance');
            return response.data.data || {};
        },
        enabled: activeTab === 'performance',
        staleTime: 10 * 60 * 1000
    });

    // Download handlers
    const downloadCSV = (data, filename) => {
        if (!data || data.length === 0) {
            showToast('No data to export', 'warning');
            return;
        }
        const headers = Object.keys(data[0]);
        const csv = [
            headers.join(','),
            ...data.map(row => headers.map(h => {
                const val = row[h];
                return typeof val === 'string' && val.includes(',') ? `"${val}"` : val;
            }).join(','))
        ].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        showToast('Report exported successfully', 'success');
    };

    const handleDownloadSalesCSV = () => {
        try {
            downloadCSV(salesData?.daily_summary || [], `sales-report-${salesDateFrom}-to-${salesDateTo}.csv`);
        } catch (error) {
            showToast('Failed to download report', 'error');
        }
    };

    const handleDownloadInventoryCSV = () => {
        try {
            downloadCSV(inventoryData?.products || [], `inventory-report-${inventoryDate}.csv`);
        } catch (error) {
            showToast('Failed to download report', 'error');
        }
    };

    const handleDownloadGSTCSV = () => {
        try {
            const data = gstr1Data?.by_rate || gstr3bData?.by_rate || [];
            downloadCSV(data, `gst-report-${gstMonth}-${gstYear}.csv`);
        } catch (error) {
            showToast('Failed to download report', 'error');
        }
    };

    // Process data for charts
    const chartData = useMemo(() => {
        if (!salesData?.daily_summary) return [];
        return salesData.daily_summary.map(item => ({
            date: new Date(item.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
            revenue: item.revenue || 0
        }));
    }, [salesData]);

    // Format currency
    const formatCurrency = (value) => {
        if (!value) return '₹0';
        // eslint-disable-next-line no-undef
        return `₹${new Intl.NumberFormat('en-IN').format(Math.round(value))}`;
    };

    return (
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
            {/* Header */}
            <div style={{ marginBottom: '32px' }}>
                <h1 style={{ fontSize: '28px', fontWeight: '600', marginBottom: '8px', color: '#1a1a1a' }}>
                    Reports & Analytics
                </h1>
                <p style={{ color: '#666' }}>Comprehensive business intelligence and metrics</p>
            </div>

            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid #e0e0e0' }}>
                {['sales', 'inventory', 'gst', 'performance'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        style={{
                            padding: '12px 16px',
                            border: 'none',
                            borderBottom: activeTab === tab ? '2px solid #d97e68' : 'none',
                            background: 'none',
                            color: activeTab === tab ? '#d97e68' : '#666',
                            cursor: 'pointer',
                            fontWeight: activeTab === tab ? '600' : '500',
                            fontSize: '14px',
                            transition: 'all 0.2s'
                        }}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)} Reports
                    </button>
                ))}
            </div>

            {/* Sales Reports Tab */}
            {activeTab === 'sales' && (
                <div>
                    {/* Controls */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                                <Calendar size={14} style={{ display: 'inline', marginRight: '4px' }} />
                                From Date
                            </label>
                            <input
                                type="date"
                                value={salesDateFrom}
                                onChange={(e) => setSalesDateFrom(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #ddd',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                                <Calendar size={14} style={{ display: 'inline', marginRight: '4px' }} />
                                To Date
                            </label>
                            <input
                                type="date"
                                value={salesDateTo}
                                onChange={(e) => setSalesDateTo(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #ddd',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                                Outlet
                            </label>
                            <select
                                value={salesOutlet}
                                onChange={(e) => setSalesOutlet(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #ddd',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            >
                                <option value="">All Outlets</option>
                                {outletsData.map(outlet => (
                                    <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                                ))}
                            </select>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                            <button
                                onClick={handleDownloadSalesCSV}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    background: '#d97e68',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '14px',
                                    fontWeight: '600',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '6px'
                                }}
                            >
                                <Download size={16} />
                                Export CSV
                            </button>
                        </div>
                    </div>

                    {/* Summary Stats */}
                    {salesData && (
                        <>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                                <StatCard
                                    title="Total Revenue"
                                    value={formatCurrency(salesData.total_revenue)}
                                    change="+12.5%"
                                />
                                <StatCard
                                    title="Total Orders"
                                    value={salesData.total_orders || 0}
                                    change="+8.2%"
                                />
                                <StatCard
                                    title="Average Order Value"
                                    value={formatCurrency(salesData.avg_order_value)}
                                    change="+4.1%"
                                />
                                <StatCard
                                    title="Conversion Rate"
                                    value={`${salesData.conversion_rate || 0}%`}
                                    change="+2.3%"
                                />
                            </div>

                            {/* Chart */}
                            {chartData.length > 0 && (
                                <div style={{
                                    background: 'white',
                                    border: '1px solid #e0e0e0',
                                    borderRadius: '8px',
                                    padding: '20px',
                                    marginBottom: '24px'
                                }}>
                                    <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                                        Revenue Trend
                                    </h3>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <LineChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="date" />
                                            <YAxis />
                                            <Tooltip />
                                            <Line type="monotone" dataKey="revenue" stroke="#d97e68" strokeWidth={2} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            )}

                            {/* Daily Summary Table */}
                            {salesData.daily_summary && salesData.daily_summary.length > 0 ? (
                                <div style={{
                                    background: 'white',
                                    border: '1px solid #e0e0e0',
                                    borderRadius: '8px',
                                    padding: '20px'
                                }}>
                                    <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                                        Daily Summary
                                    </h3>
                                    <DataTable
                                        columns={['date', 'revenue', 'orders', 'avg_order_value']}
                                        data={salesData.daily_summary}
                                        columnLabels={{ date: 'Date', revenue: 'Revenue', orders: 'Orders', avg_order_value: 'Avg Order Value' }}
                                    />
                                </div>
                            ) : (
                                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                                    No data available for the selected period
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* Inventory Reports Tab */}
            {activeTab === 'inventory' && (
                <div>
                    {/* Controls */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                                <Calendar size={14} style={{ display: 'inline', marginRight: '4px' }} />
                                Snapshot Date
                            </label>
                            <input
                                type="date"
                                value={inventoryDate}
                                onChange={(e) => setInventoryDate(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #ddd',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                                Outlet
                            </label>
                            <select
                                value={inventoryOutlet}
                                onChange={(e) => setInventoryOutlet(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #ddd',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            >
                                <option value="">All Outlets</option>
                                {outletsData.map(outlet => (
                                    <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                                ))}
                            </select>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                            <button
                                onClick={handleDownloadInventoryCSV}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    background: '#d97e68',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '14px',
                                    fontWeight: '600',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '6px'
                                }}
                            >
                                <Download size={16} />
                                Export CSV
                            </button>
                        </div>
                    </div>

                    {/* Summary Stats */}
                    {inventoryData && (
                        <>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                                <StatCard
                                    title="Total Stock Value"
                                    value={formatCurrency(inventoryData.total_stock_value)}
                                />
                                <StatCard
                                    title="Total Items"
                                    value={inventoryData.total_items || 0}
                                />
                                <StatCard
                                    title="Low Stock Items"
                                    value={inventoryData.low_stock_count || 0}
                                />
                                <StatCard
                                    title="Stock Turnover Ratio"
                                    value={`${(inventoryData.turnover_ratio || 0).toFixed(2)}x`}
                                />
                            </div>

                            {/* Products Table */}
                            {inventoryData.products && inventoryData.products.length > 0 ? (
                                <div style={{
                                    background: 'white',
                                    border: '1px solid #e0e0e0',
                                    borderRadius: '8px',
                                    padding: '20px'
                                }}>
                                    <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                                        Product Inventory
                                    </h3>
                                    <DataTable
                                        columns={['sku', 'name', 'current_stock', 'min_level', 'max_level']}
                                        data={inventoryData.products.map(p => ({
                                            ...p,
                                            highlight: p.current_stock < p.min_level
                                        }))}
                                        columnLabels={{
                                            sku: 'SKU',
                                            name: 'Product Name',
                                            current_stock: 'Current Stock',
                                            min_level: 'Min Level',
                                            max_level: 'Max Level'
                                        }}
                                    />
                                </div>
                            ) : (
                                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                                    No data available for the selected period
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* GST Reports Tab */}
            {activeTab === 'gst' && (
                <div>
                    {/* Controls */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                                Month
                            </label>
                            <select
                                value={gstMonth}
                                onChange={(e) => setGstMonth(parseInt(e.target.value))}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #ddd',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            >
                                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(m => (
                                    <option key={m} value={m}>
                                        {new Date(2024, m - 1).toLocaleString('en-IN', { month: 'long' })}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                                Year
                            </label>
                            <select
                                value={gstYear}
                                onChange={(e) => setGstYear(parseInt(e.target.value))}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #ddd',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            >
                                {[2024, 2023, 2022, 2021].map(y => (
                                    <option key={y} value={y}>{y}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                                Outlet
                            </label>
                            <select
                                value={gstOutlet}
                                onChange={(e) => setGstOutlet(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #ddd',
                                    borderRadius: '6px',
                                    fontSize: '14px'
                                }}
                            >
                                <option value="">All Outlets</option>
                                {outletsData.map(outlet => (
                                    <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                                ))}
                            </select>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                            <button
                                onClick={handleDownloadGSTCSV}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    background: '#d97e68',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '14px',
                                    fontWeight: '600',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '6px'
                                }}
                            >
                                <Download size={16} />
                                Export CSV
                            </button>
                        </div>
                    </div>

                    {/* GSTR-1 Section */}
                    {gstr1Data && (
                        <div style={{
                            background: 'white',
                            border: '1px solid #e0e0e0',
                            borderRadius: '8px',
                            padding: '20px',
                            marginBottom: '24px'
                        }}>
                            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                                GSTR-1 (Outward Supplies)
                            </h3>
                            
                            {gstr1Data.summary ? (
                                <>
                                    {/* Summary Cards */}
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                                        <StatCard
                                            title="Taxable Value"
                                            value={formatCurrency(gstr1Data.summary.total_taxable_value)}
                                        />
                                        <StatCard
                                            title="Total CGST"
                                            value={formatCurrency(gstr1Data.summary.total_cgst)}
                                        />
                                        <StatCard
                                            title="Total SGST"
                                            value={formatCurrency(gstr1Data.summary.total_sgst)}
                                        />
                                        <StatCard
                                            title="Total IGST"
                                            value={formatCurrency(gstr1Data.summary.total_igst)}
                                        />
                                    </div>

                                    {/* Rate-wise Table */}
                                    {gstr1Data.by_rate && gstr1Data.by_rate.length > 0 && (
                                        <DataTable
                                            columns={['rate', 'taxable_value', 'cgst', 'sgst', 'igst']}
                                            data={gstr1Data.by_rate}
                                            columnLabels={{
                                                rate: 'GST Rate',
                                                taxable_value: 'Taxable Value',
                                                cgst: 'CGST',
                                                sgst: 'SGST',
                                                igst: 'IGST'
                                            }}
                                        />
                                    )}
                                </>
                            ) : (
                                <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                    No GSTR-1 data available
                                </div>
                            )}
                        </div>
                    )}

                    {/* GSTR-3B Section */}
                    {gstr3bData && (
                        <div style={{
                            background: 'white',
                            border: '1px solid #e0e0e0',
                            borderRadius: '8px',
                            padding: '20px'
                        }}>
                            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                                GSTR-3B (Monthly Return)
                            </h3>
                            
                            {gstr3bData.summary ? (
                                <>
                                    {/* Summary Cards */}
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                                        <StatCard
                                            title="Output Tax Liability"
                                            value={formatCurrency(gstr3bData.summary.output_tax_liability)}
                                        />
                                        <StatCard
                                            title="Input Tax Credit"
                                            value={formatCurrency(gstr3bData.summary.input_tax_credit)}
                                        />
                                        <StatCard
                                            title="Net GST Payable"
                                            value={formatCurrency(gstr3bData.summary.net_gst_payable)}
                                        />
                                    </div>

                                    {/* Rate-wise Table */}
                                    {gstr3bData.by_rate && gstr3bData.by_rate.length > 0 && (
                                        <DataTable
                                            columns={['rate', 'output_tax', 'input_tax_credit', 'net_payable']}
                                            data={gstr3bData.by_rate}
                                            columnLabels={{
                                                rate: 'GST Rate',
                                                output_tax: 'Output Tax',
                                                input_tax_credit: 'ITC (50%)',
                                                net_payable: 'Net Payable'
                                            }}
                                        />
                                    )}
                                </>
                            ) : (
                                <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                    No GSTR-3B data available
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Performance Reports Tab */}
            {activeTab === 'performance' && (
                <div>
                    {/* Controls */}
                    <div style={{ marginBottom: '24px' }}>
                        <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#666' }}>
                            Period
                        </label>
                        <select
                            value={performancePeriod}
                            onChange={(e) => setPerformancePeriod(e.target.value)}
                            style={{
                                width: '200px',
                                padding: '8px 12px',
                                border: '1px solid #ddd',
                                borderRadius: '6px',
                                fontSize: '14px'
                            }}
                        >
                            <option value="this-month">This Month</option>
                            <option value="last-month">Last Month</option>
                            <option value="last-3-months">Last 3 Months</option>
                        </select>
                    </div>

                    {/* Outlet Performance */}
                    {performanceData && (
                        <>
                            <div style={{
                                background: 'white',
                                border: '1px solid #e0e0e0',
                                borderRadius: '8px',
                                padding: '20px',
                                marginBottom: '24px'
                            }}>
                                <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                                    Outlet Performance
                                </h3>
                                {performanceData.outlets && performanceData.outlets.length > 0 ? (
                                    <DataTable
                                        columns={['name', 'revenue', 'orders', 'avg_order_value', 'conversion_rate']}
                                        data={performanceData.outlets}
                                        columnLabels={{
                                            name: 'Outlet',
                                            revenue: 'Revenue',
                                            orders: 'Orders',
                                            avg_order_value: 'Avg Order Value',
                                            conversion_rate: 'Conversion Rate'
                                        }}
                                    />
                                ) : (
                                    <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                        No data available
                                    </div>
                                )}
                            </div>
                        </>
                    )}

                    {/* Model Performance */}
                    {modelPerformanceData && (
                        <div style={{
                            background: 'white',
                            border: '1px solid #e0e0e0',
                            borderRadius: '8px',
                            padding: '20px'
                        }}>
                            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                                Forecasting Model Performance
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
                                <StatCard
                                    title="MAE"
                                    value={`${(modelPerformanceData.mae || 0).toFixed(2)}`}
                                />
                                <StatCard
                                    title="MAPE"
                                    value={`${(modelPerformanceData.mape || 0).toFixed(2)}%`}
                                />
                                <StatCard
                                    title="RMSE"
                                    value={`${(modelPerformanceData.rmse || 0).toFixed(2)}`}
                                />
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Reports;
