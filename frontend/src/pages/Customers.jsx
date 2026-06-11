import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, Award, CreditCard, TrendingUp, Search, Plus, Filter, RotateCcw,
  ChevronDown, X, MoreVertical, Mail, Phone, MapPin, Calendar, DollarSign,
  TrendingDown, Check, Loader2, UserPlus, FileText, ArrowRight, ShieldAlert,
  Send, PlusCircle
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie
} from 'recharts';

import LoyaltyDashboard from '../components/customers/LoyaltyDashboard';
import CreditManagement from '../components/customers/CreditManagement';
import '../styles/customers.css';

/* ── CONSTANTS & MOCKS ── */
const TIER_COLORS = {
  Platinum: 'cust-tier--platinum',
  Gold: 'cust-tier--gold',
  Silver: 'cust-tier--silver',
  Bronze: 'cust-tier--bronze',
};

const SEGMENT_COLORS = {
  VIP: 'cust-segment--vip',
  Regular: 'cust-segment--regular',
  New: 'cust-segment--new',
};

// Simulated mock data for analytics
const ANALYTICS_TREND = [
  { month: 'Jan', count: 120 },
  { month: 'Feb', count: 150 },
  { month: 'Mar', count: 210 },
  { month: 'Apr', count: 290 },
  { month: 'May', count: 380 },
  { month: 'Jun', count: 480 },
];

const ANALYTICS_TIERS = [
  { name: 'Bronze', value: 240, color: '#A0522D' },
  { name: 'Silver', value: 160, color: '#9CA3AF' },
  { name: 'Gold', value: 65, color: '#D97706' },
  { name: 'Platinum', value: 15, color: '#374151' },
];

const ANALYTICS_SEGMENTS = [
  { name: 'New', value: 110, color: '#065F46' },
  { name: 'Regular', value: 320, color: '#1D4ED8' },
  { name: 'VIP', value: 50, color: '#6D28D9' },
];

