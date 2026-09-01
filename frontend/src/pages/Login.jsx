import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Activity, TrendingUp, Shield, BarChart3, Zap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import SEO from '../components/SEO';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading, isAuthenticated } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from);
    }
  }, [isAuthenticated, navigate, location]);

  const fillDemo = (role) => {
    const map = {
      admin:   ['admin',   'admin123'],
      manager: ['manager', 'manager123'],
      analyst: ['analyst', 'analyst123'],
    };
    setUsername(map[role][0]);
    setPassword(map[role][1]);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
    } catch (err) {
      console.log('Login error:', err, err?.response?.data);
      setError(err?.response?.data?.detail || err.message || 'Login failed. Check your credentials.');
    }
  };

  const features = [
    { icon: TrendingUp, text: 'AI-powered sales forecasting with Prophet ML' },
    { icon: BarChart3,  text: 'Multi-outlet analytics across all locations' },
    { icon: Shield,     text: 'GST compliance tracking and invoice automation' },
    { icon: Zap,        text: 'RAG-based AI assistant with live data context' },
  ];

  return (
    <>
      <SEO title="Sign In" description="Sign in to ERIS dashboard." />
      <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--c-canvas)' }}>

      {/* LEFT PANEL */}
      <div style={{
        width: '45%',
        background: 'var(--c-sidebar)',
        borderRight: '1px solid var(--c-border)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: '52px 56px',
        position: 'relative',
        boxSizing: 'border-box',
        textAlign: 'left',
      }}>
        <div>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 44 }}>
            <div style={{
              width: 44, height: 44,
              background: 'var(--c-brown)',
              borderRadius: 'var(--radius)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Activity size={22} color="#F3E4C9" />
            </div>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--f-display)', color: '#F3E4C9', letterSpacing: '-0.02em' }}>
                ERIS
              </div>
              <div style={{ fontSize: 10, color: 'var(--c-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
                Enterprise Intelligence
              </div>
            </div>
          </div>

          {/* Headline */}
          <h2 style={{
            fontSize: 34, fontWeight: 600,
            fontFamily: 'var(--f-display)',
            color: '#F3E4C9',
            lineHeight: 1.15,
            letterSpacing: '-0.03em',
            marginBottom: 14,
          }}>
            Retail Intelligence<br />for Modern India
          </h2>
          <p style={{
            fontSize: 14, color: 'var(--c-muted)',
            lineHeight: 1.65, marginBottom: 44, maxWidth: 340,
          }}>
            AI-driven analytics, multi-outlet management, and GST compliance — all in one platform built for Indian retail.
          </p>

          {/* Features */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {features.map(({ icon: Icon, text }) => (
              <div key={text} style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 'var(--radius)',
                  background: 'rgba(139,94,60,0.15)',
                  border: '1px solid var(--c-border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, marginTop: 1,
                }}>
                  <Icon size={14} color="#8B5E3C" />
                </div>
                <span style={{ fontSize: 13, color: 'var(--c-muted)', lineHeight: 1.5 }}>{text}</span>
              </div>
            ))}
          </div>
        </div>


      </div>

      {/* RIGHT PANEL — Login form */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 48, background: '#FFFFFF' }}>
        <div style={{ width: '100%', maxWidth: 380, textAlign: 'left' }}>

          <div style={{ textAlign: 'center', marginBottom: 36 }}>
            <h1 style={{ fontSize: 28, fontWeight: 600, fontFamily: 'var(--f-display)', color: 'var(--c-dark)', letterSpacing: '-0.02em', marginBottom: 6 }}>
              Welcome back
            </h1>
            <p style={{ fontSize: 14, color: 'var(--c-ink-muted)' }}>
              Sign in to your ERIS account
            </p>
          </div>

          {/* Demo buttons */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 9, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--c-ink-muted)', marginBottom: 10, textAlign: 'center' }}>
              Quick Demo Access
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {['admin', 'manager', 'analyst'].map(role => (
                <button
                  key={role}
                  className="action-btn"
                  onClick={() => fillDemo(role)}
                  style={{
                    flex: 1, 
                    padding: '8px 0',
                    textTransform: 'capitalize',
                    justifyContent: 'center',
                  }}
                >
                  {role}
                </button>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
            <div style={{ flex: 1, height: 1, background: 'var(--c-border)' }} />
            <span style={{ fontSize: 11, color: 'var(--c-ink-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>or</span>
            <div style={{ flex: 1, height: 1, background: 'var(--c-border)' }} />
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#5C4F3D', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                Username
              </label>
              <input
                type="text" value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="your username"
                required
              />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#5C4F3D', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPass ? 'text' : 'password'} value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••" required
                  style={{ paddingRight: 44 }}
                />
                <button type="button" onClick={() => setShowPass(p => !p)} style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-ink-muted)', padding: 2,
                }}
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div style={{
                padding: '10px 14px', marginBottom: 16,
                background: 'var(--c-critical-glow)',
                border: '1px solid var(--c-critical)',
                borderRadius: 'var(--radius)',
                fontSize: 13, color: 'var(--c-critical)',
              }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={isLoading} className="action-btn primary" style={{ width: '100%', padding: '12px' }}>
              {isLoading ? 'Signing in...' : 'Sign in to ERIS'}
            </button>
          </form>
        </div>
      </div>
    </div>
    </>
  );
}