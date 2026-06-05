import React, { useState } from 'react';
import { Settings, Percent, Save, Edit2, X, CheckCircle } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

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
        if (rate === 0) return 'bg-green-500/20 text-green-400';
        if (rate <= 5) return 'bg-blue-500/20 text-blue-400';
        if (rate <= 12) return 'bg-yellow-500/20 text-yellow-400';
        if (rate <= 18) return 'bg-orange-500/20 text-orange-400';
        return 'bg-red-500/20 text-red-400';
    };

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">GST Rates Configuration</h1>
                <p className="text-muted-foreground">Configure GST rates per category for your business type</p>
            </div>

            {/* Business Presets */}
            <GlassCard className="p-6">
                <h3 className="text-lg font-bold gradient-text mb-4 flex items-center gap-2">
                    <Settings className="w-5 h-5" /> Quick Presets by Business Type
                </h3>
                <div className="flex flex-wrap gap-3">
                    {BUSINESS_PRESETS.map(preset => (
                        <button key={preset.label}
                            onClick={() => addToast(`Preset "${preset.label}" applied (UI demo)`, 'success')}
                            className="px-4 py-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors font-medium text-sm">
                            {preset.label}
                            <span className="ml-2 text-xs opacity-70">{preset.rates.join('%, ')}%</span>
                        </button>
                    ))}
                </div>
            </GlassCard>

            {/* GST Rate Table */}
            <GlassCard className="p-6">
                <h3 className="text-lg font-bold gradient-text mb-6 flex items-center gap-2">
                    <Percent className="w-5 h-5" /> GST Rate Slabs
                </h3>
                <div className="space-y-4">
                    {rates.map((rate, idx) => (
                        <div key={rate.category}
                            className={`p-5 rounded-xl border transition-all ${editingIdx === idx ? 'border-primary bg-primary/5' : 'border-border bg-secondary/20 hover:bg-secondary/30'}`}>
                            {editingIdx === idx ? (
                                /* Edit Mode */
                                <div className="space-y-3">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-xs font-medium text-muted-foreground mb-1">Category Name</label>
                                            <input value={editValues.category} onChange={e => setEditValues({ ...editValues, category: e.target.value })}
                                                className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm focus:border-primary focus:outline-none" />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-muted-foreground mb-1">GST Rate (%)</label>
                                            <input type="number" step="0.5" min="0" max="28"
                                                value={editValues.gstin_rate}
                                                onChange={e => setEditValues({ ...editValues, gstin_rate: parseFloat(e.target.value) })}
                                                className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm focus:border-primary focus:outline-none" />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-muted-foreground mb-1">Description</label>
                                        <input value={editValues.description} onChange={e => setEditValues({ ...editValues, description: e.target.value })}
                                            className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm focus:border-primary focus:outline-none" />
                                    </div>
                                    <div className="flex gap-2 pt-1">
                                        <GradientButton onClick={() => saveEdit(idx)} className="text-sm py-2">
                                            <Save className="w-4 h-4 mr-1" /> Save
                                        </GradientButton>
                                        <button onClick={cancelEdit}
                                            className="flex items-center gap-1 px-3 py-2 rounded-lg bg-secondary/50 text-muted-foreground hover:text-foreground text-sm transition-colors">
                                            <X className="w-4 h-4" /> Cancel
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                /* View Mode */
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <span className={`px-3 py-1 rounded-full text-sm font-bold ${getRateBadgeColor(rate.gstin_rate)}`}>
                                            {rate.gstin_rate}%
                                        </span>
                                        <div>
                                            <p className="font-semibold text-foreground">{rate.category}</p>
                                            <p className="text-xs text-muted-foreground mt-0.5">{rate.description}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6 text-xs text-muted-foreground">
                                        <div className="text-center hidden md:block">
                                            <p className="font-semibold text-foreground">{rate.cgst}%</p>
                                            <p>CGST</p>
                                        </div>
                                        <div className="text-center hidden md:block">
                                            <p className="font-semibold text-foreground">{rate.sgst}%</p>
                                            <p>SGST</p>
                                        </div>
                                        <div className="text-center hidden md:block">
                                            <p className="font-mono text-foreground">{rate.example_hsn}</p>
                                            <p>HSN eg.</p>
                                        </div>
                                        <button onClick={() => startEdit(idx)}
                                            className="p-2 rounded-lg hover:bg-primary/10 transition-colors text-primary">
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </GlassCard>

            {/* Info */}
            <GlassCard className="p-4 border border-blue-500/20 bg-blue-500/5">
                <div className="flex gap-3">
                    <CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-muted-foreground">
                        <p className="font-medium text-blue-400 mb-1">How GST rates work</p>
                        <p>For intra-state sales, GST is split equally as CGST + SGST. For inter-state sales, full IGST applies. Rates here apply per product category.</p>
                    </div>
                </div>
            </GlassCard>
        </div>
    );
};

export default GSTRates;
