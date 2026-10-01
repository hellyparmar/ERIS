import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Search, UserPlus, X } from 'lucide-react';

import SEO from '../components/SEO';
import Modal from '../components/ui/Modal';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';

const money = (value) => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
}).format(Number(value) || 0);
const errorText = (error, fallback) => error?.response?.data?.detail || error?.message || fallback;

export default function Customers() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ name: '', phone: '', email: '', address: '' });
  const [formError, setFormError] = useState('');
  const canEdit = ['admin', 'manager'].includes(user?.role);

  const statsQuery = useQuery({
    queryKey: ['customer-stats'],
    queryFn: () => api.get('/api/v1/customers/stats').then((response) => response.data.data),
  });
  const customersQuery = useQuery({
    queryKey: ['customers', page, search, segment],
    queryFn: () => api.get('/api/v1/customers', {
      params: { page, per_page: 10, search: search || undefined, segment: segment || undefined },
    }).then((response) => response.data.data),
  });
  const detailQuery = useQuery({
    queryKey: ['customer', selectedId],
    queryFn: () => api.get(`/api/v1/customers/${selectedId}`).then((response) => response.data.data),
    enabled: selectedId != null,
  });
  const createMutation = useMutation({
    mutationFn: (payload) => api.post('/api/v1/customers/', payload),
    onSuccess: async () => {
      setCreateOpen(false);
      setForm({ name: '', phone: '', email: '', address: '' });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['customers'] }),
        queryClient.invalidateQueries({ queryKey: ['customer-stats'] }),
      ]);
    },
    onError: (error) => setFormError(errorText(error, 'Unable to create customer.')),
  });

  const rows = customersQuery.data?.customers || [];
  const stats = statsQuery.data;
  const submitCustomer = (event) => {
    event.preventDefault();
    setFormError('');
    createMutation.mutate({
      name: form.name.trim(), phone: form.phone.trim(),
      email: form.email.trim() || null, address: form.address.trim() || null,
    });
  };

  return (
    <>
      <SEO title="Customers" description="Customer profiles and measured lifetime value" />
      <div style={{ minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
        <div style={{ padding: '16px 22px', display: 'flex', justifyContent: 'space-between', alignItems: 'end', borderBottom: '1px solid var(--c-border)' }}>
          <div><h1 className="page-title">Customers</h1><p style={{ fontSize: 11, color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>Profiles and purchase value from recorded sales</p></div>
          {canEdit && <button className="action-btn primary" onClick={() => setCreateOpen(true)}><UserPlus size={14} /> Add customer</button>}
        </div>
        <div style={{ padding: 22, display: 'grid', gap: 20 }}>
          {stats && <div className="kpi-strip">
            <div className="kpi-cell"><div className="kpi-label">Customers</div><div className="kpi-value brown">{stats.total_customers}</div></div>
            <div className="kpi-cell"><div className="kpi-label">VIP</div><div className="kpi-value sage">{stats.vip_customers}</div></div>
            <div className="kpi-cell"><div className="kpi-label">Lifetime value</div><div className="kpi-value brown">{money(stats.total_lifetime_value)}</div></div>
            <div className="kpi-cell"><div className="kpi-label">Average value</div><div className="kpi-value">{money(stats.average_lifetime_value)}</div></div>
          </div>}
          <div className="filter-bar" style={{ display: 'flex', gap: 10 }}>
            <label style={{ position: 'relative', flex: 1, maxWidth: 320 }}><Search size={14} style={{ position: 'absolute', left: 10, top: 10 }} /><input aria-label="Search customers" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search name, phone, or email" style={{ paddingLeft: 32, width: '100%' }} /></label>
            <select aria-label="Customer segment" value={segment} onChange={(event) => { setSegment(event.target.value); setPage(1); }}><option value="">All segments</option><option value="VIP">VIP</option><option value="Regular">Regular</option><option value="New">New</option></select>
          </div>
          {customersQuery.isError && <div className="error-state">{errorText(customersQuery.error, 'Unable to load customers.')}</div>}
          <div style={{ overflowX: 'auto' }}><table className="eris-table" style={{ width: '100%' }}>
            <thead><tr><th>Name</th><th>Phone</th><th>Segment</th><th style={{ textAlign: 'right' }}>Lifetime value</th><th style={{ textAlign: 'right' }}>Orders</th></tr></thead>
            <tbody>
              {customersQuery.isLoading && <tr><td colSpan="5">Loading customers…</td></tr>}
              {!customersQuery.isLoading && rows.length === 0 && <tr><td colSpan="5">No customers match these filters.</td></tr>}
              {rows.map((customer) => <tr key={customer.id} onClick={() => setSelectedId(customer.id)} style={{ cursor: 'pointer' }}><td>{customer.name}</td><td>{customer.phone || '—'}</td><td><span className="badge neutral">{customer.segment}</span></td><td className="mono" style={{ textAlign: 'right' }}>{money(customer.lifetime_value)}</td><td className="mono" style={{ textAlign: 'right' }}>{customer.total_purchases || 0}</td></tr>)}
            </tbody>
          </table></div>
          {(customersQuery.data?.total_pages || 0) > 1 && <div style={{ display: 'flex', justifyContent: 'center', gap: 8, alignItems: 'center' }}><button className="action-btn" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</button><span>{page} / {customersQuery.data.total_pages}</span><button className="action-btn" disabled={page >= customersQuery.data.total_pages} onClick={() => setPage((value) => value + 1)}>Next</button></div>}
        </div>
      </div>
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Add customer">
        <form onSubmit={submitCustomer} style={{ display: 'grid', gap: 12 }}>
          {formError && <div className="error-state">{formError}</div>}
          <label>Name *<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
          <label>Phone *<input required minLength="10" maxLength="15" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label>
          <label>Email<input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>
          <label>Address<input value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} /></label>
          <div style={{ display: 'flex', justifyContent: 'end', gap: 8 }}><button type="button" className="action-btn" onClick={() => setCreateOpen(false)}>Cancel</button><button className="action-btn primary" disabled={createMutation.isPending}>Create</button></div>
        </form>
      </Modal>
      {selectedId && <div onClick={() => setSelectedId(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.45)', zIndex: 900 }}><aside onClick={(event) => event.stopPropagation()} style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: 'min(440px, 100%)', background: 'var(--c-canvas)', padding: 22 }}><button aria-label="Close details" onClick={() => setSelectedId(null)} style={{ float: 'right', border: 0, background: 'none' }}><X size={18} /></button>{detailQuery.isLoading ? <p>Loading profile…</p> : detailQuery.isError ? <p>{errorText(detailQuery.error, 'Unable to load customer.')}</p> : <><h2>{detailQuery.data?.name}</h2><span className="badge neutral">{detailQuery.data?.segment}</span><p>{detailQuery.data?.phone || 'No phone'}<br />{detailQuery.data?.address || 'No address'}</p><div className="kpi-strip" style={{ gridTemplateColumns: '1fr 1fr' }}><div className="kpi-cell"><div className="kpi-label">Lifetime value</div><div className="kpi-value">{money(detailQuery.data?.lifetime_value)}</div></div><div className="kpi-cell"><div className="kpi-label">Orders</div><div className="kpi-value">{detailQuery.data?.total_purchases || 0}</div></div></div></>}</aside></div>}
    </>
  );
}
