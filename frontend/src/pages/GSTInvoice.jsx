import React, { useState } from 'react';
import { FileText, Download, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { useToast } from '../components/ui/Toast';
import { api } from '../lib/api';
import '../styles/fresh-design.css';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

const GSTInvoice = () => {
    const { addToast } = useToast();
    const now = new Date();
    const [month, setMonth] = useState(now.getMonth() + 1);
    const [year, setYear] = useState(now.getFullYear());
    const [gstr1Data, setGstr1Data] = useState(null);
    const [validation, setValidation] = useState(null);
    const [loading, setLoading] = useState(false);

    const fetchGSTR1 = async () => {
        setLoading(true);
        try {
            const [dataRes, validRes] = await Promise.all([
                api.gst.getGSTR1(month, year),
                api.gst.validateGSTR1(month, year)
            ]);
            if (dataRes.data?.success) setGstr1Data(dataRes.data.data);
            if (validRes.data?.success) setValidation(validRes.data.data);
        } catch {
            addToast('Failed to fetch GSTR-1 data', 'error');
        } finally {
            setLoading(false);
        }
    };

    const downloadJSON = () => {
        if (!gstr1Data) return;
        const blob = new Blob([JSON.stringify(gstr1Data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `GSTR1_${year}_${String(month).padStart(2, '0')}.json`;
        a.click();
        URL.revokeObjectURL(url);
        addToast('GSTR-1 JSON downloaded', 'success');
    };

    const years = [];
    for (let y = 2023; y <= now.getFullYear() + 1; y++) years.push(y);

    return (
        <div className="fresh-page">
            <div style={{ marginBottom: 32 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button onClick={fetchGSTR1} disabled={loading} className="fresh-btn primary">
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            {loading ? 'Fetching...' : 'Generate GSTR-1'}
                        </button>
                        {gstr1Data && (
                            <button onClick={downloadJSON} className="fresh-btn">
                                <Download className="w-4 h-4" /> Download JSON
                            </button>
                        )}
                    </div>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Generate and manage GST invoices</p>
            </div>

            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title">Period</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, padding: '16px 0' }}>
                    <div>
                        <label className="fresh-metric-label" style={{ marginBottom: 6 }}>Month</label>
                        <select value={month} onChange={e => setMonth(parseInt(e.target.value))}
                            style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-primary)', fontSize: 13, minWidth: 160 }}>
                            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="fresh-metric-label" style={{ marginBottom: 6 }}>Year</label>
                        <select value={year} onChange={e => setYear(parseInt(e.target.value))}
                            style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-primary)', fontSize: 13 }}>
                            {years.map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                    </div>
                </div>
            </div>

            {validation && (
                <div className="fresh-section" style={{ borderLeft: `3px solid ${validation.is_valid ? 'var(--success)' : 'var(--warning)'}` }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                        {validation.is_valid
                            ? <CheckCircle className="w-5 h-5" style={{ color: 'var(--success)', flexShrink: 0, marginTop: 1 }} />
                            : <AlertCircle className="w-5 h-5" style={{ color: 'var(--warning)', flexShrink: 0, marginTop: 1 }} />}
                        <div>
                            <p style={{ fontWeight: 500, color: validation.is_valid ? 'var(--success)' : 'var(--warning)' }}>
                                {validation.is_valid ? 'Data is valid for filing' : `${validation.issues?.length} issue(s) found`}
                            </p>
                            {validation.issues?.map((issue, i) => (
                                <p key={i} style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>{issue.message}</p>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {gstr1Data && (
                <>
                    <div className="fresh-metrics">
                        {[
                            { label: 'Taxable Value', value: `₹${gstr1Data.b2c_summary?.taxable_value?.toLocaleString()}` },
                            { label: 'CGST', value: `₹${gstr1Data.b2c_summary?.cgst?.toFixed(2)}` },
                            { label: 'SGST', value: `₹${gstr1Data.b2c_summary?.sgst?.toFixed(2)}` },
                            { label: 'Total Tax', value: `₹${gstr1Data.total_liability?.total_tax?.toFixed(2)}` },
                        ].map(({ label, value }) => (
                            <div key={label} className="fresh-metric">
                                <div className="fresh-metric-value">{value}</div>
                                <div className="fresh-metric-label">{label}</div>
                            </div>
                        ))}
                    </div>

                    <div className="fresh-section">
                        <div className="fresh-section-header">
                            <span className="fresh-section-title">B2C Sales — {gstr1Data.filing_period}</span>
                        </div>
                        <table className="fresh-table">
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th className="num">Invoices</th>
                                    <th className="num">Taxable</th>
                                    <th className="num">CGST</th>
                                    <th className="num">SGST</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style={{ fontWeight: 500 }}>B2C (Unregistered)</td>
                                    <td className="num" style={{ color: 'var(--text-muted)' }}>{gstr1Data.b2c_summary?.invoice_count}</td>
                                    <td className="num">₹{gstr1Data.b2c_summary?.taxable_value?.toLocaleString()}</td>
                                    <td className="num" style={{ color: 'var(--success)' }}>₹{gstr1Data.b2c_summary?.cgst?.toFixed(2)}</td>
                                    <td className="num" style={{ color: 'var(--accent)' }}>₹{gstr1Data.b2c_summary?.sgst?.toFixed(2)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div className="fresh-section">
                        <div className="fresh-section-header">
                            <span className="fresh-section-title">HSN Summary</span>
                        </div>
                        <table className="fresh-table">
                            <thead>
                                <tr>
                                    <th>HSN</th>
                                    <th>Description</th>
                                    <th className="num">GST Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                                {gstr1Data.hsn_summary?.map(h => (
                                    <tr key={h.hsn_code}>
                                        <td style={{ fontFamily: 'monospace', color: 'var(--accent)' }}>{h.hsn_code}</td>
                                        <td>{h.description}</td>
                                        <td className="num"><span className="fresh-badge yellow">{h.igst_rate}%</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {!gstr1Data && !loading && (
                <div className="fresh-section" style={{ padding: 48, textAlign: 'center' }}>
                    <FileText className="w-16 h-16" style={{ color: 'var(--text-muted)', margin: '0 auto 16px', opacity: 0.4 }} />
                    <p style={{ color: 'var(--text-muted)' }}>Select a period and click "Generate GSTR-1" to view tax summary</p>
                </div>
            )}
        </div>
    );
};

export default GSTInvoice;
