/**
 * Enterprise Retail Intelligence System v3.0
 * COMPLIANCE HUB - GST compliance and tax reporting
 */

import { useState, useMemo } from 'react';
import {
    Scale, FileText, Shield, CheckCircle, Calendar, Download,
    AlertTriangle, TrendingUp, DollarSign, Clock, Filter
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import ActionButton from '../components/ui/ActionButton';
import {
    generateTaxTransactions,
    calculateTaxSummary,
    getComplianceStatus,
    formatCurrency,
    GST_RATES
} from '../utils/taxCalculations';

const Compliance = () => {
    const [transactions] = useState(() => generateTaxTransactions(100));

    // Calculate summaries
    const taxSummary = useMemo(() => calculateTaxSummary(transactions), [transactions]);
    const complianceStatus = useMemo(() => getComplianceStatus(transactions), [transactions]);

    // Format deadline
    const formatDeadline = (date) => {
        const days = Math.ceil((date - new Date()) / (1000 * 60 * 60 * 24));
        return { date: date.toLocaleDateString('en-IN'), days };
    };

    const deadline = formatDeadline(complianceStatus.nextDeadline);

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                    Compliance Hub
                </h1>
                <p className="text-muted-foreground">
                    GST compliance tracking and tax reporting dashboard
                </p>
            </div>

            {/* Compliance Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-1">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Total Revenue</p>
                            <p className="text-3xl font-bold text-foreground">
                                {formatCurrency(taxSummary.totalRevenue)}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                +12.5% vs last month
                            </p>
                        </div>
                        <div className="p-3 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20">
                            <TrendingUp className="text-success" size={24} />
                        </div>
                    </div>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-2">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Next Deadline</p>
                            <p className="text-2xl font-bold text-foreground">
                                {deadline.days} days
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                {deadline.date}
                            </p>
                        </div>
                        <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                            <Calendar className="text-purple-500" size={24} />
                        </div>
                    </div>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-3">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Compliance Status</p>
                            <p className="text-3xl font-bold text-foreground">
                                {complianceStatus.status}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                {complianceStatus.filingRate}% filed
                            </p>
                        </div>
                        <div className={`p-3 rounded-xl ${complianceStatus.status === 'Compliant' ? 'bg-gradient-to-br from-green-500/20 to-emerald-500/20' :
                            complianceStatus.status === 'Warning' ? 'bg-gradient-to-br from-yellow-500/20 to-orange-500/20' :
                                'bg-gradient-to-br from-red-500/20 to-pink-500/20'
                            }`}>
                            {complianceStatus.status === 'Compliant' ? (
                                <CheckCircle className="text-success" size={24} />
                            ) : (
                                <AlertTriangle className={complianceStatus.status === 'Warning' ? 'text-warning' : 'text-danger'} size={24} />
                            )}
                        </div>
                    </div>
                </GlassCard>

                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-4">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Total GST Collected</p>
                            <p className="text-3xl font-bold text-foreground">
                                {formatCurrency(taxSummary.totalGST)}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                From {taxSummary.totalTransactions} transactions
                            </p>
                        </div>
                        <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20">
                            <DollarSign className="text-blue-500" size={24} />
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* GST Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* GST by Rate */}
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-1">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                        GST Collection by Rate
                    </h2>
                    <div className="space-y-3">
                        {Object.entries(taxSummary.byRate).map(([rate, data]) => (
                            <div key={rate} className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 border border-border">
                                <div>
                                    <p className="text-sm text-muted-foreground">GST @ {rate}%</p>
                                    <p className="text-lg font-bold text-foreground">{formatCurrency(data.gst)}</p>
                                    <p className="text-xs text-muted-foreground">{data.count} transactions</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm text-muted-foreground">Revenue</p>
                                    <p className="text-lg font-semibold text-foreground">
                                        {formatCurrency(data.revenue)}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassCard>

                {/* GST by Category */}
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-2">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-4">
                        GST by Category
                    </h2>
                    <div className="space-y-3">
                        {Object.entries(taxSummary.byCategory).slice(0, 6).map(([category, data]) => (
                            <div key={category} className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 border border-border">
                                <div>
                                    <p className="text-sm font-semibold text-foreground">{category}</p>
                                    <p className="text-xs text-muted-foreground">{data.count} transactions</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-lg font-bold text-foreground">{formatCurrency(data.gst)}</p>
                                    <p className="text-xs text-muted-foreground">{formatCurrency(data.revenue)} revenue</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            </div>

            {/* Recent Transactions */}
            <GlassCard variant="gradient" className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                        Recent Tax Transactions
                    </h2>
                    <ActionButton variant="secondary" icon={Download}>
                        Export Report
                    </ActionButton>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-border">
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    Invoice
                                </th>
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    Date
                                </th>
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    Category
                                </th>
                                <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    Base Amount
                                </th>
                                <th className="text-center py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    GST Rate
                                </th>
                                <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    GST Amount
                                </th>
                                <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    Total
                                </th>
                                <th className="text-center py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">
                                    Status
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {transactions.slice(0, 15).map((txn, idx) => (
                                <tr
                                    key={txn.id}
                                    className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5 transition-all"
                                >
                                    <td className="py-3 px-4">
                                        <p className="font-semibold text-foreground text-sm">{txn.invoiceNumber}</p>
                                    </td>
                                    <td className="py-3 px-4">
                                        <p className="text-sm text-muted-foreground">
                                            {txn.date.toLocaleDateString('en-IN')}
                                        </p>
                                    </td>
                                    <td className="py-3 px-4">
                                        <p className="text-sm text-foreground">{txn.category}</p>
                                    </td>
                                    <td className="py-3 px-4 text-right">
                                        <p className="text-sm text-foreground">₹{txn.basePrice.toFixed(2)}</p>
                                    </td>
                                    <td className="py-3 px-4 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${txn.gstRate === 5 ? 'bg-green-500/20 text-green-500' :
                                            txn.gstRate === 12 ? 'bg-blue-500/20 text-blue-500' :
                                                txn.gstRate === 18 ? 'bg-purple-500/20 text-purple-500' :
                                                    'bg-yellow-500/20 text-yellow-500'
                                            }`}>
                                            {txn.gstRate}%
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-right">
                                        <p className="text-sm font-semibold text-foreground">₹{txn.gstAmount.toFixed(2)}</p>
                                    </td>
                                    <td className="py-3 px-4 text-right">
                                        <p className="text-sm font-bold text-foreground">₹{txn.finalPrice.toFixed(2)}</p>
                                    </td>
                                    <td className="py-3 px-4 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${txn.status === 'Filed' ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
                                            }`}>
                                            {txn.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </GlassCard>
        </div>
    );
};

export default Compliance;
