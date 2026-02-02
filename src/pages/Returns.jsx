import React, { useState } from 'react';
import {
    RotateCcw,
    Plus,
    Search,
    CheckCircle,
    XCircle,
    Clock,
    Package,
    DollarSign,
    Upload,
    Eye
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';

const Returns = () => {
    const [statusFilter, setStatusFilter] = useState('all');

    const returns = [
        { id: 'RMA-001', orderId: '#12345', product: 'Wireless Headphones', customer: 'John Doe', reason: 'Defective', quantity: 1, amount: 1250, status: 'pending', date: '2026-02-01', rmaDate: '2026-02-05' },
        { id: 'RMA-002', orderId: '#12346', product: 'Smart Watch', customer: 'Jane Smith', reason: 'Wrong Item', quantity: 1, amount: 4500, status: 'approved', date: '2026-01-30', rmaDate: '2026-02-03' },
        { id: 'RMA-003', orderId: '#12347', product: 'Laptop Stand', customer: 'Bob Wilson', reason: 'Not as described', quantity: 2, amount: 760, status: 'refunded', date: '2026-01-28', rmaDate: '2026-02-01' },
        { id: 'RMA-004', orderId: '#12348', product: 'USB-C Cable', customer: 'Alice Brown', reason: 'Damaged', quantity: 3, amount: 180, status: 'rejected', date: '2026-01-29', rmaDate: null }
    ];

    const stats = {
        pending: returns.filter(r => r.status === 'pending').length,
        approved: returns.filter(r => r.status === 'approved').length,
        refunded: returns.filter(r => r.status === 'refunded').length,
        totalAmount: returns.reduce((sum, r) => sum + r.amount, 0)
    };

    const filteredReturns = statusFilter === 'all' ? returns : returns.filter(r => r.status === statusFilter);

    const getStatusBadge = (status) => {
        const styles = {
            pending: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
            approved: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
            refunded: 'bg-green-500/10 text-green-500 border-green-500/20',
            rejected: 'bg-red-500/10 text-red-500 border-red-500/20'
        };
        const icons = {
            pending: Clock,
            approved: CheckCircle,
            refunded: CheckCircle,
            rejected: XCircle
        };
        const Icon = icons[status];
        return (
            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border ${styles[status]}`}>
                <Icon className="w-3 h-3" />
                {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
        );
    };

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">Returns & Refunds</h1>
                    <p className="text-muted-foreground">Manage return requests and refund processing</p>
                </div>
                <GradientButton onClick={() => { }}>
                    <Plus className="w-4 h-4 mr-2" />
                    New Return
                </GradientButton>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-amber-500/20">
                            <Clock className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Pending</p>
                            <p className="text-2xl font-bold gradient-text">{stats.pending}</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-blue-500/20">
                            <CheckCircle className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Approved</p>
                            <p className="text-2xl font-bold gradient-text">{stats.approved}</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-green-500/20">
                            <DollarSign className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Refunded</p>
                            <p className="text-2xl font-bold gradient-text">{stats.refunded}</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-purple-500/20">
                            <RotateCcw className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Total Amount</p>
                            <p className="text-2xl font-bold gradient-text">₹{stats.totalAmount.toLocaleString()}</p>
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* Returns List */}
            <GlassCard className="p-6">
                <div className="flex gap-3 mb-6">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search returns..."
                            className="w-full pl-12 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground focus:border-primary focus:outline-none"
                        />
                    </div>
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground focus:border-primary focus:outline-none"
                    >
                        <option value="all">All Status</option>
                        <option value="pending">Pending</option>
                        <option value="approved">Approved</option>
                        <option value="refunded">Refunded</option>
                        <option value="rejected">Rejected</option>
                    </select>
                </div>

                <div className="space-y-4">
                    {filteredReturns.map((ret) => (
                        <div key={ret.id} className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 hover:from-primary/10 hover:to-purple/10 transition-all">
                            <div className="flex justify-between items-start mb-3">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h4 className="font-bold text-foreground">{ret.id}</h4>
                                        {getStatusBadge(ret.status)}
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                        <div>
                                            <p className="text-xs text-muted-foreground">Order ID</p>
                                            <p className="font-medium text-foreground">{ret.orderId}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-muted-foreground">Product</p>
                                            <p className="font-medium text-foreground">{ret.product}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-muted-foreground">Customer</p>
                                            <p className="font-medium text-foreground">{ret.customer}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-muted-foreground">Reason</p>
                                            <p className="font-medium text-foreground">{ret.reason}</p>
                                        </div>
                                    </div>
                                    <div className="flex gap-6 mt-3 text-xs text-muted-foreground">
                                        <span>Qty: {ret.quantity}</span>
                                        <span>Amount: ₹{ret.amount.toLocaleString()}</span>
                                        <span>Requested: {ret.date}</span>
                                        {ret.rmaDate && <span>Expected Return: {ret.rmaDate}</span>}
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    {ret.status === 'pending' && (
                                        <>
                                            <button className="px-4 py-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 text-sm font-semibold transition-colors">
                                                Approve
                                            </button>
                                            <button className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 text-sm font-semibold transition-colors">
                                                Reject
                                            </button>
                                        </>
                                    )}
                                    {ret.status === 'approved' && (
                                        <button className="px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 text-sm font-semibold transition-colors">
                                            Process Refund
                                        </button>
                                    )}
                                    <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                        <Eye className="w-4 h-4 text-blue-400" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </GlassCard>
        </div>
    );
};

export default Returns;
