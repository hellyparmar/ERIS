import React, { useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Save, RefreshCw, CheckCircle, AlertCircle, Database, Server, User, Key, Globe, ShoppingCart, CreditCard, ExternalLink } from 'lucide-react';
import UnifiedCard from '../components/ui/UnifiedCard';
import ActionButton from '../components/ui/ActionButton';

// Mock Organization ID for demo
const ORG_ID = '00000000-0000-0000-0000-000000000001';

const INTEGRATION_TABS = [
    { id: 'odoo', name: 'Odoo ERP', icon: Database, bgClass: 'bg-purple-500', shadowColor: 'rgba(168, 85, 247, 0.5)' },
    { id: 'zoho', name: 'Zoho Books', icon: CreditCard, bgClass: 'bg-yellow-500', shadowColor: 'rgba(234, 179, 8, 0.5)' },
    { id: 'shopify', name: 'Shopify', icon: ShoppingCart, bgClass: 'bg-green-500', shadowColor: 'rgba(34, 197, 94, 0.5)' },
    { id: 'woocommerce', name: 'WooCommerce', icon: Globe, bgClass: 'bg-blue-500', shadowColor: 'rgba(59, 130, 246, 0.5)' }
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
        const inputClass = "w-full bg-background border border-input rounded-lg p-3 text-foreground focus:ring-2 focus:ring-ring focus:outline-none placeholder-muted-foreground transition";

        switch (activeTab) {
            case 'odoo':
                return (
                    <>
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-foreground">Connection Details</h3>
                            <div className="space-y-2">
                                <label className="text-sm text-muted-foreground flex items-center gap-2"><Server size={14} /> Server URL</label>
                                <input type="text" value={config.url} onChange={(e) => handleConfigChange('url', e.target.value)}
                                    placeholder="https://your-odoo-instance.com" className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-muted-foreground flex items-center gap-2"><Database size={14} /> Database Name</label>
                                <input type="text" value={config.db_name} onChange={(e) => handleConfigChange('db_name', e.target.value)}
                                    placeholder="your_database" className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-muted-foreground flex items-center gap-2"><User size={14} /> Username</label>
                                <input type="text" value={config.username} onChange={(e) => handleConfigChange('username', e.target.value)}
                                    placeholder="admin@example.com" className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-muted-foreground flex items-center gap-2"><Key size={14} /> API Key</label>
                                <input type="password" value={config.api_key} onChange={(e) => handleConfigChange('api_key', e.target.value)}
                                    placeholder="••••••••••••••••" className={inputClass} />
                            </div>
                        </div>
                    </>
                );
            case 'zoho':
                return (
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-foreground">Connection Details</h3>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Organization ID</label>
                            <input type="text" value={config.org_id} onChange={(e) => handleConfigChange('org_id', e.target.value)}
                                placeholder="123456789" className={inputClass} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Client ID</label>
                            <input type="text" value={config.client_id} onChange={(e) => handleConfigChange('client_id', e.target.value)}
                                placeholder="1000.XXXXXXXXXXXXXXX" className={inputClass} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Client Secret</label>
                            <input type="password" value={config.client_secret} onChange={(e) => handleConfigChange('client_secret', e.target.value)}
                                placeholder="••••••••••••••••" className={inputClass} />
                        </div>
                    </div>
                );
            case 'shopify':
                return (
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-foreground">Connection Details</h3>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Shop URL</label>
                            <input type="text" value={config.shop_url} onChange={(e) => handleConfigChange('shop_url', e.target.value)}
                                placeholder="your-store.myshopify.com" className={inputClass} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Access Token</label>
                            <input type="password" value={config.access_token} onChange={(e) => handleConfigChange('access_token', e.target.value)}
                                placeholder="shpat_••••••••••••••••" className={inputClass} />
                        </div>
                    </div>
                );
            case 'woocommerce':
                return (
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-foreground">Connection Details</h3>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Store URL</label>
                            <input type="text" value={config.store_url} onChange={(e) => handleConfigChange('store_url', e.target.value)}
                                placeholder="https://your-store.com" className={inputClass} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Consumer Key</label>
                            <input type="text" value={config.consumer_key} onChange={(e) => handleConfigChange('consumer_key', e.target.value)}
                                placeholder="ck_••••••••••••••••" className={inputClass} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Consumer Secret</label>
                            <input type="password" value={config.consumer_secret} onChange={(e) => handleConfigChange('consumer_secret', e.target.value)}
                                placeholder="cs_••••••••••••••••" className={inputClass} />
                        </div>
                    </div>
                );
            default: return null;
        }
    };

    const renderSyncToggles = () => {
        const config = configs[activeTab];
        const toggles = {
            odoo: [
                { key: 'sync_products', label: 'Sync Products' },
                { key: 'sync_customers', label: 'Sync Customers' }
            ],
            zoho: [{ key: 'sync_invoices', label: 'Sync Invoices' }],
            shopify: [{ key: 'sync_inventory', label: 'Sync Inventory' }],
            woocommerce: [{ key: 'sync_orders', label: 'Sync Orders' }]
        };

        return (
            <div className="mt-6 space-y-3">
                <h3 className="text-sm font-semibold text-foreground">Sync Options</h3>
                {toggles[activeTab]?.map(toggle => (
                    <label key={toggle.key} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50 transition">
                        <span className="text-sm text-foreground">{toggle.label}</span>
                        <input
                            type="checkbox"
                            checked={config[toggle.key]}
                            onChange={(e) => handleConfigChange(toggle.key, e.target.checked)}
                            className="w-4 h-4 rounded border-border bg-background checked:bg-primary focus:ring-2 focus:ring-ring"
                        />
                    </label>
                ))}
            </div>
        );
    };

    const renderGuide = () => {
        const guides = {
            odoo: [
                'Log in to Odoo Database.',
                'Go to Profile → Account Security.',
                'Generate new API Key.',
                'Enter details appropriately.'
            ],
            zoho: [
                'Go to Zoho Developer Console.',
                'Register a new specific Client.',
                'Copy Client ID and Secret.'
            ],
            shopify: [
                'Go to Shopify Admin → Apps.',
                'Create a Custom App.',
                'Reveal Admin API Access Token.'
            ],
            woocommerce: [
                'Go to WooCommerce → Settings → Advanced.',
                'REST API → Add Key.',
                'Generate Consumer Key/Secret.'
            ]
        };

        return (
            <ul className="space-y-3 text-sm text-muted-foreground">
                {guides[activeTab]?.map((step, idx) => (
                    <li key={idx} className="flex gap-2">
                        <span className="bg-muted w-5 h-5 rounded-full flex items-center justify-center text-xs text-foreground flex-shrink-0">
                            {idx + 1}
                        </span>
                        <span>{step}</span>
                    </li>
                ))}
            </ul>
        );
    };

    return (
        <div className="min-h-screen space-y-8 p-6">
            {/* Header */}
            <motion.div
                    >
                        {renderFormFields()}
                        {renderSyncToggles()}

                        {/* Status Message */}
                        <AnimatePresence>
                            {status.message && (
                                <motion.div
