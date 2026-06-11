import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Edit2, Eye, Download, X, AlertCircle, ChevronDown } from 'lucide-react';
import api, { authAPI } from '../services/api';
import { useToast } from '../contexts/ToastContext';
import DataTable from '../components/ui/DataTable';
import StatCard from '../components/ui/StatCard';
import Badge from '../components/ui/Badge';
import '../styles/inventory.css';

// Helper Functions
const fmtINR = (value) => {
  if (!value && value !== 0) return '₹0';
  return '₹' + Math.floor(value).toLocaleString('en-IN');
};

const getStockColor = (currentStock, reorderLevel) => {
  if (currentStock < reorderLevel) return 'red';
  if (currentStock <= reorderLevel * 1.2) return 'amber';
  return 'green';
};

const getStockStatus = (currentStock, reorderLevel) => {
  if (currentStock === 0) return 'Out of Stock';
  if (currentStock < reorderLevel) return 'Low Stock';
  return 'In Stock';
};

// Skeleton Components
const SkeletonRow = () => (
  <div style={{ display: 'flex', gap: '12px', padding: '12px', marginBottom: '12px' }}>
    <div className="skeleton-line" style={{ flex: 1, height: '12px' }} />
    <div className="skeleton-line" style={{ flex: 1, height: '12px' }} />
    <div className="skeleton-line" style={{ flex: 1, height: '12px' }} />
  </div>
);

const SkeletonTable = () => (
  <div style={{ marginTop: '16px' }}>
    {[...Array(5)].map((_, i) => (
      <SkeletonRow key={i} />
    ))}
  </div>
);

