import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Eye, EyeOff, Languages, Lock, LogOut, Moon, Save, User } from 'lucide-react';

import api from '../lib/api';
import SEO from '../components/SEO';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../hooks/useTheme';
import { useLanguage } from '../hooks/useLanguage';

export default function Settings() {
  const [tab, setTab] = useState('profile');
  const [showPassword, setShowPassword] = useState(false);
  const [profile, setProfile] = useState({ name: '', phone: '' });
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const { showToast } = useToast();
  const { logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const { language, changeLanguage, availableLanguages } = useLanguage();
  const queryClient = useQueryClient();

  const { data: userProfile, isLoading } = useQuery({
    queryKey: ['user-profile'],
    queryFn: () => api.get('/api/v1/settings/profile').then((response) => response.data),
  });

  useEffect(() => {
    if (userProfile) setProfile({ name: userProfile.name || '', phone: userProfile.phone || '' });
  }, [userProfile]);

  const updateProfile = useMutation({
    mutationFn: (data) => api.put('/api/v1/settings/profile', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      showToast('Profile updated', 'success');
    },
    onError: (error) => showToast(error.response?.data?.detail || 'Profile update failed', 'error'),
  });
  const changePassword = useMutation({
    mutationFn: (data) => api.post('/api/v1/settings/change-password', data),
    onSuccess: () => {
      setPasswords({ current_password: '', new_password: '', confirm_password: '' });
      showToast('Password changed', 'success');
    },
    onError: (error) => showToast(error.response?.data?.detail || 'Password change failed', 'error'),
  });

  const submitPassword = (event) => {
    event.preventDefault();
    if (passwords.new_password !== passwords.confirm_password) {
      showToast('New passwords do not match', 'warning');
      return;
    }
    changePassword.mutate({ current_password: passwords.current_password, new_password: passwords.new_password });
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'appearance', label: 'Appearance', icon: Moon },
  ];

  return (
    <div style={{ minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
      <SEO title="Settings" description="Manage your ERIS profile, password, and local display preferences" />
      <div className="content-section" style={{ borderBottom: '1px solid var(--c-border)' }}>
        <h1 className="page-title">Settings</h1>
        <p style={{ fontSize: 11, color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>Account and display preferences</p>
      </div>
      <div style={{ padding: 22, display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        <div style={{ width: 180, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {tabs.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`action-btn ${tab === id ? 'primary' : ''}`} style={{ justifyContent: 'flex-start', gap: 8 }} onClick={() => setTab(id)}>
              <Icon size={14} /> {label}
            </button>
          ))}
        </div>
        <div style={{ flex: 1, maxWidth: 680, background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', padding: 20 }}>
          {tab === 'profile' && (
            <form onSubmit={(event) => { event.preventDefault(); updateProfile.mutate(profile); }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="zone-label">Profile</div>
              {isLoading ? <div className="skeleton-row" /> : <>
                <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <span className="kpi-label">Full name</span>
                  <input value={profile.name} onChange={(event) => setProfile((value) => ({ ...value, name: event.target.value }))} required />
                </label>
                <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <span className="kpi-label">Email</span>
                  <input value={userProfile?.email || ''} disabled />
                </label>
                <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <span className="kpi-label">Phone</span>
                  <input type="tel" value={profile.phone} onChange={(event) => setProfile((value) => ({ ...value, phone: event.target.value }))} />
                </label>
                <button className="action-btn primary" type="submit" disabled={updateProfile.isPending} style={{ alignSelf: 'flex-start' }}>
                  <Save size={13} /> {updateProfile.isPending ? 'Saving…' : 'Save profile'}
                </button>
              </>}
            </form>
          )}
          {tab === 'security' && (
            <form onSubmit={submitPassword} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="zone-label">Change password</div>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span className="kpi-label">Current password</span>
                <div style={{ display: 'flex', gap: 6 }}>
                  <input style={{ flex: 1 }} type={showPassword ? 'text' : 'password'} value={passwords.current_password} onChange={(event) => setPasswords((value) => ({ ...value, current_password: event.target.value }))} required />
                  <button type="button" className="action-btn" onClick={() => setShowPassword((value) => !value)} aria-label="Toggle password visibility">{showPassword ? <EyeOff size={14} /> : <Eye size={14} />}</button>
                </div>
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><span className="kpi-label">New password</span><input type="password" minLength={8} value={passwords.new_password} onChange={(event) => setPasswords((value) => ({ ...value, new_password: event.target.value }))} required /></label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><span className="kpi-label">Confirm new password</span><input type="password" minLength={8} value={passwords.confirm_password} onChange={(event) => setPasswords((value) => ({ ...value, confirm_password: event.target.value }))} required /></label>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="action-btn primary" type="submit" disabled={changePassword.isPending}><Lock size={13} /> Change password</button>
                <button className="action-btn" type="button" onClick={logout}><LogOut size={13} /> Sign out</button>
              </div>
            </form>
          )}
          {tab === 'appearance' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="zone-label">Local display preferences</div>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><span className="kpi-label">Theme</span><select value={theme} onChange={(event) => setTheme(event.target.value)}><option value="light">Light</option><option value="dark">Dark</option><option value="system">System</option></select></label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}><span className="kpi-label"><Languages size={12} /> Language</span><select value={language} onChange={(event) => changeLanguage(event.target.value)}>{availableLanguages.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
              <p style={{ color: 'var(--c-ink-muted)', fontSize: 11, margin: 0 }}>These preferences are stored in this browser.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
