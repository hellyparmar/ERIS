/**
 * Enterprise Retail Intelligence System v3.0
 * ALERTS PAGE - Real-time Notification System
 * Refactored with Enterprise Design System
 */

import React, { useState, useEffect } from 'react';
import { API_BASE } from '../lib/api';
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
import UnifiedCard from '../components/ui/UnifiedCard';
import ActionButton from '../components/ui/ActionButton';
import { useToast } from '../components/ui/Toast';

const Alerts = () => {
    const { addToast } = useToast();
    const [filterSeverity, setFilterSeverity] = useState('all');
    const [filterCategory] = useState('all');
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalAlerts, setTotalAlerts] = useState(0);
    const perPage = 50;

    useEffect(() => {
        fetchAlerts();
    }, [currentPage, filterSeverity]);

    const fetchAlerts = async () => {
        try {
            setLoading(true);
            // Fetch with backend pagination: page and per_page parameters
            const severityParam = filterSeverity !== 'all' ? `&severity=${filterSeverity}` : '';
            const response = await fetch(`${API_BASE}/api/v1/alerts/list?page=${currentPage}&per_page=${perPage}${severityParam}`);
            const data = await response.json();
            if (data.success && data.data) {
                // Transform API data to component format
                const transformed = data.data.items.map(alert => ({
                    id: alert.id,
                    severity: alert.severity,
                    category: alert.category,
                    title: alert.title,
                    description: alert.message,
                    timestamp: new Date(alert.created_at).toLocaleString(),
                    read: alert.is_acknowledged,
                    action: alert.severity === 'critical' ? 'Take Action' : 'View Details',
                    icon: getIconForCategory(alert.category),
                    color: getSeverityColor(alert.severity)
                }));
                setAlerts(transformed);
                setTotalPages(data.data.pagination.total_pages);
                setTotalAlerts(data.data.pagination.total);
            }
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
            addToast('Failed to load alerts', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleAcknowledge = async (alertId) => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/alerts/${alertId}/acknowledge`, {
                method: 'PATCH'
            });
            const data = await response.json();
            if (data.success) {
                addToast('Alert acknowledged', 'success');
                fetchAlerts(); // Refresh list
            }
        } catch (error) {
            console.error('Failed to acknowledge alert:', error);
            addToast('Failed to acknowledge alert', 'error');
        }
    };

    const getIconForCategory = (category) => {
        const icons = {
            'stock': Package,
            'sales': DollarSign,
            'forecast': TrendingDown,
            'system': AlertCircle
        };
        return icons[category] || Info;
    };

    const getSeverityColor = (severity) => {
        const colors = {
            'critical': 'red',
            'warning': 'yellow',
            'info': 'blue'
        };
        return colors[severity] || 'gray';
    };

    const categories = ['all', 'stock', 'sales', 'forecast', 'system'];

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

    const handleDismiss = () => {
        alert("Alert dismissed! (In full version this will remove the alert)");
    };

    const handleAction = async (action) => {
        if (action === 'Create Purchase Order') {
            try {
                const response = await fetch(`${API_BASE}/api/v1/reports/purchase-order/download?item_id=PRD001&quantity=50`);
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

    const getCategoryColor = (category) => {
        switch (category) {
            case 'stock':
                return 'text-purple-600 dark:text-purple-400';
            case 'sales':
                return 'text-green-600 dark:text-green-400';
            case 'forecast':
                return 'text-orange-600 dark:text-orange-400';
            case 'system':
                return 'text-primary';
            default:
                return 'text-muted-foreground';
        }
    };

    // No client-side filtering needed - backend handles it
    const filteredAlerts = alerts;

    // Count alerts by severity
    const criticalCount = alerts.filter(a => a.severity === 'critical').length;
    const warningCount = alerts.filter(a => a.severity === 'warning').length;
    const infoCount = alerts.filter(a => a.severity === 'info').length;
    const unreadCount = alerts.filter(a => !a.read).length;

    return (
        <div className="min-h-screen space-y-8 p-6">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                    Alerts & Notifications
                </h1>
                <p className="text-muted-foreground">Real-time system alerts and actionable insights</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <UnifiedCard className="cursor-pointer hover:shadow-lg transition-shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-muted-foreground text-sm mb-1">Total Alerts</p>
                            <p className="text-3xl font-bold text-foreground">{alerts.length}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-primary/10 shadow-[0_0_10px_rgba(59,130,246,0.2)]">
                            <AlertCircle size={24} className="text-primary" />
                        </div>
                    </div>
                    <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="px-2 py-1 bg-muted rounded">{unreadCount} unread</span>
                    </div>
                </UnifiedCard>

                <UnifiedCard
                    onClick={() => setFilterSeverity('critical')}
                    className={`cursor-pointer transition-all hover:shadow-2xl ${filterSeverity === 'critical' ? 'shadow-[0_0_20px_rgba(239,68,68,0.4)]' : ''
                        }`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-muted-foreground text-sm mb-1">Critical</p>
                            <p className="text-3xl font-bold text-foreground">{criticalCount}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-destructive/10 shadow-[0_0_10px_rgba(239,68,68,0.2)]">
                            <AlertTriangle size={24} className="text-destructive" />
                        </div>
                    </div>
                    <p className="mt-3 text-xs text-muted-foreground font-medium">Requires immediate action</p>
                </UnifiedCard>

                <UnifiedCard
                    onClick={() => setFilterSeverity('warning')}
                    className={`cursor-pointer transition-all hover:shadow-2xl ${filterSeverity === 'warning' ? 'shadow-[0_0_20px_rgba(234,179,8,0.4)]' : ''
                        }`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-muted-foreground text-sm mb-1">Warnings</p>
                            <p className="text-3xl font-bold text-foreground">{warningCount}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-yellow-500/10 shadow-[0_0_10px_rgba(234,179,8,0.2)]">
                            <AlertCircle size={24} className="text-yellow-600 dark:text-yellow-500" />
                        </div>
                    </div>
                    <p className="mt-3 text-xs text-muted-foreground font-medium">Attention needed</p>
                </UnifiedCard>

                <UnifiedCard
                    onClick={() => setFilterSeverity('info')}
                    className={`cursor-pointer transition-all hover:shadow-lg ${filterSeverity === 'info' ? 'ring-2 ring-primary' : ''
                        }`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-muted-foreground text-sm mb-1">Info</p>
                            <p className="text-3xl font-bold text-foreground">{infoCount}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                            <Info size={24} className="text-primary" />
                        </div>
                    </div>
                    <p className="mt-3 text-xs text-muted-foreground font-medium">Informational updates</p>
                </UnifiedCard>
            </div>

            {/* Filters */}
            <UnifiedCard>
                <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Filter size={20} className="text-muted-foreground" />
                        <span className="text-foreground font-medium">Filters:</span>
                    </div>

                    <div className="flex gap-2 flex-wrap">
                        <ActionButton
                            onClick={() => setFilterSeverity('all')}
                            variant={filterSeverity === 'all' ? 'primary' : 'secondary'}
                            size="sm"
                        >
                            All
                        </ActionButton>
                        <ActionButton
                            onClick={() => setFilterSeverity('critical')}
                            variant={filterSeverity === 'critical' ? 'destructive' : 'secondary'}
                            size="sm"
                        >
                            Critical ({criticalCount})
                        </ActionButton>
                        <ActionButton
                            onClick={() => setFilterSeverity('warning')}
                            variant={filterSeverity === 'warning' ? 'primary' : 'secondary'}
                            size="sm"
                            className={filterSeverity === 'warning' ? 'bg-yellow-600 hover:bg-yellow-700 text-white' : ''}
                        >
                            Warnings ({warningCount})
                        </ActionButton>
                        <ActionButton
                            onClick={() => setFilterSeverity('info')}
                            variant={filterSeverity === 'info' ? 'primary' : 'secondary'}
                            size="sm"
                        >
                            Info ({infoCount})
                        </ActionButton>
                    </div>

                    <div className="ml-auto flex gap-2">
                        <ActionButton variant="secondary" size="sm">
                            Mark All as Read
                        </ActionButton>
                        <ActionButton variant="secondary" size="sm">
                            Clear All
                        </ActionButton>
                    </div>
                </div>
            </UnifiedCard>

            {/* Alerts List */}
            <div className="space-y-4">
                {filteredAlerts.length === 0 ? (
                    <UnifiedCard className="text-center py-12">
                        <CheckCircle className="mx-auto mb-4 text-green-600 dark:text-green-500" size={48} />
                        <h3 className="text-xl font-bold text-foreground mb-2">No Alerts</h3>
                        <p className="text-muted-foreground">All caught up! No alerts for this filter.</p>
                    </UnifiedCard>
                ) : (
                    filteredAlerts.map((alert) => {
                        const isPulse = alert.severity === 'critical' && !alert.read;
                        return (
                            <div
                                key={alert.id}
                            >
                                <UnifiedCard
                                    className={`${!alert.read ? 'border-l-4 border-primary' : ''} ${isPulse ? 'ring-2 ring-destructive/50' : ''
                                        }`}
                                >
                                    <div className="flex items-start gap-4">
                                        {/* Icon */}
                                        <div className={`p-3 rounded-lg ${getSeverityColor(alert.severity)} relative flex-shrink-0`}>
                                            {isPulse && (
                                                <span className="absolute inset-0 rounded-lg bg-destructive/20 animate-ping" />
                                            )}
                                            <div className="relative z-10">
                                                {getSeverityIcon(alert.severity)}
                                            </div>
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between mb-2">
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-3 mb-1 flex-wrap">
                                                        <h3 className="text-lg font-bold text-foreground">
                                                            {alert.title}
                                                        </h3>
                                                        {!alert.read && (
                                                            <span className="px-2 py-1 bg-primary/10 border border-primary/20 text-primary text-xs rounded-full font-semibold">
                                                                NEW
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-muted-foreground text-sm">{alert.description}</p>
                                                </div>
                                                <button className="p-2 hover:bg-muted rounded-lg transition flex-shrink-0">
                                                    <X size={20} className="text-muted-foreground" />
                                                </button>
                                            </div>

                                            <div className="flex items-center justify-between mt-4 gap-4 flex-wrap">
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
                                                    <ActionButton
                                                        variant="primary"
                                                        size="sm"
                                                        onClick={() => handleAction(alert.action, alert)}
                                                    >
                                                        {alert.action}
                                                    </ActionButton>
                                                    <ActionButton
                                                        variant="destructive"
                                                        size="sm"
                                                        onClick={() => handleDismiss(alert.id)}
                                                    >
                                                        Dismiss
                                                    </ActionButton>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </UnifiedCard>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Pagination */}
            {
                totalPages > 1 && (
                    <div className="flex items-center justify-center gap-2">
                        <ActionButton
                            variant="secondary"
                            size="sm"
                            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                            disabled={currentPage === 1}
                        >
                            Previous
                        </ActionButton>
                        <span className="px-4 py-2 text-muted-foreground text-sm">
                            Page {currentPage} of {totalPages} ({totalAlerts} total alerts)
                        </span>
                        <ActionButton
                            variant="secondary"
                            size="sm"
                            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                            disabled={currentPage === totalPages}
                        >
                            Next
                        </ActionButton>
                    </div>
                )
            }
        </div >
    );
};

export default Alerts;
