import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Save, RefreshCw, CheckCircle, AlertCircle, Database, Server, User, Key, Globe, ShoppingCart, CreditCard, ExternalLink } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import '../modern-design.css';

// Mock Organization ID for demo
const ORG_ID = '00000000-0000-0000-0000-000000000001';

const INTEGRATION_TABS = [
    { id: 'odoo', name: 'Odoo ERP', icon: Database, bgClass: 'bg-purple-500', textClass: 'text-white' },
    { id: 'zoho', name: 'Zoho Books', icon: CreditCard, bgClass: 'bg-yellow-500', textClass: 'text-white' },
    { id: 'shopify', name: 'Shopify', icon: ShoppingCart, bgClass: 'bg-green-500', textClass: 'text-white' },
    { id: 'woocommerce', name: 'WooCommerce', icon: Globe, bgClass: 'bg-blue-500', textClass: 'text-white' }
];

const Integrations = () => {
    const [activeTab, setActiveTab] = useState('odoo');
    const [loading, setLoading] = useState(false);
    const [testing, setTesting] = useState(false);
    const [status, setStatus] = useState({ type: '', message: '' });

    // Connections state (persisted connection status)
    const [connections, setConnections] = useState({
        odoo: false,
        zoho: false,
        shopify: false,
        woocommerce: false
    });

    // Dynamic configuration state
    const [configs, setConfigs] = useState({
        odoo: { url: '', db_name: '', username: '', api_key: '', sync_products: true, sync_customers: true },
        zoho: { org_id: '', client_id: '', client_secret: '', sync_invoices: true },
        shopify: { shop_url: '', access_token: '', sync_inventory: true },
        woocommerce: { store_url: '', consumer_key: '', consumer_secret: '', sync_orders: true }
    });

    const [syncInterval, setSyncInterval] = useState('1h');

    const handleConfigChange = (field, value) => {
        setConfigs(prev => ({
            ...prev,
            [activeTab]: {
                ...prev[activeTab],
                [field]: value
            }
        }));
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setStatus({ type: '', message: '' });

        // Simulate API call for different integrations
        setTimeout(() => {
            const isSuccess = Math.random() > 0.1; // 90% success chance
            if (isSuccess) {
                setStatus({
                    type: 'success',
                    message: `Connected to ${INTEGRATION_TABS.find(t => t.id === activeTab)?.name} successfully!`
                });
                setConnections(prev => ({ ...prev, [activeTab]: true }));
            } else {
                setStatus({
                    type: 'error',
                    message: 'Connection failed. Please check your credentials.'
                });
            }
            setTesting(false);
        }, 1500);
    };

    const handleSave = async () => {
        setLoading(true);
        // Simulate save
        setTimeout(() => {
            setStatus({ type: 'success', message: 'Configuration saved successfully!' });
            setLoading(false);
        }, 1000);
    };

    const renderFormFields = () => {
        const config = configs[activeTab];
        const inputClass = "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:border-purple-500 focus:outline-none placeholder-gray-500 dark:placeholder-gray-400";

        switch (activeTab) {
            case 'odoo':
                return (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Connection Details</h3>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-slate-300 flex items-center gap-2"><Server size={14} /> Server URL</label>
                                <input type="text" value={config.url} onChange={(e) => handleConfigChange('url', e.target.value)}
                                    placeholder="https://your-odoo-instance.com" className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-slate-300 flex items-center gap-2"><Database size={14} /> Database Name</label>
                                <input type="text" value={config.db_name} onChange={(e) => handleConfigChange('db_name', e.target.value)}
                                    placeholder="e.g. odoo16_production" className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-slate-300 flex items-center gap-2"><User size={14} /> Email / Username</label>
                                <input type="text" value={config.username} onChange={(e) => handleConfigChange('username', e.target.value)}
                                    placeholder="admin@example.com" className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-slate-300 flex items-center gap-2"><Key size={14} /> API Key / Password</label>
                                <input type="password" value={config.api_key} onChange={(e) => handleConfigChange('api_key', e.target.value)}
                                    placeholder="••••••••" className={inputClass} />
                            </div>
                        </div>
                    </>
                );
            case 'zoho':
                return (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">OAuth Credentials</h3>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-gray-400 block">Organization ID</label>
                                <input type="text" value={config.org_id} onChange={(e) => handleConfigChange('org_id', e.target.value)}
                                    placeholder="e.g. 783291..." className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-gray-400 block">Client ID</label>
                                <input type="text" value={config.client_id} onChange={(e) => handleConfigChange('client_id', e.target.value)}
                                    placeholder="Zoho Client ID" className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-gray-400 block">Client Secret</label>
                                <input type="password" value={config.client_secret} onChange={(e) => handleConfigChange('client_secret', e.target.value)}
                                    placeholder="••••••••" className={inputClass} />
                            </div>
                        </div>
                    </>
                );
            case 'shopify':
                return (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Store Access</h3>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-gray-400 block">Shop URL</label>
                                <input type="text" value={config.shop_url} onChange={(e) => handleConfigChange('shop_url', e.target.value)}
                                    placeholder="my-shop.myshopify.com" className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-gray-400 block">Admin API Access Token</label>
                                <input type="password" value={config.access_token} onChange={(e) => handleConfigChange('access_token', e.target.value)}
                                    placeholder="shpat_..." className={inputClass} />
                            </div>
                        </div>
                    </>
                );
            case 'woocommerce':
                return (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">API Keys</h3>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-gray-400 block">Store URL</label>
                                <input type="text" value={config.store_url} onChange={(e) => handleConfigChange('store_url', e.target.value)}
                                    placeholder="https://..." className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-gray-400 block">Consumer Key</label>
                                <input type="text" value={config.consumer_key} onChange={(e) => handleConfigChange('consumer_key', e.target.value)}
                                    placeholder="ck_..." className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-500 dark:text-gray-400 block">Consumer Secret</label>
                                <input type="password" value={config.consumer_secret} onChange={(e) => handleConfigChange('consumer_secret', e.target.value)}
                                    placeholder="cs_..." className={inputClass} />
                            </div>
                        </div>
                    </>
                );
            default: return null;
        }
    };

    const renderSyncToggles = () => {
        return (
            <div className="pt-4 flex gap-6">
                <label className="flex items-center gap-2 cursor-pointer text-gray-300">
                    <input type="checkbox" checked={true} readOnly className="accent-blue-500 w-4 h-4" />
                    Sync Products
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-gray-300">
                    <input type="checkbox" checked={true} readOnly className="accent-blue-500 w-4 h-4" />
                    Sync Orders
                </label>
            </div>
        );
    };

    const renderGuide = () => {
        switch (activeTab) {
            case 'odoo':
                return (
                    <ul className="space-y-3 text-sm text-gray-400">
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">1</span>Log in to Odoo Database.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">2</span>Go to Profile → Account Security.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">3</span>Generate new API Key.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">4</span>Enter details appropriately.</li>
                    </ul>
                );
            case 'zoho':
                return (
                    <ul className="space-y-3 text-sm text-gray-400">
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">1</span>Go to Zoho Developer Console.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">2</span>Register a new specific Client.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">3</span>Copy Client ID and Secret.</li>
                    </ul>
                );
            case 'shopify':
                return (
                    <ul className="space-y-3 text-sm text-gray-400">
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">1</span>Go to Shopify Admin → Apps.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">2</span>Create a Custom App.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">3</span>Reveal Admin API Access Token.</li>
                    </ul>
                );
            case 'woocommerce':
                return (
                    <ul className="space-y-3 text-sm text-gray-400">
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">1</span>Go to WooCommerce → Settings → Advanced.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">2</span>REST API → Add Key.</li>
                        <li className="flex gap-2"><span className="bg-white/10 w-5 h-5 rounded-full flex items-center justify-center text-xs">3</span>Generate Consumer Key/Secret.</li>
                    </ul>
                );
            default: return null;
        }
    };

    return (
        <div className="min-h-screen p-6 space-y-6 animate-fade-in">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                    Integrations
                </h1>
                <p className="text-muted-foreground">Manage third-party connections and APIs</p>
            </motion.div>

            {/* Top Tabs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {INTEGRATION_TABS.map((tab, idx) => {
                    const isActive = activeTab === tab.id;
                    const isConnected = connections[tab.id];
                    const Icon = tab.icon;
                    return (
                        <motion.button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className={`p-4 rounded-xl border transition-all relative overflow-hidden text-left ${isActive
                                    ? 'bg-gradient-to-br from-primary/10 to-purple/10 border-primary/50 shadow-glow-primary'
                                    : 'bg-card border-border hover:border-primary/30 hover:shadow-lg'
                                }`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <div className={`p-4 rounded-xl ${tab.bgClass} bg-opacity-80 dark:bg-opacity-90 mb-3 flex items-center justify-center shadow-lg`}>
                                    <Icon size={28} className="text-white" strokeWidth={2} />
                                </div>
                                {isConnected && (
                                    <div className="relative">
                                        <CheckCircle size={16} className="text-success relative z-10" />
                                        <span className="absolute inset-0 rounded-full bg-success/20 animate-ping" />
                                    </div>
                                )}
                            </div>
                            <h3 className="font-semibold text-foreground">{tab.name}</h3>
                            <p className="text-xs text-muted-foreground">
                                {isConnected ? (
                                    <span className="text-success font-medium">● Connected</span>
                                ) : (
                                    'Not Configured'
                                )}
                            </p>

                            {isActive && (
                                <motion.div
                                    layoutId="activeTabIndicator"
                                    className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-purple"
                                />
                            )}
                        </motion.button>
                    )
                })}
            </div>

            {/* Main Content Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left: Configuration Form */}
                <div className="lg:col-span-2">
                    <GlassCard variant="gradient" className="p-6 h-full animate-slide-up stagger-1">
                        <div className="mb-6">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    {(() => {
                                        const TabIcon = INTEGRATION_TABS.find(t => t.id === activeTab)?.icon;
                                        return TabIcon ? <TabIcon className="text-gray-400" size={24} /> : null;
                                    })()}
                                    <h2 className="text-xl font-bold text-white">
                                        Configure {INTEGRATION_TABS.find(t => t.id === activeTab)?.name}
                                    </h2>
                                </div>
                                {connections[activeTab] && (
                                    <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-medium border border-green-500/20">
                                        • Active
                                    </span>
                                )}
                            </div>
                            <p className="text-sm text-gray-400">Fill up the information of third-party database to enable real-time sync.</p>
                        </div>

                        {renderFormFields()}
                        {renderSyncToggles()}

                        {/* Status Message */}
                        <AnimatePresence>
                            {status.message && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className={`mt-4 p-3 rounded-lg flex items-center gap-2 text-sm ${status.type === 'success' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}
                                >
                                    {status.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                                    {status.message}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <div className="flex gap-4 mt-8 pt-6 border-t border-white/10">
                            <GradientButton
                                onClick={handleTestConnection}
                                disabled={testing}
                                className="flex-1 flex items-center justify-center gap-2"
                            >
                                {testing ? <RefreshCw className="animate-spin w-4 h-4" /> : <RefreshCw className="w-4 h-4" />}
                                {connections[activeTab] ? 'Test & Reconnect' : 'Connect App'}
                            </GradientButton>

                            <button
                                onClick={handleSave}
                                disabled={loading}
                                className="px-6 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white transition border border-white/10 flex items-center gap-2"
                            >
                                <Save size={16} /> Save
                            </button>
                        </div>
                    </GlassCard>
                </div>

                {/* Right: Info & Status */}
                <div className="space-y-6">
                    <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-2">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Auto-Sync Status</h3>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center p-4 bg-white/5 rounded-lg border border-white/5">
                                <div>
                                    <p className="text-slate-600 dark:text-gray-400 text-sm">Scheduler</p>
                                    <p className="text-green-600 dark:text-green-400 font-medium flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                        Running
                                    </p>
                                </div>
                                <RefreshCw size={20} className="text-gray-500 animate-spin-slow" />
                            </div>

                            <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                                <div className="flex justify-between items-center mb-2">
                                    <p className="text-slate-600 dark:text-gray-400 text-sm">Sync Interval</p>
                                    <select
                                        value={syncInterval}
                                        onChange={(e) => setSyncInterval(e.target.value)}
                                        className="bg-black/30 text-xs text-white border border-white/10 rounded px-2 py-1 focus:outline-none"
                                    >
                                        <option value="30m">30 Mins</option>
                                        <option value="1h">1 Hour</option>
                                        <option value="6h">6 Hours</option>
                                        <option value="24h">24 Hours</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </GlassCard>

                    <GlassCard variant="gradient" className="p-6 animate-slide-up stagger-3">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">How to Connect</h3>
                        {renderGuide()}
                        <div className="mt-6 pt-4 border-t border-white/10">
                            <button
                                onClick={() => addToast("Opening Documentation in new tab...", "success")}
                                className="text-xs text-blue-400 flex items-center gap-1 hover:underline bg-transparent border-none p-0"
                            >
                                <ExternalLink size={12} /> View Documentation
                            </button>
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
};

export default Integrations;
