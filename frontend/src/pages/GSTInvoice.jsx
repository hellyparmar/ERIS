import React, { useState } from 'react';
import { FileText, Download, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
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
                fetch(`${API_BASE}/api/v1/gst/gstr1?month=${month}&year=${year}`),
                fetch(`${API_BASE}/api/v1/gst/gstr1/validate?month=${month}&year=${year}`)
            ]);
            const [data, valid] = await Promise.all([dataRes.json(), validRes.json()]);
            if (data.success) setGstr1Data(data.data);
            if (valid.success) setValidation(valid.data);
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
        <div className="min-h-screen space-y-8 animate-fade-in">
            <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">GST Invoice & GSTR-1</h1>
                <p className="text-muted-foreground">View GST summaries and export GSTR-1 for filing</p>
            </div>

            <GlassCard className="p-6">
                <div className="flex flex-wrap items-end gap-4">
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Month</label>
                        <select value={month} onChange={e => setMonth(parseInt(e.target.value))}
                            className="px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none min-w-[160px]">
                            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Year</label>
                        <select value={year} onChange={e => setYear(parseInt(e.target.value))}
                            className="px-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none">
                            {years.map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                    </div>
                    <GradientButton onClick={fetchGSTR1} disabled={loading} className="py-3">
                        <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        {loading ? 'Fetching...' : 'Generate GSTR-1'}
                    </GradientButton>
                    {gstr1Data && (
                        <button onClick={downloadJSON}
                            className="flex items-center gap-2 px-4 py-3 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors font-medium">
                            <Download className="w-4 h-4" /> Download JSON
                        </button>
                    )}
                </div>
            </GlassCard>

            {validation && (
                <GlassCard className={`p-4 border ${validation.is_valid ? 'border-green-500/30 bg-green-500/5' : 'border-yellow-500/30 bg-yellow-500/5'}`}>
                    <div className="flex items-center gap-3">
                        {validation.is_valid
                            ? <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                            : <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />}
                        <div>
                            <p className={`font-medium ${validation.is_valid ? 'text-green-400' : 'text-yellow-400'}`}>
                                {validation.is_valid ? 'Data is valid for filing' : `${validation.issues?.length} issue(s) found`}
                            </p>
                            {validation.issues?.map((issue, i) => (
                                <p key={i} className="text-sm text-muted-foreground mt-1">{issue.message}</p>
                            ))}
                        </div>
                    </div>
                </GlassCard>
            )}

            {gstr1Data && (
                <>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                            { label: 'Taxable Value', value: `₹${gstr1Data.b2c_summary?.taxable_value?.toLocaleString()}`, color: 'text-blue-400' },
                            { label: 'CGST', value: `₹${gstr1Data.b2c_summary?.cgst?.toFixed(2)}`, color: 'text-green-400' },
                            { label: 'SGST', value: `₹${gstr1Data.b2c_summary?.sgst?.toFixed(2)}`, color: 'text-purple-400' },
                            { label: 'Total Tax', value: `₹${gstr1Data.total_liability?.total_tax?.toFixed(2)}`, color: 'text-yellow-400' },
                        ].map(({ label, value, color }) => (
                            <GlassCard key={label} className="p-4 text-center">
                                <p className="text-sm text-muted-foreground mb-1">{label}</p>
                                <p className={`text-2xl font-bold ${color}`}>{value}</p>
                            </GlassCard>
                        ))}
                    </div>

                    <GlassCard className="p-6">
                        <h3 className="text-lg font-bold gradient-text mb-4">B2C Sales — {gstr1Data.filing_period}</h3>
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-muted-foreground text-left border-b border-border">
                                    <th className="pb-3 pr-4">Type</th>
                                    <th className="pb-3 pr-4 text-right">Invoices</th>
                                    <th className="pb-3 pr-4 text-right">Taxable</th>
                                    <th className="pb-3 pr-4 text-right">CGST</th>
                                    <th className="pb-3 text-right">SGST</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td className="py-3 pr-4 text-foreground font-medium">B2C (Unregistered)</td>
                                    <td className="py-3 pr-4 text-right text-muted-foreground">{gstr1Data.b2c_summary?.invoice_count}</td>
                                    <td className="py-3 pr-4 text-right">₹{gstr1Data.b2c_summary?.taxable_value?.toLocaleString()}</td>
                                    <td className="py-3 pr-4 text-right text-green-400">₹{gstr1Data.b2c_summary?.cgst?.toFixed(2)}</td>
                                    <td className="py-3 text-right text-purple-400">₹{gstr1Data.b2c_summary?.sgst?.toFixed(2)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <h3 className="text-lg font-bold gradient-text mb-4">HSN Summary</h3>
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-muted-foreground text-left border-b border-border">
                                    <th className="pb-3 pr-4">HSN</th>
                                    <th className="pb-3 pr-4">Description</th>
                                    <th className="pb-3 text-right">GST Rate</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {gstr1Data.hsn_summary?.map(h => (
                                    <tr key={h.hsn_code}>
                                        <td className="py-3 pr-4 font-mono text-primary">{h.hsn_code}</td>
                                        <td className="py-3 pr-4 text-foreground">{h.description}</td>
                                        <td className="py-3 text-right text-yellow-400">{h.igst_rate}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </GlassCard>
                </>
            )}

            {!gstr1Data && !loading && (
                <GlassCard className="p-12 text-center">
                    <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-40" />
                    <p className="text-muted-foreground">Select a period and click "Generate GSTR-1" to view tax summary</p>
                </GlassCard>
            )}
        </div>
    );
};

export default GSTInvoice;
