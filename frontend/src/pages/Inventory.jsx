import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Download, X, AlertCircle } from 'lucide-react';
import api, { authAPI } from '../lib/api';
import { useToast } from '../contexts/ToastContext';
import ComplianceStatusChip from '../components/patterns/ComplianceStatusChip';
import SEO from '../components/SEO';

import Modal from '../components/ui/Modal';

const fmtINR = (value) => {
  if (!value && value !== 0) return '₹0';
  return '₹' + Math.floor(value).toLocaleString('en-IN');
};

export default function Inventory() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedOutlet, setSelectedOutlet] = useState('all');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedInventory, setSelectedInventory] = useState(null);
  const [newStockQuantity, setNewStockQuantity] = useState('');
  const [updateReason, setUpdateReason] = useState('Received Shipment');
  const [updateNotes, setUpdateNotes] = useState('');
  
  const [modalOpen, setModalOpen] = useState(false);
  const [movementData, setMovementData] = useState([]);
  const [selectedMovementProduct, setSelectedMovementProduct] = useState(null);

  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addForm, setAddForm] = useState({
    name: '', category: 'Starters', sku: '', unit_price: '', cost_price: '', current_stock: '', reorder_point: ''
  });
  const [addError, setAddError] = useState('');

  // Check ?action=new
  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('action') === 'new') {
      setAddModalOpen(true);
    }
  }, []);

  const { data: userData } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await authAPI.getUser();
      return response.data;
    },
  });
  
  const isSuperAdmin = userData?.role === 'super_admin';
  const userOutletId = userData?.outlet_id;

  const { data: inventoryData, isLoading: inventoryLoading, error: inventoryError, refetch: refetchInventory } = useQuery({
    queryKey: ['inventory', selectedOutlet],
    queryFn: async () => {
      const params = {};
      if (selectedOutlet !== 'all') {
        params.outlet_id = selectedOutlet;
      }
      const response = await api.get('/api/v1/inventory', { params });
      return response.data;
    },
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await api.get('/api/v1/categories');
      return response.data;
    },
  });

  const { data: outletsData } = useQuery({
    queryKey: ['outlets'],
    queryFn: async () => {
      const response = await api.get('/api/v1/outlets');
      return response.data?.data || response.data?.items || response.data || [];
    },
  });

  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['low-stock-alerts'],
    queryFn: async () => {
      const response = await api.get('/api/v1/inventory/alerts/low-stock');
      return response.data;
    },
  });

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['inventory-summary'],
    queryFn: async () => {
      const response = await api.get('/api/v1/inventory/summary');
      return response.data;
    },
  });

  const { data: movementDataAPI } = useQuery({
    queryKey: ['stock-movement', selectedInventory?.id || selectedInventory?.inventory_id],
    queryFn: async () => {
      const id = selectedInventory.id || selectedInventory.inventory_id;
      const response = await api.get(`/api/v1/inventory/${id}/movement`);
      return response.data;
    },
    enabled: !!selectedInventory,
  });

  const updateStockMutation = useMutation({
    mutationFn: async () => {
      const id = selectedInventory.id || selectedInventory.inventory_id;
      const response = await api.put(`/api/v1/inventory/${id}`, {
        quantity: parseInt(newStockQuantity),
        reason: updateReason,
        notes: updateNotes,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['low-stock-alerts'] });
      queryClient.invalidateQueries({ queryKey: ['inventory-summary'] });
      setDrawerOpen(false);
      setSelectedInventory(null);
      setNewStockQuantity('');
      setUpdateReason('Received Shipment');
      setUpdateNotes('');
      showToast('Stock updated successfully', 'success');
    },
  });

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setAddError('');
    try {
      const payload = {
        name: addForm.name,
        category: addForm.category,
        sku: addForm.sku || `SKU-${Date.now().toString().slice(-6)}`,
        unit_price: parseFloat(addForm.unit_price) || 0,
        cost_price: parseFloat(addForm.cost_price) || 0,
        current_stock: parseInt(addForm.current_stock) || 0,
        reorder_point: parseInt(addForm.reorder_point) || 10,
      };
      const res = await api.post('/api/v1/inventory/create', payload);
      if (res.data?.success) {
        showToast('Menu item added successfully', 'success');
        setAddModalOpen(false);
        setAddForm({ name: '', category: 'Starters', sku: '', unit_price: '', cost_price: '', current_stock: '', reorder_point: '' });
        queryClient.invalidateQueries({ queryKey: ['inventory'] });
        queryClient.invalidateQueries({ queryKey: ['inventory-summary'] });
      } else {
        setAddError(res.data?.error || 'Failed to add item');
      }
    } catch (err) {
      setAddError(err.response?.data?.detail || err.message || 'An error occurred');
    }
  };

  const filteredInventory = useMemo(() => {
    if (!inventoryData) return [];
    let filtered = Array.isArray(inventoryData) ? inventoryData : (inventoryData.items || inventoryData.data?.items || []);
    if (searchQuery.trim()) {
      filtered = filtered.filter(item =>
        (item.product?.name || item.product_name || item.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.product?.sku || item.product_sku || item.sku || '').toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(item => (item.product?.category_id || item.category_id || item.category) === selectedCategory || (item.product?.category_id || item.category_id) === parseInt(selectedCategory));
    }
    if (selectedOutlet !== 'all') {
      filtered = filtered.filter(item => item.outlet_id === parseInt(selectedOutlet) || item.outlet_id === selectedOutlet);
    }
    if (showLowStockOnly) {
      filtered = filtered.filter(item => (item.quantity ?? item.current_stock) < (item.reorder_level ?? item.product?.reorder_point));
    }
    return filtered;
  }, [inventoryData, searchQuery, selectedCategory, selectedOutlet, showLowStockOnly, isSuperAdmin, userOutletId]);

  const totalProducts = filteredInventory.length;
  const lowStockCount = filteredInventory.filter(item => (item.quantity ?? item.current_stock) < (item.reorder_level ?? item.product?.reorder_point)).length;

  const activeAlerts = (alertsData || []).slice(0, 5);
  const totalAlerts = alertsData?.length || 0;

  const apiTotal = summaryData?.total ?? 0;
  const apiLowStock = summaryData?.low_stock ?? 0;
  const apiHealthy = summaryData?.healthy ?? (apiTotal - apiLowStock - (summaryData?.out_of_stock ?? 0));
  const apiStockHealthPct = apiTotal > 0 ? Math.round((apiHealthy / apiTotal) * 100) : 100;
  const apiStockHealthClass = apiStockHealthPct >= 80 ? 'sage' : apiStockHealthPct < 50 ? 'critical' : 'brown';

  const renderSummaryValue = (value, isLoading, customClass = '') => {
    if (isLoading) {
      return (
        <span className={`shimmer-active ${customClass}`} style={{ display: 'inline-block', width: '60px', height: '24px', borderRadius: '4px' }} />
      );
    }
    return value;
  };

  return (
    <>
      <SEO title="Inventory" description="Manage outlet stock levels" />
      <style>{`
        .inventory-table-row .row-actions-hover-only {
          opacity: 0;
          transition: opacity 0.15s ease-in-out;
        }
        .inventory-table-row:hover {
          background: var(--c-brown-glow) !important;
        }
        .inventory-table-row:hover .row-actions-hover-only {
          opacity: 1;
        }
      `}</style>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0, minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
        
        {/* Header Row */}
        <div style={{
          padding: '16px 22px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          borderBottom: '1px solid var(--c-border)',
          background: 'var(--c-canvas)'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <h1 className="page-title" >Inventory</h1>
              <ComplianceStatusChip status={lowStockCount > 0 ? 'warning' : 'success'} level="L1" />
            </div>
            <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>
              {totalProducts} ingredients &middot; {totalAlerts} active alerts &middot; {lowStockCount} low stock
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="action-btn">
              <Download size={12} />
              Export CSV
            </button>
            <button className="action-btn primary" onClick={() => setAddModalOpen(true)}>
              Add Menu Item
            </button>
          </div>
        </div>

        {/* 1. TOP STAT ROW */}
        <div className="kpi-strip">
          <div className="kpi-cell">
            <div className="kpi-label">Total Ingredients</div>
            <div className="kpi-value brown">
              {renderSummaryValue(apiTotal, summaryLoading)}
            </div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">Low Stock Items</div>
            <div className={`kpi-value ${apiLowStock > 0 ? 'critical' : ''}`}>
              {renderSummaryValue(apiLowStock, summaryLoading)}
            </div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">Stock Health</div>
            <div className={`kpi-value ${apiStockHealthClass}`}>
              {renderSummaryValue(`${apiStockHealthPct}%`, summaryLoading)}
            </div>
          </div>
        </div>

        {/* 2. LOW STOCK ALERTS SECTION */}
        {totalAlerts > 0 && (
          <div className="content-section-alt">
            <div className="section-header">
              <div className="zone-label" style={{ marginBottom: 0 }}>Low Stock Alerts ({totalAlerts})</div>
            </div>
            {alertsLoading ? (
              <div style={{ color: 'var(--c-ink-muted)', fontSize: '12px' }}>Loading alerts...</div>
            ) : (
              <div className="feed-stream">
                {activeAlerts.map((alert, idx) => {
                  const isCritical = alert.current_stock < (alert.reorder_level / 2);
                  const nodeColor = isCritical ? 'var(--c-critical)' : 'var(--c-brown)';
                  const severityTag = isCritical ? 'CRITICAL' : 'WARNING';
                  const severityClass = isCritical ? 'critical' : 'warning';
                  
                  return (
                    <div key={idx} className="feed-entry" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', gap: '14px' }}>
                        <div className="feed-node" style={{ background: nodeColor }} />
                        <div className="feed-body">
                          <div className="feed-text">
                            <strong>{alert.product_name}</strong> {isSuperAdmin && `(${alert.outlet_name})`} &mdash; Stock level: <span style={{ fontFamily: 'var(--f-mono)', color: nodeColor, fontWeight: 600 }}>{alert.current_stock ?? alert.current_value}</span> / threshold: <span style={{ fontFamily: 'var(--f-mono)' }}>{alert.reorder_level ?? alert.threshold}</span>
                          </div>
                          <span className={`feed-tag ${severityClass}`}>{severityTag}</span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
                        <button className="action-btn">Resolve</button>
                        <button className="action-btn primary">Create Reorder</button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* 3. FILTER BAR */}
        <div className="content-section">
          <div className="filter-bar">
            <input 
              type="text" 
              placeholder="Search ingredient name or SKU..."
              value={searchQuery} 
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ flex: 1, minWidth: '200px' }}
            />
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              {categoriesData?.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
            <select 
              value={selectedOutlet} 
              onChange={(e) => setSelectedOutlet(e.target.value)}
            >
              <option value="all">All Outlets</option>
              {Array.isArray(outletsData) && outletsData.map(outlet => (
                <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
              ))}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px', color: 'var(--c-ink-muted)', userSelect: 'none' }}>
              <input 
                type="checkbox" 
                checked={showLowStockOnly} 
                onChange={(e) => setShowLowStockOnly(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              Low Stock Only
            </label>
          </div>
        </div>

        {/* 4. INVENTORY TABLE */}
        <div className="content-section-alt" style={{ padding: '0 22px 22px' }}>
          {inventoryLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '20px' }}>
              <div className="skeleton-row" />
              <div className="skeleton-row" />
              <div className="skeleton-row" />
              <div className="skeleton-row" />
              <div className="skeleton-row" />
            </div>
          ) : inventoryError ? (
            <div className="error-panel" style={{ marginTop: '20px' }}>
              <div style={{ fontWeight: 600, color: 'var(--c-critical)' }}>Failed to load inventory data</div>
              <button onClick={() => refetchInventory()} className="action-btn primary" style={{ marginTop: '12px' }}>Retry</button>
            </div>
          ) : (
            <div style={{ overflowX: 'auto', margin: '0 -24px' }}>
              <table className="eris-table">
                <thead>
                  <tr>
                    <th>Ingredient</th>
                    <th>Category</th>
                    <th>Stock</th>
                    <th>Reorder Level</th>
                    <th>Unit Price</th>
                    <th>Outlet</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredInventory.map((item, idx) => {
                    const currentStock = item.quantity ?? item.current_stock;
                    const reorderLevel = item.reorder_level ?? item.product?.reorder_point;
                    const isLowStock = currentStock < reorderLevel;
                    const stockClass = isLowStock ? 'critical' : 'positive';
                    
                    let statusBadgeClass = 'neutral';
                    let statusText = 'In Stock';
                    if (currentStock === 0) {
                      statusBadgeClass = 'critical';
                      statusText = 'Out of Stock';
                    } else if (isLowStock) {
                      statusBadgeClass = 'warning';
                      statusText = 'Low Stock';
                    } else {
                      statusBadgeClass = 'active';
                    }

                    const itemName = item.product?.name || 'Unknown';
                    const itemSku = item.product?.sku || 'N/A';
                    const itemCategory = item.product?.category || 'N/A';
                    const itemUnitPrice = item.product?.selling_price || 0;
                    const itemOutletName = item.outlet?.name || item.outlet_name || 'N/A';

                    return (
                      <tr 
                        key={item.id || item.inventory_id || idx} 
                        className="inventory-table-row"
                      >
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--c-dark)' }}>{itemName}</div>
                          <div style={{ fontSize: '11px', color: 'var(--c-ink-muted)' }}>SKU: {itemSku}</div>
                        </td>
                        <td>
                          {itemCategory}
                        </td>
                        <td className={`mono ${stockClass}`}>
                          {currentStock}
                        </td>
                        <td className="mono">
                          {reorderLevel}
                        </td>
                        <td className="mono">
                          {fmtINR(itemUnitPrice)}
                        </td>
                        <td>
                          {itemOutletName}
                        </td>
                        <td>
                          <div className={`badge ${statusBadgeClass}`}>
                            {statusText}
                          </div>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <div className="row-actions-hover-only" style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end' }}>
                            <button 
                              onClick={() => {
                                setSelectedInventory(item);
                                setNewStockQuantity((item.quantity ?? item.current_stock).toString());
                                setDrawerOpen(true);
                              }} 
                              className="action-btn"
                              style={{ fontSize: '10px', padding: '3px 8px' }}
                            >
                              Edit
                            </button>
                            <button 
                              onClick={() => {
                                setSelectedMovementProduct(item.product?.name || item.product_name || item.name);
                                setMovementData(movementDataAPI || []);
                                setModalOpen(true);
                              }} 
                              className="action-btn"
                              style={{ fontSize: '10px', padding: '3px 8px' }}
                            >
                              Adjust
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Edit Drawer Overlay */}
        {drawerOpen && selectedInventory && (
          <div className="drawer-overlay" onClick={() => setDrawerOpen(false)}
            style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex',
              justifyContent: 'flex-end', zIndex: 1000,
            }}>
            <div onClick={(e) => e.stopPropagation()}
              style={{
                width: 480, maxWidth: '100%', display: 'flex', flexDirection: 'column',
                background: 'var(--c-canvas)', borderLeft: '1px solid var(--c-border)',
                boxShadow: 'var(--shadow-md)', animation: 'fade-in-up 0.2s ease both',
              }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid var(--c-border)' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: '15px' }}>Edit Stock</h2>
                  <div style={{ fontSize: 13, color: 'var(--c-ink-muted)', marginTop: 2 }}>{selectedInventory.product?.name || selectedInventory.product_name || selectedInventory.name}</div>
                </div>
                <button onClick={() => setDrawerOpen(false)} className="action-btn">
                  <X size={14} />
                </button>
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
                <div style={{ marginBottom: 24 }}>
                  <label style={{ display: 'block', marginBottom: 8, fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--c-ink-muted)' }}>Current Stock</label>
                  <div style={{ fontFamily: 'var(--f-mono)', fontSize: '24px', fontWeight: 700 }}>{selectedInventory.quantity ?? selectedInventory.current_stock} units</div>
                </div>
                <div style={{ marginBottom: 24 }}>
                  <label style={{ display: 'block', marginBottom: 8, fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--c-ink-muted)' }}>New Stock Quantity</label>
                  <input type="number" value={newStockQuantity}
                    onChange={(e) => setNewStockQuantity(e.target.value)}
                    style={{ width: '100%' }} min="0"
                  />
                </div>
                <div style={{ marginBottom: 24 }}>
                  <label style={{ display: 'block', marginBottom: 8, fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--c-ink-muted)' }}>Reason</label>
                  <select value={updateReason} onChange={(e) => setUpdateReason(e.target.value)} style={{ width: '100%' }}>
                    <option>Received Shipment</option>
                    <option>Manual Correction</option>
                    <option>Damaged Goods</option>
                    <option>Stock Count Adjustment</option>
                  </select>
                </div>
                <div style={{ marginBottom: 24 }}>
                  <label style={{ display: 'block', marginBottom: 8, fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--c-ink-muted)' }}>Notes</label>
                  <textarea value={updateNotes} onChange={(e) => setUpdateNotes(e.target.value)}
                    placeholder="Add notes about this stock update..." rows={4} style={{ width: '100%' }}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', gap: 12, padding: 20, borderTop: '1px solid var(--c-border)', background: 'var(--c-footer)' }}>
                <button onClick={() => setDrawerOpen(false)} className="action-btn" style={{ flex: 1, justifyContent: 'center' }}>Cancel</button>
                <button onClick={() => updateStockMutation.mutate()}
                  disabled={updateStockMutation.isPending || !newStockQuantity}
                  className="action-btn primary" style={{ flex: 1, justifyContent: 'center' }}>
                  {updateStockMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Movement Modal */}
        {modalOpen && (
          <div className="modal-overlay" onClick={() => setModalOpen(false)}
            style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex',
              justifyContent: 'center', alignItems: 'center', zIndex: 1000,
            }}>
            <div onClick={(e) => e.stopPropagation()}
              style={{
                width: '90%', maxWidth: 800, maxHeight: '90vh', display: 'flex', flexDirection: 'column',
                background: 'var(--c-canvas)', border: '1px solid var(--c-border)', borderRadius: 'var(--radius)',
                boxShadow: 'var(--shadow-md)', animation: 'fade-in-up 0.2s ease both',
              }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid var(--c-border)' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: '15px' }}>Stock Movement</h2>
                  <div style={{ fontSize: 13, color: 'var(--c-ink-muted)', marginTop: 2 }}>{selectedMovementProduct}</div>
                </div>
                <button onClick={() => setModalOpen(false)} className="action-btn">
                  <X size={14} />
                </button>
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
                {movementData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={movementData}>
                      <defs>
                        <linearGradient id="colorQty" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8B5E3C" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="#8B5E3C" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--c-border)" />
                      <XAxis dataKey="date" tick={{ fontSize: 12, fill: 'var(--c-ink-muted)' }} stroke="var(--c-border)" />
                      <YAxis tick={{ fontSize: 12, fill: 'var(--c-ink-muted)' }} stroke="var(--c-border)" />
                      <Tooltip contentStyle={{
                        background: 'var(--c-canvas)', border: '1px solid var(--c-border)',
                        borderRadius: 'var(--radius)', color: 'var(--c-ink)',
                      }} formatter={(value) => [value, 'Quantity']} />
                      <Area type="monotone" dataKey="quantity" stroke="#8B5E3C" strokeWidth={2} fillOpacity={1} fill="url(#colorQty)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state">
                    <div className="empty-state-title">No movement data available</div>
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, padding: 20, borderTop: '1px solid var(--c-border)', background: 'var(--c-footer)' }}>
                <button onClick={() => setModalOpen(false)} className="action-btn">Close</button>
              </div>
            </div>
          </div>
        )}

        <Modal open={addModalOpen} onClose={() => setAddModalOpen(false)} title="Add Menu Item">
          <form onSubmit={handleAddSubmit}>
            {addError && <div style={{ color: 'var(--c-critical)', marginBottom: 12, fontSize: 13 }}>{addError}</div>}
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Name *</label>
                <input required value={addForm.name} onChange={e => setAddForm({ ...addForm, name: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>SKU (Optional)</label>
                <input value={addForm.sku} onChange={e => setAddForm({ ...addForm, sku: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Category *</label>
                <input required value={addForm.category} onChange={e => setAddForm({ ...addForm, category: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Current Stock</label>
                <input type="number" required value={addForm.current_stock} onChange={e => setAddForm({ ...addForm, current_stock: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Selling Price (₹)</label>
                <input type="number" step="0.01" required value={addForm.unit_price} onChange={e => setAddForm({ ...addForm, unit_price: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Cost Price (₹)</label>
                <input type="number" step="0.01" required value={addForm.cost_price} onChange={e => setAddForm({ ...addForm, cost_price: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
              </div>
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Reorder Point</label>
              <input type="number" required value={addForm.reorder_point} onChange={e => setAddForm({ ...addForm, reorder_point: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button type="button" onClick={() => setAddModalOpen(false)} className="action-btn">Cancel</button>
              <button type="submit" className="action-btn primary">Add Item</button>
            </div>
          </form>
        </Modal>

      </div>
    </>
  );
}
