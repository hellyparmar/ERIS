import { useState, useEffect, useMemo } from 'react';
import {
  Users, Award, CreditCard, TrendingUp, Search, Plus, RotateCcw,
  X, Phone, MapPin, DollarSign,
  Loader2, UserPlus, ShieldAlert,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie
} from 'recharts';

import { api } from '../lib/api';
import SEO from '../components/SEO';

const TIER_CLASSES = {
  Platinum: 'active',
  Gold: 'active',
  Silver: 'warning',
  Bronze: 'neutral',
};

const SEGMENT_CLASSES = {
  VIP: 'active',
  Regular: 'neutral',
  New: 'warning',
};

const ANALYTICS_TREND = [
  { month: 'Jan', count: 120 },
  { month: 'Feb', count: 150 },
  { month: 'Mar', count: 210 },
  { month: 'Apr', count: 290 },
  { month: 'May', count: 380 },
  { month: 'Jun', count: 480 },
];

const ANALYTICS_TIERS = [
  { name: 'Bronze', value: 240, color: '#8B5E3C' },
  { name: 'Silver', value: 160, color: '#AEB784' },
  { name: 'Gold', value: 65, color: '#2C1F14' },
  { name: 'Platinum', value: 15, color: '#091413' },
];

const ANALYTICS_SEGMENTS = [
  { name: 'New', value: 110, color: '#AEB784' },
  { name: 'Regular', value: 320, color: '#8B5E3C' },
  { name: 'VIP', value: 50, color: '#091413' },
];