/* ── COMPONENT: CUSTOMER MODAL (ADD NEW) ── */
function AddCustomerModal({ onClose, onSave }) {
  const [formData, setFormData] = useState({ name: '', phone: '', email: '', address: '' });
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
      const response = await fetch(`${import.meta.env.VITE_API_URL}/customers/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const resData = await response.json();
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
    <div className="intg-modal-overlay" onClick={onClose}>
      <motion.div className="intg-modal" onClick={e => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.95, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 16 }}>
        <div className="intg-modal__header">
          <div className="intg-modal__header-icon" style={{ background: '#EDE9FE', color: '#6D28D9' }}>
            <UserPlus size={20}/>
          </div>
          <div className="intg-modal__header-text">
            <h2>Add Customer</h2>
            <p>Create a new profile for in-store relationships</p>
          </div>
          <button className="intg-modal__close" onClick={onClose}><X size={16}/></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="intg-modal__body">
            {error && (
              <div className="intg-status-alert error">
                <ShieldAlert size={15}/>
                {error}
              </div>
            )}
            <div className="intg-form">
              <div className="intg-field">
                <label>Full Name *</label>
                <input className="intg-input no-icon" type="text" placeholder="John Doe"
                  value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required />
              </div>
              <div className="intg-field">
                <label>Phone Number *</label>
                <input className="intg-input no-icon" type="tel" placeholder="9876543210"
                  value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} required />
              </div>
              <div className="intg-field">
                <label>Email Address</label>
                <input className="intg-input no-icon" type="email" placeholder="john@example.com"
                  value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} />
              </div>
              <div className="intg-field">
                <label>Delivery Address</label>
                <input className="intg-input no-icon" type="text" placeholder="Apartment, Street Name, City"
                  value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })} />
              </div>
            </div>
          </div>
          <div className="intg-modal__footer">
            <button className="intg-btn intg-btn--secondary" type="button" onClick={onClose}>Cancel</button>
            <button className="intg-btn intg-btn--primary" type="submit" disabled={loading}>
              {loading ? <Loader2 size={14} className="intg-spin"/> : <Plus size={14}/>}
              {loading ? 'Creating...' : 'Create Customer'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

/* ── COMPONENT: CUSTOMER DETAIL SIDE PANEL ── */
function CustomerDetailPanel({ customerId, onClose, onRefreshList }) {
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');

  // Loyalty Sub-states
  const [loyalty, setLoyalty] = useState(null);
  const [loyaltyLoading, setLoyaltyLoading] = useState(false);

  // Credit Sub-states
  const [credit, setCredit] = useState(null);
  const [creditLoading, setCreditLoading] = useState(false);
  const [creditLimitVal, setCreditLimitVal] = useState('');
  const [assigningLimit, setAssigningLimit] = useState(false);
  
  const [paymentVal, setPaymentVal] = useState('');
  const [payMethod, setPayMethod] = useState('cash');
  const [payNotes, setPayNotes] = useState('');
  const [recordingPayment, setRecordingPayment] = useState(false);

  const [panelError, setPanelError] = useState('');

  const fetchDetails = async () => {
    setLoading(true);
    setPanelError('');
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/customers/${customerId}`);
      const data = await res.json();
      if (data.success) {
        setCustomer(data.data);
      } else {
        setPanelError('Failed to retrieve details');
      }
    } catch {
      setPanelError('Error connecting to API');
    } finally {
      setLoading(false);
    }
  };

  const fetchLoyalty = async () => {
    setLoyaltyLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/customers/${customerId}/loyalty`);
      const data = await res.json();
      if (data.success) {
        setLoyalty(data.data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoyaltyLoading(false);
    }
  };

  const fetchCredit = async () => {
    setCreditLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/customers/${customerId}/credit`);
      const data = await res.json();
      if (data.success) {
        setCredit(data.data);
        setCreditLimitVal(data.data.status?.credit_limit || '');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setCreditLoading(false);
    }
  };

  useEffect(() => {
    if (customerId) {
      fetchDetails();
      setTab('overview');
    }
  }, [customerId]);

  useEffect(() => {
    if (tab === 'loyalty') fetchLoyalty();
    if (tab === 'credit') fetchCredit();
  }, [tab]);

  const handleUpdateLimit = async () => {
    if (!creditLimitVal || isNaN(creditLimitVal)) return;
    setAssigningLimit(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/customers/${customerId}/credit/limit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: parseFloat(creditLimitVal) })
      });
      const data = await res.json();
      if (data.success) {
        fetchCredit();
        onRefreshList();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setAssigningLimit(false);
    }
  };

  const handleRecordPayment = async () => {
    if (!paymentVal || isNaN(paymentVal) || parseFloat(paymentVal) <= 0) return;
    setRecordingPayment(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/customers/${customerId}/credit/pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: parseFloat(paymentVal),
          payment_method: payMethod,
          notes: payNotes
        })
      });
      const data = await res.json();
      if (data.success) {
        setPaymentVal('');
        setPayNotes('');
        fetchCredit();
        onRefreshList();
      } else {
        alert(data.detail || 'Failed to record payment');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setRecordingPayment(false);
    }
  };

  return (
    <div className="intg-modal-overlay" style={{ justifyContent: 'flex-end', padding: 0 }} onClick={onClose}>
      <motion.div
        className="intg-modal"
        style={{ height: '100vh', maxWidth: '560px', borderRadius: 0, display: 'flex', flexDirection: 'column' }}
        onClick={e => e.stopPropagation()}
        initial={{ x: '100%', opacity: 0.9 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: '100%', opacity: 0.9 }}
        transition={{ type: 'spring', damping: 25, stiffness: 220 }}
      >
        {/* Header */}
        <div className="intg-modal__header">
          <div className="cust-avatar" style={{ width: 44, height: 44, background: '#8B5CF6', fontSize: 18 }}>
            {customer ? customer.name[0] : '?'}
          </div>
          <div className="intg-modal__header-text">
            <h2>{customer ? customer.name : 'Loading Profile...'}</h2>
            <p>ID: {customer ? customer.id : '...'}</p>
          </div>
          <button className="intg-modal__close" onClick={onClose}><X size={16}/></button>
        </div>

        {/* Inner Tab bar */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', background: 'var(--bg-muted)', padding: '0 12px' }}>
          <button onClick={() => setTab('overview')} className={`cust-tab ${tab === 'overview' ? 'active' : ''}`} style={{ padding: '10px 14px', fontSize: 13 }}>Overview</button>
          <button onClick={() => setTab('loyalty')} className={`cust-tab ${tab === 'loyalty' ? 'active' : ''}`} style={{ padding: '10px 14px', fontSize: 13 }}>Loyalty Balance</button>
          <button onClick={() => setTab('credit')} className={`cust-tab ${tab === 'credit' ? 'active' : ''}`} style={{ padding: '10px 14px', fontSize: 13 }}>Credit Status</button>
        </div>

        {/* Panel Content Body */}
        <div className="intg-modal__body" style={{ flex: 1, padding: 24 }}>
          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
              <Loader2 className="intg-spin" size={24} style={{ color: 'var(--text-muted)' }}/>
            </div>
          ) : panelError ? (
            <div className="intg-status-alert error"><ShieldAlert size={16}/> {panelError}</div>
          ) : (
            <>
              {tab === 'overview' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <span className={`cust-tier ${TIER_COLORS[customer.loyalty_tier] || 'cust-tier--default'}`}>
                      {customer.loyalty_tier} Tier
                    </span>
                    <span className={`cust-segment ${SEGMENT_COLORS[customer.segment] || 'cust-segment--default'}`}>
                      {customer.segment} Segment
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, background: 'var(--bg-muted)', padding: 16, borderRadius: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                      <Phone size={14} style={{ color: 'var(--text-muted)' }}/>
                      <span>{customer.phone || 'No phone number'}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                      <Mail size={14} style={{ color: 'var(--text-muted)' }}/>
                      <span style={{ wordBreak: 'break-all' }}>{customer.email || 'No email attached'}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                      <MapPin size={14} style={{ color: 'var(--text-muted)' }}/>
                      <span>{customer.address || 'No address provided'}</span>
                    </div>
                  </div>

                  <div>
                    <p className="intg-divider">Relationship Summary</p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
                      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: 12, borderRadius: 8 }}>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>LIFETIME VALUE</span>
                        <div style={{ fontSize: 16, fontWeight: 700, marginTop: 4 }}>₹{customer.lifetime_value.toLocaleString()}</div>
                      </div>
                      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: 12, borderRadius: 8 }}>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>TOTAL ORDERS</span>
                        <div style={{ fontSize: 16, fontWeight: 700, marginTop: 4 }}>{customer.total_purchases} orders</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {tab === 'loyalty' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-muted)', padding: 16, borderRadius: 10 }}>
                    <div>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>AVAILABLE POINTS</span>
                      <div style={{ fontSize: 24, fontWeight: 700, color: '#F59E0B' }}>{customer.loyalty_points} pts</div>
                    </div>
                    <Award size={32} style={{ color: '#F59E0B' }}/>
                  </div>

                  <div>
                    <p className="intg-divider">Recent Point Transactions</p>
                    {loyaltyLoading ? (
                      <div style={{ display: 'flex', justifyContent: 'center', padding: '20px 0' }}><Loader2 size={16} className="intg-spin"/></div>
                    ) : loyalty?.recent_transactions?.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}>
                        {loyalty.recent_transactions.map((t, idx) => (
                          <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', borderBottom: '1px solid var(--border)', fontSize: 12 }}>
                            <div>
                              <div style={{ fontWeight: 600 }}>{t.transaction_type}</div>
                              <div style={{ color: 'var(--text-muted)' }}>{t.date}</div>
                            </div>
                            <div style={{ fontWeight: 700, color: t.points >= 0 ? '#10B981' : '#EF4444' }}>
                              {t.points >= 0 ? `+${t.points}` : t.points}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p style={{ fontSize: 12, color: 'var(--text-faint)', marginTop: 12 }}>No loyalty activities recorded yet</p>
                    )}
                  </div>
                </div>
              )}

              {tab === 'credit' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div style={{ background: 'var(--bg-muted)', padding: 12, borderRadius: 8 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>CREDIT LIMIT</span>
                      <div style={{ fontSize: 18, fontWeight: 700 }}>₹{credit?.status?.credit_limit ? parseFloat(credit.status.credit_limit).toLocaleString() : '0'}</div>
                    </div>
                    <div style={{ background: 'var(--bg-muted)', padding: 12, borderRadius: 8 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>OUTSTANDING</span>
                      <div style={{ fontSize: 18, fontWeight: 700, color: credit?.status?.balance > 0 ? '#EF4444' : 'var(--text-primary)' }}>
                        ₹{credit?.status?.balance ? parseFloat(credit.status.balance).toLocaleString() : '0'}
                      </div>
                    </div>
                  </div>

                  <div>
                    <p className="intg-divider">Adjust Credit Limit</p>
                    <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                      <input className="intg-input no-icon" type="number" placeholder="50000"
                        value={creditLimitVal} onChange={e => setCreditLimitVal(e.target.value)} style={{ flex: 1 }}/>
                      <button className="cust-btn cust-btn--primary" onClick={handleUpdateLimit} disabled={assigningLimit}>
                        {assigningLimit ? <Loader2 size={13} className="intg-spin"/> : 'Update'}
                      </button>
                    </div>
                  </div>

                  <div>
                    <p className="intg-divider">Record Credit Payment</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 10, background: 'var(--bg-muted)', padding: 14, borderRadius: 8 }}>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <input className="intg-input no-icon" type="number" placeholder="Amount (₹)"
                          value={paymentVal} onChange={e => setPaymentVal(e.target.value)} style={{ flex: 1 }}/>
                        <select className="intg-select" value={payMethod} onChange={e => setPayMethod(e.target.value)}>
                          <option value="cash">Cash</option>
                          <option value="card">Card</option>
                          <option value="upi">UPI</option>
                          <option value="bank_transfer">Bank Transfer</option>
                        </select>
                      </div>
                      <input className="intg-input no-icon" type="text" placeholder="Notes / Reference number"
                        value={payNotes} onChange={e => setPayNotes(e.target.value)}/>
                      <button className="cust-btn cust-btn--primary" style={{ alignSelf: 'flex-end' }} onClick={handleRecordPayment} disabled={recordingPayment}>
                        {recordingPayment ? <Loader2 size={13} className="intg-spin"/> : 'Record Payment'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}

/* ── MAIN PAGES EXPORT ── */
export default function Customers() {
  const [activeTab, setActiveTab] = useState('list');
  const [stats, setStats] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeModal, setActiveModal] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState(null);

  // Advanced Filters state
  const [searchQuery, setSearchQuery] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [statusChip, setStatusChip] = useState('all'); // all, active, inactive, new

  const [pagination, setPagination] = useState({ page: 1, per_page: 10, total: 0, total_pages: 0 });

  const fetchStats = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/customers/stats`);
      const data = await response.json();
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
        ...(tierFilter && { tier: tierFilter })
      });

      const response = await fetch(`${import.meta.env.VITE_API_URL}/customers?${params}`);
      const data = await response.json();
      if (data.success) {
        setCustomers(data.data.customers);
        setPagination(prev => ({
          ...prev,
          total: data.data.total,
          total_pages: data.data.total_pages
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

  return (
    <div className="cust-page">
      {/* ── Page Header ── */}
      <div className="cust-header">
        <div className="cust-header__left">
          <p>Manage customer profiles, loyalty programs, and credit ledgers</p>
        </div>
        <div className="cust-header__right">
          {activeTab === 'list' && (
            <>
              <div className="cust-search">
                <Search size={15} className="cust-search__icon"/>
                <input
                  placeholder="Search customer name/phone..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                />
                {searchQuery && (
                  <button className="cust-search__clear" onClick={() => setSearchQuery('')}>
                    <X size={14}/>
                  </button>
                )}
              </div>
              <button className="cust-btn cust-btn--primary" onClick={() => setActiveModal(true)}>
                <UserPlus size={15}/> Add Customer
              </button>
            </>
          )}
        </div>
      </div>

      {/* ── Tabs Bar ── */}
      <div className="cust-tabs">
        <button onClick={() => setActiveTab('list')} className={`cust-tab ${activeTab === 'list' ? 'active' : ''}`}>
          <Users size={15}/> Customer List
        </button>
        <button onClick={() => setActiveTab('loyalty')} className={`cust-tab ${activeTab === 'loyalty' ? 'active' : ''}`}>
          <Award size={15}/> Loyalty Program
        </button>
        <button onClick={() => setActiveTab('credit')} className={`cust-tab ${activeTab === 'credit' ? 'active' : ''}`}>
          <CreditCard size={15}/> Credit Management
        </button>
        <button onClick={() => setActiveTab('analytics')} className={`cust-tab ${activeTab === 'analytics' ? 'active' : ''}`}>
          <TrendingUp size={15}/> Analytics
        </button>
      </div>

      {/* ── Tab Content ── */}
      <div>
        {activeTab === 'list' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* KPI Row */}
            {stats && (
              <div className="cust-kpis">
                <div className="cust-kpi">
                  <div className="cust-kpi__top">
                    <div className="cust-kpi__icon cust-kpi__icon--blue"><Users size={18}/></div>
                  </div>
                  <div className="cust-kpi__value">{stats.total_customers.toLocaleString()}</div>
                  <div className="cust-kpi__label">Total Relationships</div>
                </div>
                <div className="cust-kpi">
                  <div className="cust-kpi__top">
                    <div className="cust-kpi__icon cust-kpi__icon--purple"><Award size={18}/></div>
                  </div>
                  <div className="cust-kpi__value">{stats.vip_customers.toLocaleString()}</div>
                  <div className="cust-kpi__label">VIP Members</div>
                </div>
                <div className="cust-kpi">
                  <div className="cust-kpi__top">
                    <div className="cust-kpi__icon cust-kpi__icon--green"><DollarSign size={18}/></div>
                  </div>
                  <div className="cust-kpi__value">₹{(stats.total_lifetime_value / 1000).toFixed(1)}K</div>
                  <div className="cust-kpi__label">Total Lifetime Value</div>
                </div>
                <div className="cust-kpi">
                  <div className="cust-kpi__top">
                    <div className="cust-kpi__icon cust-kpi__icon--amber"><TrendingUp size={18}/></div>
                  </div>
                  <div className="cust-kpi__value">₹{stats.average_lifetime_value.toLocaleString()}</div>
                  <div className="cust-kpi__label">Average Ticket Size</div>
                </div>
              </div>
            )}

            {/* Filter Bar */}
            <div className="cust-filters">
              <select className="cust-filter-select" value={segmentFilter} onChange={e => setSegmentFilter(e.target.value)}>
                <option value="">All Segments</option>
                <option value="VIP">VIP</option>
                <option value="Regular">Regular</option>
                <option value="New">New</option>
              </select>

              <select className="cust-filter-select" value={tierFilter} onChange={e => setTierFilter(e.target.value)}>
                <option value="">All Tiers</option>
                <option value="Bronze">Bronze</option>
                <option value="Silver">Silver</option>
                <option value="Gold">Gold</option>
                <option value="Platinum">Platinum</option>
              </select>

              <div className="cust-filter-chips">
                <button onClick={() => setStatusChip('all')} className={`cust-chip ${statusChip === 'all' ? 'active' : ''}`}>All Statuses</button>
                <button onClick={() => setStatusChip('active')} className={`cust-chip ${statusChip === 'active' ? 'active' : ''}`}>Active</button>
                <button onClick={() => setStatusChip('inactive')} className={`cust-chip ${statusChip === 'inactive' ? 'active' : ''}`}>Inactive</button>
              </div>

              {hasActiveFilters && (
                <button className="cust-filter-reset" onClick={handleResetFilters}>
                  <RotateCcw size={13}/> Clear Filters
                </button>
              )}
            </div>

            {/* Main Table Card */}
            <div className="cust-table-card">
              <div className="cust-table-wrap">
                <table className="cust-table">
                  <thead>
                    <tr>
                      <th>Customer Name</th>
                      <th>Contact info</th>
                      <th>Segment</th>
                      <th>Tier Badge</th>
                      <th>Lifetime Value</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      Array.from({ length: 5 }).map((_, i) => (
                        <tr key={i}>
                          {Array.from({ length: 6 }).map((_, j) => (
                            <td key={j}><div className="cust-skeleton-cell"/></td>
                          ))}
                        </tr>
                      ))
                    ) : customers.length === 0 ? (
                      <tr>
                        <td colSpan="6">
                          <div className="cust-empty">
                            <div className="cust-empty__icon"><Users size={32}/></div>
                            <h3>No Customers Registered</h3>
                            <p>Get started by recording your first customer to build profile relations.</p>
                            <button className="cust-btn cust-btn--primary" onClick={() => setActiveModal(true)}>
                              <Plus size={14}/> Add First Customer
                            </button>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      customers.map(c => (
                        <tr key={c.id} onClick={() => setSelectedCustomerId(c.id)}>
                          <td>
                            <div className="cust-avatar-cell">
                              <div className="cust-avatar" style={{ background: '#8B5CF6' }}>
                                {c.name ? c.name[0] : '?'}
                              </div>
                              <div>
                                <div className="cust-name">{c.name}</div>
                                <div className="cust-id">#{c.id}</div>
                              </div>
                            </div>
                          </td>
                          <td>
                            <div className="cust-contact-primary">{c.phone}</div>
                            {c.email && <div className="cust-contact-secondary">{c.email}</div>}
                          </td>
                          <td>
                            <span className={`cust-segment ${SEGMENT_COLORS[c.segment] || 'cust-segment--default'}`}>
                              {c.segment}
                            </span>
                          </td>
                          <td>
                            <span className={`cust-tier ${TIER_COLORS[c.loyalty_tier] || 'cust-tier--default'}`}>
                              {c.loyalty_tier}
                            </span>
                          </td>
                          <td>
                            <div className="cust-ltv">₹{c.lifetime_value.toLocaleString()}</div>
                            <div className="cust-points">{c.loyalty_points} points</div>
                          </td>
                          <td>
                            <button className="cust-action-btn" onClick={e => { e.stopPropagation(); setSelectedCustomerId(c.id); }}>
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination controls */}
              {pagination.total_pages > 1 && (
                <div className="cust-pagination">
                  <div className="cust-pagination__info">
                    Showing {((pagination.page - 1) * pagination.per_page) + 1} to {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} records
                  </div>
                  <div className="cust-pagination__controls">
                    <button className="cust-page-btn" disabled={pagination.page === 1} onClick={() => setPagination(p => ({ ...p, page: p.page - 1 }))}>Prev</button>
                    {Array.from({ length: pagination.total_pages }).map((_, idx) => (
                      <button key={idx} className={`cust-page-btn ${pagination.page === idx + 1 ? 'cust-page-btn--active' : ''}`} onClick={() => setPagination(p => ({ ...p, page: idx + 1 }))}>
                        {idx + 1}
                      </button>
                    ))}
                    <button className="cust-page-btn" disabled={pagination.page === pagination.total_pages} onClick={() => setPagination(p => ({ ...p, page: p.page + 1 }))}>Next</button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Sub-Dashboards ── */}
        {activeTab === 'loyalty' && (
          <div className="cust-tab-content">
            <LoyaltyDashboard />
          </div>
        )}

        {activeTab === 'credit' && (
          <div className="cust-tab-content">
            <CreditManagement />
          </div>
        )}

        {/* ── Analytics Tab ── */}
        {activeTab === 'analytics' && (
          <div className="cust-analytics">
            <div className="cust-analytics__kpis">
              <div className="cust-kpi">
                <span className="cust-kpi__label">VIP Concentration</span>
                <div className="cust-kpi__value">12.5%</div>
              </div>
              <div className="cust-kpi">
                <span className="cust-kpi__label">LTV Growth Rate</span>
                <div className="cust-kpi__value" style={{ color: '#10B981' }}>+18.4%</div>
              </div>
              <div className="cust-kpi">
                <span className="cust-kpi__label">Credit Collection Rate</span>
                <div className="cust-kpi__value" style={{ color: '#10B981' }}>75%</div>
              </div>
              <div className="cust-kpi">
                <span className="cust-kpi__label">Loyalty Redeemed</span>
                <div className="cust-kpi__value">2.4K pts</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 20 }}>
              {/* Chart 1: growth trend */}
              <div className="cust-tab-content" style={{ minHeight: 320, display: 'flex', flexDirection: 'column' }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>Relationship Acquisition Trend</h3>
                <div style={{ flex: 1 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={ANALYTICS_TREND}>
                      <defs>
                        <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.01}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={11}/>
                      <YAxis stroke="var(--text-muted)" fontSize={11}/>
                      <Tooltip contentStyle={{ background: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}/>
                      <Area type="monotone" dataKey="count" stroke="#8B5CF6" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 2: segment distribution */}
              <div className="cust-tab-content" style={{ minHeight: 320, display: 'flex', flexDirection: 'column' }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>Segments</h3>
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={ANALYTICS_SEGMENTS} cx="50%" cy="50%" innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value">
                        {ANALYTICS_SEGMENTS.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ display: 'flex', gap: 10, justifyContent: 'center', fontSize: 11 }}>
                  {ANALYTICS_SEGMENTS.map((s, idx) => (
                    <span key={idx} style={{ color: s.color, fontWeight: 600 }}>● {s.name}</span>
                  ))}
                </div>
              </div>

              {/* Chart 3: tier distribution */}
              <div className="cust-tab-content" style={{ minHeight: 320, display: 'flex', flexDirection: 'column' }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>Tiers</h3>
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={ANALYTICS_TIERS} cx="50%" cy="50%" innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value">
                        {ANALYTICS_TIERS.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ display: 'flex', gap: 10, justifyContent: 'center', fontSize: 11 }}>
                  {ANALYTICS_TIERS.map((t, idx) => (
                    <span key={idx} style={{ color: t.color, fontWeight: 600 }}>● {t.name}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Add Customer Modal ── */}
      <AnimatePresence>
        {activeModal && (
          <AddCustomerModal
            onClose={() => setActiveModal(false)}
            onSave={(newCust) => {
              setCustomers(prev => [newCust, ...prev]);
              fetchStats();
            }}
          />
        )}
      </AnimatePresence>

      {/* ── Detail Sidebar Panel ── */}
      <AnimatePresence>
        {selectedCustomerId && (
          <CustomerDetailPanel
            customerId={selectedCustomerId}
            onClose={() => setSelectedCustomerId(null)}
            onRefreshList={fetchCustomersList}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
