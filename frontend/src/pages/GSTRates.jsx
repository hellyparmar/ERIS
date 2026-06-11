import React, { useState } from 'react';
import { Settings, Percent, Save, Edit2, X, CheckCircle } from 'lucide-react';
import { useToast } from '../components/ui/Toast';
import '../styles/fresh-design.css';

const DEFAULT_GST_RATES = [
    { category: 'Essentials', description: 'Rice, wheat, milk, eggs, vegetables', gstin_rate: 0, cgst: 0, sgst: 0, cess: 0, example_hsn: '0401' },
    { category: 'Low Tax', description: 'Tea, coffee, edible oil, medicines', gstin_rate: 5, cgst: 2.5, sgst: 2.5, cess: 0, example_hsn: '3004' },
    { category: 'Standard', description: 'Apparel, footwear, processed foods', gstin_rate: 12, cgst: 6, sgst: 6, cess: 0, example_hsn: '6109' },
    { category: 'Standard+', description: 'Electronics, FMCG, cosmetics', gstin_rate: 18, cgst: 9, sgst: 9, cess: 0, example_hsn: '8471' },
    { category: 'Luxury', description: 'Cars, ACs, premium goods, tobacco', gstin_rate: 28, cgst: 14, sgst: 14, cess: 0, example_hsn: '8703' },
];

const BUSINESS_PRESETS = [
    { label: 'General Store', rates: [0, 5, 12] },
    { label: 'Electronics', rates: [5, 18, 28] },
    { label: 'Clothing', rates: [5, 12] },
    { label: 'Restaurant', rates: [5, 12] },
    { label: 'Pharmacy', rates: [0, 5, 12] },
];

const GSTRates = () => {
    const { addToast } = useToast();
    const [rates, setRates] = useState(DEFAULT_GST_RATES);
    const [editingIdx, setEditingIdx] = useState(null);
    const [editValues, setEditValues] = useState({});

    const startEdit = (idx) => {
        setEditingIdx(idx);
        setEditValues({ ...rates[idx] });
    };

    const cancelEdit = () => {
        setEditingIdx(null);
        setEditValues({});
    };

    const saveEdit = (idx) => {
        const updated = [...rates];
        updated[idx] = {
            ...editValues,
            cgst: parseFloat(editValues.gstin_rate) / 2,
            sgst: parseFloat(editValues.gstin_rate) / 2,
        };
        setRates(updated);
        setEditingIdx(null);
        addToast(`GST rate updated for ${editValues.category}`, 'success');
    };

    const getRateBadgeColor = (rate) => {
        if (rate === 0) return 'fresh-badge green';
        if (rate <= 5) return 'fresh-badge green';
        if (rate <= 12) return 'fresh-badge yellow';
        if (rate <= 18) return 'fresh-badge yellow';
        return 'fresh-badge red';
    };

    return (
        <div className="fresh-page">
            <div style={{ marginBottom: 32 }}>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>GST rate lookup and tax slab management</p>
            </div>

            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title"><Settings size={16} /> Quick Presets by Business Type</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {BUSINESS_PRESETS.map(preset => (
                        <button key={preset.label}
                            onClick={() => addToast(`Preset "${preset.label}" applied (UI demo)`, 'success')}
                            className="fresh-btn">
                            {preset.label}
                            <span style={{ marginLeft: 6, fontSize: 11, opacity: 0.7 }}>{preset.rates.join('%, ')}%</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title"><Percent size={16} /> GST Rate Slabs</span>
                </div>
                <table className="fresh-table">
                    <thead>
                        <tr>
                            <th>Rate</th>
                            <th>Category</th>
                            <th className="num">CGST</th>
                            <th className="num">SGST</th>
                            <th>HSN</th>
                            <th style={{ width: 40 }}></th>
                        </tr>
                    </thead>
                    <tbody>
                        {rates.map((rate, idx) => (
                            editingIdx === idx ? (
                                <tr key={rate.category}>
                                    <td colSpan={6} style={{ padding: 16 }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                                                <div>
                                                    <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', marginBottom: 4 }}>Category Name</label>
                                                    <input value={editValues.category} onChange={e => setEditValues({ ...editValues, category: e.target.value })}
                                                        style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: 13 }} />
                                                </div>
                                                <div>
                                                    <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', marginBottom: 4 }}>GST Rate (%)</label>
                                                    <input type="number" step="0.5" min="0" max="28"
                                                        value={editValues.gstin_rate}
                                                        onChange={e => setEditValues({ ...editValues, gstin_rate: parseFloat(e.target.value) })}
                                                        style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: 13 }} />
                                                </div>
                                            </div>
                                            <div>
                                                <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', marginBottom: 4 }}>Description</label>
                                                <input value={editValues.description} onChange={e => setEditValues({ ...editValues, description: e.target.value })}
                                                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: 13 }} />
                                            </div>
                                            <div style={{ display: 'flex', gap: 8 }}>
                                                <button onClick={() => saveEdit(idx)} className="fresh-btn primary"><Save size={14} style={{ marginRight: 4 }} /> Save</button>
                                                <button onClick={cancelEdit} className="fresh-btn"><X size={14} style={{ marginRight: 4 }} /> Cancel</button>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                <tr key={rate.category}>
                                    <td><span className={getRateBadgeColor(rate.gstin_rate)}>{rate.gstin_rate}%</span></td>
                                    <td>
                                        <div style={{ fontWeight: 500 }}>{rate.category}</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{rate.description}</div>
                                    </td>
                                    <td className="num">{rate.cgst}%</td>
                                    <td className="num">{rate.sgst}%</td>
                                    <td style={{ fontFamily: 'monospace', color: 'var(--text-muted)', fontSize: 13 }}>{rate.example_hsn}</td>
                                    <td>
                                        <button onClick={() => startEdit(idx)} className="fresh-btn" style={{ padding: '4px 8px' }}>
                                            <Edit2 size={14} />
                                        </button>
                                    </td>
                                </tr>
                            )
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="fresh-section">
                <div className="fresh-list">
                    <div className="fresh-list-item">
                        <CheckCircle size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                        <div>
                            <div className="fresh-list-label" style={{ fontWeight: 500, color: 'var(--text-primary)' }}>How GST rates work</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>For intra-state sales, GST is split equally as CGST + SGST. For inter-state sales, full IGST applies. Rates here apply per product category.</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GSTRates;
