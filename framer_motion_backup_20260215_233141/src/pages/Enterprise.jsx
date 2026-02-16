/**
 * Enterprise Retail Intelligence System v3.0
 * ENTERPRISE PAGE - Multi-Store Intelligence
 * 
 * Features:
 * - Interactive Store Grid
 * - Real-time Performance Heatmap
 * - Consolidated Analytics
 */

import React, { useState, useEffect } from 'react';
import { API_BASE } from '../lib/api';
import { useLanguage } from '../hooks/useLanguage';
import { motion } from 'framer-motion';
import { Store, TrendingUp, MapPin, Users, DollarSign, ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { formatCurrency, formatCompactNumber } from '../lib/utils';
import { useToast } from '../components/ui/Toast';
import mockStores from '../data/storeData';

const Enterprise = () => {
    const { t } = useLanguage();
    const { addToast } = useToast();
    const [selectedRegion, setSelectedRegion] = useState('All Regions');

    const [stores, setStores] = useState([]);
    const [loading, setLoading] = useState(true);

    // Safe calculation helpers to prevent NaN
    const getTotalRevenue = () => {
        const total = stores.reduce((acc, s) => acc + (s.revenue || 0), 0);
        return isFinite(total) ? total : 0;
    };

    const getTotalOrders = () => {
        const total = stores.reduce((acc, s) => acc + (s.orders || 0), 0);
        return isFinite(total) ? total : 0;
    };

    const getTotalStaff = () => {
        const total = stores.reduce((acc, s) => acc + (s.staff || 0), 0);
        return isFinite(total) ? total : 0;
    };

    useEffect(() => {
        const fetchStores = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/enterprise/overview`);
                const data = await response.json();

                // Handle error response
                if (data.error || !Array.isArray(data)) {
                    throw new Error(data.error || 'Invalid data format');
                }

                const gradients = [
                    'from-blue-600 to-indigo-700',
                    'from-purple-600 to-pink-700',
                    'from-emerald-600 to-teal-700',
                    'from-orange-600 to-red-700',
                    'from-cyan-600 to-blue-700'
                ];

                const processedStores = data.map((store, index) => ({
                    ...store,
                    gradient: gradients[index % gradients.length]
                }));

                setStores(processedStores);
            } catch (error) {
                console.error("Failed to fetch enterprise data:", error);
                // Fallback to mock data
                setStores(mockStores);
                addToast("Using mock data - real-time sync disabled", "warning");
            } finally {
                setLoading(false);
            }
        };

        fetchStores();
    }, []);

    return (
        <div className="space-y-8 fade-in-up min-h-screen p-6">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row justify-between items-end gap-4">
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent mb-2">Enterprise Overview</h1>
                    <p className="text-muted-foreground">Real-time performance across {stores.length} locations</p>
                </motion.div>

                <div className="flex gap-2 bg-white/5 p-1 rounded-lg">
                    {['All Regions', 'North', 'South', 'East', 'West'].map(region => (
                        <button
                            key={region}
                            onClick={() => setSelectedRegion(region)}
                            className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${selectedRegion === region
                                ? 'bg-blue-600 !text-white shadow-lg'
                                : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                                }`}
                        >
                            {region}
                        </button>
                    ))}
                </div>
            </div>

            {/* High Level Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <GlassCard className="p-5">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-xl bg-green-500/10 dark:bg-green-500/20">
                            <DollarSign size={32} className="text-green-600 dark:text-green-400" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-muted-foreground mb-1">Total Revenue</p>
                            <h3 className="text-xl font-bold text-foreground mb-1">{formatCurrency(getTotalRevenue())}</h3>
                            <div className="flex items-center gap-1 text-green-500 text-xs font-bold">
                                <ArrowUpRight size={14} /> +12.5% vs Last Month
                            </div>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-5">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-xl bg-blue-500/10 dark:bg-blue-500/20">
                            <Activity size={32} className="text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-muted-foreground mb-1">Total Orders</p>
                            <h3 className="text-xl font-bold text-foreground mb-1">{formatCompactNumber(getTotalOrders())}</h3>
                            <div className="flex items-center gap-1 text-blue-500 text-xs font-bold">
                                <ArrowUpRight size={14} /> +8.2% Volume
                            </div>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-5">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-xl bg-purple-500/10 dark:bg-purple-500/20">
                            <Store size={32} className="text-purple-600 dark:text-purple-400" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-muted-foreground mb-1">Active Stores</p>
                            <h3 className="text-xl font-bold text-foreground mb-1">{stores.length}</h3>
                            <div className="flex items-center gap-1 text-purple-500 text-xs font-bold">
                                <MapPin size={14} /> 4 Regions Covered
                            </div>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-5">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-xl bg-orange-500/10 dark:bg-orange-500/20">
                            <Users size={32} className="text-orange-600 dark:text-orange-400" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-muted-foreground mb-1">Total Staff</p>
                            <h3 className="text-xl font-bold text-foreground mb-1">{getTotalStaff()}</h3>
                            <div className="flex items-center gap-1 text-orange-500 text-xs font-bold">
                                <Activity size={14} /> 94% Attendance
                            </div>
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Revenue Distribution */}
                <GlassCard className="p-6">
                    <h3 className="text-lg font-bold text-white mb-4">Revenue Distribution</h3>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={stores} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.1)" />
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#9ca3af', fontSize: 10 }} />
                                <Tooltip
                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                                />
                                <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                                    {stores.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={['#60a5fa', '#34d399', '#f472b6', '#fbbf24', '#a78bfa'][index % 5]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </GlassCard>

                {/* AI Insight */}
                <GlassCard className="p-6 bg-gradient-to-br from-indigo-900/40 to-purple-900/40 shadow-glow-indigo">
                    <div className="flex items-start gap-4">
                        <div className="p-3 rounded-xl bg-indigo-500/20 text-indigo-400">
                            <TrendingUp size={24} />
                        </div>
                        <div>
                            <h3 className="font-bold text-white mb-2">AI Insight</h3>
                            <p className="text-sm text-gray-300 leading-relaxed">
                                Bangalore Hub is outperforming targets by <span className="text-green-400 font-bold">22%</span>.
                                Consider allocating more inventory to South region to maximize Q3 growth.
                            </p>
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* Store Performance Grid */}
            <div className="space-y-6">
                <h2 className="text-2xl font-bold text-foreground mb-4">Store Performance Grid</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {(stores || [])
                        .filter(s => selectedRegion === 'All Regions' || s.region === selectedRegion)
                        .map((store, idx) => (
                            <motion.div
                                key={store.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                            >
                                <GlassCard className="h-full group hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all cursor-pointer overflow-hidden p-0">
                                    <div className="h-32 w-full relative">
                                        <div className={`w-full h-full bg-gradient-to-br ${store.gradient} relative overflow-hidden group-hover:scale-105 transition-transform duration-500`}>
                                            <div className="absolute inset-0 bg-black/10"></div>
                                        </div>
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                                        <div className="absolute bottom-4 left-4">
                                            <h3 className="text-xl font-bold text-white" style={{ color: 'white' }}>{store.name}</h3>
                                            <p className="text-xs text-gray-100 font-medium flex items-center gap-1" style={{ color: '#f3f4f6' }}><MapPin size={12} /> {store.location?.city || 'Unknown'}, {store.location?.state || ''}</p>
                                        </div>
                                        <div className={`absolute top-4 right-4 px-2 py-1 rounded text-xs font-bold ${store.status === 'excellent' ? 'bg-green-500 text-white box-shadow-green' :
                                            store.status === 'good' ? 'bg-blue-500 text-white box-shadow-blue' :
                                                'bg-red-500 text-white box-shadow-red'
                                            }`}>
                                            {store.status?.toUpperCase().replace('_', ' ') || 'UNKNOWN'}
                                        </div>
                                    </div>

                                    <div className="p-5 space-y-4">
                                        <div className="flex justify-between items-end">
                                            <div>
                                                <p className="text-xs text-gray-200 font-medium mb-1">Revenue</p>
                                                <p className="text-2xl font-bold text-white shadow-sm">{formatCurrency(store.revenue)}</p>
                                            </div>
                                            <div className={`text-right ${store.growth >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                                                <p className="text-xs text-gray-200 font-medium mb-1">Growth</p>
                                                <p className="flex items-center gap-1 font-bold text-shadow-sm">
                                                    {store.growth >= 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                                                    {Math.abs(store.growth)}%
                                                </p>
                                            </div>
                                        </div>

                                        {/* Progress Bar */}
                                        <div>
                                            <div className="flex justify-between text-xs text-gray-200 font-medium mb-1">
                                                <span>Target Achievement</span>
                                                <span>{Math.round((store.revenue / store.target) * 100)}%</span>
                                            </div>
                                            <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                                                <div
                                                    className="bg-blue-500 h-full rounded-full"
                                                    style={{ width: `${Math.min((store.revenue / store.target) * 100, 100)}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </GlassCard>
                            </motion.div>
                        ))}
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Enterprise;
