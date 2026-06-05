import React, { useState, useEffect } from 'react';
import {
    Plus, List, TrendingUp, AlertCircle, CheckCircle,
    Zap, FileText, Clock, DollarSign, Package, ArrowRight,
    RefreshCw, Search, Filter, ChevronDown, ChevronUp
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

const POSIntegration = () => {
    const { addToast } = useToast();
    
    // State Management
    const [activeTab, setActiveTab] = useState('pending'); // pending, metrics, convert, history
    const [loading, setLoading] = useState(false);
    const [pendingSales, setPendingSales] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [selectedTransactions, setSelectedTransactions] = useState([]);
    const [conversionResults, setConversionResults] = useState(null);
    const [expandedTransaction, setExpandedTransaction] = useState(null);
    const [groupByCustomer, setGroupByCustomer] = useState(true);
    const [filterCustomerId, setFilterCustomerId] = useState('');
    const [lookbackDays, setLookbackDays] = useState(30);
    
    // Fetch pending sales
    useEffect(() => {
        fetchPendingSales();
        fetchMetrics();
    }, [lookbackDays, filterCustomerId]);
    
    const fetchPendingSales = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                days: lookbackDays,
                ...(filterCustomerId && { customer_id: filterCustomerId })
            });
            
            const response = await fetch(`/api/v1/invoicing/uninvoiced-sales?${params}`);
            const data = await response.json();
            
            if (data.success) {
                setPendingSales(data.data.transactions || []);
            }
        } catch (error) {
            addToast('Failed to fetch pending sales', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    const fetchMetrics = async () => {
        try {
            const response = await fetch(`/api/v1/invoicing/conversion-metrics?days=${lookbackDays}`);
            const data = await response.json();
            
            if (data.success) {
                setMetrics(data.data);
            }
        } catch (error) {
            console.error('Failed to fetch metrics:', error);
        }
    };
    
    const handleSelectTransaction = (transactionId) => {
        setSelectedTransactions(prev =>
            prev.includes(transactionId)
                ? prev.filter(id => id !== transactionId)
                : [...prev, transactionId]
        );
    };
    
    const handleSelectAll = () => {
        if (selectedTransactions.length === pendingSales.length) {
            setSelectedTransactions([]);
        } else {
            setSelectedTransactions(pendingSales.map(t => t.transaction_id));
        }
    };
    
    const convertSelectedToInvoices = async () => {
        if (selectedTransactions.length === 0) {
            addToast('Please select at least one transaction', 'warning');
            return;
        }
        
        setLoading(true);
        try {
            const response = await fetch('/api/v1/invoicing/bulk-sales-to-invoices', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    transaction_ids: selectedTransactions,
                    group_by_customer: groupByCustomer
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                setConversionResults(data.data);
                addToast(`Created ${data.data.successful} invoices`, 'success');
                setSelectedTransactions([]);
                fetchPendingSales();
                fetchMetrics();
                setActiveTab('history');
            } else {
                addToast(data.error || 'Conversion failed', 'error');
            }
        } catch (error) {
            addToast('Failed to convert sales to invoices', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    const autoInvoiceAllPending = async () => {
        if (!window.confirm('Auto-invoice all pending sales from the last 7 days?')) {
            return;
        }
        
        setLoading(true);
        try {
            const response = await fetch('/api/v1/invoicing/auto-invoice-pending-sales?days=7', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                addToast(`Auto-invoiced ${data.data.invoices_created} transactions`, 'success');
                setConversionResults(data.data);
                fetchPendingSales();
                fetchMetrics();
                setActiveTab('history');
            }
        } catch (error) {
            addToast('Auto-invoicing failed', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
            <div className="max-w-7xl mx-auto">
                
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <Zap className="w-8 h-8 text-blue-400" />
                        <h1 className="text-4xl font-bold text-white">POS Integration</h1>
                    </div>
                    <p className="text-gray-400">Convert point-of-sale transactions to formal invoices</p>
                </div>
                
                {/* Metrics Cards */}
                {metrics && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">Total Sales</p>
                                    <p className="text-3xl font-bold text-white">{metrics.total_sales}</p>
                                </div>
                                <Package className="w-8 h-8 text-blue-400" />
                            </div>
                            <p className="text-gray-500 text-xs">Last {lookbackDays} days</p>
                        </GlassCard>
                        
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">Uninvoiced</p>
                                    <p className="text-3xl font-bold text-orange-400">{metrics.uninvoiced_sales}</p>
                                </div>
                                <Clock className="w-8 h-8 text-orange-400" />
                            </div>
                            <p className="text-gray-500 text-xs">{metrics.uninvoiced_revenue_percent?.toFixed(1)}% of revenue</p>
                        </GlassCard>
                        
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">Conversion Rate</p>
                                    <p className="text-3xl font-bold text-green-400">{metrics.conversion_rate_percent?.toFixed(1)}%</p>
                                </div>
                                <TrendingUp className="w-8 h-8 text-green-400" />
                            </div>
                            <p className="text-gray-500 text-xs">{metrics.invoiced_sales} invoiced</p>
                        </GlassCard>
                        
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">Pending Revenue</p>
                                    <p className="text-2xl font-bold text-red-400">₹{metrics.uninvoiced_revenue?.toLocaleString()}</p>
                                </div>
                                <AlertCircle className="w-8 h-8 text-red-400" />
                            </div>
                            <p className="text-gray-500 text-xs">Needs invoicing</p>
                        </GlassCard>
                    </div>
                )}
                
                {/* Tab Navigation */}
                <div className="flex gap-2 mb-6 border-b border-slate-700">
                    {[
                        { id: 'pending', label: 'Pending Sales', icon: Clock },
                        { id: 'metrics', label: 'Metrics', icon: TrendingUp },
                        { id: 'history', label: 'History', icon: FileText }
                    ].map(tab => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`px-4 py-3 flex items-center gap-2 font-medium border-b-2 transition-all ${
                                    activeTab === tab.id
                                        ? 'border-blue-500 text-blue-400'
                                        : 'border-transparent text-gray-400 hover:text-white'
                                }`}
                            >
                                <Icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>
                
                {/* PENDING SALES TAB */}
                {activeTab === 'pending' && (
                    <div className="space-y-4">
                        {/* Filters & Actions */}
                        <GlassCard>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Lookback Period</label>
                                    <select
                                        value={lookbackDays}
                                        onChange={(e) => setLookbackDays(Number(e.target.value))}
                                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                    >
                                        <option value={7}>Last 7 days</option>
                                        <option value={14}>Last 14 days</option>
                                        <option value={30}>Last 30 days</option>
                                        <option value={90}>Last 90 days</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Customer ID (Optional)</label>
                                    <input
                                        type="text"
                                        placeholder="Filter by customer..."
                                        value={filterCustomerId}
                                        onChange={(e) => setFilterCustomerId(e.target.value)}
                                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-gray-500"
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Group Options</label>
                                    <label className="flex items-center gap-2 px-3 py-2 bg-slate-700 rounded cursor-pointer hover:bg-slate-600">
                                        <input
                                            type="checkbox"
                                            checked={groupByCustomer}
                                            onChange={(e) => setGroupByCustomer(e.target.checked)}
                                            className="rounded"
                                        />
                                        <span className="text-white text-sm">Group by Customer</span>
                                    </label>
                                </div>
                            </div>
                        </GlassCard>
                        
                        {/* Action Buttons */}
                        <div className="flex gap-3">
                            <GradientButton
                                onClick={convertSelectedToInvoices}
                                disabled={selectedTransactions.length === 0 || loading}
                                className="gap-2"
                            >
                                <FileText className="w-4 h-4" />
                                Convert Selected ({selectedTransactions.length})
                            </GradientButton>
                            
                            <GradientButton
                                onClick={autoInvoiceAllPending}
                                disabled={pendingSales.length === 0 || loading}
                                variant="outline"
                                className="gap-2"
                            >
                                <Zap className="w-4 h-4" />
                                Auto-Invoice All
                            </GradientButton>
                            
                            <GradientButton
                                onClick={fetchPendingSales}
                                disabled={loading}
                                variant="secondary"
                                className="gap-2"
                            >
                                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                                Refresh
                            </GradientButton>
                        </div>
                        
                        {/* Transactions List */}
                        <GlassCard className="overflow-hidden">
                            {pendingSales.length === 0 ? (
                                <div className="p-8 text-center">
                                    <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                                    <p className="text-gray-400">No pending sales found</p>
                                    <p className="text-sm text-gray-500 mt-2">All sales have been invoiced!</p>
                                </div>
                            ) : (
                                <div>
                                    {/* Select All */}
                                    <div className="border-b border-slate-700 p-4 flex items-center gap-3 bg-slate-800">
                                        <input
                                            type="checkbox"
                                            checked={selectedTransactions.length === pendingSales.length}
                                            onChange={handleSelectAll}
                                            className="rounded"
                                        />
                                        <span className="text-white font-medium">
                                            {selectedTransactions.length > 0
                                                ? `${selectedTransactions.length} selected`
                                                : 'Select all'}
                                        </span>
                                    </div>
                                    
                                    {/* Transaction Items */}
                                    {pendingSales.map(transaction => (
                                        <div key={transaction.transaction_id} className="border-b border-slate-700 last:border-b-0">
                                            <div className="p-4 hover:bg-slate-800/50 transition">
                                                <div className="flex items-start gap-4">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedTransactions.includes(transaction.transaction_id)}
                                                        onChange={() => handleSelectTransaction(transaction.transaction_id)}
                                                        className="rounded mt-1"
                                                    />
                                                    
                                                    <div className="flex-1 cursor-pointer" onClick={() =>
                                                        setExpandedTransaction(
                                                            expandedTransaction === transaction.transaction_id ? null : transaction.transaction_id
                                                        )
                                                    }>
                                                        <div className="flex items-center justify-between mb-2">
                                                            <div className="flex items-center gap-3">
                                                                <p className="font-mono text-blue-400">{transaction.transaction_id}</p>
                                                                <span className="text-xs bg-slate-700 px-2 py-1 rounded text-gray-300">
                                                                    {transaction.items.length} items
                                                                </span>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <p className="font-bold text-white">₹{transaction.total_amount.toLocaleString()}</p>
                                                                {expandedTransaction === transaction.transaction_id ? (
                                                                    <ChevronUp className="w-4 h-4 text-gray-400" />
                                                                ) : (
                                                                    <ChevronDown className="w-4 h-4 text-gray-400" />
                                                                )}
                                                            </div>
                                                        </div>
                                                        
                                                        <p className="text-sm text-gray-400">
                                                            Customer ID: {transaction.customer_id || 'N/A'} • 
                                                            {new Date(transaction.transaction_date).toLocaleDateString()}
                                                        </p>
                                                    </div>
                                                </div>
                                                
                                                {/* Expanded Details */}
                                                {expandedTransaction === transaction.transaction_id && (
                                                    <div className="mt-4 pt-4 border-t border-slate-700 ml-10">
                                                        <div className="space-y-2">
                                                            {transaction.items.map((item, idx) => (
                                                                <div key={idx} className="flex justify-between text-sm text-gray-300">
                                                                    <span>{item.quantity}x Item ID {item.product_id}</span>
                                                                    <span>₹{(item.quantity * item.unit_price).toLocaleString()}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </GlassCard>
                    </div>
                )}
                
                {/* METRICS TAB */}
                {activeTab === 'metrics' && metrics && (
                    <GlassCard>
                        <div className="grid grid-cols-2 gap-8">
                            <div>
                                <h3 className="text-lg font-bold text-white mb-4">Sales Volume</h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-400">Total Sales</span>
                                        <span className="font-bold text-white">{metrics.total_sales}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-400">Invoiced</span>
                                        <span className="font-bold text-green-400">{metrics.invoiced_sales}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-400">Pending</span>
                                        <span className="font-bold text-orange-400">{metrics.uninvoiced_sales}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div>
                                <h3 className="text-lg font-bold text-white mb-4">Revenue</h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-400">Total</span>
                                        <span className="font-bold text-white">₹{metrics.total_revenue.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-400">Invoiced</span>
                                        <span className="font-bold text-green-400">₹{metrics.invoiced_revenue.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-400">Pending</span>
                                        <span className="font-bold text-orange-400">₹{metrics.uninvoiced_revenue.toLocaleString()}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </GlassCard>
                )}
                
                {/* HISTORY TAB */}
                {activeTab === 'history' && conversionResults && (
                    <GlassCard>
                        <div className="space-y-6">
                            <div className="flex items-start gap-4 p-4 bg-green-900/20 border border-green-500/50 rounded-lg">
                                <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0 mt-1" />
                                <div>
                                    <h3 className="font-bold text-white mb-2">Conversion Complete</h3>
                                    <p className="text-gray-300 mb-3">{conversionResults.message}</p>
                                    <div className="grid grid-cols-3 gap-4 text-sm">
                                        <div>
                                            <p className="text-gray-400">Successful</p>
                                            <p className="text-2xl font-bold text-green-400">{conversionResults.invoices_created}</p>
                                        </div>
                                        <div>
                                            <p className="text-gray-400">Failed</p>
                                            <p className="text-2xl font-bold text-orange-400">{conversionResults.invoices_failed || 0}</p>
                                        </div>
                                        <div>
                                            <p className="text-gray-400">Total Amount</p>
                                            <p className="text-2xl font-bold text-blue-400">₹{conversionResults.total_amount.toLocaleString()}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            {conversionResults.invoices && conversionResults.invoices.length > 0 && (
                                <div>
                                    <h3 className="text-lg font-bold text-white mb-4">Created Invoices</h3>
                                    <div className="space-y-2 max-h-96 overflow-y-auto">
                                        {conversionResults.invoices.map((inv, idx) => (
                                            <div key={idx} className="p-3 bg-slate-800 rounded flex justify-between items-center">
                                                <div>
                                                    <p className="font-mono text-blue-400">{inv.invoice_number}</p>
                                                    <p className="text-sm text-gray-400">{inv.items_count} items</p>
                                                </div>
                                                <p className="font-bold text-white">₹{inv.total_amount.toLocaleString()}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </GlassCard>
                )}
            </div>
        </div>
    );
};

export default POSIntegration;
