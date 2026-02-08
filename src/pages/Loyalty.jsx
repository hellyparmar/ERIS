import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
    Users,
    Gift,
    CreditCard,
    Send,
    AlertCircle,
    CheckCircle,
    Clock,
    Copy,
    Share2,
    HelpCircle,
    RefreshCw,
    UserPlus,
    TrendingUp
} from 'lucide-react';
import UnifiedCard from '../components/ui/UnifiedCard';
import ActionButton from '../components/ui/ActionButton';
import { useToast } from '../components/ui/Toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Loyalty = () => {
    const { addToast } = useToast();
    const [activeTab, setActiveTab] = useState('overview');
    const [copySuccess, setCopySuccess] = useState('');
    const [loading, setLoading] = useState(true);
    const [sendingReminder, setSendingReminder] = useState(null);

    // API Data State
    const [stats, setStats] = useState({
        referrals: { total: 0, converted: 0, pending: 0 },
        rewards: { total_earned: 0, pending: 0 },
        credit: { total_outstanding: 0, formatted: '₹0', customer_count: 0, at_risk_count: 0 }
    });
    const [creditCustomers, setCreditCustomers] = useState([]);
    const [topReferrers, setTopReferrers] = useState([]);
    const [referralCode, setReferralCode] = useState('LOADING...');

    // Fetch loyalty stats
    const fetchStats = useCallback(async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE}/api/loyalty/stats`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (error) {
            console.error('Error fetching loyalty stats:', error);
        }
    }, []);

    // Fetch credit customers
    const fetchCreditCustomers = useCallback(async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE}/api/loyalty/credit/customers?limit=20`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setCreditCustomers(data);
            }
        } catch (error) {
            console.error('Error fetching credit customers:', error);
        }
    }, []);

    // Fetch top referrers
    const fetchTopReferrers = useCallback(async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE}/api/loyalty/referrals/top-referrers?limit=5`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setTopReferrers(data);
            }
        } catch (error) {
            console.error('Error fetching top referrers:', error);
        }
    }, []);

    // Load all data on mount
    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            await Promise.all([
                fetchStats(),
                fetchCreditCustomers(),
                fetchTopReferrers()
            ]);
            // Generate a store referral code
            setReferralCode('STORE' + Math.random().toString(36).substring(2, 6).toUpperCase());
            setLoading(false);
        };
        loadData();
    }, [fetchStats, fetchCreditCustomers, fetchTopReferrers]);

    const copyToClipboard = () => {
        navigator.clipboard.writeText(referralCode);
        setCopySuccess('Copied!');
        addToast("Referral code copied to clipboard", "success");
        setTimeout(() => setCopySuccess(''), 2000);
    };

    const handleSendReminder = async (customer) => {
        setSendingReminder(customer.customer_id);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE}/api/loyalty/reminders/send`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    customer_id: customer.customer_id,
                    channel: 'whatsapp'
                })
            });

            if (response.ok) {
                await response.json();
                addToast(`WhatsApp payment reminder sent to ${customer.customer_name}`, "success");
            } else {
                const error = await response.json();
                addToast(error.detail || "Failed to send reminder", "error");
            }
        } catch (error) {
            console.error('Error sending reminder:', error);
            addToast("Failed to send reminder", "error");
        } finally {
            setSendingReminder(null);
        }
    };

    const handleBulkReminders = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE}/api/loyalty/reminders/bulk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    min_days_overdue: 1,
                    max_reminders: 10,
                    channel: 'whatsapp'
                })
            });

            if (response.ok) {
                const result = await response.json();
                addToast(`Auto-Reminders queued: ${result.sent + result.simulated} sent`, "success");
            } else {
                addToast("Failed to send bulk reminders", "error");
            }
        } catch (error) {
            console.error('Error sending bulk reminders:', error);
            addToast("Failed to send bulk reminders", "error");
        }
    };

    const handleSendInvites = async () => {
        addToast("Referral invites feature coming soon!", "info");
    };

    const handleRefresh = () => {
        fetchStats();
        fetchCreditCustomers();
        fetchTopReferrers();
        addToast("Data refreshed", "success");
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <RefreshCw className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    return (
        <div className="space-y-8 fade-in-up">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
            >
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">Loyalty & Credit</h1>
                    <p className="text-muted-foreground">Manage referrals and digital udhaar</p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRefresh}
                        className="p-2 hover:bg-white/10 rounded-lg text-muted-foreground hover:text-white transition-colors duration-200"
                        title="Refresh data"
                    >
                        <RefreshCw size={18} />
                    </button>
                    <div className="flex bg-white/5 p-1 rounded-lg">
                        {['overview', 'udhaar'].map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${activeTab === tab
                                    ? 'bg-blue-600 !text-white shadow-lg'
                                    : 'text-muted-foreground hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>
            </motion.div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <UnifiedCard className="p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-muted-foreground mb-1">Total Referrals</p>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">{stats.referrals.total}</h3>
                            <p className="text-xs text-muted-foreground mt-1 font-medium">
                                {stats.referrals.converted} converted
                            </p>
                        </div>
                        <div className="p-4 rounded-xl bg-blue-500 bg-opacity-80 dark:bg-opacity-90 shadow-lg flex items-center justify-center">
                            <Users className="w-6 h-6 text-white" strokeWidth={2.5} />
                        </div>
                    </div>
                </UnifiedCard>

                <UnifiedCard className="p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <p className="text-sm font-medium text-muted-foreground">Rewards Due</p>
                                <div className="group relative">
                                    <HelpCircle size={12} className="text-gray-500 cursor-help" />
                                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-black/90 text-xs text-white rounded text-center opacity-0 group-hover:opacity-100 transition pointer-events-none z-10">
                                        Total cashback owed to customers for successful referrals.
                                    </div>
                                </div>
                            </div>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
                                ₹{stats.rewards.pending.toLocaleString()}
                            </h3>
                        </div>
                        <div className="p-4 rounded-xl bg-purple-500 bg-opacity-80 dark:bg-opacity-90 shadow-lg flex items-center justify-center">
                            <Gift className="w-6 h-6 text-white" strokeWidth={2.5} />
                        </div>
                    </div>
                </UnifiedCard>

                <UnifiedCard className="p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <p className="text-muted-foreground text-xs uppercase tracking-wider">Active Credit</p>
                                <div className="group relative">
                                    <HelpCircle size={12} className="text-gray-500 cursor-help" />
                                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-black/90 text-xs text-white rounded text-center opacity-0 group-hover:opacity-100 transition pointer-events-none z-10">
                                        Total OUTSTANDING credit (Udhaar) given to customers.
                                    </div>
                                </div>
                            </div>
                            <h3 className="text-2xl font-bold text-foreground">{stats.credit.formatted}</h3>
                            <p className="text-xs text-muted-foreground mt-1 font-medium">
                                {stats.credit.at_risk_count} at risk
                            </p>
                        </div>
                        <div className="p-3 rounded-lg bg-yellow-500/20 text-yellow-400">
                            <CreditCard size={20} />
                        </div>
                    </div>
                </UnifiedCard>

                <UnifiedCard className="p-6 relative overflow-hidden group">
                    <div className="relative z-10">
                        <p className="text-muted-foreground text-xs font-medium mb-2 uppercase tracking-wider">Referral Code</p>
                        <div className="flex items-center justify-between gap-2 bg-secondary p-3 rounded-lg border border-border group-hover:border-primary/50 transition w-full">
                            <code className="text-xl font-mono text-primary font-bold tracking-widest truncate">{referralCode}</code>
                            <button onClick={copyToClipboard} className="text-muted-foreground hover:text-foreground shrink-0">
                                {copySuccess ? <CheckCircle size={16} className="text-green-500" /> : <Copy size={16} />}
                            </button>
                        </div>
                        <div className="mt-2 text-xs text-gray-500 dark:text-muted-foreground flex items-center gap-1">
                            <Share2 size={12} /> Share link active
                        </div>
                    </div>
                </UnifiedCard>
            </div>

            {/* TAB CONTENT: UDHAAR (Active Credit) */}
            {activeTab === 'udhaar' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                        <UnifiedCard className="overflow-hidden">
                            <div className="p-6 border-b border-white/10 flex justify-between items-center">
                                <h3 className="font-bold text-white">Digital Udhaar (Credit Accounts)</h3>
                                <ActionButton size="sm" className="text-xs" onClick={() => addToast("Add Credit User Modal Opened", "info")}>
                                    <UserPlus size={14} className="mr-1" /> Add Credit User
                                </ActionButton>
                            </div>
                            {creditCustomers.length === 0 ? (
                                <div className="p-8 text-center text-muted-foreground">
                                    <CreditCard size={48} className="mx-auto mb-4 opacity-50" />
                                    <p>No customers with active credit found</p>
                                </div>
                            ) : (
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-white/5 text-muted-foreground text-xs uppercase">
                                        <tr>
                                            <th className="px-6 py-4">Customer</th>
                                            <th className="px-6 py-4">Utilization</th>
                                            <th className="px-6 py-4">Balance</th>
                                            <th className="px-6 py-4">Trust Score</th>
                                            <th className="px-6 py-4 text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {creditCustomers.map((cust) => (
                                            <tr key={cust.customer_id} className="hover:bg-white/5 transition-colors">
                                                <td className="px-6 py-4">
                                                    <div className="font-medium text-white">{cust.customer_name}</div>
                                                    <div className="text-xs text-gray-500">
                                                        Last paid: {cust.last_payment_date || 'Never'}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-24 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                                            <div
                                                                className={`h-full rounded-full ${cust.status === 'critical' ? 'bg-red-500' :
                                                                    cust.status === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
                                                                    }`}
                                                                style={{ width: `${Math.min(cust.utilization, 100)}%` }}
                                                            ></div>
                                                        </div>
                                                        <span className="text-xs text-muted-foreground">{cust.utilization}%</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 font-bold text-white">
                                                    ₹{cust.balance.toLocaleString()}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold ${cust.credit_score >= 700 ? 'bg-green-500/20 text-green-400' :
                                                        cust.credit_score >= 600 ? 'bg-yellow-500/20 text-yellow-400' :
                                                            'bg-red-500/20 text-red-400'
                                                        }`}>
                                                        {cust.credit_score}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <button
                                                        onClick={() => handleSendReminder(cust)}
                                                        disabled={sendingReminder === cust.customer_id}
                                                        className="p-2 hover:bg-white/10 rounded-full text-blue-400 transition hover:text-blue-300 disabled:opacity-50"
                                                        title="Send WhatsApp Reminder"
                                                    >
                                                        {sendingReminder === cust.customer_id ? (
                                                            <RefreshCw size={16} className="animate-spin" />
                                                        ) : (
                                                            <Send size={16} />
                                                        )}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </UnifiedCard>
                    </div>

                    <div className="lg:col-span-1 space-y-6">
                        <UnifiedCard className="p-6 bg-gradient-to-br from-red-900/20 to-orange-900/10 border-red-500/30">
                            <div className="flex items-start gap-4">
                                <div className="p-3 bg-red-500/20 rounded-lg text-red-400">
                                    <AlertCircle size={24} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-white mb-1">Overdue Risks</h3>
                                    <p className="text-sm text-muted-foreground mb-4">
                                        {stats.credit.at_risk_count} customers exceed safe credit utilization limits.
                                        Immediate action recommended.
                                    </p>
                                    <ActionButton
                                        size="sm"
                                        variant="secondary"
                                        className="w-full"
                                        onClick={handleBulkReminders}
                                    >
                                        Auto-Send Reminders
                                    </ActionButton>
                                </div>
                            </div>
                        </UnifiedCard>

                        <UnifiedCard className="p-6">
                            <h3 className="font-bold text-white mb-4">Credit Policy</h3>
                            <ul className="space-y-3 text-sm text-muted-foreground">
                                <li className="flex items-center gap-2">
                                    <CheckCircle size={14} className="text-green-500" /> Max Limit: ₹50,000 / customer
                                </li>
                                <li className="flex items-center gap-2">
                                    <CheckCircle size={14} className="text-green-500" /> Interest-free period: 45 days
                                </li>
                                <li className="flex items-center gap-2">
                                    <Clock size={14} className="text-yellow-500" /> Auto-lock at 90 days overdue
                                </li>
                            </ul>
                        </UnifiedCard>
                    </div>
                </div>
            )}

            {/* TAB CONTENT: OVERVIEW (Referrals) */}
            {activeTab === 'overview' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <UnifiedCard className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-white">Top Referrers</h3>
                            <TrendingUp size={18} className="text-green-400" />
                        </div>
                        {topReferrers.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <Users size={48} className="mx-auto mb-4 opacity-50" />
                                <p className="text-muted-foreground">No referrers yet. Start the program!</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {topReferrers.map((referrer) => (
                                    <div key={referrer.customer_id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                                                {referrer.name?.charAt(0) || '#'}
                                            </div>
                                            <div>
                                                <p className="text-white font-medium">{referrer.name}</p>
                                                <p className="text-xs text-gray-500">{referrer.referral_count} Successful Invites</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-green-400 font-bold">+₹{referrer.total_earned.toLocaleString()}</p>
                                            <p className="text-xs text-gray-500">Earned</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </UnifiedCard>

                    <UnifiedCard className="p-6 flex flex-col justify-center items-center text-center">
                        <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400 mb-4">
                            <Share2 size={32} />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Invite New Customers</h3>
                        <p className="text-muted-foreground mb-6 max-w-xs">
                            Send invites via SMS or WhatsApp. Both you and the new customer earn ₹100 store credit.
                        </p>
                        <ActionButton
                            className="w-full max-w-sm flex flex-row items-center justify-center gap-2 whitespace-nowrap bg-blue-600 hover:bg-blue-700 text-white"
                            onClick={handleSendInvites}
                        >
                            Send Invites <Send size={16} />
                        </ActionButton>
                    </UnifiedCard>
                </div>
            )}
        </div>
    );
};

export default Loyalty;
