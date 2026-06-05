import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Activity, TrendingUp, Shield, BarChart3, Zap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading, isAuthenticated } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from);
    }
  }, [isAuthenticated, navigate, location]);

  const DEMO = {
    'admin@rdios.com':   { password: 'admin123',   role: 'admin',   name: 'System Admin' },
    'manager@rdios.com': { password: 'manager123', role: 'manager', name: 'Store Manager' },
    'analyst@rdios.com': { password: 'analyst123', role: 'analyst', name: 'Data Analyst' },
  };

  const fillDemo = (role) => {
    const map = {
      admin:   ['admin@rdios.com',   'admin123'],
      manager: ['manager@rdios.com', 'manager123'],
      analyst: ['analyst@rdios.com', 'analyst123'],
    };
    setEmail(map[role][0]);
    setPassword(map[role][1]);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      // Navigation will be handled by the useEffect above
    } catch (err) {
      console.log('Login error:', err, err?.response?.data);
      setError(err?.response?.data?.detail || err.message || 'Login failed. Check your credentials.');
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '11px 14px',
    background: 'var(--bg-overlay)',
    border: '1px solid var(--border-md)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-primary)',
    fontSize: 14,
    outline: 'none',
    fontFamily: 'inherit',
    transition: 'border-color var(--t-fast)',
  };

  const features = [
    { icon: TrendingUp, text: 'AI-powered sales forecasting with Prophet ML' },
    { icon: BarChart3,  text: 'Multi-outlet analytics across all locations' },
    { icon: Shield,     text: 'GST compliance tracking and invoice automation' },
    { icon: Zap,        text: 'RAG-based AI assistant with live data context' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-canvas)' }}>

      {/* LEFT PANEL */}
      <div style={{
        width: '45%',
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-sm)',
        display: 'flex',
        flexDirection: 'column',
        padding: '52px 56px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Decorative accent circle */}
        <div style={{
          position: 'absolute', top: -80, right: -80,
          width: 280, height: 280, borderRadius: '50%',
          background: 'var(--accent-soft)',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', bottom: -100, left: -60,
          width: 220, height: 220, borderRadius: '50%',
          background: 'var(--accent-soft)',
          opacity: 0.5,
          pointerEvents: 'none',
        }} />

        <div style={{ position: 'relative', zIndex: 1 }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 64 }}>
            <div style={{
              width: 44, height: 44,
              background: 'var(--accent)',
              borderRadius: 12,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Activity size={22} color="var(--text-on-color)" />
            </div>
            <div>
              <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                R-DIOS
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
                Enterprise Intelligence
              </div>
            </div>
          </div>

          {/* Headline */}
          <h2 style={{
            fontSize: 34, fontWeight: 800,
            color: 'var(--text-primary)',
            lineHeight: 1.15,
            letterSpacing: '-0.03em',
            marginBottom: 14,
          }}>
            Retail Intelligence<br />for Modern India
          </h2>
          <p style={{
            fontSize: 15, color: 'var(--text-secondary)',
            lineHeight: 1.65, marginBottom: 52, maxWidth: 340,
          }}>
            AI-driven analytics, multi-outlet management, and GST compliance — all in one platform built for Indian retail.
          </p>

          {/* Features */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
            {features.map(({ icon: Icon, text }) => (
              <div key={text} style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: 'var(--accent-soft)',
                  border: '1px solid var(--accent-border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, marginTop: 1,
                }}>
                  <Icon size={16} color="var(--accent)" />
                </div>
                <span style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{text}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ position: 'relative', zIndex: 1, marginTop: 'auto', paddingTop: 40 }}>
          <div style={{ fontSize: 11, color: 'var(--text-disabled)' }}>
            MSc Big Data Analytics · Built for PetPooja internship context
          </div>
        </div>
      </div>

      {/* RIGHT PANEL — Login form */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 48 }}>
        <div style={{ width: '100%', maxWidth: 380 }}>

          <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: 6 }}>
            Welcome back
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 36 }}>
            Sign in to your R-DIOS account
          </p>

          {/* Demo buttons */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>
              Quick Demo Access
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {['admin', 'manager', 'analyst'].map(role => (
                <button
                  key={role}
                  onClick={() => fillDemo(role)}
                  style={{
                    flex: 1, 
                    padding: '10px 0',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid rgba(245, 197, 24, 0.3)',
                    background: 'var(--bg-surface)',
                    color: 'var(--text-secondary)',
                    fontSize: 12, 
                    fontWeight: 700,
                    cursor: 'pointer', 
                    textTransform: 'capitalize',
                    transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent)';
                    e.currentTarget.style.background = 'linear-gradient(135deg, rgba(245, 197, 24, 0.15), rgba(245, 197, 24, 0.08))';
                    e.currentTarget.style.color = 'var(--accent)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 8px 20px rgba(245, 197, 24, 0.25)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(245, 197, 24, 0.3)';
                    e.currentTarget.style.background = 'var(--bg-surface)';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  {role}
                </button>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
            <div style={{ flex: 1, height: 1, background: 'var(--border-sm)' }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>or</span>
            <div style={{ flex: 1, height: 1, background: 'var(--border-sm)' }} />
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 6 }}>
                Email address
              </label>
              <input
                type="email" value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@rdios.com"
                required style={inputStyle}
                onFocus={e => {
                  e.target.style.borderColor = 'var(--accent)';
                  e.target.style.boxShadow = '0 0 20px rgba(108, 92, 231, 0.3), inset 0 0 0 1px rgba(108, 92, 231, 0.2)';
                  e.target.style.background = 'rgba(108, 92, 231, 0.05)';
                  e.target.style.transform = 'scale(1.01)';
                }}
                onBlur={e => {
                  e.target.style.borderColor = 'var(--border-md)';
                  e.target.style.boxShadow = 'none';
                  e.target.style.background = 'var(--bg-overlay)';
                  e.target.style.transform = 'scale(1)';
                }}
              />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 6 }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPass ? 'text' : 'password'} value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••" required
                  style={{ ...inputStyle, paddingRight: 44 }}
                  onFocus={e => {
                    e.target.style.borderColor = 'var(--accent)';
                    e.target.style.boxShadow = '0 0 20px rgba(108, 92, 231, 0.3), inset 0 0 0 1px rgba(108, 92, 231, 0.2)';
                    e.target.style.background = 'rgba(108, 92, 231, 0.05)';
                    e.target.style.transform = 'scale(1.01)';
                  }}
                  onBlur={e => {
                    e.target.style.borderColor = 'var(--border-md)';
                    e.target.style.boxShadow = 'none';
                    e.target.style.background = 'var(--bg-overlay)';
                    e.target.style.transform = 'scale(1)';
                  }}
                />
                <button type="button" onClick={() => setShowPass(p => !p)} style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2,
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = 'var(--accent)';
                  e.currentTarget.style.transform = 'translateY(-50%) scale(1.2)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--text-muted)';
                  e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
                }}
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div style={{
                padding: '10px 14px', marginBottom: 16,
                background: 'var(--danger-soft)',
                border: '1px solid rgba(231,76,60,0.2)',
                borderRadius: 'var(--radius-md)',
                fontSize: 13, color: 'var(--danger)',
              }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={isLoading} style={{
              width: '100%', 
              padding: '14px',
              fontSize: 14, 
              fontWeight: 700,
              background: isLoading ? 'linear-gradient(135deg, var(--accent-hover), rgba(125, 112, 240, 0.9))' : 'linear-gradient(135deg, var(--accent), rgba(125, 112, 240, 0.95))',
              color: 'var(--text-on-color)',
              border: 'none', 
              borderRadius: 'var(--radius-md)',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
              boxShadow: '0 4px 16px rgba(108, 92, 231, 0.3)',
              position: 'relative',
              overflow: 'hidden',
              letterSpacing: '0.5px',
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 12px 28px rgba(108, 92, 231, 0.45)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 16px rgba(108, 92, 231, 0.3)';
              }
            }}
            >
              {isLoading ? 'Signing in...' : 'Sign in to R-DIOS'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}