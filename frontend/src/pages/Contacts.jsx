import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Plus, Eye, Edit2, Trash2, X } from 'lucide-react';
import axios from 'axios';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';

const API_BASE = 'http://localhost:8000/api/v1';

// Contact Type Badge
const ContactTypeBadge = ({ type }) => {
  const colors = {
    supplier: 'bg-blue-100 text-blue-800',
    distributor: 'bg-purple-100 text-purple-800',
    logistics: 'bg-orange-100 text-orange-800',
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[type?.toLowerCase()] || 'bg-gray-100 text-gray-800'}`}>
      {type}
    </span>
  );
};

// Category Chips
const CategoryChips = ({ categories }) => {
  if (!categories || categories.length === 0) return <span className="text-gray-400">—</span>;
  const displayed = categories.slice(0, 2);
  const remaining = categories.length - 2;
  return (
    <div className="flex gap-1 flex-wrap">
      {displayed.map((cat, i) => (
        <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
          {cat}
        </span>
      ))}
      {remaining > 0 && <span className="text-xs text-gray-500">+{remaining}</span>}
    </div>
  );
};

// View Contact Drawer
const ViewContactDrawer = ({ contact, onClose, invoices }) => {
  if (!contact) return null;

  const contactInvoices = invoices?.slice(0, 5) || [];

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-lg z-50 overflow-auto">
      <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
        <h2 className="text-lg font-bold">Contact Details</h2>
        <button onClick={onClose} className="hover:bg-gray-100 p-1 rounded">
          <X size={20} />
        </button>
      </div>

      <div className="p-6 space-y-6">
        {/* Contact Information */}
        <div>
          <h3 className="font-bold text-gray-900 mb-4">{contact.company_name}</h3>
          <div className="space-y-3 text-sm">
            <div>
              <label className="text-gray-500">Contact Person</label>
              <p className="text-gray-900">{contact.contact_person || '—'}</p>
            </div>
            <div>
              <label className="text-gray-500">Type</label>
              <p className="mt-1">
                <ContactTypeBadge type={contact.contact_type} />
              </p>
            </div>
            <div>
              <label className="text-gray-500">Phone</label>
              <p className="text-blue-600">
                <a href={`tel:${contact.phone}`}>{contact.phone || '—'}</a>
              </p>
            </div>
            <div>
              <label className="text-gray-500">Email</label>
              <p className="text-blue-600">
                <a href={`mailto:${contact.email}`}>{contact.email || '—'}</a>
              </p>
            </div>
            <div>
              <label className="text-gray-500">City</label>
              <p className="text-gray-900">{contact.city || '—'}</p>
            </div>
            <div>
              <label className="text-gray-500">GST Number</label>
              <p className="font-mono text-gray-900">{contact.gst_number || '—'}</p>
            </div>
            <div>
              <label className="text-gray-500">Categories</label>
              <div className="mt-2 flex flex-wrap gap-1">
                {contact.categories?.map((cat, i) => (
                  <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Invoice History */}
        <div className="border-t pt-4">
          <h4 className="font-bold text-gray-900 mb-3">Recent Invoices</h4>
          {contactInvoices.length === 0 ? (
            <p className="text-sm text-gray-500">No invoices</p>
          ) : (
            <div className="space-y-2">
              {contactInvoices.map((inv) => (
                <div key={inv.id} className="flex justify-between items-center text-sm p-2 bg-gray-50 rounded">
                  <div>
                    <p className="font-mono text-gray-900">{inv.invoice_number}</p>
                    <p className="text-gray-500">{new Date(inv.issue_date).toLocaleDateString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">₹{(inv.total || 0).toLocaleString('en-IN')}</p>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      inv.status === 'paid' ? 'bg-green-100 text-green-800' :
                      inv.status === 'pending' ? 'bg-amber-100 text-amber-800' :
                      'bg-red-100 text-red-800'
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
    <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-lg z-50 overflow-auto">
      <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
        <h2 className="text-lg font-bold">{contact ? 'Edit Contact' : 'Add Contact'}</h2>
        <button onClick={onClose} className="hover:bg-gray-100 p-1 rounded">
          <X size={20} />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Company Name *</label>
          <input
            type="text"
            value={formData.company_name || ''}
            onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Contact Person</label>
          <input
            type="text"
            value={formData.contact_person || ''}
            onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
          <select
            value={formData.contact_type || ''}
            onChange={(e) => setFormData({ ...formData, contact_type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            required
          >
            <option value="">Select Type</option>
            <option value="Supplier">Supplier</option>
            <option value="Distributor">Distributor</option>
            <option value="Logistics">Logistics</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input
            type="tel"
            value={formData.phone || ''}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            value={formData.email || ''}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
          <input
            type="text"
            value={formData.city || ''}
            onChange={(e) => setFormData({ ...formData, city: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">GST Number</label>
          <input
            type="text"
            value={formData.gst_number || ''}
            onChange={(e) => setFormData({ ...formData, gst_number: e.target.value?.toUpperCase() })}
            placeholder="15-character GST (e.g., 18AAPCT1234K1Z5)"
            className={`w-full px-3 py-2 border rounded-lg font-mono ${
              errors.gst_number ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.gst_number && <p className="text-red-600 text-xs mt-1">{errors.gst_number}</p>}
        </div>

        <div className="pt-4 flex gap-2 border-t">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
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
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-5xl space-y-3">
          <LoadingSkeleton variant="table-row" count={8} className="w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Contacts</h1>
        <p className="text-gray-500">Manage suppliers, distributors, and logistics partners</p>
      </div>

      {/* Controls */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-64 flex items-center gap-2 bg-white border border-gray-300 rounded-lg px-3 py-2">
          <Search size={18} className="text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, phone, email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 outline-none"
          />
        </div>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg bg-white"
        >
          <option value="All">All Types</option>
          <option value="Supplier">Supplier</option>
          <option value="Distributor">Distributor</option>
          <option value="Logistics">Logistics</option>
        </select>

        <button
          onClick={() => setEditingContact({})}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} />
          Add Contact
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto md:overflow-x-visible">
          <table className="w-full min-w-max">
          <thead className="bg-gray-50 border-b border-gray-200">
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
                  className="px-6 py-3 text-left text-xs font-bold text-gray-700 bg-gray-50 cursor-pointer hover:bg-gray-100"
                >
                  {col.label}
                  {sortConfig.key === col.key && (
                    <span className="ml-1">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 bg-gray-50">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(contact => (
              <tr key={contact.id} className="border-b border-gray-200 hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <p className="font-bold text-gray-900">{contact.company_name}</p>
                    <p className="text-sm text-gray-500">{contact.city}</p>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-900">{contact.contact_person || '—'}</td>
                <td className="px-6 py-4">
                  {contact.phone ? (
                    <a href={`tel:${contact.phone}`} className="text-blue-600 hover:underline">
                      {contact.phone}
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
                <td className="px-6 py-4">
                  {contact.email ? (
                    <a href={`mailto:${contact.email}`} className="text-blue-600 hover:underline">
                      {contact.email}
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
                <td className="px-6 py-4 font-mono text-sm text-gray-900">
                  {contact.gst_number || '—'}
                </td>
                <td className="px-6 py-4">
                  <ContactTypeBadge type={contact.contact_type} />
                </td>
                <td className="px-6 py-4">
                  <CategoryChips categories={contact.categories} />
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setViewingContact(contact)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                      title="View"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={() => setEditingContact(contact)}
                      className="p-2 text-amber-600 hover:bg-amber-50 rounded"
                      title="Edit"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Delete this contact?')) {
                          deleteContactMutation.mutate(contact.id);
                        }
                      }}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                      title="Delete"
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
