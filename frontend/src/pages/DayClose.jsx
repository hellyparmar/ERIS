import React, { useState, useEffect } from 'react';
import { Calendar, DollarSign, TrendingUp, AlertTriangle, CheckCircle, Clock, RefreshCw, Unlock, Lock } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('pos_token') || ''}`,
});

const DayClose = () => {
    const { addToast } = useToast();
    const [dayStatus, setDayStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [openFloat, setOpenFloat] = useState('');
    const [openNotes, setOpenNotes] = useState('');
    const [physicalCash, setPhysicalCash] = useState('');
    const [chequesCount, setChequesCount] = useState('0');
    const [closeNotes, setCloseNotes] = useState('');
    const [reconciliation, setReconciliation] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/pos/day/status`, {
                headers: getAuthHeaders()
            });
            const data = await res.json();
            if (data.success) setDayStatus(data.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchStatus(); }, []);

    const handleOpenDay = async (e) => {
        e.preventDefault();
        if (!openFloat || isNaN(openFloat)) { addToast('Enter a valid opening float', 'error'); return; }
        setSubmitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/pos/day/open`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ opening_float: parseFloat(openFloat), notes: openNotes })
            });
            const data = await res.json();
            if (data.success) {
                addToast('Register opened successfully!', 'success');
                await fetchStatus();
            } else {
                addToast(data.detail || 'Failed to open register', 'error');
            }
        } catch (e) {
            addToast('Failed to open register', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const handleCloseDay = async (e) => {
        e.preventDefault();
        if (!physicalCash || isNaN(physicalCash)) { addToast('Enter physical cash count', 'error'); return; }
        setSubmitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/pos/day/close`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    physical_cash_count: parseFloat(physicalCash),
                    cheques_count: parseFloat(chequesCount || '0'),
                    notes: closeNotes
                })
            });
            const data = await res.json();
            if (data.success !== false) {
                setReconciliation(data);
                addToast('Register closed! Reconciliation complete.', 'success');
                await fetchStatus();
            } else {
                addToast(data.detail || 'Failed to close register', 'error');
            }
        } catch (e) {
            addToast('Failed to close register', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const statusColor = dayStatus?.status === 'open' ? 'text-green-400' : dayStatus?.status === 'closed' ? 'text-blue-400' : 'text-yellow-400';
    const statusIcon = dayStatus?.status === 'open' ? <Unlock className="w-5 h-5" /> : dayStatus?.status === 'closed' ? <Lock className="w-5 h-5" /> : <Clock className="w-5 h-5" />;

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                        Day Open / Close
                    </h1>
                    <p className="text-muted-foreground">Cash register management and end-of-day reconciliation</p>
                </div>
                <button onClick={fetchStatus} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary/50 text-muted-foreground hover:text-foreground transition-colors">
                    <RefreshCw className="w-4 h-4" /> Refresh
                </button>
            </div>

            {/* Current Status */}
            <GlassCard className="p-6">
                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-2 text-xl font-bold ${statusColor}`}>
                        {statusIcon}
                        {loading ? 'Loading...' : dayStatus ? `Register ${dayStatus.status?.replace('_', ' ')}` : 'Unknown'}
                    </div>
                    {dayStatus?.opening_float != null && (
                        <div className="flex gap-6 ml-auto text-sm text-muted-foreground">
                            <span>Opening Float: <strong className="text-foreground">₹{dayStatus.opening_float?.toLocaleString()}</strong></span>
                            {dayStatus.opened_at && <span>Opened: <strong className="text-foreground">{new Date(dayStatus.opened_at).toLocaleTimeString()}</strong></span>}
                            {dayStatus.closing_float != null && <span>Closing: <strong className="text-foreground">₹{dayStatus.closing_float?.toLocaleString()}</strong></span>}
                            {dayStatus.variance != null && (
                                <span className={dayStatus.variance === 0 ? 'text-green-400' : 'text-red-400'}>
                                    Variance: <strong>₹{dayStatus.variance?.toFixed(2)}</strong>
                                </span>
                            )}
                        </div>
                    )}
                </div>
            </GlassCard>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Open Day */}
                <GlassCard className="p-6">
                    <h2 className="text-xl font-bold gradient-text flex items-center gap-2 mb-6">
                        <Unlock className="w-5 h-5" /> Open Register
                    </h2>
                    {dayStatus?.status === 'open' ? (
                        <div className="flex flex-col items-center justify-center py-8 text-green-400">
                            <CheckCircle className="w-12 h-12 mb-3" />
                            <p className="font-semibold text-lg">Register is already open</p>
                            <p className="text-sm text-muted-foreground mt-1">Opening float: ₹{dayStatus.opening_float?.toLocaleString()}</p>
                        </div>
                    ) : (
                        <form onSubmit={handleOpenDay} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Opening Float (₹) *</label>
                                <input
                                    type="number" step="0.01" min="0"
                                    value={openFloat} onChange={e => setOpenFloat(e.target.value)}
                                    placeholder="e.g. 5000"
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Notes (optional)</label>
                                <input type="text" value={openNotes} onChange={e => setOpenNotes(e.target.value)}
                                    placeholder="Opening notes..."
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none"
                                />
                            </div>
                            <GradientButton type="submit" disabled={submitting} className="w-full">
                                <Unlock className="w-4 h-4 mr-2" />
                                {submitting ? 'Opening...' : 'Open Register'}
                            </GradientButton>
                        </form>
                    )}
                </GlassCard>

                {/* Close Day */}
                <GlassCard className="p-6">
                    <h2 className="text-xl font-bold gradient-text flex items-center gap-2 mb-6">
                        <Lock className="w-5 h-5" /> Close Register
                    </h2>
                    {dayStatus?.status !== 'open' ? (
                        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                            <Lock className="w-12 h-12 mb-3 opacity-40" />
                            <p className="font-semibold">Register not open</p>
                            <p className="text-sm mt-1">Open the register first to process sales</p>
                        </div>
                    ) : (
                        <form onSubmit={handleCloseDay} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Physical Cash Count (₹) *</label>
                                <input
                                    type="number" step="0.01" min="0"
                                    value={physicalCash} onChange={e => setPhysicalCash(e.target.value)}
                                    placeholder="Count cash in drawer"
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Cheques (₹)</label>
                                <input
                                    type="number" step="0.01" min="0"
                                    value={chequesCount} onChange={e => setChequesCount(e.target.value)}
                                    placeholder="0"
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Notes</label>
                                <input type="text" value={closeNotes} onChange={e => setCloseNotes(e.target.value)}
                                    placeholder="Closing notes..."
                                    className="w-full px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none"
                                />
                            </div>
                            <GradientButton type="submit" disabled={submitting} className="w-full">
                                <Lock className="w-4 h-4 mr-2" />
                                {submitting ? 'Closing...' : 'Close & Reconcile'}
                            </GradientButton>
                        </form>
                    )}
                </GlassCard>
            </div>

            {/* Reconciliation Result */}
            {reconciliation && (
                <GlassCard className="p-6">
                    <h2 className="text-xl font-bold gradient-text mb-6 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400" /> Reconciliation Results
                    </h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        {[
                            { label: 'Opening Float', value: `₹${reconciliation.opening_float?.toLocaleString()}`, color: 'text-blue-400' },
                            { label: 'Expected Cash', value: `₹${reconciliation.expected_cash?.toLocaleString()}`, color: 'text-yellow-400' },
                            { label: 'Physical Cash', value: `₹${reconciliation.physical_cash?.toLocaleString()}`, color: 'text-purple-400' },
                            { label: 'Variance', value: `₹${reconciliation.variance?.toFixed(2)}`, color: reconciliation.variance === 0 ? 'text-green-400' : 'text-red-400' },
                        ].map(({ label, value, color }) => (
                            <div key={label} className="text-center p-4 rounded-lg bg-secondary/30">
                                <p className="text-sm text-muted-foreground mb-1">{label}</p>
                                <p className={`text-2xl font-bold ${color}`}>{value}</p>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 text-center">
                        <span className={`px-4 py-2 rounded-full text-sm font-semibold ${reconciliation.reconciliation_status === 'matched' ? 'bg-green-500/20 text-green-400' :
                            reconciliation.reconciliation_status === 'small_variance' ? 'bg-yellow-500/20 text-yellow-400' :
                                'bg-red-500/20 text-red-400'
                            }`}>
                            {reconciliation.reconciliation_status?.replace('_', ' ').toUpperCase()}
                        </span>
                    </div>
                    {reconciliation.sales_summary && (
                        <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                            <div>Transactions: <strong className="text-foreground">{reconciliation.sales_summary.transaction_count}</strong></div>
                            <div>Total Sales: <strong className="text-foreground">₹{reconciliation.sales_summary.total_sales?.toLocaleString()}</strong></div>
                            <div>Cash Sales: <strong className="text-foreground">₹{reconciliation.sales_summary.cash_sales?.toLocaleString()}</strong></div>
                            <div>UPI Sales: <strong className="text-foreground">₹{reconciliation.sales_summary.upi_sales?.toLocaleString()}</strong></div>
                            <div>Card Sales: <strong className="text-foreground">₹{reconciliation.sales_summary.card_sales?.toLocaleString()}</strong></div>
                            <div>Khata Sales: <strong className="text-foreground">₹{reconciliation.sales_summary.khata_sales?.toLocaleString()}</strong></div>
                        </div>
                    )}
                </GlassCard>
            )}
        </div>
    );
};

export default DayClose;
