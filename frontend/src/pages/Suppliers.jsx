import React, { useState } from 'react';
import {
    Plus,
    Search,
    Star,
    FileText
} from 'lucide-react';
import '../styles/fresh-design.css';

const Suppliers = () => {

    const suppliers = [
        { id: 1, name: 'TechSupply Co.', rating: 5, contact: 'contact@techsupply.com', phone: '+91 98765 43210', address: 'Mumbai, Maharashtra', paymentTerms: 'Net 30', onTimeDelivery: 98, activeOrders: 3, totalOrders: 145, totalSpend: 1250000 },
        { id: 2, name: 'Global Electronics', rating: 4, contact: 'sales@globalelec.com', phone: '+91 98765 43211', address: 'Delhi, NCR', paymentTerms: 'Net 45', onTimeDelivery: 95, activeOrders: 2, totalOrders: 98, totalSpend: 850000 },
        { id: 3, name: 'Premium Gadgets Ltd', rating: 4.5, contact: 'info@premiumgadgets.com', phone: '+91 98765 43212', address: 'Bangalore, Karnataka', paymentTerms: 'Net 30', onTimeDelivery: 97, activeOrders: 1, totalOrders: 67, totalSpend: 560000 }
    ];

    const purchaseOrders = [
        { id: 'PO-001', supplier: 'TechSupply Co.', items: 5, amount: 125000, status: 'pending', date: '2026-02-01', deliveryDate: '2026-02-10' },
        { id: 'PO-002', supplier: 'Global Electronics', items: 3, amount: 85000, status: 'delivered', date: '2026-01-25', deliveryDate: '2026-02-05' },
        { id: 'PO-003', supplier: 'Premium Gadgets Ltd', items: 8, amount: 156000, status: 'confirmed', date: '2026-01-30', deliveryDate: '2026-02-08' }
    ];

    const renderStars = (rating) => {
        return Array.from({ length: 5 }, (_, i) => (
            <Star
                key={i}
                className={`w-4 h-4 ${i < rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}`}
            />
        ));
    };

    return (
        <div className="fresh-page">
            {/* Header */}
            <div style={{ marginBottom: 32 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button className="fresh-btn" onClick={() => {}}>
                            <FileText size={14} />
                            Create PO
                        </button>
                        <button className="fresh-btn primary" onClick={() => {}}>
                            <Plus size={14} />
                            Add Supplier
                        </button>
                    </div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                    Manage supplier relationships and procurement
                </p>
            </div>

            {/* Stats */}
            <div className="fresh-metrics">
                <div className="fresh-metric">
                    <div className="fresh-metric-value">{suppliers.length}</div>
                    <div className="fresh-metric-label">Active Suppliers</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">6</div>
                    <div className="fresh-metric-label">Active POs</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">₹26.6L</div>
                    <div className="fresh-metric-label">Total Spend</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">96.7%</div>
                    <div className="fresh-metric-label">Avg On-Time</div>
                </div>
            </div>

            <div className="fresh-split">
                {/* Suppliers List */}
                <div className="fresh-section">
                    <div className="fresh-section-header">
                        <span className="fresh-section-title">Active Suppliers</span>
                        <div style={{ position: 'relative' }}>
                            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                type="text"
                                placeholder="Search..."
                                style={{ paddingLeft: 30, paddingRight: 12, paddingTop: 6, paddingBottom: 6, borderRadius: 6, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-primary)', fontSize: 13, outline: 'none', width: 180 }}
                            />
                        </div>
                    </div>

                    <div className="fresh-list">
                        {suppliers.map((supplier) => (
                            <div key={supplier.id} className="fresh-list-item" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 12 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div>
                                        <div style={{ fontWeight: 600, marginBottom: 4 }}>{supplier.name}</div>
                                        <div style={{ display: 'flex', gap: 1 }}>{renderStars(supplier.rating)}</div>
                                    </div>
                                    <span className="fresh-badge green">Active</span>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12 }}>
                                    <div>
                                        <div style={{ color: 'var(--text-muted)' }}>Payment Terms</div>
                                        <div style={{ fontWeight: 500 }}>{supplier.paymentTerms}</div>
                                    </div>
                                    <div>
                                        <div style={{ color: 'var(--text-muted)' }}>On-Time Delivery</div>
                                        <div style={{ fontWeight: 500, color: 'var(--success)' }}>{supplier.onTimeDelivery}%</div>
                                    </div>
                                    <div>
                                        <div style={{ color: 'var(--text-muted)' }}>Active Orders</div>
                                        <div style={{ fontWeight: 500 }}>{supplier.activeOrders}</div>
                                    </div>
                                    <div>
                                        <div style={{ color: 'var(--text-muted)' }}>Total Spend</div>
                                        <div style={{ fontWeight: 500 }}>₹{(supplier.totalSpend / 100000).toFixed(1)}L</div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: 8 }}>
                                    <button className="fresh-btn" style={{ flex: 1, fontSize: 12 }}>
                                        View Details
                                    </button>
                                    <button className="fresh-btn primary" style={{ flex: 1, fontSize: 12 }}>
                                        Create PO
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Purchase Orders */}
                <div className="fresh-section">
                    <div className="fresh-section-header">
                        <span className="fresh-section-title">Recent Purchase Orders</span>
                    </div>
                    <div className="fresh-list">
                        {purchaseOrders.map((po) => {
                            const badgeClass = po.status === 'delivered' ? 'green' : po.status === 'confirmed' ? 'green' : 'yellow';
                            return (
                                <div key={po.id} className="fresh-list-item" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 12 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                        <div>
                                            <div style={{ fontWeight: 600 }}>{po.id}</div>
                                            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{po.supplier}</div>
                                        </div>
                                        <span className={`fresh-badge ${badgeClass}`}>
                                            {po.status.charAt(0).toUpperCase() + po.status.slice(1)}
                                        </span>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12 }}>
                                        <div>
                                            <div style={{ color: 'var(--text-muted)' }}>Items</div>
                                            <div style={{ fontWeight: 500 }}>{po.items}</div>
                                        </div>
                                        <div>
                                            <div style={{ color: 'var(--text-muted)' }}>Amount</div>
                                            <div style={{ fontWeight: 500 }}>₹{po.amount.toLocaleString()}</div>
                                        </div>
                                        <div>
                                            <div style={{ color: 'var(--text-muted)' }}>Order Date</div>
                                            <div style={{ fontWeight: 500 }}>{po.date}</div>
                                        </div>
                                        <div>
                                            <div style={{ color: 'var(--text-muted)' }}>Delivery Date</div>
                                            <div style={{ fontWeight: 500 }}>{po.deliveryDate}</div>
                                        </div>
                                    </div>
                                    <button className="fresh-btn" style={{ width: '100%', fontSize: 12 }}>
                                        View PO Details
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Suppliers;
