import React, { useState } from 'react';
import {
    Shield,
    Key,
    Users,
    Lock,
    Globe,
    FileText,
    CheckCircle,
    XCircle,
    Plus,
    Trash2,
    Eye,
    EyeOff,
    Download,
    AlertTriangle
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';

const Settings = () => {
    const [activeTab, setActiveTab] = useState('oauth');
    const [showSecret, setShowSecret] = useState({});
    const [securityToggles, setSecurityToggles] = useState({
        waf: true,
        csrf: true,
        ipWhitelist: false,
        twoFactor: false,
        sessionTimeout: 30
    });

    // Mock data
    const apiKeys = [
        { id: 1, name: 'Production API', key: 'pk_live_*********************xyz', created: '2026-01-15', expires: '2027-01-15', status: 'active', usage: 12450 },
        { id: 2, name: 'Development API', key: 'pk_test_*********************abc', created: '2026-01-20', expires: '2026-07-20', status: 'active', usage: 3200 },
        { id: 3, name: 'Mobile App', key: 'pk_mobile_*******************def', created: '2026-01-10', expires: '2026-12-31', status: 'active', usage: 8900 }
    ];

    const roles = [
        { id: 1, name: 'Admin', users: 2, permissions: { read: true, write: true, delete: true, admin: true } },
        { id: 2, name: 'Manager', users: 5, permissions: { read: true, write: true, delete: false, admin: false } },
        { id: 3, name: 'Staff', users: 12, permissions: { read: true, write: true, delete: false, admin: false } },
        { id: 4, name: 'Viewer', users: 8, permissions: { read: true, write: false, delete: false, admin: false } }
    ];

    const auditLogs = [
        { id: 1, user: 'admin@rdios.com', action: 'Login', resource: 'System', timestamp: '2026-02-02 09:30:15', status: 'success' },
        { id: 2, user: 'manager@rdios.com', action: 'Update', resource: 'Product #12345', timestamp: '2026-02-02 09:25:42', status: 'success' },
        { id: 3, user: 'staff@rdios.com', action: 'Delete', resource: 'Invoice #INV-001', timestamp: '2026-02-02 09:20:18', status: 'failed' },
        { id: 4, user: 'admin@rdios.com', action: 'Create', resource: 'API Key', timestamp: '2026-02-02 09:15:30', status: 'success' },
        { id: 5, user: 'viewer@rdios.com', action: 'View', resource: 'Dashboard', timestamp: '2026-02-02 09:10:05', status: 'success' }
    ];

    const ipWhitelist = [
        { id: 1, ip: '192.168.1.100', description: 'Office Network', added: '2026-01-15' },
        { id: 2, ip: '10.0.0.50', description: 'VPN Gateway', added: '2026-01-20' }
    ];

    const toggleSecurity = (key) => {
        setSecurityToggles(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const tabs = [
        { id: 'oauth', label: 'OAuth2/JWT', icon: Lock },
        { id: 'apikeys', label: 'API Keys', icon: Key },
        { id: 'rbac', label: 'RBAC', icon: Users },
        { id: 'security', label: 'Security', icon: Shield },
        { id: 'audit', label: 'Audit Logs', icon: FileText }
    ];

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">Security & Admin Settings</h1>
                    <p className="text-muted-foreground">Manage authentication, authorization, and security configurations</p>
                </div>
                <div className="flex gap-3">
                    <GradientButton onClick={() => { }}>
                        <Download className="w-4 h-4 mr-2" />
                        Export Config
                    </GradientButton>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-6 py-3 rounded-lg transition-all whitespace-nowrap ${activeTab === tab.id
                                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                                : 'bg-secondary/50 text-muted-foreground hover:bg-secondary'
                                }`}
                        >
                            <Icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* OAuth2/JWT Configuration */}
            {activeTab === 'oauth' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-4">OAuth2 Configuration</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Provider</label>
                                <select className="input-standard">
                                    <option>Auth0</option>
                                    <option>Firebase</option>
                                    <option>Custom OAuth2</option>
                                    <option>Okta</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Client ID</label>
                                <input
                                    type="text"
                                    placeholder="your-client-id"
                                    className="input-standard"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Client Secret</label>
                                <div className="relative">
                                    <input
                                        type={showSecret.oauth ? 'text' : 'password'}
                                        placeholder="••••••••••••••••••••"
                                        className="input-standard pr-12"
                                    />
                                    <button
                                        onClick={() => setShowSecret(prev => ({ ...prev, oauth: !prev.oauth }))}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                    >
                                        {showSecret.oauth ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Redirect URI</label>
                                <input
                                    type="text"
                                    placeholder="https://yourdomain.com/callback"
                                    className="input-standard"
                                />
                            </div>
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-4">JWT Settings</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Token Expiry</label>
                                <select className="input-standard">
                                    <option>15 minutes</option>
                                    <option>30 minutes</option>
                                    <option>1 hour</option>
                                    <option>24 hours</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">Refresh Token Expiry</label>
                                <select className="input-standard">
                                    <option>7 days</option>
                                    <option>30 days</option>
                                    <option>90 days</option>
                                    <option>Never</option>
                                </select>
                            </div>
                            <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                <div>
                                    <p className="font-medium text-foreground">Enable Refresh Tokens</p>
                                    <p className="text-xs text-muted-foreground">Allow long-lived sessions</p>
                                </div>
                                <button
                                    onClick={() => toggleSecurity('refreshTokens')}
                                    className={`relative w-12 h-6 rounded-full transition-colors ${securityToggles.refreshTokens ? 'bg-green-500' : 'bg-gray-600'
                                        }`}
                                >
                                    <span
                                        className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${securityToggles.refreshTokens ? 'translate-x-6' : ''
                                            }`}
                                    />
                                </button>
                            </div>
                            <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle className="w-5 h-5 text-blue-400 mt-0.5" />
                                    <div>
                                        <p className="text-sm font-medium text-blue-400">Security Recommendation</p>
                                        <p className="text-xs text-blue-300 mt-1">Use short-lived access tokens (15-30 min) with refresh tokens for better security.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </GlassCard>
                </div>
            )}

            {/* API Keys Management */}
            {activeTab === 'apikeys' && (
                <GlassCard className="p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold gradient-text">API Key Management</h3>
                        <GradientButton onClick={() => { }}>
                            <Plus className="w-4 h-4 mr-2" />
                            Generate New Key
                        </GradientButton>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Name</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">API Key</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Created</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Expires</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Usage</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Status</th>
                                    <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {apiKeys.map((key) => (
                                    <tr key={key.id} className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5">
                                        <td className="py-4 px-4 font-medium text-foreground">{key.name}</td>
                                        <td className="py-4 px-4">
                                            <code className="text-xs bg-black/20 px-2 py-1 rounded">{key.key}</code>
                                        </td>
                                        <td className="py-4 px-4 text-muted-foreground text-sm">{key.created}</td>
                                        <td className="py-4 px-4 text-muted-foreground text-sm">{key.expires}</td>
                                        <td className="py-4 px-4 text-muted-foreground text-sm">{key.usage.toLocaleString()} req</td>
                                        <td className="py-4 px-4">
                                            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-green-500/10 text-green-500 border border-green-500/20">
                                                <CheckCircle className="w-3 h-3" />
                                                {key.status}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4">
                                            <div className="flex justify-end gap-2">
                                                <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                    <Eye className="w-4 h-4 text-blue-400" />
                                                </button>
                                                <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                    <Trash2 className="w-4 h-4 text-red-400" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </GlassCard>
            )}

            {/* RBAC */}
            {activeTab === 'rbac' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <GlassCard className="p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold gradient-text">Roles & Permissions</h3>
                            <GradientButton onClick={() => { }}>
                                <Plus className="w-4 h-4 mr-2" />
                                Create Role
                            </GradientButton>
                        </div>
                        <div className="space-y-3">
                            {roles.map((role) => (
                                <div key={role.id} className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 hover:from-primary/10 hover:to-purple/10 transition-all">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <h4 className="font-bold text-foreground">{role.name}</h4>
                                            <p className="text-xs text-muted-foreground">{role.users} users assigned</p>
                                        </div>
                                        <button className="text-blue-400 hover:text-blue-300 text-sm">Edit</button>
                                    </div>
                                    <div className="flex gap-2 flex-wrap">
                                        {role.permissions.read && (
                                            <span className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30">Read</span>
                                        )}
                                        {role.permissions.write && (
                                            <span className="px-2 py-1 rounded text-xs bg-green-500/20 text-green-400 border border-green-500/30">Write</span>
                                        )}
                                        {role.permissions.delete && (
                                            <span className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400 border border-red-500/30">Delete</span>
                                        )}
                                        {role.permissions.admin && (
                                            <span className="px-2 py-1 rounded text-xs bg-purple-500/20 text-purple-400 border border-purple-500/30">Admin</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-6">Permission Matrix</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left py-2 px-3 text-muted-foreground">Module</th>
                                        <th className="text-center py-2 px-3 text-muted-foreground">Read</th>
                                        <th className="text-center py-2 px-3 text-muted-foreground">Write</th>
                                        <th className="text-center py-2 px-3 text-muted-foreground">Delete</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {['Dashboard', 'Analytics', 'Inventory', 'Customers', 'Settings'].map((module) => (
                                        <tr key={module} className="border-b border-border/50">
                                            <td className="py-3 px-3 font-medium text-foreground">{module}</td>
                                            <td className="py-3 px-3 text-center">
                                                <CheckCircle className="w-4 h-4 text-green-500 mx-auto" />
                                            </td>
                                            <td className="py-3 px-3 text-center">
                                                <CheckCircle className="w-4 h-4 text-green-500 mx-auto" />
                                            </td>
                                            <td className="py-3 px-3 text-center">
                                                <XCircle className="w-4 h-4 text-red-500 mx-auto" />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </GlassCard>
                </div>
            )}

            {/* Security Features */}
            {activeTab === 'security' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-6">Security Features</h3>
                        <div className="space-y-4">
                            {[
                                { key: 'waf', label: 'Web Application Firewall (WAF)', desc: 'Protect against common web exploits' },
                                { key: 'csrf', label: 'CSRF Protection', desc: 'Prevent cross-site request forgery attacks' },
                                { key: 'ipWhitelist', label: 'IP Whitelisting', desc: 'Restrict access to specific IP addresses' },
                                { key: 'twoFactor', label: 'Two-Factor Authentication', desc: 'Require 2FA for all admin users' }
                            ].map((feature) => (
                                <div key={feature.key} className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                    <div>
                                        <p className="font-medium text-foreground">{feature.label}</p>
                                        <p className="text-xs text-muted-foreground">{feature.desc}</p>
                                    </div>
                                    <button
                                        onClick={() => toggleSecurity(feature.key)}
                                        className={`relative w-12 h-6 rounded-full transition-colors ${securityToggles[feature.key] ? 'bg-green-500' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span
                                            className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${securityToggles[feature.key] ? 'translate-x-6' : ''
                                                }`}
                                        />
                                    </button>
                                </div>
                            ))}

                            <div className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                <label className="block text-sm font-medium text-foreground mb-3">Session Timeout (minutes)</label>
                                <input
                                    type="range"
                                    min="15"
                                    max="120"
                                    step="15"
                                    value={securityToggles.sessionTimeout}
                                    onChange={(e) => setSecurityToggles(prev => ({ ...prev, sessionTimeout: parseInt(e.target.value) }))}
                                    className="w-full"
                                />
                                <div className="flex justify-between text-xs text-muted-foreground mt-2">
                                    <span>15 min</span>
                                    <span className="font-bold text-primary">{securityToggles.sessionTimeout} min</span>
                                    <span>120 min</span>
                                </div>
                            </div>
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold gradient-text">IP Whitelist</h3>
                            <GradientButton onClick={() => { }}>
                                <Plus className="w-4 h-4 mr-2" />
                                Add IP
                            </GradientButton>
                        </div>
                        <div className="space-y-3">
                            {ipWhitelist.map((item) => (
                                <div key={item.id} className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                    <div>
                                        <p className="font-mono text-sm font-bold text-foreground">{item.ip}</p>
                                        <p className="text-xs text-muted-foreground">{item.description}</p>
                                        <p className="text-xs text-muted-foreground mt-1">Added: {item.added}</p>
                                    </div>
                                    <button className="p-2 hover:bg-red-500/10 rounded-lg transition-colors">
                                        <Trash2 className="w-4 h-4 text-red-400" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </GlassCard>
                </div>
            )}

            {/* Audit Logs */}
            {activeTab === 'audit' && (
                <GlassCard className="p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold gradient-text">Audit Logs</h3>
                        <div className="flex gap-3">
                            <input
                                type="text"
                                placeholder="Search logs..."
                                className="input-standard"
                            />
                            <GradientButton onClick={() => { }}>
                                <Download className="w-4 h-4 mr-2" />
                                Export
                            </GradientButton>
                        </div>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">User</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Action</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Resource</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Timestamp</th>
                                    <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {auditLogs.map((log) => (
                                    <tr key={log.id} className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5">
                                        <td className="py-4 px-4 text-sm text-foreground">{log.user}</td>
                                        <td className="py-4 px-4">
                                            <span className="px-2 py-1 rounded text-xs font-semibold bg-blue-500/20 text-blue-400">
                                                {log.action}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-sm text-muted-foreground">{log.resource}</td>
                                        <td className="py-4 px-4 text-sm text-muted-foreground">{log.timestamp}</td>
                                        <td className="py-4 px-4">
                                            {log.status === 'success' ? (
                                                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-green-500/10 text-green-500">
                                                    <CheckCircle className="w-3 h-3" />
                                                    Success
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-500">
                                                    <XCircle className="w-3 h-3" />
                                                    Failed
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </GlassCard>
            )}
        </div>
    );
};

export default Settings;