function AddCustomerModal({ onClose, onSave }) {
  const [formData, setFormData] = useState({ name: '', phone: '', address: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.phone) {
      setError('Name and Phone are required fields.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/api/v1/customers/', formData);
      const resData = res.data;
      if (resData.success) {
        onSave(resData.data);
        onClose();
      } else {
        setError(resData.detail || resData.message || 'Failed to create customer');
      }
    } catch (err) {
      setError('Network error. Failed to add customer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(0,0,0,0.6)',
      padding: 24,
    }} onClick={onClose}>
      <div className="animate-in" onClick={e => e.stopPropagation()} style={{
        width: '100%', maxWidth: 440,
        background: 'var(--c-canvas)', border: '1px solid var(--c-border)',
        borderRadius: 'var(--radius)', overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px', borderBottom: '1px solid var(--c-border)',
          background: 'var(--c-canvas-raised)',
        }}>
          <span style={{ fontFamily: 'var(--f-display)', fontSize: '15px', fontWeight: 600, color: 'var(--c-dark)' }}>Add Customer</span>
          <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-ink-muted)' }} onClick={onClose}><X size={16} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
            {error && (
              <div style={{ padding: '8px 12px', background: 'rgba(206,17,17,0.1)', color: 'var(--c-critical)', fontSize: '12px' }}>
                {error}
              </div>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Full Name *</span>
              <input type="text" placeholder="John Doe" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Phone Number *</span>
              <input type="tel" placeholder="9876543210" value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} required />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Delivery Address</span>
              <input type="text" placeholder="Apartment, Street, City" value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })} />
            </div>
          </div>
          <div style={{
            display: 'flex', justifyContent: 'flex-end', gap: 8,
            padding: '12px 20px', borderTop: '1px solid var(--c-border)',
            background: 'var(--c-canvas-raised)',
          }}>
            <button className="action-btn" type="button" onClick={onClose}>Cancel</button>
            <button className="action-btn primary" type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create Customer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CustomerDetailPanel({ customerId, onClose, onRefreshList }) {
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');

    
        
        
  const [panelError, setPanelError] = useState('');

  const fetchDetails = async () => {
    setLoading(true);
    setPanelError('');
    try {
      const res = await api.get(`/api/v1/customers/${customerId}`);
      const data = res.data;
      if (data.success) {
        setCustomer(data.data);
      } else {
        setPanelError('Failed to retrieve details');
      }
    } catch {
      setPanelError('Error retrieving customer');
    } finally {
      setLoading(false);
    }
  };

  
  
  useEffect(() => {
    if (customerId) {
      fetchDetails();
      setTab('overview');
    }
  }, [customerId]);

  useEffect(() => {
    
  }, [tab]);

  
  
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 900,
      background: 'rgba(0,0,0,0.5)',
    }} onClick={onClose}>
      <div
        className="animate-in"
        onClick={e => e.stopPropagation()}
        style={{
          position: 'fixed', right: 0, top: 0, height: '100vh', width: '100%', maxWidth: 460,
          background: 'var(--c-canvas)', borderLeft: '1px solid var(--c-border)',
          display: 'flex', flexDirection: 'column',
        }}
      >
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '16px 20px', borderBottom: '1px solid var(--c-border)',
          background: 'var(--c-canvas-raised)',
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'var(--c-strip)', color: 'var(--c-brown)',
            fontSize: 14, fontWeight: 700, border: '1px solid var(--c-border)'
          }}>
            {customer ? customer.name[0] : '?'}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--c-dark)' }}>
              {customer ? customer.name : 'Loading Profile...'}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--c-ink-muted)' }}>
              ID: {customer ? customer.id : '...'}
            </div>
          </div>
          <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-ink-muted)' }} onClick={onClose}><X size={16} /></button>
        </div>

        <div style={{
          display: 'flex', borderBottom: '1px solid var(--c-border)',
          background: 'var(--c-strip)', padding: '0 12px',
        }}>
          {['overview'].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: '10px 14px', fontSize: '12px', fontWeight: tab === t ? 600 : 500,
              color: tab === t ? 'var(--c-brown)' : 'var(--c-ink-muted)',
              background: 'transparent', border: 'none', cursor: 'pointer',
              borderBottom: tab === t ? '2px solid var(--c-brown)' : '2px solid transparent',
            }}>
              {t === 'overview' ? 'Overview' : t}
            </button>
          ))}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
              <Loader2 size={24} style={{ color: 'var(--c-ink-muted)', animation: 'spin 1s linear infinite' }} />
            </div>
          ) : panelError ? (
            <div style={{ padding: '8px 12px', background: 'rgba(206,17,17,0.1)', color: 'var(--c-critical)', fontSize: '12px' }}>
              {panelError}
            </div>
          ) : (
            <>
              {tab === 'overview' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

                    <div className={`badge ${SEGMENT_CLASSES[customer.segment] || 'neutral'}`}>
                      {customer.segment}
                    </div>


                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 14, background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '12px' }}>
                      <Phone size={12} style={{ color: 'var(--c-ink-muted)' }} />
                      <span>{customer.phone || 'No phone number'}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '12px' }}>
                      <MapPin size={12} style={{ color: 'var(--c-ink-muted)' }} />
                      <span>{customer.address || 'No address provided'}</span>
                    </div>
                  </div>

                  <div>
                    <div className="zone-label" style={{ marginBottom: 8 }}>Relationship Summary</div>
                    <div className="two-col">
                      <div className="col-body" style={{ background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', padding: 12 }}>
                        <div className="kpi-label">Lifetime Value</div>
                        <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'var(--f-mono)', color: 'var(--c-dark)' }}>₹{customer.lifetime_value.toLocaleString()}</div>
                      </div>
                      <div className="col-body" style={{ background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', padding: 12 }}>
                        <div className="kpi-label">Total Orders</div>
                        <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'var(--f-mono)', color: 'var(--c-dark)' }}>{customer.total_purchases}</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Customers() {
  const [activeTab, setActiveTab] = useState('list');
  const [stats, setStats] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeModal, setActiveModal] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [statusChip, setStatusChip] = useState('all');

  const [pagination, setPagination] = useState({ page: 1, per_page: 10, total: 0, total_pages: 0 });

  const fetchStats = async () => {
    try {
      const res = await api.get('/api/v1/customers/stats');
      const data = res.data;
      if (data.success) setStats(data.data);
    } catch (error) {
      console.error('Error fetching customer stats:', error);
    }
  };

  const fetchCustomersList = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pagination.page,
        per_page: pagination.per_page,
        ...(searchQuery && { search: searchQuery }),
        ...(segmentFilter && { segment: segmentFilter }),
        ...(tierFilter && { tier: tierFilter }),
      });

      const res = await api.get(`/api/v1/customers?${params}`);
      const data = res.data;
      if (data.success) {
        setCustomers(data.data.customers);
        setPagination(prev => ({
          ...prev,
          total: data.data.total,
          total_pages: data.data.total_pages,
        }));
      }
    } catch (error) {
      console.error('Error fetching customers list:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    if (activeTab === 'list') {
      fetchCustomersList();
    }
  }, [activeTab, pagination.page, searchQuery, segmentFilter, tierFilter, statusChip]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSegmentFilter('');
    setTierFilter('');
    setStatusChip('all');
    setPagination(p => ({ ...p, page: 1 }));
  };

  const hasActiveFilters = searchQuery || segmentFilter || tierFilter || statusChip !== 'all';

  const tabLabels = [
    { key: 'list', label: 'Customer List', icon: Users },
    { key: 'analytics', label: 'Analytics', icon: TrendingUp },
  ];

  return (
    <>
      <SEO title="Customer Relations" description="Manage customers" />
      <style>{`
        .customer-row:hover {
          background: var(--c-brown-glow) !important;
        }
      `}</style>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0, minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
        
        {/* Header */}
        <div style={{
          padding: '16px 22px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          borderBottom: '1px solid var(--c-border)',
          background: 'var(--c-canvas)'
        }}>
          <div>
            <h1 className="page-title" >Customers</h1>
            <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>
              Manage customer profiles
            </p>
          </div>
          {activeTab === 'list' && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <div style={{ position: 'relative' }}>
                <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-muted)' }} />
                <input
                  placeholder="Search name/phone..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{ paddingLeft: 30, fontSize: 12, width: 200 }}
                />
              </div>
              <button className="action-btn primary" onClick={() => setActiveModal(true)}>
                <UserPlus size={14} style={{ marginRight: 6 }} /> Add Customer
              </button>
            </div>
          )}
        </div>

        {/* Tab Selector */}
        <div className="filter-bar" style={{ borderBottom: '1px solid var(--c-border)', borderRadius: 0 }}>
          {tabLabels.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setActiveTab(key)} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '10px 14px',
              background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 13,
              fontWeight: activeTab === key ? 600 : 500,
              color: activeTab === key ? 'var(--c-brown)' : '#5C4F3D',
              borderBottom: activeTab === key ? '2px solid #8B5E3C' : '2px solid transparent',
              marginBottom: -1,
            }}>
              <Icon size={13} /> {label}
            </button>
          ))}
        </div>

        {/* Main Content */}
        <div style={{ padding: '22px' }}>
          {activeTab === 'list' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {stats && (
                <div className="kpi-strip">
                  <div className="kpi-cell">
                    <div className="kpi-label">Total Relationships</div>
                    <div className="kpi-value brown">{stats.total_customers.toLocaleString()}</div>
                  </div>
                  <div className="kpi-cell">
                    <div className="kpi-label">VIP Members</div>
                    <div className="kpi-value sage">{stats.vip_customers.toLocaleString()}</div>
                  </div>
                  <div className="kpi-cell">
                    <div className="kpi-label">Total Lifetime Value</div>
                    <div className="kpi-value brown">₹{(stats.total_lifetime_value / 1000).toFixed(1)}K</div>
                  </div>
                  <div className="kpi-cell">
                    <div className="kpi-label">Average Ticket Size</div>
                    <div className="kpi-value">₹{stats.average_lifetime_value.toLocaleString()}</div>
                  </div>
                </div>
              )}

              {/* Filters */}
              <div className="filter-bar">
                <select value={segmentFilter} onChange={e => setSegmentFilter(e.target.value)} style={{ width: 'auto', minWidth: 150 }}>
                  <option value="">All Segments</option>
                  <option value="VIP">VIP</option>
                  <option value="Regular">Regular</option>
                  <option value="New">New</option>
                </select>

                <select value={tierFilter} onChange={e => setTierFilter(e.target.value)} style={{ width: 'auto', minWidth: 150 }}>
                  <option value="">All Tiers</option>
                  <option value="Bronze">Bronze</option>
                  <option value="Silver">Silver</option>
                  <option value="Gold">Gold</option>
                  <option value="Platinum">Platinum</option>
                </select>

                {[
                  { key: 'all', label: 'All Statuses' },
                  { key: 'active', label: 'Active' },
                  { key: 'inactive', label: 'Inactive' },
                ].map(({ key, label }) => (
                  <button key={key} onClick={() => setStatusChip(key)} className={`action-btn ${statusChip === key ? 'primary' : ''}`}>
                    {label}
                  </button>
                ))}

                {hasActiveFilters && (
                  <button className="action-btn" onClick={handleResetFilters} style={{ marginLeft: 'auto' }}>
                    <RotateCcw size={12} style={{ marginRight: 6 }} /> Clear
                  </button>
                )}
              </div>

              {/* Customer Table */}
              <div style={{ overflowX: 'auto' }}>
                <table className="eris-table" style={{ width: '100%' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>Customer Name</th>
                      <th style={{ textAlign: 'left' }}>Contact</th>
                      <th style={{ textAlign: 'center' }}>Segment</th>
                      <th style={{ textAlign: 'right' }}>Lifetime Value</th>
                      <th style={{ textAlign: 'center' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="6" style={{ textAlign: 'center', padding: '40px 0' }}>
                          <Loader2 size={24} style={{ color: 'var(--c-ink-muted)', animation: 'spin 1s linear infinite' }} />
                        </td>
                      </tr>
                    ) : customers.length === 0 ? (
                      <tr>
                        <td colSpan="6">
                          <div className="empty-state">
                            <p className="empty-state-desc">No Customers Registered</p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      customers.map((c, idx) => (
                        <tr key={c.id} className="customer-row" onClick={() => setSelectedCustomerId(c.id)} style={{ cursor: 'pointer' }}>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                              <div style={{
                                width: 28, height: 28, borderRadius: '50%',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                background: 'var(--c-strip)', color: 'var(--c-brown)',
                                fontSize: '12px', fontWeight: 700, border: '1px solid var(--c-border)'
                              }}>
                                {c.name ? c.name[0] : '?'}
                              </div>
                              <div>
                                <div style={{ fontWeight: 600, color: 'var(--c-dark)' }}>{c.name}</div>
                                <div style={{ fontSize: '10px', color: 'var(--c-ink-muted)' }}>#{c.id}</div>
                              </div>
                            </div>
                          </td>
                          <td>
                            <div style={{ fontWeight: 500 }}>{c.phone}</div>
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <div className={`badge ${SEGMENT_CLASSES[c.segment] || 'neutral'}`}>
                              {c.segment}
                            </div>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <div className="mono" style={{ fontWeight: 700 }}>₹{c.lifetime_value.toLocaleString()}</div>
                            </td>
                          <td style={{ textAlign: 'center' }}>
                            <button className="action-btn primary" style={{ padding: '4px 10px', fontSize: '11px' }} onClick={e => { e.stopPropagation(); setSelectedCustomerId(c.id); }}>
                              View
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {pagination.total_pages > 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', gap: 6 }}>
                  <button className="action-btn" disabled={pagination.page === 1} onClick={() => setPagination(p => ({ ...p, page: p.page - 1 }))}>Prev</button>
                  <span style={{ fontSize: '12px', alignSelf: 'center' }}>{pagination.page} / {pagination.total_pages}</span>
                  <button className="action-btn" disabled={pagination.page === pagination.total_pages} onClick={() => setPagination(p => ({ ...p, page: p.page + 1 }))}>Next</button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'analytics' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="kpi-strip">
                <div className="kpi-cell">
                  <div className="kpi-label">VIP Concentration</div>
                  <div className="kpi-value brown">12.5%</div>
                </div>
                <div className="kpi-cell">
                  <div className="kpi-label">LTV Growth Rate</div>
                  <div className="kpi-value sage">+18.4%</div>
                </div>
                <div className="kpi-cell">
                  <div className="kpi-label">Credit Collection Rate</div>
                  <div className="kpi-value sage">75%</div>
                </div>
                <div className="kpi-cell">
                  <div className="kpi-label">Points Redeemed</div>
                  <div className="kpi-value">2.4K pts</div>
                </div>
              </div>

              <div className="two-col">
                <div className="col-body" style={{ flex: 1.5 }}>
                  <div className="zone-label" style={{ marginBottom: 12 }}>Relationship Acquisition Trend</div>
                  <div className="chart-inner" style={{ height: 260 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={ANALYTICS_TREND}>
                        <defs>
                          <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="var(--c-brown)" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="var(--c-brown)" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--c-border)" vertical={false} />
                        <XAxis dataKey="month" stroke="var(--c-border)" tick={{ fill: 'var(--c-ink-muted)', fontSize: 11 }} />
                        <YAxis stroke="var(--c-border)" tick={{ fill: 'var(--c-ink-muted)', fontSize: 11 }} />
                        <Tooltip />
                        <Area type="monotone" dataKey="count" stroke="var(--c-brown)" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="col-divider" />

                <div className="col-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ borderBottom: '1px solid var(--c-border)', paddingBottom: 12 }}>
                    <div className="zone-label" style={{ marginBottom: 8 }}>Segments</div>
                    <div style={{ height: 120 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={ANALYTICS_SEGMENTS} cx="50%" cy="50%" innerRadius={35} outerRadius={50} paddingAngle={4} dataKey="value">
                            {ANALYTICS_SEGMENTS.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div style={{ display: 'flex', gap: 10, justifyContent: 'center', fontSize: '10px' }}>
                      {ANALYTICS_SEGMENTS.map((s, idx) => (
                        <span key={idx} style={{ color: s.color, fontWeight: 600 }}>● {s.name}</span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="zone-label" style={{ marginBottom: 8 }}>Tiers</div>
                    <div style={{ height: 120 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={ANALYTICS_TIERS} cx="50%" cy="50%" innerRadius={35} outerRadius={50} paddingAngle={4} dataKey="value">
                            {ANALYTICS_TIERS.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div style={{ display: 'flex', gap: 10, justifyContent: 'center', fontSize: '10px' }}>
                      {ANALYTICS_TIERS.map((t, idx) => (
                        <span key={idx} style={{ color: t.color, fontWeight: 600 }}>● {t.name}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

      </div>

      {activeModal && (
        <AddCustomerModal
          onClose={() => setActiveModal(false)}
          onSave={(newCust) => {
            setCustomers(prev => [newCust, ...prev]);
            fetchStats();
          }}
        />
      )}

      {selectedCustomerId && (
        <CustomerDetailPanel
          customerId={selectedCustomerId}
          onClose={() => setSelectedCustomerId(null)}
          onRefreshList={fetchCustomersList}
        />
      )}
    </>
  );
}
