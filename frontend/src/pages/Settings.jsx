import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Save, LogOut, Eye, EyeOff, Bell, Lock, User, Shield, Trash2, Download, Database, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import api from '../lib/api';
import { useToast } from '../contexts/ToastContext';
import SEO from '../components/SEO';

const Settings = () => {
    const { showToast } = useToast();
    const [activeTab, setActiveTab] = useState('profile');
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({
        full_name: '', phone: '',
        current_password: '', new_password: '', confirm_password: '',
    });
    const [notificationSettings, setNotificationSettings] = useState({
        sms_notifications: false,
        push_notifications: true, news_and_updates: true,
    });
    const [theme, setTheme] = useState('light');
    const [seedTaskId, setSeedTaskId] = useState(null);
    const [seedingStatus, setSeedingStatus] = useState(null);
    const [seedMessage, setSeedMessage] = useState('');

    useEffect(() => {
        let interval;
        if (seedTaskId && (seedingStatus === 'pending' || seedingStatus === 'PROGRESS')) {
            interval = setInterval(async () => {
                try {
                    const res = await api.get(`/admin/seed-database/${seedTaskId}`);
                    const data = res.data;
                    setSeedingStatus(data.status);
                    setSeedMessage(data.message);
                    
                    if (data.status === 'SUCCESS' || data.status === 'success' || data.status === 'FAILURE' || data.status === 'failed') {
                        clearInterval(interval);
                        if (data.status === 'SUCCESS' || data.status === 'success') {
                            showToast('Database seeding completed successfully', 'success');
                        } else {
                            showToast(`Seeding failed: ${data.message}`, 'error');
                        }
                    }
                } catch (err) {
                    console.error('Polling error', err);
                }
            }, 3000);
        }
        return () => clearInterval(interval);
    }, [seedTaskId, seedingStatus, showToast]);

    const handleSeedDatabase = async () => {
        try {
            setSeedingStatus('pending');
            setSeedMessage('Starting generation...');
            const res = await api.post('/admin/seed-database');
            setSeedTaskId(res.data.task_id);
        } catch (err) {
            setSeedingStatus('failed');
            setSeedMessage('Failed to start task');
            showToast('Failed to start seeding task', 'error');
        }
    };


    useQuery({
        queryKey: ['user-profile'],
        queryFn: () => api.get('/api/v1/settings/profile').then(r => r.data.data || {}),
    });

    useQuery({
        queryKey: ['notifications'],
        queryFn: () => api.get('/api/v1/settings/notifications').then(r => r.data.data || {}),
    });

    const updateProfileMutation = useMutation({
        mutationFn: (data) => api.put('/api/v1/settings/profile', data),
        onSuccess: () => showToast('Profile updated successfully', 'success'),
    });

    const changePasswordMutation = useMutation({
        mutationFn: (data) => api.post('/api/v1/settings/change-password', data),
        onSuccess: () => {
            showToast('Password changed successfully', 'success');
            setFormData(prev => ({ ...prev, current_password: '', new_password: '', confirm_password: '' }));
        },
    });

    const handleProfileChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleProfileSubmit = (e) => {
        e.preventDefault();
        updateProfileMutation.mutate({ full_name: formData.full_name, phone: formData.phone });
    };

    const handlePasswordSubmit = (e) => {
        e.preventDefault();
        if (formData.new_password !== formData.confirm_password) {
            showToast('Passwords do not match', 'warning');
            return;
        }
        changePasswordMutation.mutate({ current_password: formData.current_password, new_password: formData.new_password });
    };

    const handleNotificationChange = (key) => {
        setNotificationSettings(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const tabs = [
        { id: 'profile', label: 'Profile', icon: <User size={14} /> },
        { id: 'security', label: 'Security', icon: <Lock size={14} /> },
        { id: 'notifications', label: 'Notifications', icon: <Bell size={14} /> },
        { id: 'preferences', label: 'Preferences', icon: <Shield size={14} /> },
        { id: 'database', label: 'Database', icon: <Database size={14} /> },
    ];

    return (
        <>
            <SEO title="System Settings" description="Configure profiles, notification channels, security policies, and sync triggers" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0, minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
                {/* Header */}
                <div style={{
                    padding: '16px 22px',
                    borderBottom: '1px solid var(--c-border)',
                    background: 'var(--c-canvas)'
                }}>
                    <h1 className="page-title" >Settings</h1>
                    <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>Manage your account and preferences</p>
                </div>

                <div style={{ padding: '22px', display: 'flex', gap: 24, alignItems: 'flex-start' }}>
                    {/* Tab Selection */}
                    <div style={{ width: 180, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {tabs.map(tab => {
                            const active = activeTab === tab.id;
                            return (
                                <button key={tab.id}
                                    className="action-btn"
                                    style={{
                                        justifyContent: 'flex-start',
                                        gap: 8,
                                        width: '100%',
                                        background: active ? 'var(--c-dark)' : 'transparent',
                                        color: active ? '#F3E4C9' : 'var(--c-ink)',
                                        border: active ? '1px solid var(--c-dark)' : '1px solid transparent',
                                        fontWeight: active ? 600 : 500
                                    }}
                                    onClick={() => setActiveTab(tab.id)}>
                                    {tab.icon}
                                    <span>{tab.label}</span>
                                </button>
                            );
                        })}
                    </div>

                    {/* Tab Body */}
                    <div style={{ flex: 1, background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', padding: 20 }}>
                        {activeTab === 'profile' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                <div className="zone-label">Profile Settings</div>
                                <form onSubmit={handleProfileSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Full Name</span>
                                        <input type="text" name="full_name" value={formData.full_name} onChange={handleProfileChange} placeholder="Enter your full name" />
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Phone Number</span>
                                        <input type="tel" name="phone" value={formData.phone} onChange={handleProfileChange} placeholder="Enter your phone number" />
                                    </div>
                                    <button type="submit" className="action-btn primary" style={{ alignSelf: 'flex-start', marginTop: 6 }}>
                                        <Save size={13} style={{ marginRight: 6 }} /> Save Changes
                                    </button>
                                </form>
                            </div>
                        )}

                        {activeTab === 'security' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                    <div className="zone-label">Security Settings</div>
                                    <form onSubmit={handlePasswordSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                            <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Current Password</span>
                                            <div style={{ position: 'relative' }}>
                                                <input type={showPassword ? 'text' : 'password'} name="current_password"
                                                    value={formData.current_password} onChange={handleProfileChange}
                                                    placeholder="Enter your current password" style={{ paddingRight: 40 }} />
                                                <button type="button" onClick={() => setShowPassword(!showPassword)}
                                                    style={{ position: 'absolute', right: 4, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-ink-muted)' }}>
                                                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                                                </button>
                                            </div>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                            <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>New Password</span>
                                            <input type="password" name="new_password" value={formData.new_password} onChange={handleProfileChange} placeholder="Enter new password" />
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                            <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Confirm Password</span>
                                            <input type="password" name="confirm_password" value={formData.confirm_password} onChange={handleProfileChange} placeholder="Confirm new password" />
                                        </div>
                                        <button type="submit" className="action-btn primary" style={{ alignSelf: 'flex-start', marginTop: 6 }}>
                                            <Lock size={13} style={{ marginRight: 6 }} /> Change Password
                                        </button>
                                    </form>
                                </div>

                                <div style={{ borderTop: '1px solid var(--c-border)', paddingTop: 16 }}>
                                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-dark)' }}>Two-Factor Authentication</div>
                                    <p style={{ fontSize: 11, color: 'var(--c-ink-muted)', margin: '4px 0 10px 0' }}>
                                        Add an extra layer of security to your retail registry account.
                                    </p>
                                    <button className="action-btn">Enable 2FA</button>
                                </div>
                            </div>
                        )}

                        {activeTab === 'notifications' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                <div className="zone-label">Notification Preferences</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                    {[
                                        { key: 'sms_notifications', label: 'SMS Notifications', desc: 'Receive updates via SMS' },
                                        { key: 'push_notifications', label: 'Push Notifications', desc: 'Receive browser push notifications' },
                                        { key: 'news_and_updates', label: 'News and Updates', desc: 'Receive news about new features' },
                                    ].map(item => (
                                        <div key={item.key} style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            padding: '10px 12px', border: '1px solid var(--c-border)', background: 'var(--c-canvas)'
                                        }}>
                                            <div>
                                                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--c-dark)' }}>{item.label}</div>
                                                <div style={{ fontSize: 11, color: 'var(--c-ink-muted)', marginTop: 2 }}>{item.desc}</div>
                                            </div>
                                            <input type="checkbox" checked={notificationSettings[item.key]}
                                                onChange={() => handleNotificationChange(item.key)} />
                                        </div>
                                    ))}
                                </div>
                                <button className="action-btn primary" style={{ alignSelf: 'flex-start', marginTop: 6 }}>Save Preferences</button>
                            </div>
                        )}

                        {activeTab === 'preferences' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                    <div className="zone-label">General Preferences</div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Theme</span>
                                        <select value={theme} onChange={(e) => setTheme(e.target.value)} style={{ maxWidth: 300 }}>
                                            <option value="light">Light</option>
                                            <option value="dark">Dark</option>
                                            <option value="auto">Auto</option>
                                        </select>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Language</span>
                                        <select style={{ maxWidth: 300 }}>
                                            <option value="en">English</option>
                                            <option value="hi">Hindi</option>
                                        </select>
                                    </div>
                                    <button className="action-btn primary" style={{ alignSelf: 'flex-start', marginTop: 6 }}>Save Preferences</button>
                                </div>

                                <div style={{ borderTop: '1px solid var(--c-border)', paddingTop: 16 }}>
                                    <div className="zone-label" style={{ marginBottom: 12 }}>Account Actions</div>
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                        <button className="action-btn"><Download size={13} style={{ marginRight: 6 }} /> Download My Data</button>
                                        <button className="action-btn" style={{ color: 'var(--c-critical)' }}><Trash2 size={13} style={{ marginRight: 6 }} /> Delete Account</button>
                                        <button className="action-btn"><LogOut size={13} style={{ marginRight: 6 }} /> Logout</button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'database' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                <div className="zone-label">Database Management</div>
                                <div style={{ padding: '16px', background: 'var(--c-canvas)', border: '1px solid var(--c-border)' }}>
                                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--c-dark)', marginBottom: 8 }}>Historical Data Generation</div>
                                    <p style={{ fontSize: 11, color: 'var(--c-ink-muted)', marginBottom: 16 }}>Generate 1-2 years of realistic historical data (Sales, Inventory, Customers) across 5 outlets. This process runs in the background and takes a few minutes.</p>
                                    
                                    <button 
                                        className="action-btn primary" 
                                        onClick={handleSeedDatabase}
                                        disabled={seedingStatus === 'PROGRESS' || seedingStatus === 'pending'}
                                    >
                                        {seedingStatus === 'PROGRESS' || seedingStatus === 'pending' ? <><Loader size={13} className="spin" style={{marginRight: 6}}/> Seeding in progress...</> : 'Seed Historical Data'}
                                    </button>
                                    
                                    {seedMessage && (
                                        <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', fontSize: 12, color: 'var(--c-ink)' }}>
                                            {seedMessage}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
};

export default Settings;
