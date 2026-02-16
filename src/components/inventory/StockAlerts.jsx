import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Info, X } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SEVERITY_CONFIG = {
    critical: {
        icon: AlertTriangle,
        color: 'red',
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-600',
        badge: 'bg-red-500'
    },
    warning: {
        icon: AlertTriangle,
        color: 'orange',
        bg: 'bg-orange-50',
        border: 'border-orange-200',
        text: 'text-orange-600',
        badge: 'bg-orange-500'
    },
    info: {
        icon: Info,
        color: 'yellow',
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-600',
        badge: 'bg-yellow-500'
    }
};

export default function StockAlerts() {
    const [alerts, setAlerts] = useState([]);
    const [counts, setCounts] = useState({ critical: 0, warning: 0, info: 0 });
    const [selectedSeverity, setSelectedSeverity] = useState(null);
    const [loading, setLoading] = useState(true);

    // Fetch alerts
    const fetchAlerts = async () => {
        try {
            const url = selectedSeverity
                ? `${API_BASE}/inventory/alerts?severity=${selectedSeverity}`
                : `${API_BASE}/inventory/alerts`;

            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                setAlerts(data.data.alerts);
                setCounts({
                    critical: data.data.critical_count,
                    warning: data.data.warning_count,
                    info: data.data.info_count
                });
            }
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    // Auto-refresh every 5 seconds
    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 5000);
        return () => clearInterval(interval);
    }, [selectedSeverity]);

    // Acknowledge alert
    const acknowledgeAlert = async (alertId) => {
        try {
            const response = await fetch(`${API_BASE}/inventory/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: 1 }) // TODO: Get from auth context
            });

            if (response.ok) {
                fetchAlerts(); // Refresh list
            }
        } catch (error) {
            console.error('Failed to acknowledge alert:', error);
        }
    };

    if (loading) {
        return <div className="p-6 text-center text-gray-600">Loading alerts...</div>;
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-800">Stock Alerts</h2>
                <p className="text-gray-600">Real-time low stock monitoring</p>
            </div>

            {/* Severity Filters */}
            <div className="flex gap-3">
                <button
                    onClick={() => setSelectedSeverity(null)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedSeverity === null
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                >
                    All ({counts.critical + counts.warning + counts.info})
                </button>

                {Object.entries(counts).map(([severity, count]) => {
                    const config = SEVERITY_CONFIG[severity];
                    return (
                        <button
                            key={severity}
                            onClick={() => setSelectedSeverity(severity)}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${selectedSeverity === severity
                                    ? `${config.badge} text-white`
                                    : `${config.bg} ${config.text} hover:opacity-80`
                                }`}
                        >
                            <config.icon className="w-4 h-4" />
                            {severity.charAt(0).toUpperCase() + severity.slice(1)} ({count})
                        </button>
                    );
                })}
            </div>

            {/* Alerts List */}
            <div className="space-y-3">
                {alerts.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 rounded-lg">
                        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                        <p className="text-gray-600">No active alerts</p>
                        <p className="text-sm text-gray-400">All stock levels are healthy</p>
                    </div>
                ) : (
                    alerts.map((alert) => {
                        const config = SEVERITY_CONFIG[alert.severity];
                        const Icon = config.icon;

                        return (
                            <div
                                key={alert.id}
                                className={`p-4 rounded-lg border-2 ${config.bg} ${config.border}`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3 flex-1">
                                        <Icon className={`w-6 h-6 ${config.text} mt-1`} />
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="font-bold text-gray-800">{alert.product_name}</h3>
                                                <span className={`px-2 py-0.5 text-xs font-semibold rounded ${config.badge} text-white`}>
                                                    {alert.severity.toUpperCase()}
                                                </span>
                                            </div>
                                            <p className={`text-sm ${config.text} mb-2`}>{alert.message}</p>
                                            <div className="flex gap-4 text-xs text-gray-600">
                                                <span>Current: <strong>{alert.current_stock}</strong> units</span>
                                                <span>Reorder Point: <strong>{alert.reorder_point}</strong> units</span>
                                                <span>Category: <strong>{alert.category}</strong></span>
                                            </div>
                                        </div>
                                    </div>

                                    {!alert.acknowledged_at && (
                                        <button
                                            onClick={() => acknowledgeAlert(alert.id)}
                                            className="ml-4 px-3 py-1 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                                        >
                                            Acknowledge
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
