
import React, { useState, useEffect } from 'react';
import { API_BASE } from '../lib/api';
import {
    FileText,
    RefreshCw,
    CheckCircle,
    AlertCircle,
    Search,
    Filter,
    MoreHorizontal,
    X,
    Settings,
    Eye,
    Clock,
    Zap,
    Server,
    CheckSquare
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

const Invoices = () => {
    const { addToast } = useToast();
    // Mock Data simulating DB
    const [invoices, setInvoices] = useState([
        { id: "INV-001", customer: "ABC Corp", amount: "₹15,000", date: "2026-01-21", status: "paid", tally_status: "synced" },
        { id: "INV-002", customer: "XYZ Ltd", amount: "₹22,500", date: "2026-01-21", status: "pending", tally_status: "pending" },
        { id: "INV-003", customer: "Demo Store", amount: "₹8,750", date: "2026-01-20", status: "paid", tally_status: "failed" },
        { id: "INV-004", customer: "Retail Hub", amount: "₹31,200", date: "2026-01-20", status: "paid", tally_status: "pending" },
        { id: "INV-005", customer: "Shop Plus", amount: "₹12,400", date: "2026-01-19", status: "pending", tally_status: "pending" },
    ]);

    const [syncing, setSyncing] = useState(null); // ID of invoice currently syncing
    const [showFilterMenu, setShowFilterMenu] = useState(false);
    const [activeTab, setActiveTab] = useState('invoices'); // invoices, sync-dashboard, settings
    const [showTallySettings, setShowTallySettings] = useState(false);
    const [batchSyncing, setBatchSyncing] = useState(false);
    const [tallyConfig, setTallyConfig] = useState({
        host: 'localhost',
        port: 9000,
        autoSync: true,
        syncFrequency: 'hourly'
    });
    const [syncHistory, setSyncHistory] = useState([
        { id: 1, invoiceId: 'INV-001', timestamp: '2026-02-09 10:30 AM', status: 'success', amount: '₹15,000', dataPoints: 5 },
        { id: 2, invoiceId: 'INV-002', timestamp: '2026-02-09 09:15 AM', status: 'failed', amount: '₹22,500', error: 'Connection timeout', dataPoints: 0 },
        { id: 3, invoiceId: 'INV-003', timestamp: '2026-02-09 08:45 AM', status: 'success', amount: '₹8,750', dataPoints: 5 },
        { id: 4, invoiceId: 'INV-004', timestamp: '2026-02-09 07:20 AM', status: 'success', amount: '₹31,200', dataPoints: 5 },
        { id: 5, invoiceId: 'INV-005', timestamp: '2026-02-08 04:00 PM', status: 'pending', amount: '₹12,400', dataPoints: 3 },
    ]);
    const [filters, setFilters] = useState({
        status: null,
        tallyStatus: null,
        dateFrom: null,
        dateTo: null
    });

    const handleSync = async (invoiceId) => {
        setSyncing(invoiceId);
        try {
            const response = await fetch(`${API_BASE}/api/v1/invoices/${invoiceId}/sync-tally`, {
                method: 'POST'
            });
            const data = await response.json();

            // Update local state based on result
            setInvoices(prev => prev.map(inv => {
                if (inv.id === invoiceId) {
                    return {
                        ...inv,
                        tally_status: data.status === 'success' ? 'synced' : 'failed'
                    };
                }
                return inv;
            }));

            if (data.status !== 'success') {
                alert(`Sync Failed: ${data.message}`);
            }
        } catch (error) {
            console.error("Sync error:", error);
            alert("Connection Error");
            setInvoices(prev => prev.map(inv => inv.id === invoiceId ? { ...inv, tally_status: 'failed' } : inv));
        } finally {
            setSyncing(null);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'paid': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
            case 'pending': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    const getTallyStatus = (status) => {
        switch (status) {
            case 'synced':
                return (
                    <div className="flex items-center gap-1.5 text-green-500 font-medium">
                        <CheckCircle size={14} />
                        <span className="text-xs">Synced</span>
                    </div>
                );
            case 'failed':
                return (
                    <div className="flex items-center gap-1.5 text-red-500 font-medium">
                        <AlertCircle size={14} />
                        <span className="text-xs">Failed</span>
                    </div>
                );
            case 'pending':
                return (
                    <div className="flex items-center gap-1.5 text-gray-400 font-medium">
                        <div className="w-1.5 h-1.5 rounded-full bg-gray-400"></div>
                        <span className="text-xs">Pending</span>
                    </div>
                );
            default: return null;
        }
    };

    const getFilteredInvoices = () => {
        return invoices.filter(inv => {
            if (filters.status && inv.status !== filters.status) return false;
            if (filters.tallyStatus && inv.tally_status !== filters.tallyStatus) return false;
            if (filters.dateFrom && inv.date < filters.dateFrom) return false;
            if (filters.dateTo && inv.date > filters.dateTo) return false;
            return true;
        });
    };

    const clearFilters = () => {
        setFilters({
            status: null,
            tallyStatus: null,
            dateFrom: null,
            dateTo: null
        });
    };

    const activeFilterCount = Object.values(filters).filter(v => v !== null).length;

    const handleBatchSync = async () => {
        setBatchSyncing(true);
        try {
            const pendingInvoices = invoices.filter(inv => inv.tally_status !== 'synced');

            for (const inv of pendingInvoices) {
                await new Promise(resolve => setTimeout(resolve, 500));
                setInvoices(prev => prev.map(i =>
                    i.id === inv.id ? { ...i, tally_status: 'synced' } : i
                ));
                setSyncHistory(prev => [{
                    id: prev.length + 1,
                    invoiceId: inv.id,
                    timestamp: new Date().toLocaleString(),
                    status: 'success',
                    amount: inv.amount,
                    dataPoints: 5
                }, ...prev]);
            }
            addToast(`Batch synced ${pendingInvoices.length} invoices successfully!`, "success");
        } catch (error) {
            addToast("Batch sync failed", "error");
        } finally {
            setBatchSyncing(false);
        }
    };

    const testTallyConnection = async () => {
        try {
            addToast("Testing Tally connection...", "info");
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1500));
            addToast("✓ Tally connection successful!", "success");
        } catch (error) {
            addToast("✗ Connection failed", "error");
        }
    };

    return (
        <div className="space-y-8 fade-in-up min-h-screen p-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent mb-2">Invoices</h1>
                    <p className="text-muted-foreground">Manage sales and Tally integration</p>
                </div>
                <div className="flex gap-2 flex-wrap">
                    <button
                        onClick={() => setShowTallySettings(!showTallySettings)}
                        className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-white/10 border border-gray-200 dark:border-white/10 rounded-lg text-gray-600 dark:text-white hover:bg-gray-50 dark:hover:bg-white/20 transition text-sm"
                    >
                        <Settings size={16} /> Tally Settings
                    </button>
                    <button
                        onClick={handleBatchSync}
                        disabled={batchSyncing}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm disabled:opacity-50"
                    >
                        {batchSyncing ? <RefreshCw size={16} className="animate-spin" /> : <Zap size={16} />}
                        Batch Sync
                    </button>
                </div>
            </div>

            {/* Tally Settings Modal */}
            {showTallySettings && (
                <GlassCard className="p-6 border border-blue-500/30">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Server size={20} /> Tally Connection Settings
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Host</label>
                                    <input
                                        type="text"
                                        value={tallyConfig.host}
                                        onChange={(e) => setTallyConfig({ ...tallyConfig, host: e.target.value })}
                                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Port</label>
                                    <input
                                        type="number"
                                        value={tallyConfig.port}
                                        onChange={(e) => setTallyConfig({ ...tallyConfig, port: parseInt(e.target.value) })}
                                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Sync Frequency</label>
                                    <select
                                        value={tallyConfig.syncFrequency}
                                        onChange={(e) => setTallyConfig({ ...tallyConfig, syncFrequency: e.target.value })}
                                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="manual">Manual</option>
                                        <option value="hourly">Every Hour</option>
                                        <option value="daily">Daily</option>
                                    </select>
                                </div>
                                <label className="flex items-center gap-2 text-gray-300 mt-4">
                                    <input
                                        type="checkbox"
                                        checked={tallyConfig.autoSync}
                                        onChange={(e) => setTallyConfig({ ...tallyConfig, autoSync: e.target.checked })}
                                        className="rounded"
                                    />
                                    <span className="text-sm">Enable Auto Sync</span>
                                </label>
                                <button
                                    onClick={testTallyConnection}
                                    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition font-medium text-sm mt-4"
                                >
                                    Test Connection
                                </button>
                            </div>
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-white mb-4">Connection Status</h3>
                            <div className="space-y-3">
                                <div className="p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
                                    <p className="flex items-center gap-2 text-green-400 font-medium">
                                        <CheckCircle size={16} /> Connection: Active
                                    </p>
                                    <p className="text-xs text-green-400/70 mt-1">Last tested: 2 minutes ago</p>
                                </div>
                                <div className="p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                                    <p className="text-sm text-blue-300"><span className="font-medium">Synced Invoices:</span> 3 / 5</p>
                                    <p className="text-sm text-blue-300 mt-1"><span className="font-medium">Pending:</span> 2</p>
                                </div>
                                <div className="p-4 bg-gray-700/50 border border-white/10 rounded-lg">
                                    <p className="text-sm text-gray-300"><span className="font-medium">Last Sync:</span> 12:30 PM</p>
                                    <p className="text-sm text-gray-300 mt-1"><span className="font-medium">Data Points Synced:</span> 42</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </GlassCard>
            )}

            {/* Tab Navigation */}
            <div className="flex gap-2 bg-white/5 dark:bg-white/5 p-1 rounded-lg w-fit">
                {[
                    { id: 'invoices', label: 'Invoices', icon: FileText },
                    { id: 'sync-dashboard', label: 'Sync Dashboard', icon: Eye },
                    { id: 'audit-log', label: 'Audit Log', icon: Clock }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2 rounded-md text-sm font-bold transition-all flex items-center gap-2 ${activeTab === tab.id
                            ? 'bg-blue-600 text-white shadow-lg'
                            : 'text-muted-foreground hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <tab.icon size={16} />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* INVOICES TAB */}
            {activeTab === 'invoices' && (
                <>
                    <div className="space-y-4">
                        <div className="flex flex-1 md:flex-none gap-3">
                            <div className="relative flex items-center w-full md:w-64 px-3 py-2 bg-white dark:bg-white/10 border border-gray-200 dark:border-white/10 rounded-lg focus-within:ring-2 focus-within:ring-blue-500 transition">
                                <Search className="text-gray-500 dark:text-gray-400 mr-2 shrink-0" size={20} />
                                <input
                                    type="text"
                                    placeholder="Search invoices..."
                                    className="w-full bg-transparent border-none focus:outline-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 h-full"
                                />
                            </div>
                            <div className="relative">
                                <button
                                    onClick={() => setShowFilterMenu(!showFilterMenu)}
                                    className={`p-2 rounded-lg border transition ${activeFilterCount > 0
                                        ? 'bg-blue-500/20 border-blue-500/30 text-blue-400'
                                        : 'bg-white dark:bg-white/10 border-gray-200 dark:border-white/10 text-gray-600 dark:text-white hover:bg-gray-50 dark:hover:bg-white/20'
                                        }`}
                                >
                                    <Filter size={20} />
                                    {activeFilterCount > 0 && (
                                        <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                                            {activeFilterCount}
                                        </span>
                                    )}
                                </button>

                                {/* Filter Dropdown Menu */}
                                {showFilterMenu && (
                                    <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-slate-900 rounded-lg border border-gray-200 dark:border-slate-700 shadow-2xl z-50 p-5 space-y-4">
                                        <div className="flex justify-between items-center mb-4 pb-3 border-b border-gray-150 dark:border-slate-800">
                                            <h3 className="font-semibold text-gray-900 dark:text-white text-sm">Filter Invoices</h3>
                                            <button onClick={() => setShowFilterMenu(false)} className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition">
                                                <X size={18} />
                                            </button>
                                        </div>

                                        {/* Status Filter */}
                                        <div>
                                            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">Invoice Status</label>
                                            <select
                                                value={filters.status || ''}
                                                onChange={(e) => setFilters({ ...filters, status: e.target.value || null })}
                                                className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white text-sm font-medium hover:border-gray-400 dark:hover:border-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition appearance-none"
                                            >
                                                <option value="">All Status</option>
                                                <option value="paid">Paid</option>
                                                <option value="pending">Pending</option>
                                            </select>
                                        </div>

                                        {/* Tally Status Filter */}
                                        <div>
                                            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">Tally Status</label>
                                            <select
                                                value={filters.tallyStatus || ''}
                                                onChange={(e) => setFilters({ ...filters, tallyStatus: e.target.value || null })}
                                                className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white text-sm font-medium hover:border-gray-400 dark:hover:border-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition appearance-none"
                                            >
                                                <option value="">All Status</option>
                                                <option value="synced">Synced</option>
                                                <option value="pending">Pending</option>
                                                <option value="failed">Failed</option>
                                            </select>
                                        </div>

                                        {/* Date From Filter */}
                                        <div>
                                            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">Date From</label>
                                            <input
                                                type="date"
                                                value={filters.dateFrom || ''}
                                                onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value || null })}
                                                className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white text-sm font-medium hover:border-gray-400 dark:hover:border-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition"
                                            />
                                        </div>

                                        {/* Date To Filter */}
                                        <div>
                                            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">Date To</label>
                                            <input
                                                type="date"
                                                value={filters.dateTo || ''}
                                                onChange={(e) => setFilters({ ...filters, dateTo: e.target.value || null })}
                                                className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white text-sm font-medium hover:border-gray-400 dark:hover:border-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition"
                                            />
                                        </div>

                                        {/* Clear Filters Button */}
                                        {activeFilterCount > 0 && (
                                            <button
                                                onClick={clearFilters}
                                                className="w-full px-4 py-2 text-xs font-semibold text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-slate-800 rounded-md hover:bg-gray-200 dark:hover:bg-slate-700 transition border border-gray-200 dark:border-slate-700 uppercase tracking-wide"
                                            >
                                                Clear All Filters
                                            </button>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                        <GradientButton
                            onClick={() => addToast("New Invoice Form opened", "info")}
                        >
                            <FileText size={16} /> New Invoice
                        </GradientButton>
                    </div>

                    {/* INVOICES TABLE */}
                    <GlassCard className="overflow-hidden">
                        <table className="w-full text-left text-sm">
                            <thead>
                                <tr className="bg-white/5 dark:bg-white/5 text-muted-foreground font-semibold text-xs uppercase tracking-wider border-b border-white/10">
                                    <th className="px-6 py-4">Invoice ID</th>
                                    <th className="px-6 py-4">Customer</th>
                                    <th className="px-6 py-4">Date</th>
                                    <th className="px-6 py-4">Amount</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4">Tally Status</th>
                                    <th className="px-6 py-4 text-center">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {getFilteredInvoices().map((inv) => (
                                    <tr key={inv.id} className="hover:bg-muted/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-muted-foreground font-medium text-xs">{inv.id}</td>
                                        <td className="px-6 py-4 font-medium text-foreground">{inv.customer}</td>
                                        <td className="px-6 py-4 text-foreground font-medium">{inv.date}</td>
                                        <td className="px-6 py-4 font-bold text-foreground">{inv.amount}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${getStatusColor(inv.status)}`}>
                                                {inv.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            {getTallyStatus(inv.tally_status)}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="flex items-center justify-center gap-3">
                                                {/* Sync Button */}
                                                <button
                                                    onClick={() => handleSync(inv.id)}
                                                    disabled={syncing === inv.id || inv.tally_status === 'synced'}
                                                    className={`
                                                flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                                                ${inv.tally_status === 'synced'
                                                            ? 'bg-transparent text-gray-400 cursor-default'
                                                            : 'bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 border border-blue-500/20'}
                                            `}
                                                >
                                                    {syncing === inv.id ? (
                                                        <RefreshCw size={14} className="animate-spin" />
                                                    ) : (
                                                        <RefreshCw size={14} />
                                                    )}
                                                    {inv.tally_status === 'synced' ? 'Synced' : 'Sync to Tally'}
                                                </button>

                                                <button className="text-gray-400 hover:text-white transition">
                                                    <MoreHorizontal size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </GlassCard>
                </>
            )}

            {/* SYNC DASHBOARD TAB */}
            {activeTab === 'sync-dashboard' && (
                <>
                    <div className="space-y-6">
                        {/* Sync Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <GlassCard className="p-6">
                                <p className="text-sm text-muted-foreground mb-2">Total Synced</p>
                                <h3 className="text-3xl font-bold text-green-400">3 / 5</h3>
                                <p className="text-xs text-green-400/70 mt-2">60% success rate</p>
                            </GlassCard>
                            <GlassCard className="p-6">
                                <p className="text-sm text-muted-foreground mb-2">Pending Sync</p>
                                <h3 className="text-3xl font-bold text-yellow-400">2</h3>
                                <p className="text-xs text-yellow-400/70 mt-2">Last sync: 10 mins ago</p>
                            </GlassCard>
                            <GlassCard className="p-6">
                                <p className="text-sm text-muted-foreground mb-2">Failed Attempts</p>
                                <h3 className="text-3xl font-bold text-red-400">1</h3>
                                <p className="text-xs text-red-400/70 mt-2">INV-002: Connection timeout</p>
                            </GlassCard>
                            <GlassCard className="p-6">
                                <p className="text-sm text-muted-foreground mb-2">Data Points Synced</p>
                                <h3 className="text-3xl font-bold text-blue-400">42</h3>
                                <p className="text-xs text-blue-400/70 mt-2">Customer, Item, Tax data</p>
                            </GlassCard>
                        </div>

                        {/* Sync History */}
                        <GlassCard className="p-6 overflow-x-auto">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Clock size={20} /> Sync History (Last 5)
                            </h3>
                            <table className="w-full text-sm text-left">
                                <thead>
                                    <tr className="text-xs text-muted-foreground font-semibold uppercase border-b border-white/10">
                                        <th className="pb-3 pr-4">Invoice</th>
                                        <th className="pb-3 pr-4">Timestamp</th>
                                        <th className="pb-3 pr-4">Amount</th>
                                        <th className="pb-3 pr-4">Status</th>
                                        <th className="pb-3 pr-4">Data Points</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {syncHistory.map(log => (
                                        <tr key={log.id} className="hover:bg-white/5 transition">
                                            <td className="py-3 pr-4 font-mono text-blue-400">{log.invoiceId}</td>
                                            <td className="py-3 pr-4 text-gray-300 text-xs">{log.timestamp}</td>
                                            <td className="py-3 pr-4 font-bold">{log.amount}</td>
                                            <td className="py-3 pr-4">
                                                <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-bold ${log.status === 'success' ? 'bg-green-500/20 text-green-400' :
                                                    log.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                        'bg-yellow-500/20 text-yellow-400'
                                                    }`}>
                                                    {log.status === 'success' && <CheckCircle size={12} />}
                                                    {log.status === 'failed' && <AlertCircle size={12} />}
                                                    {log.status === 'pending' && <Clock size={12} />}
                                                    {log.status}
                                                </span>
                                                {log.error && <p className="text-xs text-red-400 mt-1">{log.error}</p>}
                                            </td>
                                            <td className="py-3 pr-4"><span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs font-medium">{log.dataPoints}</span></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </GlassCard>
                    </div>
                </>
            )}

            {/* AUDIT LOG TAB */}
            {activeTab === 'audit-log' && (
                <>
                    <GlassCard className="p-6 overflow-x-auto">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <CheckSquare size={20} /> Detailed Sync Audit Log
                        </h3>
                        <p className="text-sm text-muted-foreground mb-4">Complete record of all data synced to Tally ERP</p>
                        <table className="w-full text-sm text-left">
                            <thead>
                                <tr className="text-xs text-muted-foreground font-semibold uppercase border-b border-white/10">
                                    <th className="pb-3 pr-4">Invoice ID</th>
                                    <th className="pb-3 pr-4">Customer</th>
                                    <th className="pb-3 pr-4">Data Synced</th>
                                    <th className="pb-3 pr-4">Timestamp</th>
                                    <th className="pb-3 pr-4">Sync Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {syncHistory.map(log => (
                                    <tr key={log.id} className="hover:bg-white/5 transition">
                                        <td className="py-3 pr-4 font-mono text-blue-400">{log.invoiceId}</td>
                                        <td className="py-3 pr-4">{invoices.find(inv => inv.id === log.invoiceId)?.customer || 'N/A'}</td>
                                        <td className="py-3 pr-4">
                                            <div className="text-xs space-y-1">
                                                <p>✓ Amount: {log.amount}</p>
                                                <p>✓ Customer Details</p>
                                                <p>✓ Tax/GST Info</p>
                                                {log.dataPoints > 0 && <p>✓ {log.dataPoints} data points</p>}
                                            </div>
                                        </td>
                                        <td className="py-3 pr-4 text-gray-400 text-xs">{log.timestamp}</td>
                                        <td className="py-3 pr-4">
                                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold ${log.status === 'success' ? 'bg-green-500/20 text-green-400' :
                                                log.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                    'bg-yellow-500/20 text-yellow-400'
                                                }`}>
                                                {log.status.toUpperCase()}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </GlassCard>
                </>
            )}
        </div>
    );
};

export default Invoices;
