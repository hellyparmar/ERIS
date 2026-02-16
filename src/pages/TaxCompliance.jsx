
import React, { useState } from 'react';
import {
    FileText,
    TrendingUp,
    AlertCircle,
    CheckCircle,
    Download,
    Calendar,
    DollarSign,
    PieChart
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
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

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler, ArcElement);

const TaxCompliance = () => {
    const [activeTab, setActiveTab] = useState('gst'); // gst, tds, income_tax

    // Determine if we are in dark mode (simple check)
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

    // Mock Data
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
                borderColor: '#10b981', // green-500
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Output Liability',
                data: [25000, 28000, 32000, 29000, 31000],
                borderColor: '#ef4444', // red-500
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
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
                backgroundColor: ['#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899'],
                borderWidth: 0
            }
        ]
    };



    return (
        <div className="min-h-screen fade-in-up space-y-8 p-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">Tax & Compliance</h1>
                    <p className="text-muted-foreground">Automated tax liability tracking and filing</p>
                </div>
                <GradientButton
                    className="flex items-center justify-center gap-2 whitespace-nowrap"
                    onClick={() => alert("Tax Filing initiated to GST Portal successfully.")}
                >
                    <FileText size={16} /> File Returns
                </GradientButton>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <GlassCard className="p-6">
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-muted-foreground text-sm">Total Tax Liability</span>
                        <DollarSign className="text-blue-500 w-5 h-5" />
                    </div>
                    <h3 className="text-2xl font-bold text-foreground">₹{taxSummary.total_liability.toLocaleString()}</h3>
                </GlassCard>
                <GlassCard className="p-6">
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-gray-400 text-sm">Tax Paid</span>
                        <CheckCircle className="text-green-500 w-5 h-5" />
                    </div>
                    <h3 className="text-2xl font-bold text-green-500">₹{taxSummary.paid.toLocaleString()}</h3>
                </GlassCard>
                <GlassCard className="p-6">
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-gray-400 text-sm">Pending Due</span>
                        <AlertCircle className="text-red-500 w-5 h-5" />
                    </div>
                    <h3 className="text-2xl font-bold text-red-500">₹{taxSummary.pending.toLocaleString()}</h3>
                </GlassCard>
                <GlassCard className="p-6">
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-muted-foreground text-sm">Next Due Date</span>
                        <Calendar className="text-yellow-500 w-5 h-5" />
                    </div>
                    <h3 className="text-2xl font-bold text-foreground">{taxSummary.next_due}</h3>
                </GlassCard>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-gray-200 dark:border-gray-800 pb-2">
                {[
                    { id: 'gst', label: 'GST Returns' },
                    { id: 'tds', label: 'TDS Filing' },
                    { id: 'income_tax', label: 'Income Tax' }
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2 font-medium transition-all relative ${activeTab === tab.id
                            ? 'text-primary'
                            : 'text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        {tab.label}
                        {activeTab === tab.id && (
                            <div
                                layoutId="activeTaxTab"
                                className="absolute bottom-[-9px] left-0 right-0 h-0.5 bg-blue-500"
                            />
                        )}
                    </button>
                ))}
            </div>

            {/* Content Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Visual */}
                <div className="lg:col-span-2">
                    <GlassCard className="p-6 h-full">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                                {activeTab === 'gst' ? 'GST Liability vs Credit' :
                                    activeTab === 'tds' ? 'TDS Category Breakdown' : 'Tax Projection'}
                            </h3>
                        </div>
                        <div className="h-[350px]">
                            {activeTab === 'gst' && <Line data={gstData} options={chartOptions} />}
                            {activeTab === 'tds' && (
                                <div className="flex items-center justify-center h-full">
                                    <div className="w-[300px] h-[300px]">
                                        <Doughnut data={tdsData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }} />
                                    </div>
                                </div>
                            )}
                            {activeTab === 'income_tax' && (
                                <div className="flex items-center justify-center h-full text-gray-500">
                                    Advance Tax Projection Chart (Data coming soon)
                                </div>
                            )}
                        </div>
                    </GlassCard>
                </div>

                {/* Right Side: Calculation / Breakdown */}
                <div className="lg:col-span-1 space-y-6">
                    <GlassCard className="p-6">
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Detailed Calculation</h3>
                        <div className="space-y-4 text-sm">
                            <div className="flex justify-between py-2 border-b border-border">
                                <span className="text-muted-foreground">Gross Revenue</span>
                                <span className="text-foreground font-medium">₹12,45,000</span>
                            </div>
                            <div className="flex justify-between py-2 border-b border-border">
                                <span className="text-muted-foreground">Taxable Amount</span>
                                <span className="text-foreground font-medium">₹10,50,000</span>
                            </div>
                            <div className="flex justify-between py-2 border-b border-border">
                                <span className="text-muted-foreground">Applicable Rate</span>
                                <span className="text-foreground font-medium">18%</span>
                            </div>
                            <div className="flex justify-between py-2 pt-4">
                                <span className="text-foreground font-bold">Total Tax</span>
                                <span className="text-blue-500 font-bold">₹1,89,000</span>
                            </div>
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6 bg-blue-50 dark:bg-blue-900/10">
                        <div className="flex items-start gap-3">
                            <AlertCircle className="text-blue-500 mt-1" size={20} />
                            <div>
                                <h4 className="font-bold text-blue-700 dark:text-blue-200">Compliance Tip</h4>
                                <p className="text-sm text-blue-600 dark:text-blue-300 mt-1">
                                    File your GSTR-1 by the 11th to avoid penalties. You have pending invoices.
                                </p>
                            </div>
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
};

export default TaxCompliance;
