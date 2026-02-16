import React, { useState, useEffect } from 'react';
import {
    Plus, List, TrendingUp, AlertCircle, CheckCircle, Clock,
    DollarSign, CreditCard, FileText, Trash2, Eye, RefreshCw,
    Download, Filter, ChevronDown, ChevronUp, Percent, Calendar
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

const BillManagement = () => {
    const { addToast } = useToast();
    
    // State Management
    const [activeTab, setActiveTab] = useState('bills'); // bills, pending, gst, analytics
    const [loading, setLoading] = useState(false);
    const [bills, setBills] = useState([]);
    const [pendingBills, setPendingBills] = useState([]);
    const [gstSummary, setGstSummary] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [dashboardMetrics, setDashboardMetrics] = useState(null);
    const [selectedBill, setSelectedBill] = useState(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [expandedBill, setExpandedBill] = useState(null);
    const [lookbackDays, setLookbackDays] = useState(90);
    const [filterSupplier, setFilterSupplier] = useState('');
    const [filterStatus, setFilterStatus] = useState('');
    
    // Form states
    const [formData, setFormData] = useState({
        billNumber: '',
        supplierId: '',
        billDate: new Date().toISOString().split('T')[0],
        dueDate: '',
        items: [{ category: '', description: '', quantity: 1, unitPrice: 0 }],
        notes: ''
    });
    
    // Fetch data
    useEffect(() => {
        fetchBills();
        fetchAnalytics();
        fetchDashboard();
    }, [lookbackDays, filterSupplier, filterStatus]);
    
    const fetchBills = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                days: lookbackDays,
                ...(filterSupplier && { supplier_id: filterSupplier }),
                ...(filterStatus && { status: filterStatus })
            });
            
            const response = await fetch(`/api/v1/bills?${params}`);
            const data = await response.json();
            
            if (data.success) {
                setBills(data.data.bills || []);
            }
        } catch (error) {
            addToast('Failed to fetch bills', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    const fetchAnalytics = async () => {
        try {
            const [gstRes, analyticsRes] = await Promise.all([
                fetch(`/api/v1/bills/analytics/gst-input-summary?days=${lookbackDays}`),
                fetch(`/api/v1/bills/analytics/vendor?days=${lookbackDays}`)
            ]);
            
            const gstData = await gstRes.json();
            const analyticsData = await analyticsRes.json();
            
            if (gstData.success) setGstSummary(gstData.data);
            if (analyticsData.success) setAnalytics(analyticsData.data);
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        }
    };
    
    const fetchDashboard = async () => {
        try {
            const response = await fetch(`/api/v1/bills/dashboard/summary?days=${lookbackDays}`);
            const data = await response.json();
            
            if (data.success) {
                setDashboardMetrics(data.data);
                setPendingBills([{ count: data.data.pending_bills_count }]); // Simplified
            }
        } catch (error) {
            console.error('Failed to fetch dashboard:', error);
        }
    };
    
    const handleCreateBill = async (e) => {
        e.preventDefault();
        
        if (!formData.billNumber || !formData.supplierId || formData.items.length === 0) {
            addToast('Please fill in all required fields', 'warning');
            return;
        }
        
        setLoading(true);
        try {
            const response = await fetch('/api/v1/bills/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bill_number: formData.billNumber,
                    supplier_id: parseInt(formData.supplierId),
                    bill_date: new Date(formData.billDate),
                    due_date: formData.dueDate ? new Date(formData.dueDate) : null,
                    items: formData.items.map(item => ({
                        category: item.category,
                        description: item.description,
                        quantity: parseInt(item.quantity),
                        unit_price: parseFloat(item.unitPrice)
                    })),
                    notes: formData.notes
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                addToast('Bill created successfully', 'success');
                setShowCreateForm(false);
                resetForm();
                fetchBills();
                fetchAnalytics();
            } else {
                addToast(data.error || 'Failed to create bill', 'error');
            }
        } catch (error) {
            addToast('Error creating bill', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    const handleRecordPayment = async (billId, amount) => {
        setLoading(true);
        try {
            const response = await fetch(`/api/v1/bills/${billId}/payment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount,
                    payment_date: new Date(),
                    payment_method: 'transfer',
                    notes: 'Payment recorded'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                addToast('Payment recorded', 'success');
                fetchBills();
                fetchAnalytics();
            }
        } catch (error) {
            addToast('Failed to record payment', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    const handleClaimGST = async (billId) => {
        setLoading(true);
        try {
            const response = await fetch(`/api/v1/bills/${billId}/claim-gst`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: null }) // Claim all
            });
            
            const data = await response.json();
            
            if (data.success) {
                addToast('GST claimed', 'success');
                fetchBills();
                fetchAnalytics();
            }
        } catch (error) {
            addToast('Failed to claim GST', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    const resetForm = () => {
        setFormData({
            billNumber: '',
            supplierId: '',
            billDate: new Date().toISOString().split('T')[0],
            dueDate: '',
            items: [{ category: '', description: '', quantity: 1, unitPrice: 0 }],
            notes: ''
        });
    };
    
    const addItemRow = () => {
        setFormData({
            ...formData,
            items: [...formData.items, { category: '', description: '', quantity: 1, unitPrice: 0 }]
        });
    };
    
    const removeItemRow = (index) => {
        setFormData({
            ...formData,
            items: formData.items.filter((_, i) => i !== index)
        });
    };
    
    const updateItem = (index, field, value) => {
        const newItems = [...formData.items];
        newItems[index][field] = value;
        setFormData({ ...formData, items: newItems });
    };
    
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
            <div className="max-w-7xl mx-auto">
                
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <FileText className="w-8 h-8 text-green-400" />
                        <h1 className="text-4xl font-bold text-white">Bill Management</h1>
                    </div>
                    <p className="text-gray-400">Manage vendor bills, payments, and GST input credits</p>
                </div>
                
                {/* Dashboard Metrics */}
                {dashboardMetrics && (
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">Total Bills</p>
                                    <p className="text-3xl font-bold text-white">{dashboardMetrics.bills_count}</p>
                                </div>
                                <FileText className="w-8 h-8 text-blue-400" />
                            </div>
                            <p className="text-gray-500 text-xs">Last {lookbackDays} days</p>
                        </GlassCard>
                        
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">Total Payable</p>
                                    <p className="text-2xl font-bold text-white">₹{dashboardMetrics.total_payable?.toLocaleString()}</p>
                                </div>
                                <DollarSign className="w-8 h-8 text-yellow-400" />
                            </div>
                            <p className="text-gray-500 text-xs">Amount due</p>
                        </GlassCard>
                        
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">Pending Payment</p>
                                    <p className="text-2xl font-bold text-orange-400">₹{dashboardMetrics.pending_amount?.toLocaleString()}</p>
                                </div>
                                <Clock className="w-8 h-8 text-orange-400" />
                            </div>
                            <p className="text-gray-500 text-xs">{dashboardMetrics.pending_bills_count} bills pending</p>
                        </GlassCard>
                        
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">GST Input Available</p>
                                    <p className="text-2xl font-bold text-green-400">₹{dashboardMetrics.gst_input_available?.toLocaleString()}</p>
                                </div>
                                <Percent className="w-8 h-8 text-green-400" />
                            </div>
                            <p className="text-gray-500 text-xs">To be claimed</p>
                        </GlassCard>
                        
                        <GlassCard>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <p className="text-gray-400 text-sm">Payment Rate</p>
                                    <p className="text-3xl font-bold text-purple-400">{dashboardMetrics.payment_rate_percent?.toFixed(1)}%</p>
                                </div>
                                <TrendingUp className="w-8 h-8 text-purple-400" />
                            </div>
                            <p className="text-gray-500 text-xs">Paid vs total</p>
                        </GlassCard>
                    </div>
                )}
                
                {/* Tab Navigation */}
                <div className="flex gap-2 mb-6 border-b border-slate-700">
                    {[
                        { id: 'bills', label: 'All Bills', icon: List },
                        { id: 'pending', label: 'Pending', icon: Clock },
                        { id: 'gst', label: 'GST Input', icon: Percent },
                        { id: 'analytics', label: 'Analytics', icon: TrendingUp }
                    ].map(tab => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`px-4 py-3 flex items-center gap-2 font-medium border-b-2 transition-all ${
                                    activeTab === tab.id
                                        ? 'border-green-500 text-green-400'
                                        : 'border-transparent text-gray-400 hover:text-white'
                                }`}
                            >
                                <Icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>
                
                {/* ALL BILLS TAB */}
                {activeTab === 'bills' && (
                    <div className="space-y-4">
                        {/* Actions */}
                        <div className="flex gap-3">
                            <GradientButton
                                onClick={() => setShowCreateForm(!showCreateForm)}
                                className="gap-2"
                            >
                                <Plus className="w-4 h-4" />
                                {showCreateForm ? 'Cancel' : 'New Bill'}
                            </GradientButton>
                            
                            <GradientButton
                                onClick={fetchBills}
                                disabled={loading}
                                variant="secondary"
                                className="gap-2"
                            >
                                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                                Refresh
                            </GradientButton>
                        </div>
                        
                        {/* Create Form */}
                        {showCreateForm && (
                            <GlassCard className="p-6">
                                <h3 className="text-lg font-bold text-white mb-4">Create New Bill</h3>
                                <form onSubmit={handleCreateBill} className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm text-gray-400 mb-2">Bill Number</label>
                                            <input
                                                type="text"
                                                value={formData.billNumber}
                                                onChange={(e) => setFormData({ ...formData, billNumber: e.target.value })}
                                                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                                placeholder="B-001"
                                            />
                                        </div>
                                        
                                        <div>
                                            <label className="block text-sm text-gray-400 mb-2">Supplier ID</label>
                                            <input
                                                type="number"
                                                value={formData.supplierId}
                                                onChange={(e) => setFormData({ ...formData, supplierId: e.target.value })}
                                                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                                placeholder="1"
                                            />
                                        </div>
                                        
                                        <div>
                                            <label className="block text-sm text-gray-400 mb-2">Bill Date</label>
                                            <input
                                                type="date"
                                                value={formData.billDate}
                                                onChange={(e) => setFormData({ ...formData, billDate: e.target.value })}
                                                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                            />
                                        </div>
                                        
                                        <div>
                                            <label className="block text-sm text-gray-400 mb-2">Due Date</label>
                                            <input
                                                type="date"
                                                value={formData.dueDate}
                                                onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
                                                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                            />
                                        </div>
                                    </div>
                                    
                                    {/* Bill Items */}
                                    <div>
                                        <h4 className="text-md font-bold text-white mb-3">Line Items</h4>
                                        <div className="space-y-3">
                                            {formData.items.map((item, idx) => (
                                                <div key={idx} className="flex gap-3 items-end">
                                                    <input
                                                        type="text"
                                                        placeholder="Category"
                                                        value={item.category}
                                                        onChange={(e) => updateItem(idx, 'category', e.target.value)}
                                                        className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                                                    />
                                                    <input
                                                        type="text"
                                                        placeholder="Description"
                                                        value={item.description}
                                                        onChange={(e) => updateItem(idx, 'description', e.target.value)}
                                                        className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                                                    />
                                                    <input
                                                        type="number"
                                                        placeholder="Qty"
                                                        value={item.quantity}
                                                        onChange={(e) => updateItem(idx, 'quantity', e.target.value)}
                                                        className="w-20 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                                                    />
                                                    <input
                                                        type="number"
                                                        placeholder="Price"
                                                        value={item.unitPrice}
                                                        onChange={(e) => updateItem(idx, 'unitPrice', e.target.value)}
                                                        className="w-24 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                                                    />
                                                    {formData.items.length > 1 && (
                                                        <button
                                                            type="button"
                                                            onClick={() => removeItemRow(idx)}
                                                            className="p-2 text-red-400 hover:bg-red-900/20 rounded"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                        <button
                                            type="button"
                                            onClick={addItemRow}
                                            className="mt-3 text-sm text-blue-400 hover:text-blue-300"
                                        >
                                            + Add Item
                                        </button>
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-2">Notes</label>
                                        <textarea
                                            value={formData.notes}
                                            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                                            rows="2"
                                            placeholder="Additional notes..."
                                        />
                                    </div>
                                    
                                    <div className="flex gap-3">
                                        <GradientButton type="submit" disabled={loading}>
                                            {loading ? 'Creating...' : 'Create Bill'}
                                        </GradientButton>
                                        <GradientButton
                                            type="button"
                                            onClick={() => {
                                                setShowCreateForm(false);
                                                resetForm();
                                            }}
                                            variant="outline"
                                        >
                                            Cancel
                                        </GradientButton>
                                    </div>
                                </form>
                            </GlassCard>
                        )}
                        
                        {/* Bills List */}
                        <GlassCard className="overflow-hidden">
                            {bills.length === 0 ? (
                                <div className="p-8 text-center">
                                    <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                                    <p className="text-gray-400">No bills found</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-slate-700">
                                    {bills.map(bill => (
                                        <div key={bill.id} className="p-4 hover:bg-slate-800/50 transition">
                                            <div
                                                className="flex items-start justify-between cursor-pointer"
                                                onClick={() => setExpandedBill(expandedBill === bill.id ? null : bill.id)}
                                            >
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-3 mb-2">
                                                        <p className="font-mono text-green-400">{bill.bill_number}</p>
                                                        <span className={`text-xs px-2 py-1 rounded ${
                                                            bill.payment_status === 'paid' ? 'bg-green-900/50 text-green-300' :
                                                            bill.payment_status === 'partial' ? 'bg-yellow-900/50 text-yellow-300' :
                                                            'bg-orange-900/50 text-orange-300'
                                                        }`}>
                                                            {bill.payment_status}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-gray-400">
                                                        Supplier: {bill.supplier_id} • Due: {new Date(bill.due_date).toLocaleDateString()}
                                                    </p>
                                                </div>
                                                
                                                <div className="text-right">
                                                    <p className="font-bold text-white">₹{bill.total?.toLocaleString()}</p>
                                                    <p className="text-sm text-green-400">GST Input: ₹{bill.gst_input_available?.toLocaleString()}</p>
                                                </div>
                                                
                                                {expandedBill === bill.id ? (
                                                    <ChevronUp className="w-4 h-4 text-gray-400 ml-4" />
                                                ) : (
                                                    <ChevronDown className="w-4 h-4 text-gray-400 ml-4" />
                                                )}
                                            </div>
                                            
                                            {/* Expanded View */}
                                            {expandedBill === bill.id && (
                                                <div className="mt-4 pt-4 border-t border-slate-700 space-y-3">
                                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                                        <div>
                                                            <p className="text-gray-400">Bill Date</p>
                                                            <p className="text-white">{new Date(bill.bill_date).toLocaleDateString()}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-gray-400">Amount Paid</p>
                                                            <p className="text-white">₹{(bill.total - (bill.total - bill.subtotal))?.toLocaleString()}</p>
                                                        </div>
                                                    </div>
                                                    
                                                    <div className="flex gap-2 pt-2">
                                                        <GradientButton
                                                            size="sm"
                                                            onClick={() => handleRecordPayment(bill.id, bill.total)}
                                                            disabled={bill.payment_status === 'paid'}
                                                        >
                                                            <CreditCard className="w-3 h-3" />
                                                            Record Payment
                                                        </GradientButton>
                                                        
                                                        {bill.gst_input_available > 0 && (
                                                            <GradientButton
                                                                size="sm"
                                                                variant="outline"
                                                                onClick={() => handleClaimGST(bill.id)}
                                                            >
                                                                <Percent className="w-3 h-3" />
                                                                Claim GST
                                                            </GradientButton>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </GlassCard>
                    </div>
                )}
                
                {/* PENDING TAB */}
                {activeTab === 'pending' && (
                    <GlassCard>
                        <h3 className="text-lg font-bold text-white mb-4">Pending Bills</h3>
                        <p className="text-gray-400">Bills awaiting payment or partially paid</p>
                    </GlassCard>
                )}
                
                {/* GST TAB */}
                {activeTab === 'gst' && gstSummary && (
                    <div className="space-y-4">
                        <GlassCard>
                            <h3 className="text-lg font-bold text-white mb-6">GST Input Credit Summary</h3>
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                <div>
                                    <p className="text-gray-400 text-sm mb-2">Total GST in Bills</p>
                                    <p className="text-3xl font-bold text-white">₹{gstSummary.total_gst_in_bills?.toLocaleString()}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm mb-2">GST Claimed</p>
                                    <p className="text-3xl font-bold text-green-400">₹{gstSummary.total_gst_claimed?.toLocaleString()}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm mb-2">Available to Claim</p>
                                    <p className="text-3xl font-bold text-orange-400">₹{gstSummary.total_gst_available?.toLocaleString()}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm mb-2">Claimed %</p>
                                    <p className="text-3xl font-bold text-blue-400">{gstSummary.claimed_percent?.toFixed(1)}%</p>
                                </div>
                            </div>
                        </GlassCard>
                    </div>
                )}
                
                {/* ANALYTICS TAB */}
                {activeTab === 'analytics' && analytics && (
                    <GlassCard>
                        <h3 className="text-lg font-bold text-white mb-6">Bill Analytics</h3>
                        <div className="grid grid-cols-2 gap-8">
                            <div>
                                <h4 className="font-bold text-white mb-4">Payment Metrics</h4>
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Total Payable</span>
                                        <span className="text-white font-bold">₹{analytics.total_amount?.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Paid</span>
                                        <span className="text-green-400 font-bold">₹{analytics.total_paid?.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Pending</span>
                                        <span className="text-orange-400 font-bold">₹{analytics.pending_amount?.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Payment Rate</span>
                                        <span className="text-blue-400 font-bold">{analytics.payment_rate_percent?.toFixed(1)}%</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div>
                                <h4 className="font-bold text-white mb-4">GST Metrics</h4>
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Bills</span>
                                        <span className="text-white font-bold">{analytics.bill_count}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Total GST</span>
                                        <span className="text-white font-bold">₹{analytics.total_gst?.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Avg Bill Value</span>
                                        <span className="text-white font-bold">₹{analytics.average_bill_value?.toLocaleString()}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </GlassCard>
                )}
            </div>
        </div>
    );
};

export default BillManagement;
