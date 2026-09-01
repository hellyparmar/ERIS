import React, { useState } from 'react';
import { FileText, AlertCircle } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';
import { Line, Doughnut } from 'react-chartjs-2';
import InkStamp from '../components/patterns/InkStamp';
import SEO from '../components/SEO';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ArcElement
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler, ArcElement);

const DEFAULT_GST_RATES = [
    { category: 'Essentials', description: 'unprocessed ingredients (rice, flour, vegetables, eggs)', gstin_rate: 0, cgst: 0, sgst: 0, cess: 0, example_hsn: '0401' },
    { category: 'Food Service', description: 'prepared food served in restaurants, takeaway meals', gstin_rate: 5, cgst: 2.5, sgst: 2.5, cess: 0, example_hsn: '3004' },
    { category: 'Packaged Food', description: 'branded beverages, packaged snacks, branded dairy', gstin_rate: 12, cgst: 6, sgst: 6, cess: 0, example_hsn: '6109' },
    { category: 'Premium Service', description: 'food + beverages in AC restaurants (combined rate), alcohol (beer, wine) — note: state excise applies separately', gstin_rate: 18, cgst: 9, sgst: 9, cess: 0, example_hsn: '8471' },
    { category: 'Luxury', description: 'premium imported spirits, aerated drinks in luxury venues', gstin_rate: 28, cgst: 14, sgst: 14, cess: 0, example_hsn: '8703' },
];

