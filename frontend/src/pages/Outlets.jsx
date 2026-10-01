import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Building2, MapPin, Phone, Plus, Search } from 'lucide-react';

import SEO from '../components/SEO';
import Modal from '../components/ui/Modal';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';
import '../styles/outlets.css';

const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value) || 0);
const errorText = (error, fallback) => error?.response?.data?.detail || error?.message || fallback;

export default function Outlets() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ name: '', city: '', address: '', phone: '' });
  const [formError, setFormError] = useState('');
  const isAdmin = user?.role === 'admin';

  const outletsQuery = useQuery({ queryKey: ['outlets'], queryFn: () => api.get('/api/v1/outlets').then((response) => response.data) });
  const detailQuery = useQuery({
    queryKey: ['outlet', selectedId],
    queryFn: () => api.get(`/api/v1/outlets/${selectedId}`).then((response) => response.data),
    enabled: selectedId != null,
  });
  const createMutation = useMutation({
    mutationFn: (payload) => api.post('/api/v1/outlets/', null, { params: payload }),
    onSuccess: async () => {
      setCreateOpen(false);
      setForm({ name: '', city: '', address: '', phone: '' });
      await queryClient.invalidateQueries({ queryKey: ['outlets'] });
    },
    onError: (error) => setFormError(errorText(error, 'Unable to create outlet.')),
  });
  const deactivateMutation = useMutation({
    mutationFn: (id) => api.delete(`/api/v1/outlets/${id}`),
    onSuccess: async () => {
      setSelectedId(null);
      await queryClient.invalidateQueries({ queryKey: ['outlets'] });
    },
  });

  const rows = useMemo(() => (outletsQuery.data || []).filter((outlet) => {
    const needle = search.trim().toLowerCase();
    return !needle || [outlet.name, outlet.city, outlet.address, outlet.phone].some((value) => String(value || '').toLowerCase().includes(needle));
  }), [outletsQuery.data, search]);

  const submit = (event) => {
    event.preventDefault();
    setFormError('');
    createMutation.mutate({ ...form, phone: form.phone || undefined });
  };

  return <>
    <SEO title="Outlets" description="Manage the organization's retail outlets" />
    <div className="outlets-container">
      <div className="outlets-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div><h1 className="page-title">Outlets</h1><p style={{ margin: 0, color: 'var(--c-ink-muted)', fontSize: 12 }}>One organization, {outletsQuery.data?.length || 0} active locations</p></div>
        {isAdmin && <button className="btn-add-outlet" onClick={() => setCreateOpen(true)}><Plus size={18} /> Add outlet</button>}
      </div>
      <div className="filter-search" style={{ maxWidth: 380, marginBottom: 20 }}><Search size={18} className="filter-search-icon" /><input className="filter-input" aria-label="Search outlets" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name, city, address, or phone" /></div>
      {outletsQuery.isError && <div className="error-state">{errorText(outletsQuery.error, 'Unable to load outlets.')}</div>}
      <div className="outlets-grid">
        {rows.map((outlet) => <button key={outlet.id} className="outlet-card" onClick={() => setSelectedId(outlet.id)} style={{ textAlign: 'left' }}>
          <div className="outlet-card-header"><div className="outlet-info-header"><Building2 size={18} /><h3 className="outlet-name">{outlet.name}</h3></div><span className={`badge ${outlet.is_active ? 'active' : 'neutral'}`}>{outlet.is_active ? 'Active' : 'Inactive'}</span></div>
          <div className="outlet-location"><MapPin size={16} /><div><div>{outlet.address || 'Address not provided'}</div><div className="location-city">{outlet.city || 'City not provided'}</div></div></div>
          <div className="outlet-contacts"><div className="contact-item"><Phone size={14} />{outlet.phone || 'Phone not provided'}</div></div>
        </button>)}
      </div>
      {!outletsQuery.isLoading && rows.length === 0 && <div className="outlets-empty"><MapPin size={40} /><p>No outlets match this search.</p></div>}
    </div>

    <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Add outlet">
      <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
        {formError && <div className="error-state">{formError}</div>}
        <label>Name *<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>City *<input required value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} /></label>
        <label>Address *<input required value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} /></label>
        <label>Phone<input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label>
        <div style={{ display: 'flex', justifyContent: 'end', gap: 8 }}><button type="button" className="action-btn" onClick={() => setCreateOpen(false)}>Cancel</button><button className="action-btn primary" disabled={createMutation.isPending}>Create</button></div>
      </form>
    </Modal>

    <Modal open={selectedId != null} onClose={() => setSelectedId(null)} title={detailQuery.data?.name || 'Outlet details'}>
      {detailQuery.isLoading ? <p>Loading outlet…</p> : detailQuery.isError ? <div className="error-state">{errorText(detailQuery.error, 'Unable to load outlet.')}</div> : detailQuery.data && <div style={{ display: 'grid', gap: 16 }}>
        <p><MapPin size={14} /> {detailQuery.data.address || 'Address not provided'}, {detailQuery.data.city || ''}<br /><Phone size={14} /> {detailQuery.data.phone || 'Phone not provided'}</p>
        <div className="kpi-strip" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}><div className="kpi-cell"><div className="kpi-label">Month revenue</div><div className="kpi-value">{money(detailQuery.data.performance?.revenue_this_month)}</div></div><div className="kpi-cell"><div className="kpi-label">Active alerts</div><div className="kpi-value">{detailQuery.data.performance?.active_alerts || 0}</div></div><div className="kpi-cell"><div className="kpi-label">Top product</div><div style={{ fontWeight: 600 }}>{detailQuery.data.performance?.top_product || 'No sales yet'}</div></div></div>
        {isAdmin && <button className="action-btn" disabled={deactivateMutation.isPending} onClick={() => { if (window.confirm('Deactivate this outlet?')) deactivateMutation.mutate(selectedId); }}>Deactivate outlet</button>}
      </div>}
    </Modal>
  </>;
}