// Inventory Page
export default function Inventory() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  
  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedOutlet, setSelectedOutlet] = useState('all');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [showAlertsCollapsed, setShowAlertsCollapsed] = useState(false);
  
  // Drawer State
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedInventory, setSelectedInventory] = useState(null);
  const [newStockQuantity, setNewStockQuantity] = useState('');
  const [updateReason, setUpdateReason] = useState('Received Shipment');
  const [updateNotes, setUpdateNotes] = useState('');
  
  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [movementData, setMovementData] = useState([]);
  const [selectedMovementProduct, setSelectedMovementProduct] = useState(null);

  // Get User Context
  const { data: userData } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await authAPI.getUser();
      return response.data;
    },
  });
  
  const isSuperAdmin = userData?.role === 'super_admin';
  const userOutletId = userData?.outlet_id;

  // Fetch Inventory
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

  // Fetch Categories
  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await api.get('/api/v1/categories');
      return response.data;
    },
  });

  // Fetch Outlets
  const { data: outletsData } = useQuery({
    queryKey: ['outlets'],
    queryFn: async () => {
      const response = await api.get('/api/v1/outlets');
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // Fetch Low Stock Alerts
  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['low-stock-alerts'],
    queryFn: async () => {
      const response = await api.get('/api/v1/inventory/alerts/low-stock');
      return response.data;
    },
  });

  // Fetch Stock Movement
  const { data: movementDataAPI } = useQuery({
    queryKey: ['stock-movement', selectedInventory?.id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/inventory/${selectedInventory.id}/movement`);
      return response.data;
    },
    enabled: !!selectedInventory,
  });

  // Update Stock Mutation
  const updateStockMutation = useMutation({
    mutationFn: async () => {
      const response = await api.put(`/api/v1/inventory/${selectedInventory.id}`, {
        quantity: parseInt(newStockQuantity),
        reason: updateReason,
        notes: updateNotes,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['low-stock-alerts'] });
      setDrawerOpen(false);
      setSelectedInventory(null);
      setNewStockQuantity('');
      setUpdateReason('Received Shipment');
      setUpdateNotes('');
      showToast('Stock updated successfully', 'success');
    },
  });

  // Filtered Inventory
  const filteredInventory = useMemo(() => {
    if (!inventoryData) return [];
    
    let filtered = inventoryData;
    
    // Filter by search
    if (searchQuery.trim()) {
      filtered = filtered.filter(item =>
        item.product?.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.product?.sku?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(item => item.product?.category_id === parseInt(selectedCategory));
    }
    
    // Filter by outlet
    if (!isSuperAdmin && userOutletId) {
      filtered = filtered.filter(item => item.outlet_id === userOutletId);
    } else if (selectedOutlet !== 'all') {
      filtered = filtered.filter(item => item.outlet_id === parseInt(selectedOutlet));
    }
    
    // Filter by low stock
    if (showLowStockOnly) {
      filtered = filtered.filter(item => item.quantity < item.reorder_level);
    }
    
    return filtered;
  }, [inventoryData, searchQuery, selectedCategory, selectedOutlet, showLowStockOnly, isSuperAdmin, userOutletId]);

  // Table Columns
  const columns = [
    {
      header: 'Product',
      accessor: 'product',
      render: (item) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ fontWeight: '600', color: '#1A1A1A' }}>
            {item.product?.name}
          </div>
          <div style={{ fontSize: '12px', color: '#9CA3AF' }}>
            SKU: {item.product?.sku}
          </div>
        </div>
      ),
    },
    {
      header: 'Category',
      accessor: 'category',
      render: (item) => (
        <Badge variant="blue" text={item.product?.category?.name} />
      ),
    },
    {
      header: 'Current Stock',
      accessor: 'quantity',
      render: (item) => {
        const color = getStockColor(item.quantity, item.reorder_level);
        const colorMap = {
          red: '#EF4444',
          amber: '#F59E0B',
          green: '#10B981',
        };
        return (
          <div style={{
            fontWeight: '600',
            color: colorMap[color],
            fontSize: '14px',
          }}>
            {item.quantity}
          </div>
        );
      },
    },
    {
      header: 'Reorder Level',
      accessor: 'reorder_level',
      render: (item) => <div>{item.reorder_level}</div>,
    },
    {
      header: 'Unit Price',
      accessor: 'unit_price',
      render: (item) => <div>{fmtINR(item.unit_price)}</div>,
    },
    {
      header: 'Cost Price',
      accessor: 'cost_price',
      render: (item) => <div>{fmtINR(item.cost_price)}</div>,
    },
    ...(isSuperAdmin ? [{
      header: 'Outlet',
      accessor: 'outlet',
      render: (item) => <div>{item.outlet?.name || 'N/A'}</div>,
    }] : []),
    {
      header: 'Status',
      accessor: 'status',
      render: (item) => {
        const status = getStockStatus(item.quantity, item.reorder_level);
        const variantMap = {
          'In Stock': 'green',
          'Low Stock': 'yellow',
          'Out of Stock': 'red',
        };
        return <Badge variant={variantMap[status]} text={status} />;
      },
    },
    {
      header: 'Actions',
      accessor: 'actions',
      render: (item) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => {
              setSelectedInventory(item);
              setNewStockQuantity(item.quantity.toString());
              setDrawerOpen(true);
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 12px',
              background: '#EDE9FE',
              border: '1px solid #DDD6FE',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '500',
              color: '#6D28D9',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#DDD6FE';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#EDE9FE';
            }}
          >
            <Edit2 size={14} />
            Edit Stock
          </button>
          <button
            onClick={() => {
              setSelectedMovementProduct(item.product?.name);
              setMovementData(movementDataAPI || []);
              setModalOpen(true);
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 12px',
              background: '#E0F2FE',
              border: '1px solid #BAE6FD',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '500',
              color: '#0369A1',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#BAE6FD';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#E0F2FE';
            }}
          >
            <Eye size={14} />
            Movement
          </button>
        </div>
      ),
    },
  ];

  // Get active alerts
  const activeAlerts = (alertsData || []).slice(0, 5);
  const totalAlerts = alertsData?.length || 0;

  // Calculate stats
  const totalProducts = filteredInventory.length;
  const lowStockCount = filteredInventory.filter(item => item.quantity < item.reorder_level).length;

  return (
    <div className="inventory">
      {/* Header Section */}
      <div className="inventory-header">
        <div>
          <p className="page-subtitle">
            {totalProducts} products • {totalAlerts} active alerts
          </p>
        </div>
      </div>

      {/* Alerts Section */}
      {totalAlerts > 0 && (
        <div className="inventory-alerts-section">
          <button
            className="alerts-toggle"
            onClick={() => setShowAlertsCollapsed(!showAlertsCollapsed)}
          >
            <AlertCircle size={18} />
            <span>Low Stock Alerts ({totalAlerts})</span>
            <ChevronDown size={18} style={{
              transform: showAlertsCollapsed ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s',
            }} />
          </button>
          
          {!showAlertsCollapsed && (
            <div className="alerts-container">
              {alertsLoading ? (
                <div>Loading alerts...</div>
              ) : (
                <>
                  <div className="alerts-list">
                    {activeAlerts.map((alert, idx) => (
                      <div key={idx} className="alert-card">
                        <div className="alert-info">
                          <div className="alert-product">
                            <strong>{alert.product?.name}</strong>
                            {isSuperAdmin && <span className="alert-outlet">{alert.outlet?.name}</span>}
                          </div>
                          <div className="alert-stock">
                            Stock: <strong>{alert.current_stock}</strong> / Threshold: <strong>{alert.threshold}</strong>
                          </div>
                        </div>
                        <div className="alert-actions">
                          <button className="alert-button resolve">Resolve</button>
                          <button className="alert-button reorder">Create Reorder</button>
                        </div>
                      </div>
                    ))}
                  </div>
                  {totalAlerts > 5 && (
                    <div style={{ padding: '12px', textAlign: 'center' }}>
                      <a href="#" style={{ color: '#2563EB', fontSize: '13px', textDecoration: 'none' }}>
                        View All {totalAlerts} Alerts
                      </a>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Filter Bar */}
      <div className="inventory-filter-bar">
        <input
          type="text"
          placeholder="Search product name or SKU..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="filter-input"
        />
        
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Categories</option>
          {categoriesData?.map(cat => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
        
        {isSuperAdmin && (
          <select
            value={selectedOutlet}
            onChange={(e) => setSelectedOutlet(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Outlets</option>
            {outletsData?.map(outlet => (
              <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
            ))}
          </select>
        )}
        
        <label className="filter-toggle">
          <input
            type="checkbox"
            checked={showLowStockOnly}
            onChange={(e) => setShowLowStockOnly(e.target.checked)}
          />
          <span>Show Low Stock Only</span>
        </label>
        
        <button className="action-button bulk-update">
          Bulk Update
        </button>
        
        <button className="action-button export-csv">
          <Download size={16} />
          Export CSV
        </button>
      </div>

      {/* Table Section */}
      <div className="inventory-table-section">
        {inventoryLoading ? (
          <SkeletonTable />
        ) : inventoryError ? (
          <div className="table-error">
            <AlertCircle size={24} />
            <p>Failed to load inventory</p>
            <button onClick={() => refetchInventory()}>Retry</button>
          </div>
        ) : (
          <div className="overflow-x-auto md:overflow-x-visible">
            <DataTable columns={columns} data={filteredInventory} />
          </div>
        )}
      </div>

      {/* Edit Stock Drawer */}
      {drawerOpen && selectedInventory && (
        <div className="drawer-overlay" onClick={() => setDrawerOpen(false)}>
          <div className="drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <h2>Edit Stock - {selectedInventory.product?.name}</h2>
              <button
                onClick={() => setDrawerOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                <X size={24} />
              </button>
            </div>
            
            <div className="drawer-content">
              <div className="drawer-section">
                <label className="drawer-label">Current Stock</label>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#1A1A1A' }}>
                  {selectedInventory.quantity} units
                </div>
              </div>
              
              <div className="drawer-section">
                <label className="drawer-label">New Stock Quantity</label>
                <input
                  type="number"
                  value={newStockQuantity}
                  onChange={(e) => setNewStockQuantity(e.target.value)}
                  className="drawer-input"
                  min="0"
                />
              </div>
              
              <div className="drawer-section">
                <label className="drawer-label">Reason</label>
                <select
                  value={updateReason}
                  onChange={(e) => setUpdateReason(e.target.value)}
                  className="drawer-select"
                >
                  <option>Received Shipment</option>
                  <option>Manual Correction</option>
                  <option>Damaged Goods</option>
                  <option>Stock Count Adjustment</option>
                </select>
              </div>
              
              <div className="drawer-section">
                <label className="drawer-label">Notes</label>
                <textarea
                  value={updateNotes}
                  onChange={(e) => setUpdateNotes(e.target.value)}
                  className="drawer-textarea"
                  placeholder="Add notes about this stock update..."
                  rows={4}
                />
              </div>
            </div>
            
            <div className="drawer-footer">
              <button
                onClick={() => setDrawerOpen(false)}
                className="drawer-button cancel"
              >
                Cancel
              </button>
              <button
                onClick={() => updateStockMutation.mutate()}
                disabled={updateStockMutation.isPending || !newStockQuantity}
                className="drawer-button save"
              >
                {updateStockMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stock Movement Modal */}
      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Stock Movement - {selectedMovementProduct}</h2>
              <button
                onClick={() => setModalOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                <X size={24} />
              </button>
            </div>
            
            <div className="modal-content">
              {movementData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={movementData}>
                    <defs>
                      <linearGradient id="colorQuantity" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 12, fill: 'var(--text-muted)' }}
                      stroke="#525252"
                    />
                    <YAxis
                      tick={{ fontSize: 12, fill: 'var(--text-muted)' }}
                      stroke="#525252"
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--bg-card)',
                        border: '1px solid rgba(245,158,11,0.2)',
                        borderRadius: '12px',
                        color: 'var(--text-primary)',
                      }}
                      formatter={(value) => [value, 'Quantity']}
                    />
                    <Area
                      type="monotone"
                      dataKey="quantity"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorQuantity)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#6B7280' }}>No movement data available</p>
                </div>
              )}
            </div>
            
            <div className="modal-footer">
              <button
                onClick={() => setModalOpen(false)}
                className="modal-button close"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