const TaxCompliance = () => {
    const { showToast } = useToast();
    const [activeTab, setActiveTab] = useState('gst');
    const [gstRatesOpen, setGstRatesOpen] = useState(false);

    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#e2e8f0' : '#475569';
    const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'top', labels: { usePointStyle: true, color: textColor } },
        },
        scales: {
            x: { grid: { color: gridColor }, ticks: { color: textColor } },
            y: { grid: { color: gridColor }, ticks: { color: textColor } }
        }
    };

    const taxSummary = {
        total_liability: 124500,
        paid: 85000,
        pending: 39500,
        next_due: 'May 20, 2025'
    };

    const gstData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        datasets: [
            {
                label: 'Input Tax Credit',
                data: [12000, 15000, 18000, 14000, 16000],
                borderColor: '#AECB84',
                backgroundColor: 'rgba(174,203,132,0.15)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Output Liability',
                data: [25000, 28000, 32000, 29000, 31000],
                borderColor: '#8B5E3C',
                backgroundColor: 'rgba(139,94,60,0.15)',
                fill: true,
                tension: 0.4
            }
        ]
    };

    const tdsData = {
        labels: ['Contractors', 'Rent', 'Professional Fees', 'Salaries'],
        datasets: [
            {
                data: [35, 20, 15, 30],
                backgroundColor: ['#8B5E3C', '#AECB84', '#D4C5B9', '#B05E5E'],
                borderWidth: 0
            }
        ]
    };

    return (
        <>
            <SEO title="Tax Compliance Tracker" description="GST tracking, input tax credit, and output tax liabilities" />
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
                        <h1 className="page-title" >Tax Compliance</h1>
                        <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>GST filing and compliance tracking</p>
                    </div>
                    <button
                        className="action-btn primary"
                        style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                        onClick={() => showToast('Tax Filing initiated to GST Portal successfully.', 'success')}
                    >
                        <FileText size={13} /> File Returns
                    </button>
                </div>

                {/* Content body */}
                <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: 20 }}>
                    
                    {/* KPI Strip */}
                    <div className="kpi-strip">
                        <div className="kpi-cell">
                            <div className="kpi-label">Total Tax Liability</div>
                            <div className="kpi-value brown">₹{taxSummary.total_liability.toLocaleString()}</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Tax Paid</div>
                            <div className="kpi-value sage">₹{taxSummary.paid.toLocaleString()}</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Pending Due</div>
                            <div className="kpi-value critical">₹{taxSummary.pending.toLocaleString()}</div>
                        </div>
                        <div className="kpi-cell">
                            <div className="kpi-label">Next Due Date</div>
                            <div className="kpi-value" style={{ fontSize: '16px', paddingTop: 8 }}>{taxSummary.next_due}</div>
                        </div>
                    </div>

                    {/* Tab Navigation */}
                    <div className="filter-bar">
                        {[
                            { id: 'gst', label: 'GST Returns' },
                            { id: 'tds', label: 'TDS Filing' },
                            { id: 'income_tax', label: 'Income Tax' }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                className={`action-btn ${activeTab === tab.id ? 'primary' : ''}`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Chart & Summary Row */}
                    <div className="two-col" style={{ gap: '22px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                            <div className="content-section-alt">
                                <div className="section-header">
                                    <div className="zone-label" style={{ marginBottom: 0 }}>
                                        {activeTab === 'gst' ? 'GST Liability vs Credit' :
                                         activeTab === 'tds' ? 'TDS Category Breakdown' : 'Tax Projection'}
                                    </div>
                                </div>
                                <div className="chart-inner" style={{ height: 320, marginTop: 16 }}>
                                    {activeTab === 'gst' && <Line data={gstData} options={chartOptions} />}
                                    {activeTab === 'tds' && (
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                                            <div style={{ width: 280, height: 280 }}>
                                                <Doughnut data={tdsData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: textColor } } } }} />
                                            </div>
                                        </div>
                                    )}
                                    {activeTab === 'income_tax' && (
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--c-ink-muted)', fontSize: 13 }}>
                                            Advance Tax Projection Chart (Data coming soon)
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            <div className="content-section" style={{ position: 'relative', overflow: 'hidden' }}>
                                <div className="section-header">
                                    <div className="zone-label" style={{ marginBottom: 0 }}>Detailed Calculation</div>
                                </div>
                                <div style={{ position: 'absolute', right: 8, bottom: 8, zIndex: 10 }}>
                                    <InkStamp text="GST PASSED" status="success" size="sm" />
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '13px', marginTop: 14 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--c-ink-muted)' }}>
                                        <span>Gross Revenue</span>
                                        <span style={{ fontFamily: 'var(--f-mono)' }}>₹12,45,000</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--c-ink-muted)' }}>
                                        <span>Taxable Amount</span>
                                        <span style={{ fontFamily: 'var(--f-mono)' }}>₹10,50,000</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--c-ink-muted)' }}>
                                        <span>Applicable Rate</span>
                                        <span>18%</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, borderTop: '1px solid var(--c-border)', paddingTop: 10, color: 'var(--c-dark)', fontWeight: 600 }}>
                                        <span>Total Tax</span>
                                        <span style={{ color: 'var(--c-brown)', fontFamily: 'var(--f-mono)' }}>₹1,89,000</span>
                                    </div>
                                </div>
                            </div>

                            <div className="content-section" style={{ display: 'flex', gap: 12 }}>
                                <AlertCircle size={16} style={{ color: 'var(--c-brown)', flexShrink: 0, marginTop: 1 }} />
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--c-dark)', marginBottom: 4 }}>Compliance Tip</div>
                                    <p style={{ fontSize: 11, color: 'var(--c-ink-muted)', lineHeight: 1.5, margin: 0 }}>
                                        File your GSTR-1 by the 11th to avoid penalties. You have pending invoices.
                                    </p>
                                </div>
                            </div>
                            
                            {/* Collapsible GST Rates Panel */}
                            <div className="content-section" style={{ padding: 0, overflow: 'hidden' }}>
                                <button 
                                    onClick={() => setGstRatesOpen(!gstRatesOpen)}
                                    style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', background: 'transparent', border: 'none', cursor: 'pointer', fontFamily: 'inherit' }}
                                >
                                    <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--c-dark)' }}>GST Rates Reference</span>
                                    <span style={{ color: 'var(--c-ink-muted)', fontSize: 16 }}>{gstRatesOpen ? '−' : '+'}</span>
                                </button>
                                {gstRatesOpen && (
                                    <div style={{ padding: '0 16px 16px', borderTop: '1px solid var(--c-border)' }}>
                                        <table className="eris-table" style={{ width: '100%', fontSize: '11px', marginTop: 12 }}>
                                            <thead>
                                                <tr>
                                                    <th style={{ textAlign: 'left', padding: '8px 4px' }}>Category & Description</th>
                                                    <th style={{ textAlign: 'center', padding: '8px 4px' }}>Rate</th>
                                                    <th style={{ textAlign: 'center', padding: '8px 4px' }}>CGST+SGST</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {DEFAULT_GST_RATES.map((rate, idx) => (
                                                    <tr key={idx}>
                                                        <td style={{ padding: '8px 4px' }}>
                                                            <div style={{ fontWeight: 600 }}>{rate.category}</div>
                                                            <div style={{ fontSize: '10px', color: 'var(--c-ink-muted)', marginTop: '2px' }}>{rate.description}</div>
                                                        </td>
                                                        <td style={{ textAlign: 'center', padding: '8px 4px', fontWeight: 600 }}>{rate.gstin_rate}%</td>
                                                        <td style={{ textAlign: 'center', padding: '8px 4px', color: 'var(--c-ink-muted)' }}>{rate.cgst}% + {rate.sgst}%</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default TaxCompliance;
