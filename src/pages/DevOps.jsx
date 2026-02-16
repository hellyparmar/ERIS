import React from 'react';
import {
    GitBranch,
    Play,
    CheckCircle,
    XCircle,
    Clock,
    RotateCcw,
    FileText,
    Package,
    Server,
    Activity,
    AlertCircle,
    TrendingUp,
    Download
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const DevOps = () => {

    // Mock data
    const pipelines = [
        {
            id: 1,
            name: 'Production Deploy',
            status: 'success',
            stages: [
                { name: 'Test', status: 'success', duration: '2m 15s' },
                { name: 'Build', status: 'success', duration: '3m 24s' },
                { name: 'Deploy', status: 'success', duration: '1m 45s' }
            ],
            triggeredBy: 'admin@rdios.com',
            commit: 'feat: Add new analytics features',
            commitHash: 'a1b2c3d',
            timestamp: '2026-02-02 07:30:15'
        },
        {
            id: 2,
            name: 'Staging Deploy',
            status: 'running',
            stages: [
                { name: 'Test', status: 'success', duration: '2m 10s' },
                { name: 'Build', status: 'running', duration: '1m 30s' },
                { name: 'Deploy', status: 'pending', duration: '-' }
            ],
            triggeredBy: 'developer@rdios.com',
            commit: 'fix: Resolve dashboard API issues',
            commitHash: 'e4f5g6h',
            timestamp: '2026-02-02 09:15:42'
        }
    ];

    const deployments = [
        { id: 1, env: 'Production', version: 'v5.0.1', status: 'success', deployedBy: 'admin@rdios.com', timestamp: '2h ago', commit: 'a1b2c3d' },
        { id: 2, env: 'Staging', version: 'v5.0.2', status: 'success', deployedBy: 'developer@rdios.com', timestamp: '30m ago', commit: 'e4f5g6h' },
        { id: 3, env: 'Development', version: 'v5.1.0-dev', status: 'success', deployedBy: 'developer@rdios.com', timestamp: '15m ago', commit: 'i7j8k9l' },
        { id: 4, env: 'Production', version: 'v5.0.0', status: 'success', deployedBy: 'admin@rdios.com', timestamp: '1d ago', commit: 'm0n1o2p' }
    ];

    const environments = [
        { name: 'Production', status: 'healthy', version: 'v5.0.1', uptime: '99.98%', lastDeploy: '2h ago', instances: 3 },
        { name: 'Staging', status: 'healthy', version: 'v5.0.2', uptime: '99.95%', lastDeploy: '30m ago', instances: 2 },
        { name: 'Development', status: 'healthy', version: 'v5.1.0-dev', uptime: '99.90%', lastDeploy: '15m ago', instances: 1 }
    ];

    const buildMetrics = {
        testCoverage: 85,
        buildTime: '3m 24s',
        dockerImageSize: '245 MB',
        successRate: 94.5,
        avgBuildTime: '3m 12s'
    };

    // Deployment frequency chart data (Recharts format)
    const deploymentChartData = [
        { day: 'Mon', deployments: 3 },
        { day: 'Tue', deployments: 5 },
        { day: 'Wed', deployments: 4 },
        { day: 'Thu', deployments: 6 },
        { day: 'Fri', deployments: 8 },
        { day: 'Sat', deployments: 2 },
        { day: 'Sun', deployments: 1 }
    ];

    const getStatusIcon = (status) => {
        switch (status) {
            case 'success':
                return <CheckCircle className="w-5 h-5 text-green-500" />;
            case 'running':
                return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
            case 'failed':
                return <XCircle className="w-5 h-5 text-red-500" />;
            case 'pending':
                return <Clock className="w-5 h-5 text-gray-500" />;
            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen space-y-8 p-6 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">DevOps Dashboard</h1>
                    <p className="text-muted-foreground">CI/CD pipelines, deployments, and infrastructure monitoring</p>
                </div>
                <div className="flex gap-3">
                    <GradientButton onClick={() => { }}>
                        <Play className="w-4 h-4 mr-2" />
                        Trigger Deploy
                    </GradientButton>
                </div>
            </div>

            {/* Build Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-blue-500/20">
                            <Activity className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Test Coverage</p>
                            <p className="text-2xl font-bold gradient-text">{buildMetrics.testCoverage}%</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-green-500/20">
                            <Clock className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Build Time</p>
                            <p className="text-2xl font-bold gradient-text">{buildMetrics.buildTime}</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-purple-500/20">
                            <Package className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Image Size</p>
                            <p className="text-2xl font-bold gradient-text">{buildMetrics.dockerImageSize}</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-amber-500/20">
                            <TrendingUp className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Success Rate</p>
                            <p className="text-2xl font-bold gradient-text">{buildMetrics.successRate}%</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-pink-500/20">
                            <GitBranch className="w-5 h-5 text-pink-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Avg Build</p>
                            <p className="text-2xl font-bold gradient-text">{buildMetrics.avgBuildTime}</p>
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* CI/CD Pipelines */}
            <GlassCard className="p-6">
                <h3 className="text-xl font-bold gradient-text mb-6">Active CI/CD Pipelines</h3>
                <div className="space-y-6">
                    {pipelines.map((pipeline) => (
                        <div key={pipeline.id} className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <div className="flex items-center gap-3 mb-2">
                                        <h4 className="font-bold text-foreground">{pipeline.name}</h4>
                                        {getStatusIcon(pipeline.status)}
                                    </div>
                                    <p className="text-sm text-muted-foreground">{pipeline.commit}</p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        <code className="bg-black/20 px-2 py-0.5 rounded">{pipeline.commitHash}</code>
                                        {' '} by {pipeline.triggeredBy} • {pipeline.timestamp}
                                    </p>
                                </div>
                                <div className="flex gap-2">
                                    <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                        <FileText className="w-4 h-4 text-blue-400" />
                                    </button>
                                    <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                        <RotateCcw className="w-4 h-4 text-amber-400" />
                                    </button>
                                </div>
                            </div>

                            {/* Pipeline Stages */}
                            <div className="flex gap-4">
                                {pipeline.stages.map((stage, idx) => (
                                    <div key={idx} className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            {getStatusIcon(stage.status)}
                                            <span className="text-sm font-medium text-foreground">{stage.name}</span>
                                        </div>
                                        <div className="h-2 bg-black/20 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full transition-all ${stage.status === 'success' ? 'bg-green-500 w-full' :
                                                    stage.status === 'running' ? 'bg-blue-500 w-2/3 animate-pulse' :
                                                        stage.status === 'failed' ? 'bg-red-500 w-full' :
                                                            'bg-gray-500 w-0'
                                                    }`}
                                            />
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">{stage.duration}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </GlassCard>

            {/* Environments & Deployment History */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Environments */}
                <GlassCard className="p-6">
                    <h3 className="text-xl font-bold gradient-text mb-6">Environments</h3>
                    <div className="space-y-3">
                        {environments.map((env) => (
                            <div key={env.name} className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 hover:from-primary/10 hover:to-purple/10 transition-all">
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <h4 className="font-bold text-foreground">{env.name}</h4>
                                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-500/10 text-green-500">
                                                <CheckCircle className="w-3 h-3" />
                                                {env.status}
                                            </span>
                                        </div>
                                        <p className="text-xs text-muted-foreground">Version: {env.version}</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <button className="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 text-xs font-semibold transition-colors">
                                            Deploy
                                        </button>
                                        <button className="px-3 py-1 rounded-lg bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 text-xs font-semibold transition-colors">
                                            Rollback
                                        </button>
                                    </div>
                                </div>
                                <div className="grid grid-cols-3 gap-4 text-xs">
                                    <div>
                                        <p className="text-muted-foreground">Uptime</p>
                                        <p className="font-bold text-green-400">{env.uptime}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Instances</p>
                                        <p className="font-bold text-foreground">{env.instances}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Last Deploy</p>
                                        <p className="font-bold text-foreground">{env.lastDeploy}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassCard>

                {/* Deployment Frequency */}
                <GlassCard className="p-6">
                    <h3 className="text-xl font-bold gradient-text mb-6">Deployment Frequency</h3>
                    <div style={{ height: '250px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={deploymentChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis dataKey="day" stroke="#94a3b8" />
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
                                    dataKey="deployments"
                                    stroke="rgb(102, 126, 234)"
                                    strokeWidth={2}
                                    fill="rgba(102, 126, 234, 0.1)"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                        <div>
                            <p className="text-xs text-muted-foreground">This Week</p>
                            <p className="text-2xl font-bold gradient-text">29</p>
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Last Week</p>
                            <p className="text-2xl font-bold text-muted-foreground">24</p>
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Avg/Week</p>
                            <p className="text-2xl font-bold text-muted-foreground">26</p>
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* Deployment History */}
            <GlassCard className="p-6">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold gradient-text">Deployment History</h3>
                    <GradientButton onClick={() => { }}>
                        <Download className="w-4 h-4 mr-2" />
                        Export Logs
                    </GradientButton>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-border">
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Environment</th>
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Version</th>
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Commit</th>
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Deployed By</th>
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Time</th>
                                <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Status</th>
                                <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {deployments.map((deploy) => (
                                <tr key={deploy.id} className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5">
                                    <td className="py-4 px-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${deploy.env === 'Production' ? 'bg-green-500/20 text-green-400' :
                                            deploy.env === 'Staging' ? 'bg-blue-500/20 text-blue-400' :
                                                'bg-purple-500/20 text-purple-400'
                                            }`}>
                                            {deploy.env}
                                        </span>
                                    </td>
                                    <td className="py-4 px-4 font-mono text-sm text-foreground">{deploy.version}</td>
                                    <td className="py-4 px-4">
                                        <code className="text-xs bg-black/20 px-2 py-1 rounded">{deploy.commit}</code>
                                    </td>
                                    <td className="py-4 px-4 text-sm text-muted-foreground">{deploy.deployedBy}</td>
                                    <td className="py-4 px-4 text-sm text-muted-foreground">{deploy.timestamp}</td>
                                    <td className="py-4 px-4">
                                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-green-500/10 text-green-500">
                                            <CheckCircle className="w-3 h-3" />
                                            {deploy.status}
                                        </span>
                                    </td>
                                    <td className="py-4 px-4">
                                        <div className="flex justify-end gap-2">
                                            <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                <FileText className="w-4 h-4 text-blue-400" />
                                            </button>
                                            <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                <RotateCcw className="w-4 h-4 text-amber-400" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </GlassCard>
        </div>
    );
};

export default DevOps;
