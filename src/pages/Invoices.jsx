
import React, { useState } from 'react';
import {
    FileText,
    RefreshCw,
    CheckCircle,
    AlertCircle,
    Search,
    Filter,
    MoreHorizontal
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

    const handleSync = async (invoiceId) => {
        setSyncing(invoiceId);
        try {
            const response = await fetch(`http://localhost:8000/api/v1/invoices/${invoiceId}/sync-tally`, {
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

    return (
        <div className="space-y-8 fade-in-up min-h-screen">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent mb-2">Invoices</h1>
                    <p className="text-muted-foreground">Manage sales and Tally integration</p>
                </div>
                <div className="flex gap-3">
                    <div className="flex flex-1 md:flex-none gap-3">
                        <div className="relative flex items-center w-full md:w-64 px-3 py-2 bg-white dark:bg-white/10 border border-gray-200 dark:border-white/10 rounded-lg focus-within:ring-2 focus-within:ring-blue-500 transition">
                            <Search className="text-gray-500 dark:text-gray-400 mr-2 shrink-0" size={20} />
                            <input
                                type="text"
                                placeholder="Search invoices..."
                                className="w-full bg-transparent border-none focus:outline-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 h-full"
                            />
                        </div>
                        <button className="p-2 bg-white dark:bg-white/10 border border-gray-200 dark:border-white/10 rounded-lg text-gray-600 dark:text-white hover:bg-gray-50 dark:hover:bg-white/20 transition">
                            <Filter size={20} />
                        </button>
                    </div>
                    <GradientButton
                        className="flex items-center justify-center gap-2 whitespace-nowrap"
                        onClick={() => addToast("New Invoice Form opened", "info")}
                    >
                        <FileText size={16} /> New Invoice
                    </GradientButton>
                </div>
            </div>

            <GlassCard className="overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead>
                        <tr className="bg-slate-50 dark:bg-slate-950/50 text-muted-foreground font-semibold text-xs uppercase tracking-wider">
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
                        {invoices.map((inv) => (
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
        </div>
    );
};

export default Invoices;
