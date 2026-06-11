import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Plus, Eye, Edit2, Trash2, X } from 'lucide-react';
import axios from 'axios';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import '../styles/fresh-design.css';

const API_BASE = 'http://localhost:8000/api/v1';

// Contact Type Badge
const ContactTypeBadge = ({ type }) => {
  const colors = {
    supplier: 'fresh-badge green',
    distributor: 'fresh-badge yellow',
    logistics: 'fresh-badge',
  };
  return (
    <span className={colors[type?.toLowerCase()] || 'fresh-badge'}>
      {type}
    </span>
  );
};

// Category Chips
const CategoryChips = ({ categories }) => {
  if (!categories || categories.length === 0) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
  const displayed = categories.slice(0, 2);
  const remaining = categories.length - 2;
  return (
    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
      {displayed.map((cat, i) => (
        <span key={i} className="fresh-badge" style={{ fontSize: 11 }}>
          {cat}
        </span>
      ))}
      {remaining > 0 && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>+{remaining}</span>}
    </div>
  );
};

// View Contact Drawer
const ViewContactDrawer = ({ contact, onClose, invoices }) => {
  if (!contact) return null;

  const contactInvoices = invoices?.slice(0, 5) || [];

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-sm z-50 overflow-auto">
      <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
        <h2 className="text-lg font-bold">Contact Details</h2>
        <button onClick={onClose} className="hover:bg-[var(--bg-muted)] p-1 rounded">
          <X size={20} />
        </button>
      </div>

      <div className="p-6 space-y-6">
        {/* Contact Information */}
        <div>
          <h3 className="font-bold text-[var(--text-primary)] mb-4">{contact.company_name}</h3>
          <div className="space-y-3 text-sm">
            <div>
              <label className="text-[var(--text-muted)]">Contact Person</label>
              <p className="text-[var(--text-primary)]">{contact.contact_person || '—'}</p>
            </div>
            <div>
              <label className="text-[var(--text-muted)]">Type</label>
              <p className="mt-1">
                <ContactTypeBadge type={contact.contact_type} />
              </p>
            </div>
            <div>
              <label className="text-[var(--text-muted)]">Phone</label>
              <p className="text-blue-600">
                <a href={`tel:${contact.phone}`}>{contact.phone || '—'}</a>
              </p>
            </div>
            <div>
              <label className="text-[var(--text-muted)]">Email</label>
              <p className="text-blue-600">
                <a href={`mailto:${contact.email}`}>{contact.email || '—'}</a>
              </p>
            </div>
            <div>
              <label className="text-[var(--text-muted)]">City</label>
              <p className="text-[var(--text-primary)]">{contact.city || '—'}</p>
            </div>
            <div>
              <label className="text-[var(--text-muted)]">GST Number</label>
              <p className="font-mono text-[var(--text-primary)]">{contact.gst_number || '—'}</p>
            </div>
            <div>
              <label className="text-[var(--text-muted)]">Categories</label>
              <div className="mt-2 flex flex-wrap gap-1">
                {contact.categories?.map((cat, i) => (
                  <span key={i} className="fresh-badge" style={{ fontSize: 11 }}>
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Invoice History */}
        <div className="border-t pt-4">
          <h4 className="font-bold text-[var(--text-primary)] mb-3">Recent Invoices</h4>
          {contactInvoices.length === 0 ? (
            <p className="text-sm text-[var(--text-muted)]">No invoices</p>
          ) : (
            <div className="fresh-list">
              {contactInvoices.map((inv) => (
                <div key={inv.id} className="fresh-list-item" style={{ justifyContent: 'space-between' }}>
                  <div>
                    <p className="font-mono" style={{ color: 'var(--text-primary)', fontSize: 13 }}>{inv.invoice_number}</p>
                    <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>{new Date(inv.issue_date).toLocaleDateString()}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontWeight: 600, fontSize: 13 }}>₹{(inv.total || 0).toLocaleString('en-IN')}</p>
                    <span className={`fresh-badge ${
                      inv.status === 'paid' ? 'green' :
                      inv.status === 'pending' ? 'yellow' :
                      'red'
                    }`}>
                      {inv.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Contact Form Drawer
const ContactFormDrawer = ({ contact, onClose, onSuccess }) => {
  const [formData, setFormData] = useState(contact || {});
  const [errors, setErrors] = useState({});
  const queryClient = useQueryClient();

  const validateGST = (gst) => /^[A-Z0-9]{15}$/.test(gst);

  const mutation = useMutation({
    mutationFn: async (data) => {
      if (contact?.id) {
        return axios.put(`${API_BASE}/contacts/${contact.id}`, data);
      } else {
        return axios.post(`${API_BASE}/contacts`, data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      onSuccess?.();
      onClose();
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};

    if (formData.gst_number && !validateGST(formData.gst_number)) {
      newErrors.gst_number = 'GST must be 15 alphanumeric characters';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    mutation.mutate(formData);
  };

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-sm z-50 overflow-auto">
      <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
        <h2 className="text-lg font-bold">{contact ? 'Edit Contact' : 'Add Contact'}</h2>
        <button onClick={onClose} className="hover:bg-[var(--bg-muted)] p-1 rounded">
          <X size={20} />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Company Name *</label>
          <input
            type="text"
            value={formData.company_name || ''}
            onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Contact Person</label>
          <input
            type="text"
            value={formData.contact_person || ''}
            onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
            className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Type *</label>
          <select
            value={formData.contact_type || ''}
            onChange={(e) => setFormData({ ...formData, contact_type: e.target.value })}
            className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg"
            required
          >
            <option value="">Select Type</option>
            <option value="Supplier">Supplier</option>
            <option value="Distributor">Distributor</option>
            <option value="Logistics">Logistics</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Phone</label>
          <input
            type="tel"
            value={formData.phone || ''}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">Email</label>
          <input
            type="email"
            value={formData.email || ''}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">City</label>
          <input
            type="text"
            value={formData.city || ''}
            onChange={(e) => setFormData({ ...formData, city: e.target.value })}
            className="w-full px-3 py-2 border border-[var(--border-color)] rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">GST Number</label>
          <input
            type="text"
            value={formData.gst_number || ''}
            onChange={(e) => setFormData({ ...formData, gst_number: e.target.value?.toUpperCase() })}
            placeholder="15-character GST (e.g., 18AAPCT1234K1Z5)"
            className={`w-full px-3 py-2 border rounded-lg font-mono ${
              errors.gst_number ? 'border-red-500' : 'border-[var(--border-color)]'
            }`}
          />
          {errors.gst_number && <p className="text-red-600 text-xs mt-1">{errors.gst_number}</p>}
        </div>

        <div className="pt-4 flex gap-2 border-t">
          <button
            type="button"
            onClick={onClose}
            className="fresh-btn"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="fresh-btn primary"
          >
            {mutation.isPending ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Main Contacts Page
export default function Contacts() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [viewingContact, setViewingContact] = useState(null);
  const [editingContact, setEditingContact] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'company_name', direction: 'asc' });

  const queryClient = useQueryClient();

  const { data: contacts = [], isLoading } = useQuery({
    queryKey: ['contacts'],
    queryFn: async () => {
      const res = await axios.get(`${API_BASE}/contacts`);
      return res.data;
    },
  });

  const { data: invoices = [] } = useQuery({
    queryKey: ['invoices'],
    queryFn: async () => {
      const res = await axios.get(`${API_BASE}/invoices`);
      return res.data;
    },
  });

  const deleteContactMutation = useMutation({
    mutationFn: (id) => axios.delete(`${API_BASE}/contacts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    },
  });

  // Filter and sort
  const filtered = useMemo(() => {
    return contacts
      .filter(c => {
        const matchSearch = !searchTerm ||
          c.company_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.contact_person?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.phone?.includes(searchTerm) ||
          c.email?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchType = typeFilter === 'All' || c.contact_type === typeFilter;

        return matchSearch && matchType;
      })
      .sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
  }, [contacts, searchTerm, typeFilter, sortConfig]);

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-muted)] p-6">
        <div className="w-full max-w-5xl space-y-3">
          <LoadingSkeleton variant="table-row" count={8} className="w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="fresh-page">
      <div style={{ marginBottom: 32 }}>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Business contacts and vendor directory</p>
      </div>

      {/* Controls + Table */}
      <div className="fresh-section">
        <div className="fresh-section-header">
          <span className="fresh-section-title">All Contacts</span>
          <button
            onClick={() => setEditingContact({})}
            className="fresh-btn primary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Plus size={18} />
            Add Contact
          </button>
        </div>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
          <div style={{ flex: 1, minWidth: 240, display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', border: '1px solid var(--border-color)', borderRadius: 8 }}>
            <Search size={18} style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search by name, phone, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ flex: 1, outline: 'none', border: 'none', background: 'transparent', fontSize: 13 }}
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{ padding: '6px 12px', border: '1px solid var(--border-color)', borderRadius: 8, background: 'transparent', fontSize: 13, cursor: 'pointer' }}
          >
            <option value="All">All Types</option>
            <option value="Supplier">Supplier</option>
            <option value="Distributor">Distributor</option>
            <option value="Logistics">Logistics</option>
          </select>
        </div>

        <table className="fresh-table">
          <thead>
            <tr>
              {[
                { key: 'company_name', label: 'Company' },
                { key: 'contact_person', label: 'Contact Person' },
                { key: 'phone', label: 'Phone' },
                { key: 'email', label: 'Email' },
                { key: 'gst_number', label: 'GST Number' },
                { key: 'contact_type', label: 'Type' },
                { key: 'categories', label: 'Categories' },
              ].map(col => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  style={{ cursor: 'pointer' }}
                >
                  {col.label}
                  {sortConfig.key === col.key && (
                    <span style={{ marginLeft: 4 }}>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(contact => (
              <tr key={contact.id}>
                <td>
                  <div>
                    <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{contact.company_name}</p>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{contact.city}</p>
                  </div>
                </td>
                <td style={{ color: 'var(--text-primary)' }}>{contact.contact_person || '—'}</td>
                <td>
                  {contact.phone ? (
                    <a href={`tel:${contact.phone}`} style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                      {contact.phone}
                    </a>
                  ) : '—'}
                </td>
                <td>
                  {contact.email ? (
                    <a href={`mailto:${contact.email}`} style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                      {contact.email}
                    </a>
                  ) : '—'}
                </td>
                <td style={{ fontFamily: 'monospace', fontSize: 13, color: 'var(--text-primary)' }}>
                  {contact.gst_number || '—'}
                </td>
                <td>
                  <ContactTypeBadge type={contact.contact_type} />
                </td>
                <td>
                  <CategoryChips categories={contact.categories} />
                </td>
                <td>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button
                      onClick={() => setViewingContact(contact)}
                      className="fresh-btn"
                      title="View"
                      style={{ padding: '4px 8px' }}
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={() => setEditingContact(contact)}
                      className="fresh-btn"
                      title="Edit"
                      style={{ padding: '4px 8px' }}
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Delete this contact?')) {
                          deleteContactMutation.mutate(contact.id);
                        }
                      }}
                      className="fresh-btn"
                      title="Delete"
                      style={{ padding: '4px 8px', color: 'var(--error)' }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Drawers */}
      {viewingContact && (
        <ViewContactDrawer
          contact={viewingContact}
          onClose={() => setViewingContact(null)}
          invoices={invoices.filter(inv => inv.supplier_id === viewingContact.id)}
        />
      )}

      {editingContact && (
        <ContactFormDrawer
          contact={editingContact.id ? editingContact : null}
          onClose={() => setEditingContact(null)}
          onSuccess={() => setEditingContact(null)}
        />
      )}
    </div>
  );
}
