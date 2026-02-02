import React from 'react';
import {
    Activity,
    Server,
    Database,
    Zap,
    DollarSign,
    Clock,
    TrendingDown,
    AlertTriangle,
    CheckCircle,
    Cpu,
    HardDrive,
    Network
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const Monitoring = () => {

    const systemMetrics = {
        cpu: 45,
        memory: 62,
        disk: 38,
        network: 28
    };

    const costOptimization = [
        { service: 'Database', current: 12500, optimized: 9800, savings: 2700, status: 'optimized' },
        { service: 'Storage', current: 8900, optimized: 6500, savings: 2400, status: 'pending' },
        { service: 'Compute', current: 15600, optimized: 13200, savings: 2400, status: 'optimized' },
        { service: 'Network', current: 5400, optimized: 4800, savings: 600, status: 'pending' }
    ];

    const rateLimits = [
        { endpoint: '/api/v1/dashboard', requests: 1245, limit: 5000, status: 'healthy' },
        { endpoint: '/api/v1/analytics', requests: 892, limit: 3000, status: 'healthy' },
        { endpoint: '/api/v1/pos', requests: 2456, limit: 3000, status: 'warning' },
        { endpoint: '/api/v1/auth', requests: 456, limit: 1000, status: 'healthy' }
    ];

    const batchJobs = [
        { id: 1, name: 'Daily Sales Report', status: 'completed', duration: '2m 15s', nextRun: '23:45', lastRun: '2h ago' },
        { id: 2, name: 'Inventory Sync', status: 'running', duration: '1m 30s', nextRun: '00:00', lastRun: 'Running' },
        { id: 3, name: 'Analytics Aggregation', status: 'queued', duration: '-', nextRun: '01:00', lastRun: '1d ago' },
        { id: 4, name: 'Backup Database', status: 'completed', duration: '5m 45s', nextRun: '02:00', lastRun: '4h ago' }
    ];

    // Performance data for Recharts
    const performanceData = [
        { time: '00:00', cpu: 35, memory: 48 },
        { time: '04:00', cpu: 42, memory: 52 },
        { time: '08:00', cpu: 58, memory: 65 },
        { time: '12:00', cpu: 65, memory: 70 },
        { time: '16:00', cpu: 52, memory: 62 },
        { time: '20:00', cpu: 45, memory: 58 }
    ];

    // Resource data for Recharts
    const resourceData = [
        { name: 'CPU', value: systemMetrics.cpu, color: 'rgba(102, 126, 234, 0.8)' },
        { name: 'Memory', value: systemMetrics.memory, color: 'rgba(168, 85, 247, 0.8)' },
        { name: 'Disk', value: systemMetrics.disk, color: 'rgba(16, 185, 129, 0.8)' },
        { name: 'Network', value: systemMetrics.network, color: 'rgba(245, 158, 11, 0.8)' }
    ];

    const totalSavings = costOptimization.reduce((sum, item) => sum + item.savings, 0);

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">System Monitoring</h1>
                    <p className="text-muted-foreground">Infrastructure health, cost optimization, and performance metrics</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/20 text-green-400">
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-sm font-semibold">All Systems Operational</span>
                    </div>
                </div>
            </div>

            {/* System Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-blue-500/20">
                            <Cpu className="w-5 h-5 text-blue-400" />
                        </div>
                        <div className="flex-1">
                            <p className="text-xs text-muted-foreground">CPU Usage</p>
                            <p className="text-2xl font-bold gradient-text">{systemMetrics.cpu}%</p>
                            <div className="h-1 bg-black/20 rounded-full mt-2 overflow-hidden">
                                <div className="h-full bg-blue-500" style={{ width: `${systemMetrics.cpu}%` }} />
                            </div>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-purple-500/20">
                            <Server className="w-5 h-5 text-purple-400" />
                        </div>
                        <div className="flex-1">
                            <p className="text-xs text-muted-foreground">Memory</p>
                            <p className="text-2xl font-bold gradient-text">{systemMetrics.memory}%</p>
                            <div className="h-1 bg-black/20 rounded-full mt-2 overflow-hidden">
                                <div className="h-full bg-purple-500" style={{ width: `${systemMetrics.memory}%` }} />
                            </div>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-green-500/20">
                            <HardDrive className="w-5 h-5 text-green-400" />
                        </div>
                        <div className="flex-1">
                            <p className="text-xs text-muted-foreground">Disk</p>
                            <p className="text-2xl font-bold gradient-text">{systemMetrics.disk}%</p>
                            <div className="h-1 bg-black/20 rounded-full mt-2 overflow-hidden">
                                <div className="h-full bg-green-500" style={{ width: `${systemMetrics.disk}%` }} />
                            </div>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-amber-500/20">
                            <Network className="w-5 h-5 text-amber-400" />
                        </div>
                        <div className="flex-1">
                            <p className="text-xs text-muted-foreground">Network</p>
                            <p className="text-2xl font-bold gradient-text">{systemMetrics.network}%</p>
                            <div className="h-1 bg-black/20 rounded-full mt-2 overflow-hidden">
                                <div className="h-full bg-amber-500" style={{ width: `${systemMetrics.network}%` }} />
                            </div>
                        </div>
                    </div>
                </GlassCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Performance Chart */}
                <GlassCard className="p-6">
                    <h3 className="text-xl font-bold gradient-text mb-4">Performance Trends (24h)</h3>
                    <div style={{ height: '250px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={performanceData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis dataKey="time" stroke="#94a3b8" />
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
                                    dataKey="cpu"
                                    stroke="rgb(102, 126, 234)"
                                    strokeWidth={2}
                                    name="CPU %"
                                />
                                <Line
                                    type="monotone"
                                    dataKey="memory"
                                    stroke="rgb(168, 85, 247)"
                                    strokeWidth={2}
                                    name="Memory %"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </GlassCard>

                {/* Resource Distribution */}
                <GlassCard className="p-6">
                    <h3 className="text-xl font-bold gradient-text mb-4">Resource Distribution</h3>
                    <div style={{ height: '250px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={resourceData}
                                    dataKey="value"
                                    nameKey="name"
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={90}
                                    paddingAngle={2}
                                >
                                    {resourceData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '8px'
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </GlassCard>
            </div>

            {/* Cost Optimization */}
            <GlassCard className="p-6">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-xl font-bold gradient-text">Cost Optimization</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            Potential monthly savings: <span className="font-bold text-green-400">₹{totalSavings.toLocaleString()}</span>
                        </p>
                    </div>
                    <GradientButton onClick={() => { }}>
                        <TrendingDown className="w-4 h-4 mr-2" />
                        Apply Optimizations
                    </GradientButton>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {costOptimization.map((item) => (
                        <div key={item.service} className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <h4 className="font-bold text-foreground">{item.service}</h4>
                                    <p className="text-xs text-muted-foreground">Monthly cost analysis</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${item.status === 'optimized' ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'
                                    }`}>
                                    {item.status === 'optimized' ? 'Optimized' : 'Pending'}
                                </span>
                            </div>
                            <div className="grid grid-cols-3 gap-3 text-xs">
                                <div>
                                    <p className="text-muted-foreground">Current</p>
                                    <p className="font-bold text-foreground">₹{item.current.toLocaleString()}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Optimized</p>
                                    <p className="font-bold text-blue-400">₹{item.optimized.toLocaleString()}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Savings</p>
                                    <p className="font-bold text-green-400">₹{item.savings.toLocaleString()}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </GlassCard>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Rate Limiting */}
                <GlassCard className="p-6">
                    <h3 className="text-xl font-bold gradient-text mb-6">API Rate Limits</h3>
                    <div className="space-y-4">
                        {rateLimits.map((limit) => (
                            <div key={limit.endpoint} className="p-3 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                <div className="flex justify-between items-center mb-2">
                                    <code className="text-sm font-mono text-foreground">{limit.endpoint}</code>
                                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${limit.status === 'healthy' ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'
                                        }`}>
                                        {limit.status}
                                    </span>
                                </div>
                                <div className="flex justify-between text-xs text-muted-foreground mb-2">
                                    <span>{limit.requests.toLocaleString()} / {limit.limit.toLocaleString()} requests</span>
                                    <span>{((limit.requests / limit.limit) * 100).toFixed(1)}%</span>
                                </div>
                                <div className="h-2 bg-black/20 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${limit.status === 'healthy' ? 'bg-green-500' : 'bg-amber-500'}`}
                                        style={{ width: `${(limit.requests / limit.limit) * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassCard>

                {/* Batch Jobs */}
                <GlassCard className="p-6">
                    <h3 className="text-xl font-bold gradient-text mb-6">Batch Processing Queue</h3>
                    <div className="space-y-3">
                        {batchJobs.map((job) => (
                            <div key={job.id} className="p-3 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <h4 className="font-medium text-foreground text-sm">{job.name}</h4>
                                        <p className="text-xs text-muted-foreground">Last run: {job.lastRun}</p>
                                    </div>
                                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${job.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                        job.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                                            'bg-amber-500/20 text-amber-400'
                                        }`}>
                                        {job.status}
                                    </span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-muted-foreground">
                                        <Clock className="w-3 h-3 inline mr-1" />
                                        Next: {job.nextRun}
                                    </span>
                                    {job.duration !== '-' && (
                                        <span className="text-muted-foreground">Duration: {job.duration}</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            </div>
        </div>
    );
};

export default Monitoring;
