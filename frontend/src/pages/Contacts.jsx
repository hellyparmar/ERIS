import React, { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Search,
  Building2,
  Phone,
  MapPin,
  Tag,
  Edit2,
  Trash2,
  Filter,
  CheckCircle2,
  XCircle,
  Truck,
  Users,
  Package,
  Layers,
  FileSpreadsheet
} from 'lucide-react';
import SEO from '../components/SEO';
import Modal from '../components/ui/Modal';
import api from '../lib/api';
import { useToast } from '../components/ui/Toast';

export default function Contacts() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);

  // Modal states
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedContact, setSelectedContact] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [contactToDelete, setContactToDelete] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    company_name: '',
    contact_person: '',
    phone: '',
    gst_number: '',
    address: '',
    city: '',
    contact_type: 'supplier',
    product_categories: ''
  });
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Query contacts
  const { data: contactsResponse, isLoading } = useQuery({
    queryKey: ['contacts', search, typeFilter, statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (search.trim()) params.append('search', search.trim());
      if (typeFilter !== 'all') params.append('contact_type', typeFilter);
      if (statusFilter !== 'all') params.append('is_active', statusFilter === 'active');
      params.append('page', page);
      params.append('per_page', '12');

      const res = await api.get(`/api/v1/contacts/?${params.toString()}`);
      return res.data;
    }
  });

  const contactsList = contactsResponse?.items || [];
  const totalCount = contactsResponse?.total || 0;
  const totalPages = contactsResponse?.total_pages || 1;

  // KPI counts
  const kpiStats = useMemo(() => {
    const total = totalCount;
    const suppliers = contactsList.filter(c => c.contact_type === 'supplier').length;
    const distributors = contactsList.filter(c => c.contact_type === 'distributor').length;
    const logistics = contactsList.filter(c => c.contact_type === 'logistics').length;
    return { total, suppliers, distributors, logistics };
  }, [contactsList, totalCount]);

  const openAddModal = () => {
    setFormData({
      company_name: '',
      contact_person: '',
      phone: '',
      gst_number: '',
      address: '',
      city: '',
      contact_type: 'supplier',
      product_categories: ''
    });
    setFormError('');
    setAddModalOpen(true);
  };

  const openEditModal = (contact) => {
    setSelectedContact(contact);
    setFormData({
      company_name: contact.company_name,
      contact_person: contact.contact_person,
      phone: contact.phone,
      gst_number: contact.gst_number || '',
      address: contact.address,
      city: contact.city,
      contact_type: contact.contact_type,
      product_categories: Array.isArray(contact.product_categories) ? contact.product_categories.join(', ') : ''
    });
    setFormError('');
    setEditModalOpen(true);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setIsSubmitting(true);
    try {
      const cats = formData.product_categories
        ? formData.product_categories.split(',').map(s => s.trim()).filter(Boolean)
        : [];

      const payload = {
        company_name: formData.company_name.trim(),
        contact_person: formData.contact_person.trim(),
        phone: formData.phone.trim(),
        gst_number: formData.gst_number.trim() || null,
        address: formData.address.trim(),
        city: formData.city.trim(),
        contact_type: formData.contact_type,
        product_categories: cats
      };

      await api.post('/api/v1/contacts/', payload);
      addToast('Business contact created successfully', 'success');
      setAddModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    } catch (err) {
      setFormError(err.response?.data?.detail || err.message || 'Failed to create contact');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!selectedContact) return;
    setFormError('');
    setIsSubmitting(true);
    try {
      const cats = formData.product_categories
        ? formData.product_categories.split(',').map(s => s.trim()).filter(Boolean)
        : [];

      const payload = {
        company_name: formData.company_name.trim(),
        contact_person: formData.contact_person.trim(),
        phone: formData.phone.trim(),
        gst_number: formData.gst_number.trim() || null,
        address: formData.address.trim(),
        city: formData.city.trim(),
        contact_type: formData.contact_type,
        product_categories: cats
      };

      await api.put(`/api/v1/contacts/${selectedContact.contact_id}`, payload);
      addToast('Contact updated successfully', 'success');
      setEditModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    } catch (err) {
      setFormError(err.response?.data?.detail || err.message || 'Failed to update contact');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!contactToDelete) return;
    try {
      await api.delete(`/api/v1/contacts/${contactToDelete.contact_id}`);
      addToast('Contact deactivated successfully', 'success');
      setDeleteModalOpen(false);
      setContactToDelete(null);
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to deactivate contact', 'error');
    }
  };

  const getTypeBadgeColor = (type) => {
    switch (type) {
      case 'supplier':
        return { bg: 'rgba(56, 161, 105, 0.12)', color: '#2F855A', border: 'rgba(56, 161, 105, 0.3)' };
      case 'distributor':
        return { bg: 'rgba(214, 158, 46, 0.12)', color: '#B7791F', border: 'rgba(214, 158, 46, 0.3)' };
      case 'logistics':
        return { bg: 'rgba(49, 130, 206, 0.12)', color: '#2B6CB0', border: 'rgba(49, 130, 206, 0.3)' };
      default:
        return { bg: 'rgba(113, 128, 150, 0.12)', color: '#4A5568', border: 'rgba(113, 128, 150, 0.3)' };
    }
  };

  return (
    <>
      <SEO title="Business Contacts" description="Directory of suppliers, distributors, and logistics partners" />
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
            <h1 className="page-title">Business Contacts</h1>
            <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>
              Directory of suppliers, distributors, logistics vendors, and commercial partners
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="action-btn primary" onClick={openAddModal}>
              <Plus size={13} style={{ marginRight: 6 }} />
              Add Contact
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* KPI Strip */}
          <div className="kpi-strip">
            <div className="kpi-cell">
              <div className="kpi-label">Total Contacts</div>
              <div className="kpi-value brown">{totalCount}</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Suppliers</div>
              <div className="kpi-value sage">{kpiStats.suppliers}</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Distributors</div>
              <div className="kpi-value">{kpiStats.distributors}</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Logistics Hubs</div>
              <div className="kpi-value" style={{ color: '#2B6CB0' }}>{kpiStats.logistics}</div>
            </div>
          </div>

          {/* Filters Bar */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 12,
            padding: '12px 16px',
            background: 'var(--c-card)',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--c-border)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 260 }}>
              <div style={{ position: 'relative', width: '100%', maxWidth: 320 }}>
                <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-muted)' }} />
                <input
                  type="text"
                  placeholder="Search company, contact, phone..."
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  style={{
                    paddingLeft: 30,
                    width: '100%',
                    height: 32,
                    fontSize: 12,
                    background: 'var(--c-canvas)',
                    border: '1px solid var(--c-border)',
                    borderRadius: 'var(--radius)'
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 11, color: 'var(--c-ink-muted)' }}>Type:</span>
                <select
                  value={typeFilter}
                  onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
                  style={{
                    height: 32,
                    fontSize: 12,
                    padding: '0 8px',
                    background: 'var(--c-canvas)',
                    border: '1px solid var(--c-border)',
                    borderRadius: 'var(--radius)'
                  }}
                >
                  <option value="all">All Types</option>
                  <option value="supplier">Suppliers</option>
                  <option value="distributor">Distributors</option>
                  <option value="logistics">Logistics</option>
                </select>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 11, color: 'var(--c-ink-muted)' }}>Status:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                  style={{
                    height: 32,
                    fontSize: 12,
                    padding: '0 8px',
                    background: 'var(--c-canvas)',
                    border: '1px solid var(--c-border)',
                    borderRadius: 'var(--radius)'
                  }}
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>
          </div>

          {/* Contacts Grid */}
          {isLoading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--c-ink-muted)', fontSize: 13 }}>
              Loading business contacts...
            </div>
          ) : contactsList.length === 0 ? (
            <div style={{
              padding: '60px 20px',
              textAlign: 'center',
              background: 'var(--c-card)',
              borderRadius: 'var(--radius)',
              border: '1px dashed var(--c-border)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12
            }}>
              <Building2 size={40} style={{ color: 'var(--c-border)', strokeWidth: 1.5 }} />
              <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--c-ink)' }}>No business contacts found</div>
              <p style={{ fontSize: 12, color: 'var(--c-ink-muted)', maxWidth: 360, margin: 0 }}>
                {search ? 'No contacts match your active search filters.' : 'Add suppliers, wholesale vendors, and logistics partners to keep your chain connected.'}
              </p>
              <button className="action-btn primary" onClick={openAddModal} style={{ marginTop: 8 }}>
                <Plus size={13} style={{ marginRight: 6 }} />
                Add Contact
              </button>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: 16
            }}>
              {contactsList.map((contact) => {
                const badgeStyle = getTypeBadgeColor(contact.contact_type);
                return (
                  <div
                    key={contact.contact_id}
                    style={{
                      background: 'var(--c-card)',
                      borderRadius: 'var(--radius)',
                      border: '1px solid var(--c-border)',
                      padding: 16,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 12,
                      transition: 'border-color 0.15s ease'
                    }}
                  >
                    {/* Card Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--c-ink)' }}>
                          {contact.company_name}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--c-ink-muted)', marginTop: 2 }}>
                          {contact.contact_person}
                        </div>
                      </div>
                      <div style={{
                        fontSize: 10,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                        padding: '3px 8px',
                        borderRadius: 12,
                        background: badgeStyle.bg,
                        color: badgeStyle.color,
                        border: `1px solid ${badgeStyle.border}`
                      }}>
                        {contact.contact_type}
                      </div>
                    </div>

                    {/* Contact Details */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 11, color: 'var(--c-ink)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Phone size={12} style={{ color: 'var(--c-ink-muted)' }} />
                        <span>{contact.phone}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                        <MapPin size={12} style={{ color: 'var(--c-ink-muted)', marginTop: 2, flexShrink: 0 }} />
                        <span>{contact.address}, {contact.city}</span>
                      </div>
                      {contact.gst_number && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--c-ink-muted)' }}>GSTIN:</span>
                          <span style={{ fontFamily: 'monospace', fontSize: 11, background: 'var(--c-canvas)', padding: '1px 6px', borderRadius: 4, border: '1px solid var(--c-border)' }}>
                            {contact.gst_number}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Product Categories */}
                    {contact.product_categories && contact.product_categories.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 2 }}>
                        {contact.product_categories.map((cat, idx) => (
                          <span
                            key={idx}
                            style={{
                              fontSize: 10,
                              background: 'var(--c-canvas)',
                              color: 'var(--c-ink-muted)',
                              padding: '2px 6px',
                              borderRadius: 4,
                              border: '1px solid var(--c-border)'
                            }}
                          >
                            {cat}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Card Footer */}
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingTop: 10,
                      borderTop: '1px solid var(--c-border)',
                      marginTop: 'auto'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                        {contact.is_active ? (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#2F855A' }}>
                            <CheckCircle2 size={12} /> Active
                          </span>
                        ) : (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#C53030' }}>
                            <XCircle size={12} /> Inactive
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          title="Edit contact"
                          onClick={() => openEditModal(contact)}
                          style={{
                            border: '1px solid var(--c-border)',
                            background: 'var(--c-canvas)',
                            borderRadius: 'var(--radius)',
                            padding: '4px 8px',
                            cursor: 'pointer',
                            color: 'var(--c-ink)'
                          }}
                        >
                          <Edit2 size={12} />
                        </button>
                        <button
                          title="Deactivate contact"
                          onClick={() => { setContactToDelete(contact); setDeleteModalOpen(true); }}
                          style={{
                            border: '1px solid var(--c-border)',
                            background: 'var(--c-canvas)',
                            borderRadius: 'var(--radius)',
                            padding: '4px 8px',
                            cursor: 'pointer',
                            color: '#C53030'
                          }}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Pagination Bar */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
              <button
                className="action-btn"
                disabled={page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <div style={{ display: 'flex', alignItems: 'center', padding: '0 8px', fontSize: 12, color: 'var(--c-ink-muted)' }}>
                Page {page} of {totalPages}
              </div>
              <button
                className="action-btn"
                disabled={page >= totalPages}
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Add Contact Modal */}
      <Modal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} title="Add Business Contact">
        <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {formError && (
            <div style={{ padding: '8px 12px', background: 'rgba(229, 62, 62, 0.1)', color: '#C53030', borderRadius: 'var(--radius)', fontSize: 12 }}>
              {formError}
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Company Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. AgroFresh Supplies Ltd"
              value={formData.company_name}
              onChange={e => setFormData({ ...formData, company_name: e.target.value })}
              style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Contact Person *</label>
              <input
                type="text"
                required
                placeholder="e.g. Vikram Desai"
                value={formData.contact_person}
                onChange={e => setFormData({ ...formData, contact_person: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Relationship Type *</label>
              <select
                value={formData.contact_type}
                onChange={e => setFormData({ ...formData, contact_type: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              >
                <option value="supplier">Supplier</option>
                <option value="distributor">Distributor</option>
                <option value="logistics">Logistics</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Phone *</label>
              <input
                type="text"
                required
                placeholder="e.g. +919876543210"
                value={formData.phone}
                onChange={e => setFormData({ ...formData, phone: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>City *</label>
              <input
                type="text"
                required
                placeholder="e.g. Mumbai"
                value={formData.city}
                onChange={e => setFormData({ ...formData, city: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>GSTIN (Optional)</label>
              <input
                type="text"
                maxLength={15}
                placeholder="e.g. 27AABCA1234A1Z5"
                value={formData.gst_number}
                onChange={e => setFormData({ ...formData, gst_number: e.target.value.toUpperCase() })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Product Categories</label>
              <input
                type="text"
                placeholder="e.g. Vegetables, Dairy, Spices"
                value={formData.product_categories}
                onChange={e => setFormData({ ...formData, product_categories: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Address *</label>
            <textarea
              required
              rows={3}
              placeholder="e.g. Plot 45, APMC Market Yard, Vashi"
              value={formData.address}
              onChange={e => setFormData({ ...formData, address: e.target.value })}
              style={{ width: '100%', padding: 10, fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
            <button type="button" className="action-btn" onClick={() => setAddModalOpen(false)}>Cancel</button>
            <button type="submit" className="action-btn primary" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Contact'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Contact Modal */}
      <Modal isOpen={editModalOpen} onClose={() => setEditModalOpen(false)} title="Edit Business Contact">
        <form onSubmit={handleEditSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {formError && (
            <div style={{ padding: '8px 12px', background: 'rgba(229, 62, 62, 0.1)', color: '#C53030', borderRadius: 'var(--radius)', fontSize: 12 }}>
              {formError}
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Company Name *</label>
            <input
              type="text"
              required
              value={formData.company_name}
              onChange={e => setFormData({ ...formData, company_name: e.target.value })}
              style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Contact Person *</label>
              <input
                type="text"
                required
                value={formData.contact_person}
                onChange={e => setFormData({ ...formData, contact_person: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Relationship Type *</label>
              <select
                value={formData.contact_type}
                onChange={e => setFormData({ ...formData, contact_type: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              >
                <option value="supplier">Supplier</option>
                <option value="distributor">Distributor</option>
                <option value="logistics">Logistics</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Phone *</label>
              <input
                type="text"
                required
                value={formData.phone}
                onChange={e => setFormData({ ...formData, phone: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>City *</label>
              <input
                type="text"
                required
                value={formData.city}
                onChange={e => setFormData({ ...formData, city: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>GSTIN</label>
              <input
                type="text"
                maxLength={15}
                value={formData.gst_number}
                onChange={e => setFormData({ ...formData, gst_number: e.target.value.toUpperCase() })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Product Categories</label>
              <input
                type="text"
                value={formData.product_categories}
                onChange={e => setFormData({ ...formData, product_categories: e.target.value })}
                style={{ width: '100%', height: 34, padding: '0 10px', fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--c-ink-muted)', marginBottom: 4 }}>Address *</label>
            <textarea
              required
              rows={3}
              value={formData.address}
              onChange={e => setFormData({ ...formData, address: e.target.value })}
              style={{ width: '100%', padding: 10, fontSize: 12, border: '1px solid var(--c-border)', borderRadius: 'var(--radius)', background: 'var(--c-canvas)', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
            <button type="button" className="action-btn" onClick={() => setEditModalOpen(false)}>Cancel</button>
            <button type="submit" className="action-btn primary" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={deleteModalOpen} onClose={() => setDeleteModalOpen(false)} title="Deactivate Contact">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <p style={{ fontSize: 13, color: 'var(--c-ink)', margin: 0 }}>
            Are you sure you want to deactivate <strong>{contactToDelete?.company_name}</strong>? It will no longer appear in active procurement and vendor listings.
          </p>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
            <button className="action-btn" onClick={() => setDeleteModalOpen(false)}>Cancel</button>
            <button
              className="action-btn"
              onClick={handleDeleteConfirm}
              style={{ background: '#C53030', color: '#FFF', borderColor: '#C53030' }}
            >
              Deactivate Contact
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
