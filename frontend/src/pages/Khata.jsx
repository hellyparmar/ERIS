import React, { useState, useEffect } from 'react';
import { CreditCard, AlertCircle, CheckCircle, Clock, Search, Plus, Phone, RefreshCw, TrendingDown, TrendingUp, IndianRupee } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Khata = () => {
    const { addToast } = useToast();
    const [accounts, setAccounts] = useState([]);
    const [summary, setSummary] = useState(null);
    const [overdue, setOverdue] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [tab, setTab] = useState('accounts'); // accounts | overdue | record

    // Record credit sale form
    const [creditForm, setCreditForm] = useState({ customer_id: '', amount: '', notes: '' });
    // Payment form
    const [payForm, setPayForm] = useState({ customer_id: '', amount: '', payment_method: 'cash' });
    const [submitting, setSubmitting] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [accountsRes, summaryRes, overdueRes] = await Promise.all([
                fetch(`${API_BASE}/api/v1/khata/accounts${search ? `?search=${search}` : ''}`),
                fetch(`${API_BASE}/api/v1/khata/summary`),
                fetch(`${API_BASE}/api/v1/khata/overdue`)
            ]);
            const [accountsData, summaryData, overdueData] = await Promise.all([
                accountsRes.json(), summaryRes.json(), overdueRes.json()
            ]);
            if (accountsData.success) setAccounts(accountsData.data || []);
            if (summaryData.success) setSummary(summaryData.data);
            if (overdueData.success) setOverdue(overdueData.data || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);
    useEffect(() => {
        const t = setTimeout(() => fetchData(), 400);
        return () => clearTimeout(t);
    }, [search]);

    const handleCreditSale = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/khata/credit-sale`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ customer_id: parseInt(creditForm.customer_id), amount: parseFloat(creditForm.amount), notes: creditForm.notes })
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Credit sale recorded! Balance: ₹${data.data.new_balance}`, 'success');
                setCreditForm({ customer_id: '', amount: '', notes: '' });
                fetchData();
            } else {
                addToast(data.detail || 'Failed to record credit sale', 'error');
            }
        } catch { addToast('Network error', 'error'); }
        finally { setSubmitting(false); }
    };

    const handlePayment = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/khata/payment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ customer_id: parseInt(payForm.customer_id), amount: parseFloat(payForm.amount), payment_method: payForm.payment_method })
            });
            const data = await res.json();
            if (data.success) {
                addToast(data.data.fully_settled ? '✅ Account fully settled!' : `Payment recorded. Remaining: ₹${data.data.remaining_balance}`, 'success');
                setPayForm({ customer_id: '', amount: '', payment_method: 'cash' });
                fetchData();
            } else {
                addToast(data.detail || 'Payment failed', 'error');
            }
        } catch { addToast('Network error', 'error'); }
        finally { setSubmitting(false); }
    };

    const TABS = [
        { id: 'accounts', label: 'All Accounts' },
        { id: 'overdue', label: `Overdue (${overdue.length})` },
        { id: 'record', label: 'Record' },
    ];

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">Khata — Credit Ledger</h1>
                <p className="text-muted-foreground">Track credit sales and outstanding customer balances</p>
            </div>

            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                        { label: 'Total Accounts', value: summary.total_accounts, icon: CreditCard, color: 'text-blue-400' },
                        { label: 'Total Outstanding', value: `₹${(summary.total_outstanding || 0).toLocaleString()}`, icon: IndianRupee, color: 'text-red-400' },
                        { label: 'With Balance', value: summary.accounts_with_balance, icon: AlertCircle, color: 'text-yellow-400' },
                        { label: 'Avg Balance', value: `₹${(summary.avg_balance || 0).toLocaleString()}`, icon: TrendingDown, color: 'text-purple-400' },
                    ].map(({ label, value, icon: Icon, color }) => (
                        <GlassCard key={label} className="p-4">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm text-muted-foreground">{label}</p>
                                <Icon className={`w-4 h-4 ${color}`} />
                            </div>
                            <p className={`text-2xl font-bold ${color}`}>{value}</p>
                        </GlassCard>
                    ))}
                </div>
            )}

            {/* Tabs */}
            <div className="flex gap-2 border-b border-border pb-0">
                {TABS.map(t2 => (
                    <button key={t2.id} onClick={() => setTab(t2.id)}
                        className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${tab === t2.id ? 'bg-primary/10 text-primary border-b-2 border-primary' : 'text-muted-foreground hover:text-foreground'}`}>
                        {t2.label}
                    </button>
                ))}
            </div>

            {/* Accounts Tab */}
            {tab === 'accounts' && (
                <GlassCard className="p-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <input type="text" placeholder="Search customer..." value={search} onChange={e => setSearch(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none text-sm" />
                        </div>
                        <button onClick={fetchData} className="p-2 rounded-lg bg-secondary/50 hover:bg-secondary/80 transition-colors">
                            <RefreshCw className="w-4 h-4 text-muted-foreground" />
                        </button>
                    </div>
                    {loading ? (
                        <div className="text-center py-12 text-muted-foreground">Loading...</div>
                    ) : accounts.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">No credit accounts found</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border text-muted-foreground text-left">
                                        <th className="pb-3 pr-4">Customer</th>
                                        <th className="pb-3 pr-4">Phone</th>
                                        <th className="pb-3 pr-4 text-right">Balance</th>
                                        <th className="pb-3 pr-4 text-right">Credit Limit</th>
                                        <th className="pb-3 text-right">Last Payment</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {accounts.map(acc => (
                                        <tr key={acc.id} className="hover:bg-secondary/20 transition-colors">
                                            <td className="py-3 pr-4 font-medium text-foreground">{acc.customer_name}</td>
                                            <td className="py-3 pr-4 text-muted-foreground">{acc.customer_phone || '—'}</td>
                                            <td className={`py-3 pr-4 text-right font-bold ${acc.current_balance > 0 ? 'text-red-400' : 'text-green-400'}`}>
                                                ₹{acc.current_balance?.toLocaleString()}
                                            </td>
                                            <td className="py-3 pr-4 text-right text-muted-foreground">₹{acc.credit_limit?.toLocaleString()}</td>
                                            <td className="py-3 text-right text-muted-foreground text-xs">
                                                {acc.last_payment_date ? new Date(acc.last_payment_date).toLocaleDateString() : 'Never'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </GlassCard>
            )}

            {/* Overdue Tab */}
            {tab === 'overdue' && (
                <GlassCard className="p-6">
                    <h3 className="text-lg font-bold gradient-text mb-4">Overdue Accounts</h3>
                    {overdue.length === 0 ? (
                        <div className="text-center py-12">
                            <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                            <p className="text-green-400 font-semibold">All accounts are clear!</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {overdue.map(acc => (
                                <div key={acc.customer_id} className="flex items-center justify-between p-4 rounded-lg bg-red-500/5 border border-red-500/20">
                                    <div>
                                        <p className="font-medium text-foreground">{acc.customer_name}</p>
                                        {acc.customer_phone && <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1"><Phone className="w-3 h-3" />{acc.customer_phone}</p>}
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xl font-bold text-red-400">₹{acc.outstanding_balance?.toLocaleString()}</p>
                                        <p className="text-xs text-muted-foreground">
                                            Last paid: {acc.last_payment_date ? new Date(acc.last_payment_date).toLocaleDateString() : 'Never'}
                                        </p>
                                    </div>
                                </div>
                            ))}
                            <div className="pt-4 border-t border-border flex justify-between text-sm">
                                <span className="text-muted-foreground">Total Outstanding:</span>
                                <span className="font-bold text-red-400">₹{overdue.reduce((s, a) => s + a.outstanding_balance, 0).toLocaleString()}</span>
                            </div>
                        </div>
                    )}
                </GlassCard>
            )}

            {/* Record Tab */}
            {tab === 'record' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Credit Sale */}
                    <GlassCard className="p-6">
                        <h3 className="text-lg font-bold gradient-text mb-4 flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-red-400" /> Record Credit Sale
                        </h3>
                        <form onSubmit={handleCreditSale} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Customer ID *</label>
                                <input type="number" value={creditForm.customer_id} onChange={e => setCreditForm({ ...creditForm, customer_id: e.target.value })}
                                    placeholder="Enter customer ID"
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Amount (₹) *</label>
                                <input type="number" step="0.01" min="0.01" value={creditForm.amount} onChange={e => setCreditForm({ ...creditForm, amount: e.target.value })}
                                    placeholder="e.g. 500"
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Notes</label>
                                <input type="text" value={creditForm.notes} onChange={e => setCreditForm({ ...creditForm, notes: e.target.value })}
                                    placeholder="e.g. Groceries on credit"
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none" />
                            </div>
                            <GradientButton type="submit" disabled={submitting} className="w-full">
                                <Plus className="w-4 h-4 mr-2" />
                                {submitting ? 'Recording...' : 'Add Credit Sale'}
                            </GradientButton>
                        </form>
                    </GlassCard>

                    {/* Record Payment */}
                    <GlassCard className="p-6">
                        <h3 className="text-lg font-bold gradient-text mb-4 flex items-center gap-2">
                            <TrendingDown className="w-5 h-5 text-green-400" /> Record Payment
                        </h3>
                        <form onSubmit={handlePayment} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Customer ID *</label>
                                <input type="number" value={payForm.customer_id} onChange={e => setPayForm({ ...payForm, customer_id: e.target.value })}
                                    placeholder="Enter customer ID"
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Amount Paid (₹) *</label>
                                <input type="number" step="0.01" min="0.01" value={payForm.amount} onChange={e => setPayForm({ ...payForm, amount: e.target.value })}
                                    placeholder="e.g. 250"
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Payment Method</label>
                                <select value={payForm.payment_method} onChange={e => setPayForm({ ...payForm, payment_method: e.target.value })}
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none">
                                    <option value="cash">Cash</option>
                                    <option value="upi">UPI</option>
                                    <option value="card">Card</option>
                                    <option value="bank_transfer">Bank Transfer</option>
                                </select>
                            </div>
                            <GradientButton type="submit" disabled={submitting} className="w-full">
                                <CheckCircle className="w-4 h-4 mr-2" />
                                {submitting ? 'Recording...' : 'Record Payment'}
                            </GradientButton>
                        </form>
                    </GlassCard>
                </div>
            )}
        </div>
    );
};

export default Khata;
