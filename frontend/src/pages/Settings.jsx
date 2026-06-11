import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Save, LogOut, Eye, EyeOff, Bell, Lock, User, Shield, Trash2, Download, Database, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import api from '../services/api';
import { useToast } from '../contexts/ToastContext';
import '../styles/settings.css';

const Settings = () => {
    const { showToast } = useToast();
    const [activeTab, setActiveTab] = useState('profile');
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        phone: '',
        current_password: '',
        new_password: '',
        confirm_password: '',
    });
    const [notification_settings, setNotificationSettings] = useState({
        email_notifications: true,
        sms_notifications: false,
        push_notifications: true,
        news_and_updates: true,
    });
    const [theme, setTheme] = useState('light');

    // Tally integration state (using useRef to track Tally data without triggering re-renders)
    // State for Tally integration is managed through query and mutation states

    // Load user profile
    useQuery({
        queryKey: ['user-profile'],
        queryFn: () => api.get('/api/v1/settings/profile').then(r => r.data.data || {}),
    });

    // Load notification settings
    useQuery({
        queryKey: ['notifications'],
        queryFn: () => api.get('/api/v1/settings/notifications').then(r => r.data.data || {}),
    });

    // Update profile mutation
    const updateProfileMutation = useMutation({
        mutationFn: (data) => api.put('/api/v1/settings/profile', data),
        onSuccess: () => {
            showToast('Profile updated successfully', 'success');
        },
    });

    // Change password mutation
    const changePasswordMutation = useMutation({
        mutationFn: (data) => api.post('/api/v1/settings/change-password', data),
        onSuccess: () => {
            showToast('Password changed successfully', 'success');
            setFormData(prev => ({...prev, current_password: '', new_password: '', confirm_password: ''}));
        },
    });

    // Check Tally connection status
    const tallyStatusQuery = useQuery({
        queryKey: ['tally-status'],
        queryFn: () => api.get('/api/v1/integrations/tally/status').then(r => r.data),
        refetchInterval: 30000, // Refetch every 30 seconds
    });

    // Sync invoices to Tally mutation
    const syncTallyMutation = useMutation({
        mutationFn: (data) => api.post('/api/v1/integrations/tally/sync-invoices', data),
        onSuccess: (response) => {
            showToast(`Sync complete: ${response.data.message}`, 'success');
        },
        onError: (error) => {
            showToast(`Sync failed: ${error.response?.data?.detail || 'Unknown error'}`, 'error');
        },
    });

    const handleProfileChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleProfileSubmit = (e) => {
        e.preventDefault();
        updateProfileMutation.mutate({
            full_name: formData.full_name,
            email: formData.email,
            phone: formData.phone,
        });
    };

    const handlePasswordSubmit = (e) => {
        e.preventDefault();
        if (formData.new_password !== formData.confirm_password) {
            showToast('Passwords do not match', 'warning');
            return;
        }
        changePasswordMutation.mutate({
            current_password: formData.current_password,
            new_password: formData.new_password,
        });
    };

    const handleNotificationChange = (key) => {
        setNotificationSettings(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    return (
        <div className="settings-page">
            <div className="settings-header">
                <p className="subtitle">Manage your account and preferences</p>
            </div>

            <div className="settings-container">
                <div className="settings-sidebar">
                    <button
                        className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
                        onClick={() => setActiveTab('profile')}
                    >
                        <User size={18} /> Profile
                    </button>
                    <button
                        className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
                        onClick={() => setActiveTab('security')}
                    >
                        <Lock size={18} /> Security
                    </button>
                    <button
                        className={`tab-button ${activeTab === 'notifications' ? 'active' : ''}`}
                        onClick={() => setActiveTab('notifications')}
                    >
                        <Bell size={18} /> Notifications
                    </button>
                    <button
                        className={`tab-button ${activeTab === 'preferences' ? 'active' : ''}`}
                        onClick={() => setActiveTab('preferences')}
                    >
                        <Shield size={18} /> Preferences
                    </button>
                    <button
                        className={`tab-button ${activeTab === 'integrations' ? 'active' : ''}`}
                        onClick={() => setActiveTab('integrations')}
                    >
                        <Database size={18} /> Integrations
                    </button>
                </div>

                <div className="settings-content">
                    {/* Profile Tab */}
                    {activeTab === 'profile' && (
                        <div className="settings-section">
                            <h2>Profile Settings</h2>
                            <form onSubmit={handleProfileSubmit}>
                                <div className="form-group">
                                    <label>Full Name</label>
                                    <input
                                        type="text"
                                        name="full_name"
                                        value={formData.full_name}
                                        onChange={handleProfileChange}
                                        placeholder="Enter your full name"
                                        className="form-input"
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Email Address</label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={formData.email}
                                        onChange={handleProfileChange}
                                        placeholder="Enter your email"
                                        className="form-input"
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Phone Number</label>
                                    <input
                                        type="tel"
                                        name="phone"
                                        value={formData.phone}
                                        onChange={handleProfileChange}
                                        placeholder="Enter your phone number"
                                        className="form-input"
                                    />
                                </div>

                                <button type="submit" className="btn-primary">
                                    <Save size={18} /> Save Changes
                                </button>
                            </form>
                        </div>
                    )}

                    {/* Security Tab */}
                    {activeTab === 'security' && (
                        <div className="settings-section">
                            <h2>Security Settings</h2>
                            <form onSubmit={handlePasswordSubmit}>
                                <div className="form-group">
                                    <label>Current Password</label>
                                    <div className="password-input">
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            name="current_password"
                                            value={formData.current_password}
                                            onChange={handleProfileChange}
                                            placeholder="Enter your current password"
                                            className="form-input"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="show-password-btn"
                                        >
                                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                        </button>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>New Password</label>
                                    <input
                                        type="password"
                                        name="new_password"
                                        value={formData.new_password}
                                        onChange={handleProfileChange}
                                        placeholder="Enter new password"
                                        className="form-input"
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Confirm Password</label>
                                    <input
                                        type="password"
                                        name="confirm_password"
                                        value={formData.confirm_password}
                                        onChange={handleProfileChange}
                                        placeholder="Confirm new password"
                                        className="form-input"
                                    />
                                </div>

                                <button type="submit" className="btn-primary">
                                    <Lock size={18} /> Change Password
                                </button>
                            </form>

                            <div className="settings-section-divider"></div>

                            <h3>Two-Factor Authentication</h3>
                            <p>Add an extra layer of security to your account</p>
                            <button className="btn-secondary">Enable 2FA</button>
                        </div>
                    )}

                    {/* Notifications Tab */}
                    {activeTab === 'notifications' && (
                        <div className="settings-section">
                            <h2>Notification Preferences</h2>

                            <div className="notification-item">
                                <div className="notification-info">
                                    <h3>Email Notifications</h3>
                                    <p>Receive updates via email</p>
                                </div>
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={notification_settings.email_notifications}
                                        onChange={() => handleNotificationChange('email_notifications')}
                                    />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="notification-item">
                                <div className="notification-info">
                                    <h3>SMS Notifications</h3>
                                    <p>Receive updates via SMS</p>
                                </div>
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={notification_settings.sms_notifications}
                                        onChange={() => handleNotificationChange('sms_notifications')}
                                    />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="notification-item">
                                <div className="notification-info">
                                    <h3>Push Notifications</h3>
                                    <p>Receive browser push notifications</p>
                                </div>
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={notification_settings.push_notifications}
                                        onChange={() => handleNotificationChange('push_notifications')}
                                    />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="notification-item">
                                <div className="notification-info">
                                    <h3>News and Updates</h3>
                                    <p>Receive news about new features and updates</p>
                                </div>
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={notification_settings.news_and_updates}
                                        onChange={() => handleNotificationChange('news_and_updates')}
                                    />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <button className="btn-primary">Save Preferences</button>
                        </div>
                    )}

                    {/* Preferences Tab */}
                    {activeTab === 'preferences' && (
                        <div className="settings-section">
                            <h2>General Preferences</h2>

                            <div className="form-group">
                                <label>Theme</label>
                                <select value={theme} onChange={(e) => setTheme(e.target.value)} className="form-input">
                                    <option value="light">Light</option>
                                    <option value="dark">Dark</option>
                                    <option value="auto">Auto</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>Language</label>
                                <select className="form-input">
                                    <option value="en">English</option>
                                    <option value="hi">Hindi</option>
                                </select>
                            </div>

                            <button className="btn-primary">Save Preferences</button>

                            <div className="settings-section-divider"></div>

                            <h3>Account Actions</h3>

                            <div className="action-buttons">
                                <button className="btn-secondary">
                                    <Download size={18} /> Download My Data
                                </button>
                                <button className="btn-danger">
                                    <Trash2 size={18} /> Delete Account
                                </button>
                                <button className="btn-secondary">
                                    <LogOut size={18} /> Logout
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Integrations Tab */}
                    {activeTab === 'integrations' && (
                        <div className="settings-section">
                            <h2>System Integrations</h2>

                            {/* Tally ERP Integration Card */}
                            <div className="integration-card">
                                <div className="integration-header">
                                    <div className="integration-title">
                                        <Database size={24} />
                                        <div>
                                            <h3>Tally ERP Integration</h3>
                                            <p>Sync invoices with Tally accounting software</p>
                                        </div>
                                    </div>
                                    {tallyStatusQuery.isLoading ? (
                                        <div className="status-badge loading">
                                            <Loader size={16} className="spinner" />
                                            <span>Checking...</span>
                                        </div>
                                    ) : tallyStatusQuery.data?.connected ? (
                                        <div className="status-badge connected">
                                            <CheckCircle size={16} />
                                            <span>Connected</span>
                                        </div>
                                    ) : (
                                        <div className="status-badge disconnected">
                                            <AlertCircle size={16} />
                                            <span>Disconnected</span>
                                        </div>
                                    )}
                                </div>

                                <div className="integration-details">
                                    {tallyStatusQuery.isLoading && <p>Checking connection status...</p>}
                                    {tallyStatusQuery.data?.connected && (
                                        <>
                                            <p className="success-message">
                                                ✓ Connected to Tally at {tallyStatusQuery.data.tally_host}:{tallyStatusQuery.data.tally_port}
                                            </p>
                                            <div className="integration-actions">
                                                <button 
                                                    className="btn-primary"
                                                    onClick={() => syncTallyMutation.mutate({ invoices: [] })}
                                                    disabled={syncTallyMutation.isPending}
                                                >
                                                    {syncTallyMutation.isPending ? (
                                                        <>
                                                            <Loader size={18} className="spinner" /> Syncing...
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Download size={18} /> Sync Invoices
                                                        </>
                                                    )}
                                                </button>
                                            </div>
                                        </>
                                    )}
                                    {tallyStatusQuery.data && !tallyStatusQuery.data.connected && (
                                        <>
                                            <p className="error-message">
                                                ✗ {tallyStatusQuery.data.message}
                                            </p>
                                            <div className="integration-help">
                                                <h4>How to connect:</h4>
                                                <ol>
                                                    <li>Ensure Tally ERP is running on your local machine</li>
                                                    <li>Tally's web server should be listening on {tallyStatusQuery.data.tally_host}:{tallyStatusQuery.data.tally_port}</li>
                                                    <li>Check firewall settings to allow local connections</li>
                                                    <li>Refresh this page to check status again</li>
                                                </ol>
                                            </div>
                                            <button 
                                                className="btn-secondary"
                                                onClick={() => tallyStatusQuery.refetch()}
                                            >
                                                Retry Connection
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Settings;
