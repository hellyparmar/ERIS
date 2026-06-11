import React, { useState } from 'react';
import { FileText, AlertCircle } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';
import { Line, Doughnut } from 'react-chartjs-2';
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
import '../styles/fresh-design.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler, ArcElement);

const TaxCompliance = () => {
    const { showToast } = useToast();
    const [activeTab, setActiveTab] = useState('gst');

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
                borderColor: 'var(--success)',
                backgroundColor: 'var(--success-soft)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Output Liability',
                data: [25000, 28000, 32000, 29000, 31000],
                borderColor: 'var(--error)',
                backgroundColor: 'var(--danger-soft)',
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
                backgroundColor: ['var(--accent)', 'var(--info)', 'var(--warning)', 'var(--error)'],
                borderWidth: 0
            }
        ]
    };

    return (
        <div className="fresh-page">
            <div style={{ marginBottom: 32 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    <button
                        className="fresh-btn primary"
                        style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                        onClick={() => showToast('Tax Filing initiated to GST Portal successfully.', 'success')}
                    >
                        <FileText size={16} /> File Returns
                    </button>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>GST filing and compliance tracking</p>
            </div>

            {/* Summary Metrics */}
            <div className="fresh-metrics">
                <div className="fresh-metric">
                    <div className="fresh-metric-value">₹{taxSummary.total_liability.toLocaleString()}</div>
                    <div className="fresh-metric-label">Total Tax Liability</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value" style={{ color: 'var(--success)' }}>₹{taxSummary.paid.toLocaleString()}</div>
                    <div className="fresh-metric-label">Tax Paid</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value" style={{ color: 'var(--error)' }}>₹{taxSummary.pending.toLocaleString()}</div>
                    <div className="fresh-metric-label">Pending Due</div>
                </div>
                <div className="fresh-metric">
                    <div className="fresh-metric-value">{taxSummary.next_due}</div>
                    <div className="fresh-metric-label">Next Due Date</div>
                </div>
            </div>

            {/* Tabs */}
            <div className="fresh-pills" style={{ marginBottom: 24 }}>
                {[
                    { id: 'gst', label: 'GST Returns' },
                    { id: 'tds', label: 'TDS Filing' },
                    { id: 'income_tax', label: 'Income Tax' }
                ].map((tab) => (
                    <button
                        key={tab.id}
                        className={`fresh-pill ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Main Content */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
                {/* Chart */}
                <div className="fresh-section">
                    <div className="fresh-section-header">
                        <span className="fresh-section-title">
                            {activeTab === 'gst' ? 'GST Liability vs Credit' :
                             activeTab === 'tds' ? 'TDS Category Breakdown' : 'Tax Projection'}
                        </span>
                    </div>
                    <div className="fresh-chart" style={{ height: 350 }}>
                        {activeTab === 'gst' && <Line data={gstData} options={chartOptions} />}
                        {activeTab === 'tds' && (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                                <div style={{ width: 300, height: 300 }}>
                                    <Doughnut data={tdsData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }} />
                                </div>
                            </div>
                        )}
                        {activeTab === 'income_tax' && (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                                Advance Tax Projection Chart (Data coming soon)
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                    {/* Detailed Calculation */}
                    <div className="fresh-section">
                        <div className="fresh-section-header">
                            <span className="fresh-section-title">Detailed Calculation</span>
                        </div>
                        <div className="fresh-list">
                            <div className="fresh-list-item">
                                <span className="fresh-list-label">Gross Revenue</span>
                                <span className="fresh-list-value">₹12,45,000</span>
                            </div>
                            <div className="fresh-list-item">
                                <span className="fresh-list-label">Taxable Amount</span>
                                <span className="fresh-list-value">₹10,50,000</span>
                            </div>
                            <div className="fresh-list-item">
                                <span className="fresh-list-label">Applicable Rate</span>
                                <span className="fresh-list-value">18%</span>
                            </div>
                            <div className="fresh-list-item" style={{ borderBottom: 'none', marginTop: 8 }}>
                                <span className="fresh-list-label" style={{ fontWeight: 600 }}>Total Tax</span>
                                <span className="fresh-list-value" style={{ color: 'var(--accent)', fontWeight: 600 }}>₹1,89,000</span>
                            </div>
                        </div>
                    </div>

                    {/* Compliance Tip */}
                    <div className="fresh-section" style={{ background: 'var(--accent-soft)' }}>
                        <div style={{ display: 'flex', gap: 12 }}>
                            <AlertCircle size={20} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: 2 }} />
                            <div>
                                <div className="fresh-section-title" style={{ fontSize: 14, marginBottom: 4 }}>Compliance Tip</div>
                                <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>
                                    File your GSTR-1 by the 11th to avoid penalties. You have pending invoices.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TaxCompliance;
