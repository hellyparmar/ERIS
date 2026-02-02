/**
 * Enterprise Retail Intelligence System v3.0
 * ALERTS PAGE - Real-time Notification System
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    AlertTriangle,
    AlertCircle,
    Info,
    CheckCircle,
    TrendingDown,
    Package,
    DollarSign,
    Clock,
    Filter,
    X
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import '../modern-design.css';

const Alerts = () => {
    const [filterSeverity, setFilterSeverity] = useState('all');
    const [filterCategory, setFilterCategory] = useState('all');

    // Alert data
    const [alerts] = useState([
        {
            id: 1,
            severity: 'critical',
            category: 'stock',
            title: 'Critical Stock Level',
            description: 'Premium Headphones inventory critically low (5 units remaining)',
            timestamp: '2 minutes ago',
            read: false,
            action: 'Create Purchase Order',
            icon: Package,
            color: 'red'
        },
        {
            id: 2,
            severity: 'warning',
            category: 'stock',
            title: 'Low Stock Alert',
            description: 'Wireless Mouse approaching reorder point (18 units left)',
            timestamp: '15 minutes ago',
            read: false,
            action: 'View Stock Details',
            icon: Package,
            color: 'yellow'
        },
        {
            id: 3,
            severity: 'info',
            category: 'sales',
            title: 'Sales Milestone Achieved',
            description: 'Daily sales target of ₹50,000 reached! Current: ₹52,340',
            timestamp: '1 hour ago',
            read: true,
            action: 'View Report',
            icon: DollarSign,
            color: 'green'
        },
        {
            id: 4,
            severity: 'critical',
            category: 'forecast',
            title: 'Demand Spike Predicted',
            description: 'AI forecasts 35% demand increase for Designer T-Shirts in next 7 days',
            timestamp: '2 hours ago',
            read: false,
            action: 'Adjust Inventory',
            icon: TrendingDown,
            color: 'purple'
        },
        {
            id: 5,
            severity: 'warning',
            category: 'system',
            title: 'Sync Pending',
            description: 'Tally synchronization delayed - 23 transactions pending',
            timestamp: '3 hours ago',
            read: true,
            action: 'Retry Sync',
            icon: AlertCircle,
            color: 'orange'
        },
        {
            id: 6,
            severity: 'info',
            category: 'stock',
            title: 'Restock Completed',
            description: 'Organic Coffee Beans restocked successfully (75 units added)',
            timestamp: '5 hours ago',
            read: true,
            action: 'View Details',
            icon: CheckCircle,
            color: 'blue'
        },
        {
            id: 7,
            severity: 'critical',
            category: 'stock',
            title: 'Out of Stock',
            description: 'Yoga Mat Pro is completely out of stock - 3 pending orders',
            timestamp: '6 hours ago',
            read: false,
            action: 'Urgent Reorder',
            icon: Package,
            color: 'red'
        },
        {
            id: 8,
            severity: 'info',
            category: 'sales',
            title: 'New Customer Record',
            description: 'Total customers reached 850+ milestone today',
            timestamp: '8 hours ago',
            read: true,
            action: 'View Analytics',
            icon: CheckCircle,
            color: 'green'
        }
    ]);

    const getSeverityIcon = (severity) => {
        switch (severity) {
            case 'critical':
                return <AlertTriangle size={20} />;
            case 'warning':
                return <AlertCircle size={20} />;
            case 'info':
                return <Info size={20} />;
            default:
                return <Info size={20} />;
        }
    };

    const handleDismiss = (id) => {
        // In a real app, this would make an API call
        // const updatedAlerts = alerts.filter(a => a.id !== id);
        alert("Alert dismissed! (In full version this will remove the alert)");
    };

    const handleAction = async (action, alertDetails) => {
        if (action === 'Create Purchase Order') {
            try {
                // Trigger PDF download from backend
                const response = await fetch(`http://localhost:8000/api/v1/reports/purchase-order/download?item_id=PRD001&quantity=50`);
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = "Purchase_Order_PRD001.pdf";
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    alert("Purchase Order Generated & Downloaded!");
                } else {
                    alert("Failed to generate PDF. Check backend.");
                }
            } catch (e) {
                console.error(e);
                alert("Error connecting to server.");
            }
        } else {
            alert(`Action triggered: ${action}`);
        }
    };

    const getSeverityColor = (severity) => {
        switch (severity) {
            case 'critical':
                return 'bg-red-500/20 border-red-500/30 text-red-400';
            case 'warning':
                return 'bg-yellow-500/20 border-yellow-500/30 text-yellow-400';
            case 'info':
                return 'bg-blue-500/20 border-blue-500/30 text-blue-400';
            default:
                return 'bg-gray-500/20 border-gray-500/30 text-gray-400';
        }
    };

    const getCategoryColor = (category) => {
        switch (category) {
            case 'stock':
                return 'text-purple-400';
            case 'sales':
                return 'text-green-400';
            case 'forecast':
                return 'text-orange-400';
            case 'system':
                return 'text-blue-400';
            default:
                return 'text-gray-400';
        }
    };

    // Filter alerts
    const filteredAlerts = alerts.filter(alert => {
        const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity;
        const matchesCategory = filterCategory === 'all' || alert.category === filterCategory;
        return matchesSeverity && matchesCategory;
    });

    // Count alerts by severity
    const criticalCount = alerts.filter(a => a.severity === 'critical').length;
    const warningCount = alerts.filter(a => a.severity === 'warning').length;
    const infoCount = alerts.filter(a => a.severity === 'info').length;
    const unreadCount = alerts.filter(a => !a.read).length;

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                    Alerts & Notifications
                </h1>
                <p className="text-muted-foreground">Real-time system alerts and actionable insights</p>
            </motion.div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-1">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-400 text-sm mb-1">Total Alerts</p>
                            <p className="text-3xl font-bold text-gray-900 dark:text-white">{alerts.length}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-blue-600/20 border border-blue-500/30">
                            <AlertCircle size={24} className="text-blue-400" />
                        </div>
                    </div>
                    <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                        <span className="px-2 py-1 bg-white/10 rounded">{unreadCount} unread</span>
                    </div>
                </GlassCard>

                <GlassCard
                    variant="gradient"
                    onClick={() => setFilterSeverity('critical')}
                    className={`p-6 cursor-pointer transition-all hover:scale-105 hover:shadow-glow-danger animate-slide-up stagger-2 ${filterSeverity === 'critical' ? 'ring-2 ring-danger shadow-glow-danger' : ''
                        }`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-400 text-sm mb-1">Critical</p>
                            <p className="text-3xl font-bold text-gray-900 dark:text-white">{criticalCount}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-red-600/20 border border-red-500/30">
                            <AlertTriangle size={24} className="text-red-400" />
                        </div>
                    </div>
                    <p className="mt-3 text-xs text-red-400 font-medium">Requires immediate action</p>
                </GlassCard>

                <GlassCard
                    variant="gradient"
                    onClick={() => setFilterSeverity('warning')}
                    className={`p-6 cursor-pointer transition-all hover:scale-105 hover:shadow-glow-warning animate-slide-up stagger-3 ${filterSeverity === 'warning' ? 'ring-2 ring-warning shadow-glow-warning' : ''
                        }`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-400 text-sm mb-1">Warnings</p>
                            <p className="text-3xl font-bold text-gray-900 dark:text-white">{warningCount}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-yellow-600/20 border border-yellow-500/30">
                            <AlertCircle size={24} className="text-yellow-400" />
                        </div>
                    </div>
                    <p className="mt-3 text-xs text-yellow-400 font-medium">Attention needed</p>
                </GlassCard>

                <GlassCard
                    variant="gradient"
                    onClick={() => setFilterSeverity('info')}
                    className={`p-6 cursor-pointer transition-all hover:scale-105 hover:shadow-glow-primary animate-slide-up stagger-4 ${filterSeverity === 'info' ? 'ring-2 ring-primary shadow-glow-primary' : ''
                        }`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-400 text-sm mb-1">Info</p>
                            <p className="text-3xl font-bold text-gray-900 dark:text-white">{infoCount}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-blue-600/20 border border-blue-500/30">
                            <Info size={24} className="text-blue-400" />
                        </div>
                    </div>
                    <p className="mt-3 text-xs text-blue-400 font-medium">Informational updates</p>
                </GlassCard>
            </div>

            {/* Filters */}
            <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-5">
                <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Filter size={20} className="text-gray-400" />
                        <span className="text-gray-400">Filters:</span>
                    </div>

                    <div className="flex gap-2">
                        <button
                            onClick={() => setFilterSeverity('all')}
                            className={`px-4 py-2 rounded-lg transition ${filterSeverity === 'all'
                                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/30'
                                : 'bg-gray-100 dark:bg-slate-800/50 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-700 border border-transparent dark:border-white/10'
                                }`}
                        >
                            All
                        </button>
                        <button
                            onClick={() => setFilterSeverity('critical')}
                            className={`px-4 py-2 rounded-lg transition ${filterSeverity === 'critical'
                                ? 'bg-red-600 text-white'
                                : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/20'
                                }`}
                        >
                            Critical ({criticalCount})
                        </button>
                        <button
                            onClick={() => setFilterSeverity('warning')}
                            className={`px-4 py-2 rounded-lg transition ${filterSeverity === 'warning'
                                ? 'bg-yellow-600 text-white'
                                : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/20'
                                }`}
                        >
                            Warnings ({warningCount})
                        </button>
                        <button
                            onClick={() => setFilterSeverity('info')}
                            className={`px-4 py-2 rounded-lg transition ${filterSeverity === 'info'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/20'
                                }`}
                        >
                            Info ({infoCount})
                        </button>
                    </div>

                    <div className="ml-auto flex gap-2">
                        <button className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-gray-400 text-sm transition">
                            Mark All as Read
                        </button>
                        <button className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-gray-400 text-sm transition">
                            Clear All
                        </button>
                    </div>
                </div>
            </GlassCard>

            {/* Alerts List */}
            <div className="space-y-4">
                {filteredAlerts.length === 0 ? (
                    <GlassCard variant="gradient" className="p-12 text-center">
                        <CheckCircle className="mx-auto mb-4 text-green-400" size={48} />
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No Alerts</h3>
                        <p className="text-gray-400">All caught up! No alerts for this filter.</p>
                    </GlassCard>
                ) : (
                    filteredAlerts.map((alert, idx) => {
                        const isPulse = alert.severity === 'critical' && !alert.read;
                        return (
                            <motion.div
                                key={alert.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.05 }}
                            >
                                <GlassCard
                                    variant="gradient"
                                    className={`p-6 transition-all ${!alert.read ? 'border-l-4 border-primary' : ''
                                        } ${isPulse ? 'animate-pulse-custom ring-2 ring-danger/50' : ''
                                        }`}
                                >
                                    <div className="flex items-start gap-4">
                                        {/* Icon */}
                                        <div className={`p-3 rounded-lg ${getSeverityColor(alert.severity)} relative`}>
                                            {isPulse && (
                                                <span className="absolute inset-0 rounded-lg bg-danger/20 animate-ping" />
                                            )}
                                            <div className="relative z-10">
                                                {getSeverityIcon(alert.severity)}
                                            </div>
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1">
                                            <div className="flex items-start justify-between mb-2">
                                                <div>
                                                    <div className="flex items-center gap-3 mb-1">
                                                        <h3 className="text-lg font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
                                                            {alert.title}
                                                        </h3>
                                                        {!alert.read && (
                                                            <span className="px-2 py-1 bg-primary/20 border border-primary/30 text-primary text-xs rounded-full font-semibold animate-pulse-custom">
                                                                NEW
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-muted-foreground text-sm">{alert.description}</p>
                                                </div>
                                                <button className="p-2 hover:bg-white/10 rounded-lg transition">
                                                    <X size={20} className="text-muted-foreground" />
                                                </button>
                                            </div>

                                            <div className="flex items-center justify-between mt-4">
                                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                                    <span className="flex items-center gap-1">
                                                        <Clock size={14} />
                                                        {alert.timestamp}
                                                    </span>
                                                    <span className={`capitalize font-medium ${getCategoryColor(alert.category)}`}>
                                                        {alert.category}
                                                    </span>
                                                </div>

                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleAction(alert.action, alert)}
                                                        className="px-4 py-2 bg-gradient-to-r from-primary to-purple hover:shadow-lg hover:shadow-primary/30 rounded-lg text-white text-sm transition-all font-medium"
                                                    >
                                                        {alert.action}
                                                    </button>
                                                    <button
                                                        onClick={() => handleDismiss(alert.id)}
                                                        className="px-4 py-2 bg-muted/30 hover:bg-muted/50 rounded-lg text-foreground text-sm transition-all font-medium border border-border"
                                                    >
                                                        Dismiss
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </GlassCard>
                            </motion.div>
                        );
                    })
                )}
            </div>

            {/* Pagination */}
            {filteredAlerts.length > 0 && (
                <div className="flex items-center justify-center gap-2">
                    <button className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-gray-400 text-sm transition">
                        Previous
                    </button>
                    <span className="px-4 py-2 text-gray-400 text-sm">Page 1 of 1</span>
                    <button className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-gray-400 text-sm transition">
                        Next
                    </button>
                </div>
            )}
        </div>
    );
};

export default Alerts;
