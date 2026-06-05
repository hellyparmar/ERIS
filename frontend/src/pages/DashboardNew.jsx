import React, { useState, useEffect } from 'react';
import { API_BASE } from '@/lib/api';
import {
    Search,
    RefreshCw,
    User,
    ChevronRight,
    ArrowUpRight,
    CheckCircle,
    Clock,
    AlertCircle
} from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import UnifiedCard from '../components/ui/UnifiedCard';
import LoadingNotice from '../components/ui/LoadingNotice';

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const DashboardNew = () => {
    const [realtimeData, setRealtimeData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [username, setUsername] = useState('User');

    // Initial fetch on component mount
    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/v1/dashboard/realtime`);
                const data = await res.json();
                setRealtimeData(data);
                
                // Get username from localStorage
                const user = JSON.parse(localStorage.getItem('rdios-user') || '{}');
                setUsername(user.name || user.username || 'User');
                
                setLoading(false);
            } catch (error) {
                console.error('Failed to fetch realtime data:', error);
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Format currency
    const formatCurrency = (value) => {
        if (!value || value === 0) return '—';
        return `₹${(value / 100000).toFixed(2)}L`;
    };

    // Top Metrics Data for Amber Gradient Cards
    const metricCardsData = [
        {
            id: 'revenue',
            title: 'Total Revenue',
            count: '7',
            value: realtimeData ? formatCurrency(realtimeData.total_revenue) : '—',
        },
        {
            id: 'orders',
            title: 'Active Orders',
            count: '12',
            value: realtimeData ? realtimeData.total_orders?.toLocaleString() || '—' : '—',
        },
        {
            id: 'value',
            title: 'Inventory Value',
            count: '5',
            value: '₹45.2L',
        }
    ];

    // Chart Data with Purple and Amber lines
    const getChartData = (range) => {
        const baseData1 = [50, 120, 150, 140, 200, 220, 300, 280, 350, 320, 400, 450];
        const baseData2 = [40, 90, 110, 100, 160, 180, 220, 200, 260, 240, 310, 340];

        let modifier = 1;
        if (range === '7D') modifier = 0.5;
        if (range === '90D') modifier = 2;

        return {
            labels: ['May 8', 'May 10', 'May 12', 'May 14', 'May 16', 'May 18', 'May 20', 'May 22', 'May 24', 'May 26', 'May 28', 'May 30'],
            datasets: [
                {
                    label: 'Portfolio A',
                    data: baseData1.map(v => v * modifier),
                    borderColor: '#8b5cf6', // Soft Purple
                    backgroundColor: 'rgba(139, 92, 246, 0.08)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointBackgroundColor: '#8b5cf6',
                    pointBorderColor: '#1e1e2e',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Portfolio B',
                    data: baseData2.map(v => v * modifier),
                    borderColor: '#f59e0b', // Warm Amber
                    backgroundColor: 'rgba(245, 158, 11, 0.08)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointBackgroundColor: '#f59e0b',
                    pointBorderColor: '#1e1e2e',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }
            ]
        };
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    usePointStyle: true,
                    boxWidth: 10,
                    boxHeight: 10,
                    padding: 20,
                    font: {
                        size: 12,
                        weight: '500',
                        family: 'Inter, system-ui, sans-serif'
                    },
                    color: '#9090a8',
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: '#1e1e2e',
                titleColor: '#ffffff',
                bodyColor: '#e0e0e8',
                borderColor: '#2a2a3a',
                borderWidth: 1,
                cornerRadius: 8,
                padding: 10,
                titleFont: {
                    size: 12,
                    weight: '600',
                    family: 'Inter, system-ui, sans-serif'
                },
                bodyFont: {
                    size: 11,
                    family: 'Inter, system-ui, sans-serif'
                },
                boxPadding: 6,
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#2a2a3a',
                    drawBorder: false,
                    drawTicks: false,
                },
                ticks: {
                    callback: (value) => `₹${value}`,
                    font: {
                        size: 11,
                        weight: '500',
                        family: 'Inter, system-ui, sans-serif'
                    },
                    color: '#9090a8',
                    padding: 12,
                },
                border: {
                    display: false,
                }
            },
            x: {
                grid: {
                    display: false,
                    drawBorder: false,
                    drawTicks: false,
                },
                ticks: {
                    font: {
                        size: 11,
                        weight: '500',
                        family: 'Inter, system-ui, sans-serif'
                    },
                    color: '#9090a8',
                    padding: 12,
                },
                border: {
                    display: false,
                }
            }
        }
    };

    // Policy records for right sidebar
    const policyRecords = [
        {
            id: 'POL-2024-001',
            title: 'Premium Cover',
            date: 'Valid till: 31 Dec 2024',
            status: 'active',
            action: 'renew'
        },
        {
            id: 'POL-2024-002',
            title: 'Health Plus',
            date: 'Valid till: 15 Nov 2024',
            status: 'pending',
            action: 'pay'
        },
        {
            id: 'POL-2024-003',
            title: 'Term Plan',
            date: 'Expired: 28 Feb 2024',
            status: 'overdue',
            action: 'withdraw'
        }
    ];

    return (
        <div className="min-h-screen p-6" style={{ backgroundColor: '#0f0f1a' }}>
            {/* Loading Overlay */}
            {loading && (
                <div className="fixed inset-0 flex items-center justify-center z-50" style={{ backgroundColor: 'rgba(15, 15, 26, 0.9)' }}>
                    <div className="text-center space-y-4">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
                            <div className="w-8 h-8 border-4 rounded-full animate-spin" style={{ borderColor: '#f59e0b', borderTopColor: 'transparent' }}></div>
                        </div>
                        <div>
                            <p className="text-lg font-semibold text-white">Loading Dashboard</p>
                            <p className="text-sm mt-1 text-[#9090a8]">Fetching real-time data...</p>
                        </div>
                    </div>
                </div>
            )}

            {!loading && (
                <div className="space-y-6 max-w-full">
                    {/* TOP HEADER */}
                    <div className="flex justify-between items-center">
                        {/* Left: Logo/Name & Greeting */}
                        <div className="flex-1">
                            <h1 className="text-3xl font-bold text-white mb-1">Enterprise System</h1>
                            <div className="flex items-baseline gap-2">
                                <p className="text-white font-bold text-xl">Hello, {username}</p>
                                <p className="text-[#9090a8] text-sm">Welcome back to your dashboard</p>
                            </div>
                        </div>

                        {/* Right: Icons */}
                        <div className="flex items-center gap-4">
                            <button className="p-2 hover:bg-[#16161f] rounded-lg transition">
                                <Search size={20} color="#b0b0c8" />
                            </button>
                            <button className="p-2 hover:bg-[#16161f] rounded-lg transition">
                                <RefreshCw size={20} color="#b0b0c8" />
                            </button>
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#f59e0b] to-[#d4832a] flex items-center justify-center cursor-pointer hover:shadow-lg transition">
                                <User size={20} color="white" />
                            </div>
                        </div>
                    </div>

                    {/* METRIC CARDS - Warm Amber Gradients */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {metricCardsData.map((card) => (
                            <div
                                key={card.id}
                                className="relative overflow-hidden rounded-[16px] p-6 h-48 group hover:shadow-xl transition-all cursor-pointer"
                                style={{
                                    background: 'linear-gradient(135deg, #d4832a 0%, #c06b1a 100%)',
                                }}
                            >
                                <div className="relative z-10 flex flex-col justify-between h-full">
                                    {/* Top row: Title + Count + Arrow */}
                                    <div className="flex justify-between items-start">
                                        <div className="flex items-center gap-3">
                                            <h3 className="text-white font-bold text-base">{card.title}</h3>
                                            <span className="bg-white/20 px-2 py-0.5 rounded-md text-white text-xs font-semibold">({card.count})</span>
                                        </div>
                                        <ChevronRight size={20} color="white" className="group-hover:translate-x-1 transition" />
                                    </div>

                                    {/* Bottom: Large Value */}
                                    <div>
                                        <p className="text-white font-bold text-3xl">{card.value}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* MAIN LAYOUT - Chart + Bottom Panels */}
                    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
                        {/* Chart Section - 3/4 width */}
                        <div className="xl:col-span-3">
                            <div className="bg-[#1e1e2e] rounded-[16px] p-6">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-white font-bold text-lg">Portfolio / Stats</h3>
                                    <div className="text-sm text-[#9090a8]">
                                        Last 30 days
                                    </div>
                                </div>
                                <div style={{ height: '300px' }}>
                                    <Line data={getChartData('30D')} options={chartOptions} />
                                </div>
                            </div>
                        </div>

                        {/* Right Sidebar - Stacked Policy Cards */}
                        <div className="space-y-4">
                            {policyRecords.map((record) => (
                                <div
                                    key={record.id}
                                    className="bg-[#1e1e2e] rounded-[12px] p-4 relative border border-[#2a2a3a] hover:border-[#3a3a4a] transition"
                                >
                                    {/* Status Badge - Top Left */}
                                    <div className="absolute top-3 left-3">
                                        {record.status === 'active' && (
                                            <div className="flex items-center gap-1.5 bg-[#4ade80]/15 px-2.5 py-1 rounded-full">
                                                <CheckCircle size={12} color="#4ade80" />
                                                <span className="text-xs font-semibold text-[#4ade80]">Active</span>
                                            </div>
                                        )}
                                        {record.status === 'pending' && (
                                            <div className="flex items-center gap-1.5 bg-[#facc15]/15 px-2.5 py-1 rounded-full">
                                                <Clock size={12} color="#facc15" />
                                                <span className="text-xs font-semibold text-[#facc15]">Pending</span>
                                            </div>
                                        )}
                                        {record.status === 'overdue' && (
                                            <div className="flex items-center gap-1.5 bg-[#ef4444]/15 px-2.5 py-1 rounded-full">
                                                <AlertCircle size={12} color="#ef4444" />
                                                <span className="text-xs font-semibold text-[#ef4444]">Overdue</span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Content */}
                                    <div className="pt-8 pb-3">
                                        <p className="text-white font-bold text-sm mb-1">{record.title}</p>
                                        <p className="text-[#9090a8] text-xs">{record.date}</p>
                                    </div>

                                    {/* Action Button */}
                                    <div className="mt-3 pt-3 border-t border-[#2a2a3a]">
                                        {record.action === 'pay' && (
                                            <button className="w-full py-2 bg-[#d4832a] hover:bg-[#c06b1a] text-white text-xs font-semibold rounded-lg transition">
                                                Pay Now
                                            </button>
                                        )}
                                        {record.action === 'renew' && (
                                            <button className="w-full py-2 border border-[#d4832a] text-[#d4832a] text-xs font-semibold rounded-lg hover:bg-[#d4832a]/10 transition">
                                                Renew
                                            </button>
                                        )}
                                        {record.action === 'withdraw' && (
                                            <button className="w-full py-2 border border-[#3a3a4a] text-[#9090a8] text-xs font-semibold rounded-lg hover:border-[#4a4a5a] transition">
                                                Withdraw
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* BOTTOM DATA PANELS */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Left Panel - Transactions */}
                        <div className="bg-[#1e1e2e] rounded-[16px] p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-white font-bold text-lg">Recent Transactions</h3>
                                <span className="text-xs text-[#9090a8] bg-[#2a2a3a] px-3 py-1 rounded-full">Last 7 days</span>
                            </div>
                            <div className="space-y-3">
                                {[
                                    { desc: 'Online Purchase', amount: '₹5,200', type: 'debit' },
                                    { desc: 'Store Credit', amount: '₹10,000', type: 'credit' },
                                    { desc: 'Refund Processed', amount: '₹1,500', type: 'credit' }
                                ].map((tx, idx) => (
                                    <div key={idx} className="flex justify-between items-center py-2.5 border-b border-[#2a2a3a] last:border-0">
                                        <p className="text-[#e0e0e8] text-sm font-medium">{tx.desc}</p>
                                        <p className={`text-sm font-bold ${tx.type === 'debit' ? 'text-[#ef4444]' : 'text-[#4ade80]'}`}>
                                            {tx.type === 'debit' ? '- ' : '+ '}{tx.amount}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Panel - Summary Stats */}
                        <div className="bg-[#1e1e2e] rounded-[16px] p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-white font-bold text-lg">Summary</h3>
                                <span className="text-xs text-[#9090a8] bg-[#2a2a3a] px-3 py-1 rounded-full">This Month</span>
                            </div>
                            <div className="space-y-3">
                                {[
                                    { label: 'Total Transactions', value: '248' },
                                    { label: 'Avg Transaction Size', value: '₹3,250' },
                                    { label: 'Peak Activity', value: '2:30 PM - 4:00 PM' }
                                ].map((stat, idx) => (
                                    <div key={idx} className="flex justify-between items-center py-2.5 border-b border-[#2a2a3a] last:border-0">
                                        <p className="text-[#9090a8] text-sm">{stat.label}</p>
                                        <p className="text-white text-sm font-semibold">{stat.value}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DashboardNew;
