import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Truck } from 'lucide-react';

import SEO from '../components/SEO';
import Modal from '../components/ui/Modal';
import { api } from '../lib/api';

const emptyForm = { name: '', contact_person: '', phone: '', gst_number: '', city: '', state: '', address: '', payment_terms_days: 30 };
const errorText = (error) => error?.response?.data?.detail || error?.message || 'Unable to save supplier.';

export default function Suppliers() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState('');
  const suppliersQuery = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => api.get('/api/v1/suppliers/').then((response) => response.data.items || []),
  });
  const createMutation = useMutation({
    mutationFn: (payload) => api.post('/api/v1/suppliers/', payload),
    onSuccess: async () => {
      setOpen(false);
      setForm(emptyForm);
      await queryClient.invalidateQueries({ queryKey: ['suppliers'] });
    },
    onError: (requestError) => setError(errorText(requestError)),
  });
  const submit = (event) => {
    event.preventDefault();
    setError('');
    createMutation.mutate(Object.fromEntries(Object.entries(form).map(([key, value]) => [key, typeof value === 'string' && !value.trim() ? null : value])));
  };

  return <>
    <SEO title="Suppliers" description="Organization supplier directory" />
    <div style={{ minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
      <div style={{ padding: '16px 22px', display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--c-border)' }}><div><h1 className="page-title">Suppliers</h1><p style={{ margin: 0, fontSize: 11, color: 'var(--c-ink-muted)' }}>Vendor directory for inventory sourcing</p></div><button className="action-btn primary" onClick={() => setOpen(true)}><Plus size={14} /> Add supplier</button></div>
      <div style={{ padding: 22 }}>
        {suppliersQuery.isError && <div className="error-state">Unable to load suppliers.</div>}
        <div style={{ overflowX: 'auto' }}><table className="eris-table" style={{ width: '100%' }}><thead><tr><th>Supplier</th><th>Contact</th><th>Location</th><th>GSTIN</th><th>Terms</th></tr></thead><tbody>
          {suppliersQuery.isLoading && <tr><td colSpan="5">Loading suppliers…</td></tr>}
          {!suppliersQuery.isLoading && !suppliersQuery.data?.length && <tr><td colSpan="5">No active suppliers.</td></tr>}
          {suppliersQuery.data?.map((supplier) => <tr key={supplier.id}><td><Truck size={14} /> {supplier.name}</td><td>{supplier.contact_person || '—'}<br />{supplier.phone || ''}</td><td>{[supplier.city, supplier.state].filter(Boolean).join(', ') || '—'}</td><td className="mono">{supplier.gst_number || '—'}</td><td>{supplier.payment_terms_days} days</td></tr>)}
        </tbody></table></div>
      </div>
    </div>
    <Modal open={open} onClose={() => setOpen(false)} title="Add supplier"><form onSubmit={submit} style={{ display: 'grid', gap: 10 }}>
      {error && <div className="error-state">{error}</div>}
      <label>Name *<input required minLength="2" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
      <label>Contact person<input value={form.contact_person} onChange={(event) => setForm({ ...form, contact_person: event.target.value })} /></label>
      <label>Phone<input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label>
      <label>GSTIN<input maxLength="20" value={form.gst_number} onChange={(event) => setForm({ ...form, gst_number: event.target.value.toUpperCase() })} /></label>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}><label>City<input value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} /></label><label>State<input value={form.state} onChange={(event) => setForm({ ...form, state: event.target.value })} /></label></div>
      <label>Address<input value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} /></label>
      <label>Payment terms (days)<input type="number" min="0" max="365" value={form.payment_terms_days} onChange={(event) => setForm({ ...form, payment_terms_days: Number(event.target.value) })} /></label>
      <div style={{ display: 'flex', justifyContent: 'end', gap: 8 }}><button type="button" className="action-btn" onClick={() => setOpen(false)}>Cancel</button><button className="action-btn primary" disabled={createMutation.isPending}>Create</button></div>
    </form></Modal>
  </>;
}
