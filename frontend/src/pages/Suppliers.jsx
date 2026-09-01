import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Plus,
    Search,
    Star,
    FileText
} from 'lucide-react';
import SEO from '../components/SEO';
import Modal from '../components/ui/Modal';
import api from '../lib/api';
import { useToast } from '../components/ui/Toast';

const Suppliers = () => {

    const queryClient = useQueryClient();

    const { data: suppliersList, isLoading: isLoadingSuppliers } = useQuery({
        queryKey: ['suppliers'],
        queryFn: () => api.get('/api/v1/suppliers/').then(r => r.data?.data?.suppliers || r.data?.data?.items || r.data?.suppliers || r.data?.data || [])
    });
    const suppliers = Array.isArray(suppliersList) ? suppliersList : [];

    const { data: purchaseOrdersList, isLoading: isLoadingPOs } = useQuery({
        queryKey: ['purchase-orders'],
        queryFn: () => api.get('/api/v1/suppliers/purchase-orders/all').then(r => r.data?.data?.items || r.data?.data || r.data?.purchase_orders || r.data || [])
    });
    const purchaseOrders = Array.isArray(purchaseOrdersList) ? purchaseOrdersList : [];

    const renderStars = (rating) => {
        return Array.from({ length: 5 }, (_, i) => (
            <Star
                key={i}
                size={12}
                style={{ color: i < rating ? 'var(--c-brown)' : 'var(--c-border)', fill: i < rating ? 'var(--c-brown)' : 'transparent' }}
            />
        ));
    };

    const { addToast } = useToast();
    const [addModalOpen, setAddModalOpen] = useState(false);
    const [addForm, setAddForm] = useState({
        name: '', contact_name: '', phone: '', payment_terms: '', address: ''
    });
    const [addError, setAddError] = useState('');

    const handleAddSubmit = async (e) => {
        e.preventDefault();
        setAddError('');
        try {
            const res = await api.post('/api/v1/suppliers/', addForm);
            if (res.data?.success) {
                addToast('Supplier added successfully', 'success');
                setAddModalOpen(false);
                setAddForm({ name: '', contact_name: '', phone: '', payment_terms: '', address: '' });
                queryClient.invalidateQueries({ queryKey: ['suppliers'] });
            } else {
                setAddError(res.data?.error || 'Failed to add supplier');
            }
        } catch (err) {
            setAddError(err.response?.data?.detail || err.message || 'An error occurred');
        }
    };

    return (
        <>
            <SEO title="Suppliers Directory" description="Procurement orders, vendor metrics, and ratings" />
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
                        <h1 className="page-title" >Suppliers</h1>
                        <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>Manage supplier relationships and procurement</p>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button className="action-btn" onClick={() => {}}>
                            <FileText size={13} style={{ marginRight: 6 }} />
                            Create PO
                        </button>
                        <button className="action-btn primary" onClick={() => setAddModalOpen(true)}>
                            <Plus size={13} style={{ marginRight: 6 }} />
                            Add Supplier
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: 20 }}>
                    {/* KPI Strip */}
                    <div className="kpi-strip">
                        <div className="kpi-cell">
                            <div className="kpi-label">Active Suppliers</div>
                            <div className="kpi-value brown">{suppliers.length}</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Active POs</div>
                            <div className="kpi-value">{purchaseOrders.length}</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Total Spend</div>
                            <div className="kpi-value brown">₹26.6L</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Avg On-Time</div>
                            <div className="kpi-value sage">96.7%</div>
                        </div>
                    </div>

                    {/* Two column layout */}
                    <div className="two-col" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '22px' }}>
                        {/* Left column */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div className="zone-label" style={{ flex: 1 }}>Active Suppliers</div>
                                <div style={{ position: 'relative' }}>
                                    <Search size={12} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-muted)' }} />
                                    <input
                                        type="text"
                                        placeholder="Search..."
                                        style={{ paddingLeft: 28, width: 140, height: 28, fontSize: 11 }}
                                    />
                                </div>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                                {isLoadingSuppliers ? (
                                    <div style={{ padding: '14px 0', color: 'var(--c-ink-muted)', fontSize: '13px' }}>Loading suppliers...</div>
                                ) : suppliers.length === 0 ? (
                                    <div style={{ padding: '14px 0', color: 'var(--c-ink-muted)', fontSize: '13px' }}>No suppliers available.</div>
                                ) : (
                                    suppliers.map((supplier) => (
                                        <div key={supplier.id} className="feed-entry" style={{ display: 'flex', alignItems: 'flex-start', gap: 14, padding: '14px 0', borderBottom: '1px solid var(--c-border)' }}>
                                            {/* Left: name + stars + badge */}
                                            <div style={{ flex: 1, minWidth: 0 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                                    <span style={{ fontWeight: 700, color: '#1A1208', fontSize: 14 }}>{supplier.name}</span>
                                                    <div className={`badge ${supplier.is_active !== false ? 'active' : 'neutral'}`}>
                                                        {supplier.is_active !== false ? 'Active' : 'Inactive'}
                                                    </div>
                                                </div>
                                                <div style={{ display: 'flex', gap: 2, marginTop: 5 }}>{renderStars(supplier.rating ?? 5)}</div>
                                            </div>
                                            {/* Middle: terms + delivery */}
                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px', fontSize: 12, color: '#5C4F3D', minWidth: 180 }}>
                                                <div>
                                                    <span style={{ color: 'var(--c-ink-muted)', fontSize: 10, display: 'block' }}>Payment</span>
                                                    <span style={{ fontWeight: 600 }}>{supplier.payment_terms || 'N/A'}</span>
                                                </div>
                                                <div>
                                                    <span style={{ color: 'var(--c-ink-muted)', fontSize: 10, display: 'block' }}>On-Time</span>
                                                    <span style={{ fontWeight: 600, color: 'var(--c-sage)' }}>{supplier.on_time_delivery_rate != null ? Math.round(supplier.on_time_delivery_rate * 100) : 100}%</span>
                                                </div>
                                                <div>
                                                    <span style={{ color: 'var(--c-ink-muted)', fontSize: 10, display: 'block' }}>Active POs</span>
                                                    <span style={{ fontWeight: 600 }}>{supplier.active_orders ?? 0}</span>
                                                </div>
                                                <div>
                                                    <span style={{ color: 'var(--c-ink-muted)', fontSize: 10, display: 'block' }}>Total Spend</span>
                                                    <span style={{ fontWeight: 600, fontFamily: 'var(--f-mono)' }}>₹{((supplier.total_spend ?? 0) / 100000).toFixed(1)}L</span>
                                                </div>
                                            </div>
                                            {/* Right: actions */}
                                            <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                                                <button className="action-btn" style={{ padding: '4px 10px', fontSize: 11 }}>View</button>
                                                <button className="action-btn primary" style={{ padding: '4px 10px', fontSize: 11 }}>Create PO</button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Right column */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                            <div className="section-header" style={{ marginBottom: 0 }}>
                                <div className="zone-label" style={{ marginBottom: 0 }}>Recent Purchase Orders</div>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 0, marginTop: 12 }}>
                                {isLoadingPOs ? (
                                    <div style={{ padding: '12px 0', color: 'var(--c-ink-muted)', fontSize: '13px' }}>Loading purchase orders...</div>
                                ) : purchaseOrders.length === 0 ? (
                                    <div style={{ padding: '12px 0', color: 'var(--c-ink-muted)', fontSize: '13px' }}>No purchase orders yet.</div>
                                ) : (
                                    purchaseOrders.map((po) => {
                                        const statusClass = po.status === 'delivered' || po.status === 'confirmed' ? 'active' : 'warning';
                                        return (
                                            <div key={po.id} className="feed-entry" style={{ padding: '12px 0', borderBottom: '1px solid var(--c-border)' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <span style={{ fontWeight: 700, color: '#1A1208', fontSize: 13, fontFamily: 'var(--f-mono)' }}>{po.po_number || po.id}</span>
                                                    <div className={`badge ${statusClass}`}>
                                                        {po.status ? po.status.charAt(0).toUpperCase() + po.status.slice(1) : 'Unknown'}
                                                    </div>
                                                </div>
                                                <div style={{ fontSize: 12, color: '#5C4F3D', marginTop: 6, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                                                    <span>{po.supplier?.name || 'Unknown Supplier'}</span>
                                                    <span style={{ fontFamily: 'var(--f-mono)', color: 'var(--c-dark)', fontWeight: 600 }}>₹{(po.total_amount || 0).toLocaleString()}</span>
                                                    <span>{po.items?.length || 0} items</span>
                                                    <span>Due {po.expected_delivery_date ? new Date(po.expected_delivery_date).toLocaleDateString() : 'N/A'}</span>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                <Modal open={addModalOpen} onClose={() => setAddModalOpen(false)} title="Add Supplier">
                    <form onSubmit={handleAddSubmit}>
                        {addError && <div style={{ color: 'var(--c-critical)', marginBottom: 12, fontSize: 13 }}>{addError}</div>}
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                            <div>
                                <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Company Name *</label>
                                <input required value={addForm.name} onChange={e => setAddForm({ ...addForm, name: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Contact Name</label>
                                <input value={addForm.contact_name} onChange={e => setAddForm({ ...addForm, contact_name: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
                            </div>
                        </div>

                        <div style={{ marginBottom: 16 }}>
                            <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Phone</label>
                            <input value={addForm.phone} onChange={e => setAddForm({ ...addForm, phone: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} />
                        </div>

                        <div style={{ marginBottom: 16 }}>
                            <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Payment Terms</label>
                            <input value={addForm.payment_terms} onChange={e => setAddForm({ ...addForm, payment_terms: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} placeholder="e.g. Net 30" />
                        </div>

                        <div style={{ marginBottom: 24 }}>
                            <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>Address</label>
                            <textarea value={addForm.address} onChange={e => setAddForm({ ...addForm, address: e.target.value })} style={{ width: '100%', padding: '6px 12px' }} rows={3}></textarea>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                            <button type="button" onClick={() => setAddModalOpen(false)} className="action-btn">Cancel</button>
                            <button type="submit" className="action-btn primary">Add Supplier</button>
                        </div>
                    </form>
                </Modal>
            </div>
        </>
    );
};

export default Suppliers;
