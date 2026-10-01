import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell } from 'lucide-react';
import api from '../lib/api';
import SEO from '../components/SEO';

export default function Alerts() {
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('active');
  const [selectedOutlet, setSelectedOutlet] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);

  const queryClient = useQueryClient();
  const itemsPerPage = 20;

  const { data: userData } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await api.get('/api/v1/auth/me');
      return response.data;
    },
  });

  const isSuperAdmin = userData?.role === 'admin';

  const { data: outletsData } = useQuery({
    queryKey: ['outlets'],
    queryFn: async () => {
      const response = await api.get('/api/v1/outlets');
      return response.data.outlets || [];
    },
  });

  const { data: alertsResponse, isLoading, isError, error: _err } = useQuery({
    queryKey: ['alerts', filterStatus],
    queryFn: async () => {
      const params = {
        per_page: 100,
      };
      if (filterStatus === 'active') {
        params.unread_only = true;
      } else if (filterStatus === 'resolved') {
        params.acknowledged = true;
      }
      return api.get('/api/v1/alerts/list', { params })
        .then(response => response.data.items ?? [])
        .catch(err => {
          console.error("Alerts API Error:", err);
          throw err;
        });
    },
    retry: 1,
  });

  const alertsData = useMemo(() => {
    const list = Array.isArray(alertsResponse) ? alertsResponse : [];
    return list.map((a) => ({
      ...a,
      type: a.alert_type || a.category,
      status: a.acknowledged || a.is_acknowledged ? 'resolved' : 'active',
      resolved_at: a.acknowledged_at || a.resolved_at,
    }));
  }, [alertsResponse]);

  const filteredAlerts = useMemo(() => {
    if (!alertsData) return [];
    let filtered = [...alertsData];
    if (filterType !== 'all') {
      filtered = filtered.filter((alert) => alert.type === filterType);
    }
    if (selectedOutlet !== 'all' && isSuperAdmin) {
      filtered = filtered.filter((alert) => alert.outlet_id === parseInt(selectedOutlet));
    }
    return filtered;
  }, [alertsData, filterType, selectedOutlet, isSuperAdmin]);

  const stats = useMemo(() => {
    let resolvedToday = 0;
    if (alertsData) {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      resolvedToday = alertsData.filter(
        (a) => a.status === 'resolved' && new Date(a.resolved_at) >= today
      ).length;
    }

    if (!alertsData) return { active: 0, resolvedToday: 0, critical: 0 };
    const activeAlerts = alertsData.filter((a) => a.status === 'active');
    const criticalAlerts = activeAlerts.filter((a) => a.severity === 'critical');
    
    return { active: activeAlerts.length, resolvedToday, critical: criticalAlerts.length };
  }, [alertsData]);

  const totalPages = Math.ceil(filteredAlerts.length / itemsPerPage);
  const paginatedAlerts = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredAlerts.slice(start, start + itemsPerPage);
  }, [filteredAlerts, currentPage]);

  const resolveAlertMutation = useMutation({
    mutationFn: async (alertId) => {
      const response = await api.patch(`/api/v1/alerts/${alertId}/acknowledge`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      setCurrentPage(1);
    },
  });

  const getOutletName = (outletId) => {
    const outlet = outletsData?.find((o) => o.id === outletId);
    return outlet?.name || `Outlet ${outletId}`;
  };

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

  const getAlertNodeColor = (alert) => {
    if (alert.severity === 'critical') return 'var(--c-critical)';
    if (alert.type === 'low_stock') return 'var(--c-brown)';
    return 'var(--c-sage)';
  };

  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const tabs = [
    { id: 'all', label: 'All' },
    { id: 'low_stock', label: 'Low Stock' },
    { id: 'stockout', label: 'Stockout' },
    { id: 'sales_anomaly', label: 'Sales Anomaly' },
  ];

  return (
    <>
      <SEO title="Inventory Alerts" description="Monitor and resolve alerts" />
      <style>{`
        @keyframes blink-dot {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        .blinking-dot {
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--c-critical);
          animation: blink-dot 1.2s infinite ease-in-out;
        }
      `}</style>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0, minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
        
        {/* Header Row */}
        <div style={{
          padding: '16px 22px',
          borderBottom: '1px solid var(--c-border)',
          background: 'var(--c-canvas)'
        }}>
          <h1 className="page-title" >Alerts</h1>
          <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>
            Monitor and acknowledge persisted inventory warnings
          </p>
        </div>

        {/* 1. KPI STRIP */}
        <div className="kpi-strip">
          <div className="kpi-cell">
            <div className="kpi-label">Active Alerts</div>
            <div className="kpi-value critical">{stats.active}</div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">Resolved Today</div>
            <div className="kpi-value sage">{stats.resolvedToday}</div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">Critical</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div className="kpi-value critical">{stats.critical}</div>
              {stats.critical > 0 && <span className="blinking-dot" />}
            </div>
          </div>
        </div>

        {/* 2. FILTER TABS */}
        <div className="content-section-alt">
          <div className="filter-bar">
            <div style={{ display: 'flex', gap: '20px', flex: 1 }}>
              {tabs.map((tab) => {
                const isActive = filterType === tab.id;
                return (
                  <div
                    key={tab.id}
                    onClick={() => { setFilterType(tab.id); setCurrentPage(1); }}
                    style={{
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: 600,
                      paddingBottom: '8px',
                      color: isActive ? 'var(--c-brown)' : 'var(--c-ink-muted)',
                      borderBottom: isActive ? '2px solid var(--c-brown)' : '2px solid transparent',
                      transition: 'all 0.15s ease-in-out'
                    }}
                  >
                    {tab.label}
                  </div>
                );
              })}
            </div>
            
            <div style={{ display: 'flex', gap: '8px' }}>
              {isSuperAdmin && (
                <select 
                  value={selectedOutlet}
                  onChange={(e) => { setSelectedOutlet(e.target.value); setCurrentPage(1); }}
                >
                  <option value="all">All Outlets</option>
                  {outletsData?.map((outlet) => (
                    <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                  ))}
                </select>
              )}
              <select 
                value={filterStatus}
                onChange={(e) => { setFilterStatus(e.target.value); setCurrentPage(1); }}
              >
                <option value="active">Active</option>
                <option value="resolved">Resolved</option>
                <option value="all">All</option>
              </select>
            </div>
          </div>
        </div>

        {/* 3. ALL ALERTS AS FEED STREAM */}
        <div className="content-section">
          <div className="section-header">
            <div className="zone-label" style={{ marginBottom: 0 }}>Alert Feed</div>
          </div>
        {isLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="skeleton-row" style={{ height: '70px', borderRadius: 'var(--radius)' }} />
            <div className="skeleton-row" style={{ height: '70px', borderRadius: 'var(--radius)' }} />
            <div className="skeleton-row" style={{ height: '70px', borderRadius: 'var(--radius)' }} />
          </div>
        ) : isError ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--c-critical)' }}>
            Failed to load alerts. Check console for details.
          </div>
        ) : paginatedAlerts.length === 0 ? (
          <div style={{
            padding: '48px 24px',
            textAlign: 'center',
            background: 'var(--c-canvas-raised)',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--c-border)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
          }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'var(--c-brown-glow)',
              color: 'var(--c-brown)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '4px',
            }}>
              <Bell size={20} />
            </div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--c-dark)' }}>No active alerts</div>
            <p style={{ fontSize: '12px', color: 'var(--c-ink-muted)', maxWidth: '320px', margin: 0, lineHeight: 1.5 }}>
              All clear &mdash; you'll be notified here when stock, expiry or revenue anomalies are detected.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            <div className="feed-stream">
              {paginatedAlerts.map((alert, idx) => {
                const nodeColor = getAlertNodeColor(alert);
                const isResolved = alert.status === 'resolved';
                
                return (
                  <div 
                    key={alert.id || idx} 
                    className="feed-entry"
                    style={{ justifyContent: 'space-between', alignItems: 'center' }}
                  >
                    <div style={{ display: 'flex', gap: '14px' }}>
                      <div className="feed-node" style={{ background: isResolved ? 'var(--c-sage)' : nodeColor }} />
                      
                      <div className="feed-body">
                        <div className="feed-text">
                          {alert.type.replace('_', ' ').toUpperCase()}: {alert.product_name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--c-ink-muted)', marginTop: '2px' }}>
                          Product: {alert.product_name} &middot; Outlet: {getOutletName(alert.outlet_id)}
                        </div>
                        <div style={{ fontFamily: 'var(--f-mono)', fontSize: '11px', color: 'var(--c-ink-muted)', marginTop: '2px' }}>
                          Stock: {alert.current_stock} / Threshold: {alert.reorder_level}
                        </div>
                        {isResolved ? (
                          <div className="feed-tag resolved">
                            Resolved {formatTimeSince(alert.resolved_at)}
                          </div>
                        ) : (
                          <div className="feed-time">Created {formatTimeSince(alert.created_at || new Date())}</div>
                        )}
                      </div>
                    </div>

                    {!isResolved && (
                      <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
                        <button 
                          className="action-btn"
                          onClick={() => resolveAlertMutation.mutate(alert.id)}
                          disabled={resolveAlertMutation.isPending}
                        >
                          {resolveAlertMutation.isPending ? 'Resolving…' : 'Resolve'}
                        </button>
                      </div>
                    )}

                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            {filteredAlerts.length > itemsPerPage && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: '24px' }}>
                <button className="action-btn" onClick={() => goToPage(currentPage - 1)} disabled={currentPage === 1}>
                  ← Previous
                </button>
                {[...Array(totalPages)].map((_, i) => {
                  const page = i + 1;
                  const isActive = page === currentPage;
                  return (
                    <button 
                      key={page} 
                      className={`action-btn ${isActive ? 'primary' : ''}`}
                      onClick={() => goToPage(page)}
                    >
                      {page}
                    </button>
                  );
                })}
                <button className="action-btn" onClick={() => goToPage(currentPage + 1)} disabled={currentPage === totalPages}>
                  Next →
                </button>
              </div>
            )}
          </div>
        )}
        </div>
      </div>
    </>
  );
}
