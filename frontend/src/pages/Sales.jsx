import React, { useState, useMemo, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Plus, X } from 'lucide-react';
import api from '../lib/api';
import SEO from '../components/SEO';
import Modal from '../components/ui/Modal';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';

const formatCurrency = (value) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);

export default function Sales() {
  const { user } = useAuth();
  const canWrite = user?.role === 'admin' || user?.role === 'manager';
  const [selectedOutlet, setSelectedOutlet] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('30');
  
  const { addToast } = useToast();
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addForm, setAddForm] = useState({
    outlet_id: '',
    product_id: '',
    quantity: 1,
    discount: 0,
    payment_method: 'card'
  });
  const [addError, setAddError] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (canWrite && params.get('action') === 'new') {
      setAddModalOpen(true);
    }
  }, [canWrite]);
  
  const { data: outletsData } = useQuery({
    queryKey: ['outlets'],
    queryFn: () => api.get('/api/v1/outlets').then(r => r.data.data || []),
  });

  useEffect(() => {
    if (!addForm.outlet_id && outletsData?.length) {
      setAddForm((current) => ({
        ...current,
        outlet_id: selectedOutlet || String(outletsData[0].id),
      }));
    }
  }, [addForm.outlet_id, outletsData, selectedOutlet]);

  const { data: saleInventory = [] } = useQuery({
    queryKey: ['saleInventory', addForm.outlet_id],
    queryFn: () => api.get('/api/v1/inventory', {
      params: { outlet_id: Number(addForm.outlet_id) },
    }).then((response) => Array.isArray(response.data) ? response.data : response.data?.items || []),
    enabled: Boolean(addForm.outlet_id),
  });

  const { data: salesData } = useQuery({
    queryKey: ['sales', selectedOutlet, selectedPeriod],
    queryFn: () => {
      const params = new URLSearchParams();
      if (selectedOutlet) params.append('outlet_id', selectedOutlet);
      params.append('days', selectedPeriod);
      return api.get(`/api/v1/analytics/dashboard/revenue-trend?${params}`).then(r => r.data || []);
    },
  });

  const { data: topProductsData } = useQuery({
    queryKey: ['topProducts', selectedOutlet, selectedPeriod],
    queryFn: () => {
      const params = new URLSearchParams();
      if (selectedOutlet) params.append('outlet_id', selectedOutlet);
      params.append('period', `${selectedPeriod}d`);
      params.append('limit', '10');
      return api.get(`/api/v1/analytics/dashboard/top-products?${params}`).then(r => r.data || []);
    },
  });

  const { data: outletPerformanceData } = useQuery({
    queryKey: ['outletPerformance', selectedPeriod],
    queryFn: () => {
      return api.get(`/api/v1/analytics/dashboard/outlet-performance?period=${selectedPeriod}d`).then(r => r.data || []);
    },
  });

  const summaryStats = useMemo(() => {
    if (!salesData || salesData.length === 0) {
      return { totalRevenue: 0, avgDailySales: 0, totalTransactions: 0, growth: 0 };
    }
    const totalRevenue = salesData.reduce((sum, item) => sum + (item.revenue || 0), 0);
    const avgDailySales = totalRevenue / salesData.length;
    const totalTransactions = salesData.reduce((sum, item) => sum + (item.transactions || 0), 0);
    const mid = Math.floor(salesData.length / 2);
    const firstHalf = salesData.slice(0, mid).reduce((s, i) => s + (i.revenue || 0), 0);
    const secondHalf = salesData.slice(mid).reduce((s, i) => s + (i.revenue || 0), 0);
    const growth = firstHalf > 0 ? ((secondHalf - firstHalf) / firstHalf) * 100 : 0;
    return { totalRevenue, avgDailySales, totalTransactions, growth };
  }, [salesData]);

  const maxOutletRevenue = useMemo(() =>
    Math.max(...(outletPerformanceData || []).map(o => o.revenue || 0), 1),
  [outletPerformanceData]);

  const queryClient = useQueryClient();
  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setAddError('');
    try {
      const inventoryItem = saleInventory.find(
        (item) => Number(item.product?.id) === Number(addForm.product_id),
      );
      if (!inventoryItem || inventoryItem.quantity < Number(addForm.quantity)) {
        setAddError('Please select a valid product.');
        return;
      }
      const unitPrice = Number(inventoryItem.product.selling_price);
      const quantity = Number(addForm.quantity);
      const discount = Number(addForm.discount) || 0;
      const taxableAmount = Math.max(0, (unitPrice * quantity) - discount);
      const taxAmount = taxableAmount * (Number(inventoryItem.product.gst_rate) || 0) / 100;
      
      const payload = {
        outlet_id: Number(addForm.outlet_id),
        customer_id: null,
        discount,
        tax_amount: Number(taxAmount.toFixed(2)),
        payment_method: addForm.payment_method,
        items: [{
          product_id: Number(addForm.product_id),
          quantity,
        }]
      };

      const res = await api.post('/api/v1/sales/', payload);
      if (res.data) {
        addToast('Sale recorded successfully', 'success');
        setAddModalOpen(false);
        setAddForm((current) => ({ ...current, product_id: '', quantity: 1, discount: 0, payment_method: 'card' }));
        queryClient.invalidateQueries({ queryKey: ['sales'] });
        queryClient.invalidateQueries({ queryKey: ['topProducts'] });
        queryClient.invalidateQueries({ queryKey: ['outletPerformance'] });
      }
    } catch (err) {
      setAddError(err.response?.data?.detail || err.message || 'An error occurred');
    }
  };

  return (
    <>
      <SEO title="Sales & Revenue" description="Track sales performance across outlets" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0, minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
        
        {/* Page header and filters */}
        <div style={{
          background: '#222831',
          padding: '10px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
          width: '100%',
          boxSizing: 'border-box'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '14px', color: '#F3E4C9', fontWeight: '700' }}>Sales & Revenue</span>
            <span style={{ fontSize: '10px', color: '#F3E4C9', opacity: 0.7 }}>Recorded transaction performance</span>
          </div>
          
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {canWrite && (
              <button className="action-btn primary" onClick={() => setAddModalOpen(true)}>
                <Plus size={13} /> New Sale
              </button>
            )}
            <select 
              value={selectedOutlet} 
              onChange={(e) => setSelectedOutlet(e.target.value)} 
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                background: 'transparent',
                borderColor: 'rgba(243,228,201,0.2)',
                color: '#F3E4C9',
                outline: 'none',
                borderRadius: 'var(--radius)'
              }}
            >
              <option value="" style={{ background: 'var(--c-dark)', color: '#F3E4C9' }}>All Outlets</option>
              {outletsData?.map(outlet => (
                <option key={outlet.id} value={outlet.id} style={{ background: 'var(--c-dark)', color: '#F3E4C9' }}>{outlet.name}</option>
              ))}
            </select>
            <select 
              value={selectedPeriod} 
              onChange={(e) => setSelectedPeriod(e.target.value)} 
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                background: 'transparent',
                borderColor: 'rgba(243,228,201,0.2)',
                color: '#F3E4C9',
                outline: 'none',
                borderRadius: 'var(--radius)'
              }}
            >
              <option value="7" style={{ background: 'var(--c-dark)', color: '#F3E4C9' }}>7 Days</option>
              <option value="14" style={{ background: 'var(--c-dark)', color: '#F3E4C9' }}>14 Days</option>
              <option value="30" style={{ background: 'var(--c-dark)', color: '#F3E4C9' }}>30 Days</option>
              <option value="90" style={{ background: 'var(--c-dark)', color: '#F3E4C9' }}>90 Days</option>
            </select>
          </div>
        </div>

        {/* 2. KPI STRIP */}
        <div className="kpi-strip" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="kpi-cell">
            <div className="kpi-label">Total Revenue</div>
            <div className="kpi-value brown">{formatCurrency(summaryStats.totalRevenue)}</div>
            {summaryStats.growth !== undefined && (
              <div className={`kpi-delta ${summaryStats.growth >= 0 ? 'up' : 'down'}`}>
                {summaryStats.growth >= 0 ? <TrendingUp size={12} style={{ display: 'inline', marginRight: 2 }} /> : <TrendingDown size={12} style={{ display: 'inline', marginRight: 2 }} />}
                {Math.abs(summaryStats.growth).toFixed(1)}% vs prior period
              </div>
            )}
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">Avg Daily Sales</div>
            <div className="kpi-value sage">{formatCurrency(summaryStats.avgDailySales)}</div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">Total Transactions</div>
            <div className="kpi-value">{summaryStats.totalTransactions.toLocaleString()}</div>
          </div>
        </div>

        {/* 3. SALES TREND CHART */}
        <div className="content-section-alt">
          <div className="section-header">
            <div className="zone-label" style={{ marginBottom: 0 }}>Sales Trend</div>
          </div>
          <div style={{ marginTop: '12px' }}>
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={salesData || []}>
                <defs>
                  <linearGradient id="salesOcher" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5E3C" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#8B5E3C" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--c-border)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--c-ink-muted)', fontFamily: 'var(--f-mono)' }} stroke="var(--c-border)"
                  tickFormatter={(d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--c-ink-muted)', fontFamily: 'var(--f-mono)' }} stroke="var(--c-border)"
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v) => formatCurrency(v)} labelFormatter={(l) => new Date(l).toLocaleDateString()} contentStyle={{
                  background: 'var(--c-canvas)', border: '1px solid var(--c-border)',
                  borderRadius: 'var(--radius)', fontSize: 12, color: 'var(--c-ink)',
                  fontFamily: 'var(--f-mono)',
                }} />
                <Area type="monotone" dataKey="revenue" stroke="#8B5E3C" fillOpacity={1} fill="url(#salesOcher)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 4. TWO-COL GRID */}
        <div className="content-section" style={{ padding: 0 }}>
          <div className="two-col">
            {/* Left: Top Products */}
            <div className="col-body">
              <div className="section-header">
                <div className="zone-label" style={{ marginBottom: 0 }}>Top Menu Items</div>
              </div>
            <div className="rank-list" style={{ marginTop: '12px' }}>
              {(topProductsData || []).slice(0, 8).map((product, idx) => {
                const maxProd = topProductsData[0]?.revenue || 1;
                const pct = ((product.revenue || 0) / maxProd) * 100;
                const fillColors = ['var(--c-brown)', 'var(--c-sage)', 'var(--c-critical)', 'var(--c-muted)', 'var(--c-muted)'];
                const fillColor = fillColors[idx] || 'var(--c-muted)';
                
                return (
                  <div key={idx} className="rank-row">
                    <div className="rank-num">#{idx + 1}</div>
                    <div className="rank-name">
                      <div>{product.name}</div>
                      <div style={{ fontSize: '10px', color: 'var(--c-ink-muted)' }}>{product.category} &middot; {(product.quantity || 0).toLocaleString()} units</div>
                    </div>
                    <div className="rank-track">
                      <div className="rank-fill" style={{ width: `${pct}%`, background: fillColor }} />
                    </div>
                    <div className="rank-value">{formatCurrency(product.revenue)}</div>
                  </div>
                );
              })}
              {(!topProductsData || topProductsData.length === 0) && (
                <div className="empty-state">
                  <div className="empty-state-title">No menu item data</div>
                </div>
              )}
            </div>
          </div>

          {/* Column Divider */}
          <div className="col-divider" />

            {/* Right: Outlet Performance */}
            <div className="col-body">
              <div className="section-header">
                <div className="zone-label" style={{ marginBottom: 0 }}>Outlet Performance</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '12px' }}>
                {(outletPerformanceData || []).map((outlet, idx) => {
                  const pct = ((outlet.revenue || 0) / maxOutletRevenue) * 100;
                  return (
                    <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <span style={{ fontSize: '13px', color: '#1A1208' }}>{outlet.name}</span>
                        <span className="mono" style={{ textAlign: 'right', fontWeight: 600 }}>{formatCurrency(outlet.revenue)}</span>
                      </div>
                      <div style={{ background: '#EDE8E0', height: '6px', borderRadius: '3px', width: '100%' }}>
                        <div style={{ width: `${pct}%`, background: '#8B5E3C', height: '100%', borderRadius: '3px' }} />
                      </div>
                      <div style={{ display: 'flex', gap: '12px', fontSize: '10px', color: 'var(--c-ink-muted)' }}>
                        <span style={outlet.growth >= 0 ? { color: 'var(--c-sage)' } : { color: 'var(--c-critical)' }}>
                          {outlet.growth >= 0 ? '↑' : '↓'} {Math.abs(outlet.growth || 0)}%
                        </span>
                        <span>{(outlet.transactions || 0).toLocaleString()} transactions</span>
                      </div>
                    </div>
                  );
                })}
              {(!outletPerformanceData || outletPerformanceData.length === 0) && (
                <div className="empty-state">
                  <div className="empty-state-title">No outlet data</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <Modal open={canWrite && addModalOpen} onClose={() => setAddModalOpen(false)} title="New Quick Sale">
        <form onSubmit={handleAddSubmit}>
          {addError && <div style={{ color: 'var(--c-critical)', marginBottom: 12, fontSize: 13 }}>{addError}</div>}
          
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Outlet *</label>
            <select required value={addForm.outlet_id} onChange={e => setAddForm({ ...addForm, outlet_id: e.target.value, product_id: '' })} style={{ width: '100%', padding: '6px 12px' }}>
              <option value="">-- Select outlet --</option>
              {outletsData?.map(outlet => (
                <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Select Product *</label>
            <select required value={addForm.product_id} onChange={e => setAddForm({ ...addForm, product_id: e.target.value })} style={{ width: '100%', padding: '6px 12px' }}>
              <option value="">-- Choose in-stock product --</option>
              {saleInventory.filter(item => item.quantity > 0).map(item => (
                <option key={item.product.id} value={item.product.id}>
                  {item.product.name} — {item.quantity} available
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Quantity</label>
              <input type="number" required min="1" value={addForm.quantity} onChange={e => setAddForm({ ...addForm, quantity: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Discount (₹)</label>
              <input type="number" min="0" step="0.01" value={addForm.discount} onChange={e => setAddForm({ ...addForm, discount: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Payment Method</label>
            <select value={addForm.payment_method} onChange={e => setAddForm({ ...addForm, payment_method: e.target.value })} style={{ width: '100%', padding: '6px 12px' }}>
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="upi">UPI</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <button type="button" onClick={() => setAddModalOpen(false)} className="action-btn">Cancel</button>
            <button type="submit" className="action-btn primary">Complete Sale</button>
          </div>
        </form>
      </Modal>

    </div>
  </>
  );
}
