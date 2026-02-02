import React, { useState } from 'react';
import { Tag, TrendingUp, DollarSign, Users, Calendar, Play, Pause, Edit, BarChart2, Search, Filter, Plus } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Promotions = () => {
    const [statusFilter, setStatusFilter] = useState('active');

    const promotions = [
        { id: 1, code: 'FLASH20', name: '20% Off Flash Sale', type: 'percentage', discount: 20, used: 245, limit: 1000, revenue: 125000, status: 'active', startDate: '2026-01-01', endDate: '2026-01-31', conversion: 12.5 },
        { id: 2, code: 'BOGO50', name: 'Buy 1 Get 1 50% Off', type: 'bogo', discount: 50, used: 89, limit: 500, revenue: 67000, status: 'active', startDate: '2026-01-15', endDate: '2026-02-15', conversion: 15.2 },
        { id: 3, code: 'SAVE500', name: 'Flat ₹500 Off', type: 'fixed', discount: 500, used: 156, limit: 750, revenue: 98000, status: 'active', startDate: '2026-01-10', endDate: '2026-02-10', conversion: 10.8 },
        { id: 4, code: 'WINTER25', name: 'Winter Sale 25%', type: 'percentage', discount: 25, used: 500, limit: 500, revenue: 185000, status: 'expired', startDate: '2025-12-01', endDate: '2025-12-31', conversion: 18.5 }
    ];

    // Campaign data for Recharts
    const campaignData = [
        { week: 'Week 1', revenue: 45000 },
        { week: 'Week 2', revenue: 52000 },
        { week: 'Week 3', revenue: 48000 },
        { week: 'Week 4', revenue: 61000 }
    ];

    const filteredPromotions = statusFilter === 'all' ? promotions : promotions.filter(p => p.status === statusFilter);
    const totalRevenue = promotions.reduce((sum, p) => sum + p.revenue, 0);
    const avgConversion = promotions.reduce((sum, p) => sum + p.conversion, 0) / promotions.length;

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">Promotions Engine</h1>
                    <p className="text-muted-foreground">Manage discounts, coupons, and marketing campaigns</p>
                </div>
                <GradientButton onClick={() => { }}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Promotion
                </GradientButton>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-blue-500/20">
                            <Tag className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Active Campaigns</p>
                            <p className="text-2xl font-bold gradient-text">3</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-green-500/20">
                            <DollarSign className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Total Revenue</p>
                            <p className="text-2xl font-bold gradient-text">₹{(totalRevenue / 100000).toFixed(1)}L</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-purple-500/20">
                            <Users className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Total Redemptions</p>
                            <p className="text-2xl font-bold gradient-text">990</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-amber-500/20">
                            <TrendingUp className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Avg Conversion</p>
                            <p className="text-2xl font-bold gradient-text">{avgConversion.toFixed(1)}%</p>
                        </div>
                    </div>
                </GlassCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Promotions List */}
                <div className="lg:col-span-2">
                    <GlassCard className="p-6">
                        <div className="flex gap-3 mb-6">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                                <input
                                    type="text"
                                    placeholder="Search promotions..."
                                    className="w-full pl-12 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground focus:border-primary focus:outline-none"
                                />
                            </div>
                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground focus:border-primary focus:outline-none"
                            >
                                <option value="all">All Status</option>
                                <option value="active">Active</option>
                                <option value="expired">Expired</option>
                                <option value="paused">Paused</option>
                            </select>
                        </div>

                        <div className="space-y-4">
                            {filteredPromotions.map((promo) => (
                                <div key={promo.id} className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 hover:from-primary/10 hover:to-purple/10 transition-all">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <div className="flex items-center gap-3 mb-1">
                                                <h4 className="font-bold text-foreground">{promo.name}</h4>
                                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${promo.status === 'active' ? 'bg-green-500/20 text-green-400' :
                                                    promo.status === 'expired' ? 'bg-gray-500/20 text-gray-400' :
                                                        'bg-amber-500/20 text-amber-400'
                                                    }`}>
                                                    {promo.status.charAt(0).toUpperCase() + promo.status.slice(1)}
                                                </span>
                                            </div>
                                            <p className="text-sm text-muted-foreground mb-2">
                                                Code: <code className="bg-black/20 px-2 py-0.5 rounded font-mono">{promo.code}</code>
                                            </p>
                                        </div>
                                        <div className="flex gap-2">
                                            <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                <Edit className="w-4 h-4 text-blue-400" />
                                            </button>
                                            <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                {promo.status === 'active' ? (
                                                    <Pause className="w-4 h-4 text-amber-400" />
                                                ) : (
                                                    <Play className="w-4 h-4 text-green-400" />
                                                )}
                                            </button>
                                            <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                <BarChart2 className="w-4 h-4 text-purple-400" />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs mb-3">
                                        <div>
                                            <p className="text-muted-foreground">Type</p>
                                            <p className="font-medium text-foreground capitalize">{promo.type}</p>
                                        </div>
                                        <div>
                                            <p className="text-muted-foreground">Discount</p>
                                            <p className="font-medium text-foreground">
                                                {promo.type === 'fixed' ? `₹${promo.discount}` : `${promo.discount}%`}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-muted-foreground">Used / Limit</p>
                                            <p className="font-medium text-foreground">{promo.used} / {promo.limit}</p>
                                        </div>
                                        <div>
                                            <p className="text-muted-foreground">Revenue</p>
                                            <p className="font-medium text-green-400">₹{promo.revenue.toLocaleString()}</p>
                                        </div>
                                    </div>

                                    <div className="flex justify-between items-center">
                                        <div className="text-xs text-muted-foreground">
                                            <Calendar className="w-3 h-3 inline mr-1" />
                                            {promo.startDate} to {promo.endDate}
                                        </div>
                                        <div className="text-xs">
                                            <span className="text-muted-foreground">Conversion: </span>
                                            <span className="font-bold text-primary">{promo.conversion}%</span>
                                        </div>
                                    </div>

                                    {/* Progress Bar */}
                                    <div className="mt-3">
                                        <div className="h-2 bg-black/20 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                                                style={{ width: `${(promo.used / promo.limit) * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </GlassCard>
                </div>

                {/* Campaign Performance */}
                <div className="space-y-6">
                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-4">Campaign Performance</h3>
                        <div style={{ height: '200px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={campaignData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                    <XAxis dataKey="week" stroke="#94a3b8" />
                                    <YAxis stroke="#94a3b8" />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                            border: '1px solid rgba(255,255,255,0.1)',
                                            borderRadius: '8px'
                                        }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="revenue"
                                        stroke="rgb(102, 126, 234)"
                                        strokeWidth={2}
                                        fill="rgba(102, 126, 234, 0.1)"
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="mt-4 grid grid-cols-2 gap-4 text-center">
                            <div>
                                <p className="text-xs text-muted-foreground">This Month</p>
                                <p className="text-xl font-bold gradient-text">₹2.06L</p>
                            </div>
                            <div>
                                <p className="text-xs text-muted-foreground">Last Month</p>
                                <p className="text-xl font-bold text-muted-foreground">₹1.85L</p>
                            </div>
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-4">Top Performing</h3>
                        <div className="space-y-3">
                            {promotions.slice(0, 3).map((promo, idx) => (
                                <div key={promo.id} className="p-3 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                    <div className="flex items-center gap-3">
                                        <span className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${idx === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                                            idx === 1 ? 'bg-gray-400/20 text-gray-400' :
                                                'bg-orange-500/20 text-orange-400'
                                            }`}>
                                            {idx + 1}
                                        </span>
                                        <div className="flex-1">
                                            <p className="font-medium text-foreground text-sm">{promo.code}</p>
                                            <p className="text-xs text-muted-foreground">{promo.used} redemptions</p>
                                        </div>
                                        <p className="font-bold gradient-text">₹{(promo.revenue / 1000).toFixed(0)}K</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
};

export default Promotions;
