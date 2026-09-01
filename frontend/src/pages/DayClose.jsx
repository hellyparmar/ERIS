import React, { useState, useEffect } from 'react';
import { Calendar, DollarSign, TrendingUp, AlertTriangle, CheckCircle, Clock, RefreshCw, Unlock, Lock } from 'lucide-react';
import api from '../lib/api';
import { useToast } from '../contexts/ToastContext';
import ComplianceStatusChip from '../components/patterns/ComplianceStatusChip';
import InkStamp from '../components/patterns/InkStamp';
import SEO from '../components/SEO';

const DayClose = () => {
    const { showToast } = useToast();
    const [dayStatus, setDayStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [openFloat, setOpenFloat] = useState('');
    const [openNotes, setOpenNotes] = useState('');
    const [physicalCash, setPhysicalCash] = useState('');
    const [chequesCount, setChequesCount] = useState('0');
    const [closeNotes, setCloseNotes] = useState('');
    const [reconciliation, setReconciliation] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    const fetchStatus = async () => {
        try {
            const res = await api.get('/api/v1/pos/day/status');
            const data = res.data;
            if (data.success) setDayStatus(data.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchStatus(); }, []);

    const handleOpenDay = async (e) => {
        e.preventDefault();
        if (!openFloat || isNaN(openFloat)) { showToast('Enter a valid opening float', 'error'); return; }
        setSubmitting(true);
        try {
            const res = await api.post('/api/v1/pos/day/open', { opening_float: parseFloat(openFloat), notes: openNotes });
            const data = res.data;
            if (data.success) {
                showToast('Register opened successfully!', 'success');
                await fetchStatus();
            } else {
                showToast(data.detail || 'Failed to open register', 'error');
            }
        } catch (e) {
            showToast('Failed to open register', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const handleCloseDay = async (e) => {
        e.preventDefault();
        if (!physicalCash || isNaN(physicalCash)) { showToast('Enter physical cash count', 'error'); return; }
        setSubmitting(true);
        try {
            const res = await api.post('/api/v1/pos/day/close', {
                physical_cash_count: parseFloat(physicalCash),
                cheques_count: parseFloat(chequesCount || '0'),
                notes: closeNotes,
            });
            const data = res.data;
            if (data.success !== false) {
                setReconciliation(data);
                showToast('Register closed! Reconciliation complete.', 'success');
                await fetchStatus();
            } else {
                showToast(data.detail || 'Failed to close register', 'error');
            }
        } catch (e) {
            showToast('Failed to close register', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const isOpen = dayStatus?.status === 'open';
    const isClosed = dayStatus?.status === 'closed';
    const statusIcon = isOpen ? <Unlock size={16} /> : isClosed ? <Lock size={16} /> : <Clock size={16} />;
    const statusColor = isOpen ? 'var(--c-sage)' : isClosed ? 'var(--c-ink-muted)' : 'var(--c-brown)';

    const fmt = (v) => v != null ? `₹${v.toLocaleString()}` : '—';

    return (
        <>
            <SEO title="Register Day Close" description="Manage end-of-day register opening, closing and cash reconciliations." />
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
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <h1 className="page-title" >Day Open / Close</h1>
                            <ComplianceStatusChip status={isOpen ? 'info' : 'success'} level="L2" />
                        </div>
                        <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>
                            Cash register management and end-of-day reconciliation
                        </p>
                    </div>
                    <button className="action-btn" onClick={fetchStatus}>
                        <RefreshCw size={13} style={{ marginRight: 6 }} /> Refresh
                    </button>
                </div>

                {/* Status Bar */}
                <div style={{ padding: '16px 22px', borderBottom: '1px solid var(--c-border)', background: 'var(--c-canvas-raised)', position: 'relative' }}>
                    {isClosed && (
                        <div style={{ position: 'absolute', right: 30, top: 12, zIndex: 10 }}>
                            <InkStamp text="REGISTER CLOSED" status="success" size="sm" />
                        </div>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15, fontWeight: 700, color: statusColor }}>
                            {statusIcon}
                            {loading ? 'Loading...' : dayStatus ? `Register ${dayStatus.status?.replace('_', ' ')}` : 'Unknown'}
                        </div>
                        {dayStatus?.opening_float != null && (
                            <div style={{ display: 'flex', gap: 16, marginLeft: 'auto', fontSize: 12, color: 'var(--c-ink-muted)', flexWrap: 'wrap' }}>
                                <span>Opening Float: <strong style={{ color: 'var(--c-dark)' }}>{fmt(dayStatus.opening_float)}</strong></span>
                                {dayStatus.opened_at && <span>Opened: <strong style={{ color: 'var(--c-dark)' }}>{new Date(dayStatus.opened_at).toLocaleTimeString()}</strong></span>}
                                {dayStatus.closing_float != null && <span>Closing: <strong style={{ color: 'var(--c-dark)' }}>{fmt(dayStatus.closing_float)}</strong></span>}
                                {dayStatus.variance != null && (
                                    <span style={{ color: dayStatus.variance === 0 ? 'var(--c-sage)' : 'var(--c-critical)' }}>
                                        Variance: <strong>{fmt(dayStatus.variance)}</strong>
                                    </span>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="two-col" style={{ flex: 1 }}>
                    <div className="col-body" style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
                        
                        {/* Forms Row */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '22px' }}>
                    {/* Open Register Panel */}
                    <div style={{ background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', padding: '20px' }}>
                        <div className="zone-label" style={{ marginBottom: 16 }}>Open Register</div>
                        {isOpen ? (
                            <div className="empty-state" style={{ padding: '40px 0' }}>
                                <CheckCircle size={36} style={{ color: 'var(--c-sage)', marginBottom: 12 }} />
                                <p style={{ fontSize: '13px', fontWeight: 600, margin: 0 }}>Register is already open</p>
                                <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>Opening float: {fmt(dayStatus.opening_float)}</p>
                            </div>
                        ) : (
                            <form onSubmit={handleOpenDay} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Opening Float (₹) *</span>
                                    <input type="number" step="0.01" min="0" value={openFloat} onChange={e => setOpenFloat(e.target.value)} placeholder="e.g. 5000" required />
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Notes (optional)</span>
                                    <input type="text" value={openNotes} onChange={e => setOpenNotes(e.target.value)} placeholder="Opening notes..." />
                                </div>
                                <button type="submit" className="action-btn primary" disabled={submitting} style={{ marginTop: 6 }}>
                                    <Unlock size={14} style={{ marginRight: 6 }} /> {submitting ? 'Opening...' : 'Open Register'}
                                </button>
                            </form>
                        )}
                    </div>

                    {/* Close Register Panel */}
                    <div style={{ background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', padding: '20px' }}>
                        <div className="zone-label" style={{ marginBottom: 16 }}>Close Register</div>
                        {!isOpen ? (
                            <div className="empty-state" style={{ padding: '40px 0' }}>
                                <Lock size={36} style={{ color: 'var(--c-ink-muted)', marginBottom: 12 }} />
                                <p style={{ fontSize: '13px', fontWeight: 600, margin: 0 }}>Register not open</p>
                                <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>Open register to process transactions.</p>
                            </div>
                        ) : (
                            <form onSubmit={handleCloseDay} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Physical Cash Count (₹) *</span>
                                    <input type="number" step="0.01" min="0" value={physicalCash} onChange={e => setPhysicalCash(e.target.value)} placeholder="Count cash in drawer" required />
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Cheques (₹)</span>
                                    <input type="number" step="0.01" min="0" value={chequesCount} onChange={e => setChequesCount(e.target.value)} placeholder="0" />
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Notes</span>
                                    <input type="text" value={closeNotes} onChange={e => setCloseNotes(e.target.value)} placeholder="Closing notes..." />
                                </div>
                                <button type="submit" className="action-btn primary" disabled={submitting} style={{ marginTop: 6 }}>
                                    <Lock size={14} style={{ marginRight: 6 }} /> {submitting ? 'Closing...' : 'Close & Reconcile'}
                                </button>
                            </form>
                        )}
                    </div>
                </div>
                {/* Reconciliation Panel */}
                {reconciliation && (
                    <div style={{ background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', padding: '20px' }}>
                        <div className="zone-label" style={{ marginBottom: 16 }}>Reconciliation Results</div>
                        <div className="kpi-strip" style={{ marginBottom: 20 }}>
                            <div className="kpi-cell">
                                <div className="kpi-label">Opening Float</div>
                                <div className="kpi-value">{fmt(reconciliation.opening_float)}</div>
                            </div>
                            <div className="kpi-cell">
                                <div className="kpi-label">Expected Cash</div>
                                <div className="kpi-value brown">{fmt(reconciliation.expected_cash)}</div>
                            </div>
                            <div className="kpi-cell">
                                <div className="kpi-label">Physical Cash</div>
                                <div className="kpi-value sage">{fmt(reconciliation.physical_cash)}</div>
                            </div>
                            <div className="kpi-cell">
                                <div className="kpi-label">Variance</div>
                                <div className={`kpi-value ${reconciliation.variance === 0 ? 'sage' : 'critical'}`}>{fmt(reconciliation.variance)}</div>
                            </div>
                        </div>
                        
                        {reconciliation.reconciliation_status && (
                            <div style={{ marginBottom: 20 }}>
                                <div className={`badge ${
                                    reconciliation.reconciliation_status === 'matched' ? 'active' :
                                    reconciliation.reconciliation_status === 'small_variance' ? 'warning' : 'critical'
                                }`} style={{ fontSize: '11px', padding: '4px 12px', display: 'inline-flex' }}>
                                    Reconciliation Status: {reconciliation.reconciliation_status?.replace('_', ' ').toUpperCase()}
                                </div>
                            </div>
                        )}

                        {reconciliation.sales_summary && (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, fontSize: '13px' }}>
                                <div>Transactions: <strong style={{ color: 'var(--c-dark)' }}>{reconciliation.sales_summary.transaction_count}</strong></div>
                                <div>Total Sales: <strong style={{ color: 'var(--c-dark)', fontFamily: 'var(--f-mono)' }}>{fmt(reconciliation.sales_summary.total_sales)}</strong></div>
                                <div>Cash Sales: <strong style={{ color: 'var(--c-dark)', fontFamily: 'var(--f-mono)' }}>{fmt(reconciliation.sales_summary.cash_sales)}</strong></div>
                                <div>UPI Sales: <strong style={{ color: 'var(--c-dark)', fontFamily: 'var(--f-mono)' }}>{fmt(reconciliation.sales_summary.upi_sales)}</strong></div>
                                <div>Card Sales: <strong style={{ color: 'var(--c-dark)', fontFamily: 'var(--f-mono)' }}>{fmt(reconciliation.sales_summary.card_sales)}</strong></div>
                            </div>
                        )}
                    </div>
                )}
            </div>
            
            <div className="col-divider" />
                    
                    {/* Shift Timeline Rail */}
                    <div className="col-body" style={{ background: 'var(--c-canvas)', padding: '22px' }}>
                        <div className="zone-label" style={{ marginBottom: 16 }}>Shift Timeline</div>
                        <div className="feed-stream">
                            <div className="feed-item">
                                <div className="feed-icon" style={{ background: 'var(--c-sage-glow)', color: 'var(--c-sage)' }}><Unlock size={12}/></div>
                                <div className="feed-content">
                                    <div className="feed-title">Register Opened</div>
                                    <div className="feed-desc">Opening float set to ₹5,000.</div>
                                    <div className="feed-time">09:00 AM</div>
                                </div>
                            </div>
                            <div className="feed-item">
                                <div className="feed-icon" style={{ background: 'var(--c-brown-glow)', color: 'var(--c-brown)' }}><TrendingUp size={12}/></div>
                                <div className="feed-content">
                                    <div className="feed-title">Peak Sales Hour</div>
                                    <div className="feed-desc">42 transactions processed.</div>
                                    <div className="feed-time">01:30 PM</div>
                                </div>
                            </div>
                            {isClosed && (
                                <>
                                    <div className="feed-item">
                                        <div className="feed-icon" style={{ background: 'var(--c-sage-glow)', color: 'var(--c-sage)' }}><Lock size={12}/></div>
                                        <div className="feed-content">
                                            <div className="feed-title">Register Closed</div>
                                            <div className="feed-desc">Final physical count verified.</div>
                                            <div className="feed-time">Just now</div>
                                        </div>
                                    </div>
                                    <div className="feed-item">
                                        <div className="feed-icon" style={{ background: 'var(--c-sage-glow)', color: 'var(--c-sage)' }}><CheckCircle size={12}/></div>
                                        <div className="feed-content">
                                            <div className="feed-title">Reconciliation Complete</div>
                                            <div className="feed-desc">Automated matching performed.</div>
                                            <div className="feed-time">Just now</div>
                                        </div>
                                    </div>
                                </>
                            )}
                            {!isClosed && (
                                <div className="feed-item">
                                    <div className="feed-icon" style={{ background: 'rgba(211,212,192,0.3)', color: 'var(--c-ink-muted)' }}><Clock size={12}/></div>
                                    <div className="feed-content">
                                        <div className="feed-title">Awaiting Day Close</div>
                                        <div className="feed-desc">Shift is currently active.</div>
                                        <div className="feed-time">--:--</div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default DayClose;
