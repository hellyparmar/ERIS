import React, { useState, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import api from '../services/api';
import '../styles/alerts.css';

const Alerts = () => {
  // State management
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('active');
  const [selectedOutlet, setSelectedOutlet] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [resolvePopover, setResolvePopover] = useState(null);
  const [reorderPopover, setReorderPopover] = useState(null);
  const [resolveNotes, setResolveNotes] = useState('');

  const queryClient = useQueryClient();
  const itemsPerPage = 20;

  // Get user info
  const { data: userData } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await api.get('/api/v1/auth/me');
      return response.data.user;
    },
  });

  const isSuperAdmin = userData?.role === 'super_admin';

  // Fetch outlets for dropdown
  const { data: outletsData } = useQuery({
    queryKey: ['outlets'],
    queryFn: async () => {
      const response = await api.get('/api/v1/outlets');
      return response.data.outlets || [];
    },
  });

  // Fetch all alerts
  const { data: alertsData, isLoading } = useQuery({
    queryKey: ['alerts', filterStatus],
    queryFn: async () => {
      const response = await api.get('/api/v1/inventory/alerts', {
        params: {
          status: filterStatus,
        },
      });
      return response.data.alerts || [];
    },
  });

  // Filter and paginate alerts
  const filteredAlerts = useMemo(() => {
    if (!alertsData) return [];

    let filtered = [...alertsData];

    // Filter by type
    if (filterType !== 'all') {
      filtered = filtered.filter((alert) => {
        if (filterType === 'low-stock') return alert.type === 'low_stock';
        if (filterType === 'overstock') return alert.type === 'overstock';
        if (filterType === 'expiry') return alert.type === 'expiry_warning';
        return true;
      });
    }

    // Filter by outlet
    if (selectedOutlet !== 'all' && isSuperAdmin) {
      filtered = filtered.filter((alert) => alert.outlet_id === parseInt(selectedOutlet));
    }

    return filtered;
  }, [alertsData, filterType, selectedOutlet, isSuperAdmin]);

  // Calculate summary stats
  const stats = useMemo(() => {
    if (!alertsData) return { active: 0, resolvedToday: 0, critical: 0 };

    const activeAlerts = alertsData.filter((a) => a.status === 'active');
    const criticalAlerts = activeAlerts.filter(
      (a) => a.current_stock === 0 || a.type === 'critical'
    );

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const resolvedToday = alertsData.filter(
      (a) => a.status === 'resolved' && new Date(a.resolved_at) >= today
    ).length;

    return {
      active: activeAlerts.length,
      resolvedToday,
      critical: criticalAlerts.length,
    };
  }, [alertsData]);

  // Paginate
  const totalPages = Math.ceil(filteredAlerts.length / itemsPerPage);
  const paginatedAlerts = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredAlerts.slice(start, start + itemsPerPage);
  }, [filteredAlerts, currentPage]);

  // Resolve alert mutation
  const resolveAlertMutation = useMutation({
    mutationFn: async ({ alertId, notes }) => {
      const response = await api.post(`/api/v1/inventory/alerts/${alertId}/resolve`, {
        notes: notes || '',
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      setResolvePopover(null);
      setResolveNotes('');
      setCurrentPage(1);
    },
  });

  // Get outlet name
  const getOutletName = (outletId) => {
    const outlet = outletsData?.find((o) => o.id === outletId);
    return outlet?.name || `Outlet ${outletId}`;
  };

  // Format time since created
  const formatTimeSince = (date) => {
    const now = new Date();
    const created = new Date(date);
    const diffMs = now - created;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Get alert badge color and icon
  const getAlertStyle = (type) => {
    switch (type) {
      case 'low_stock':
        return { borderColor: '#F59E0B', badgeColor: '#FEF3C7', badgeText: '#92400E', label: 'Low Stock' };
      case 'overstock':
        return { borderColor: '#3B82F6', badgeColor: '#DBEAFE', badgeText: '#1E40AF', label: 'Overstock' };
      case 'expiry_warning':
        return { borderColor: '#F59E0B', badgeColor: '#FEF3C7', badgeText: '#92400E', label: 'Expiry Warning' };
      case 'critical':
        return { borderColor: '#EF4444', badgeColor: '#FEE2E2', badgeText: '#991B1B', label: 'Critical' };
      default:
        return { borderColor: '#3B82F6', badgeColor: '#DBEAFE', badgeText: '#1E40AF', label: 'Info' };
    }
  };

  // Get progress bar color
  const getProgressColor = (currentStock, reorderLevel) => {
    const percentage = (currentStock / reorderLevel) * 100;
    if (percentage === 0) return '#EF4444'; // red for critical
    if (percentage < 25) return '#EF4444'; // red
    if (percentage < 50) return '#F59E0B'; // amber
    return '#10B981'; // green
  };

  const handleResolve = (alert) => {
    setResolvePopover(alert.id);
    setResolveNotes('');
  };

  const confirmResolve = (alertId) => {
    resolveAlertMutation.mutate({ alertId, notes: resolveNotes });
  };

  const handleCreateReorder = (alert) => {
    setReorderPopover(alert.id);
  };

  // Handle pagination
  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Render empty state
  if (!isLoading && filteredAlerts.length === 0 && filterStatus === 'active') {
    return (
      <div className="alerts-container">
        <div className="alerts-empty-state">
          <CheckCircle size={64} />
          <h2>All inventory levels are healthy</h2>
          <p>Great job maintaining optimal stock levels across all products</p>
        </div>
      </div>
    );
  }

  return (
    <div className="alerts-container">
      {/* Header */}
      <div className="alerts-header">
        <p className="page-subtitle">Monitor and manage low stock, overstock, and expiry warnings</p>
      </div>

      {/* Summary Stats */}
      <div className="alerts-stats">
        <div className="stat-card stat-pink">
          <div className="stat-value">{stats.active}</div>
          <div className="stat-label">Active Alerts</div>
        </div>
        <div className="stat-card stat-green">
          <div className="stat-value">{stats.resolvedToday}</div>
          <div className="stat-label">Resolved Today</div>
        </div>
        <div className="stat-card stat-red">
          <div className="stat-value">{stats.critical}</div>
          <div className="stat-label">Critical</div>
        </div>
      </div>

      {/* Filters */}
      <div className="alerts-filters">
        <div className="filter-tabs">
          {[
            { id: 'all', label: 'All' },
            { id: 'low-stock', label: 'Low Stock' },
            { id: 'overstock', label: 'Overstock' },
            { id: 'expiry', label: 'Expiry Warning' },
          ].map((tab) => (
            <button
              key={tab.id}
              className={`filter-tab ${filterType === tab.id ? 'active' : ''}`}
              onClick={() => {
                setFilterType(tab.id);
                setCurrentPage(1);
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="filter-controls">
          {isSuperAdmin && (
            <select
              className="filter-select"
              value={selectedOutlet}
              onChange={(e) => {
                setSelectedOutlet(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="all">All Outlets</option>
              {outletsData?.map((outlet) => (
                <option key={outlet.id} value={outlet.id}>
                  {outlet.name}
                </option>
              ))}
            </select>
          )}

          <select
            className="filter-select"
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="active">Active</option>
            <option value="resolved">Resolved</option>
            <option value="all">All</option>
          </select>
        </div>
      </div>

      {/* Alert Cards Grid */}
      <div className="alerts-grid">
        {isLoading ? (
          <div className="skeleton-grid">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton-card" />
            ))}
          </div>
        ) : paginatedAlerts.length === 0 ? (
          <div className="no-results">
            <AlertCircle size={40} />
            <p>No alerts match the selected filters</p>
          </div>
        ) : (
          paginatedAlerts.map((alert) => {
            const style = getAlertStyle(alert.type);
            const progressColor = getProgressColor(alert.current_stock, alert.reorder_level);
            const isResolved = alert.status === 'resolved';
            const progressPercent = (alert.current_stock / alert.reorder_level) * 100;

            return (
              <div
                key={alert.id}
                className={`alert-card ${isResolved ? 'resolved' : ''}`}
                style={{ borderLeftColor: style.borderColor }}
              >
                {/* Top Row */}
                <div className="alert-top">
                  <span
                    className="alert-badge"
                    style={{
                      backgroundColor: style.badgeColor,
                      color: style.badgeText,
                    }}
                  >
                    {style.label}
                  </span>
                  <span className="alert-outlet">{getOutletName(alert.outlet_id)}</span>
                  <span className="alert-time">
                    {isResolved
                      ? `Resolved ${formatTimeSince(alert.resolved_at)}`
                      : formatTimeSince(alert.created_at)}
                  </span>
                </div>

                {/* Product Name */}
                <h3 className="alert-product">{alert.product_name}</h3>

                {/* Metrics */}
                <div className="alert-metrics">
                  Current stock: <strong>{alert.current_stock}</strong> units · Threshold:{' '}
                  <strong>{alert.reorder_level}</strong> units
                </div>

                {/* Progress Bar */}
                {!isResolved && (
                  <div className="alert-progress-container">
                    <div className="alert-progress-bar">
                      <div
                        className="alert-progress-fill"
                        style={{
                          width: `${Math.min(progressPercent, 100)}%`,
                          backgroundColor: progressColor,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                {isResolved ? (
                  <div className="alert-resolved-note">
                    <CheckCircle size={16} />
                    <span>Alert resolved</span>
                  </div>
                ) : (
                  <div className="alert-actions">
                    <div className="action-left">
                      <button
                        className="btn-resolve"
                        onClick={() => handleResolve(alert)}
                        disabled={resolveAlertMutation.isPending}
                      >
                        {resolveAlertMutation.isPending ? 'Resolving...' : 'Resolve'}
                      </button>
                      <button className="btn-reorder" onClick={() => handleCreateReorder(alert)}>
                        Create Reorder
                      </button>
                    </div>
                    <a href={`/products/${alert.product_id}`} className="btn-view-link">
                      View Product →
                    </a>
                  </div>
                )}

                {/* Resolve Popover */}
                {resolvePopover === alert.id && (
                  <div className="popover-overlay">
                    <div className="popover resolve-popover">
                      <div className="popover-header">
                        <h3>Resolve Alert</h3>
                        <button
                          className="popover-close"
                          onClick={() => setResolvePopover(null)}
                        >
                          <X size={18} />
                        </button>
                      </div>
                      <div className="popover-content">
                        <p className="popover-text">Add notes about this resolution (optional):</p>
                        <textarea
                          className="popover-textarea"
                          value={resolveNotes}
                          onChange={(e) => setResolveNotes(e.target.value)}
                          placeholder="e.g., Restocked items from warehouse..."
                          rows={3}
                        />
                      </div>
                      <div className="popover-footer">
                        <button
                          className="btn-cancel"
                          onClick={() => setResolvePopover(null)}
                        >
                          Cancel
                        </button>
                        <button
                          className="btn-confirm"
                          onClick={() => confirmResolve(alert.id)}
                          disabled={resolveAlertMutation.isPending}
                        >
                          {resolveAlertMutation.isPending ? 'Resolving...' : 'Confirm'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Reorder Popover */}
                {reorderPopover === alert.id && (
                  <div className="popover-overlay">
                    <div className="popover reorder-popover">
                      <div className="popover-header">
                        <h3>Create Purchase Order</h3>
                        <button
                          className="popover-close"
                          onClick={() => setReorderPopover(null)}
                        >
                          <X size={18} />
                        </button>
                      </div>
                      <div className="popover-content">
                        <div className="reorder-field">
                          <label>Product:</label>
                          <p className="reorder-value">{alert.product_name}</p>
                        </div>
                        <div className="reorder-field">
                          <label>Current Stock:</label>
                          <p className="reorder-value">{alert.current_stock} units</p>
                        </div>
                        <div className="reorder-field">
                          <label>Suggested Order Quantity:</label>
                          <p className="reorder-value">
                            {Math.max(alert.reorder_level * 2 - alert.current_stock, alert.reorder_level)} units
                          </p>
                        </div>
                      </div>
                      <div className="popover-footer">
                        <button
                          className="btn-cancel"
                          onClick={() => setReorderPopover(null)}
                        >
                          Close
                        </button>
                        <a href="/invoices" className="btn-create-po">
                          Create PO in Invoices
                        </a>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      {!isLoading && filteredAlerts.length > itemsPerPage && (
        <div className="alerts-pagination">
          <button
            className="btn-page"
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage === 1}
          >
            ← Previous
          </button>

          <div className="page-numbers">
            {[...Array(totalPages)].map((_, i) => {
              const page = i + 1;
              if (page === 1 || page === totalPages || (page >= currentPage - 1 && page <= currentPage + 1)) {
                return (
                  <button
                    key={page}
                    className={`btn-page-number ${page === currentPage ? 'active' : ''}`}
                    onClick={() => goToPage(page)}
                  >
                    {page}
                  </button>
                );
              }
              if (page === currentPage - 2 || page === currentPage + 2) {
                return (
                  <span key={page} className="page-ellipsis">
                    …
                  </span>
                );
              }
              return null;
            })}
          </div>

          <button
            className="btn-page"
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

export default Alerts;
