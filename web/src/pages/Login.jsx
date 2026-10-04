import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, ArrowRight, Bot, LineChart, LogIn, Receipt, ShieldCheck } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { initialsOf } from '../components/Layout'

const FEATURES = [
  { icon: LineChart, title: 'Forecasts that pick their model', text: 'Prophet, XGBoost, Holt-Winters and more, back-tested on every series' },
  { icon: Bot, title: 'An assistant that shows its work', text: 'Plain-English answers, each with its data source and method' },
  { icon: Activity, title: 'Why numbers moved', text: 'Traffic, basket, promotions, stock-outs and weather, quantified' },
  { icon: Receipt, title: 'Operations in one place', text: 'Billing, stock, purchase orders, demo GST invoices and reports' },
]

const AVATAR_TINTS = ['var(--brand-grad)', 'linear-gradient(135deg,#0ea5e9,#6366f1)', 'linear-gradient(135deg,#10b981,#0ea5e9)',
  'linear-gradient(135deg,#f59e0b,#ef4444)', 'linear-gradient(135deg,#ec4899,#8b5cf6)']

export default function Login() {
  const { login } = useApp()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null)
  const health = useQuery({ queryKey: ['health'], queryFn: () => api('/health'), refetchInterval: (q) => (q.state.data?.seeding?.running ? 2000 : false) })
  const seeding = health.data?.seeding
  // demo sign-in shortcuts come from the API: none on an install with real data
  const demo = useQuery({ queryKey: ['demo-accounts', Boolean(seeding?.running)], queryFn: () => api('/auth/demo-accounts'), enabled: health.isSuccess })
  const demoAccounts = demo.data || []

  const signIn = async (mail, pass, who = 'form') => {
    setBusy(who)
    setError(null)
    try {
      await login(mail, pass)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="login-page">
      <section className="login-hero">
        <div className="brand">
          <div className="brand-mark">E</div>
          <div><b>ERIS</b><small>Enterprise Retail Intelligence System</small></div>
        </div>
        <div className="stack" style={{ gap: 18 }}>
          <span className="badge" style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.08)', color: '#c7d2fe', borderColor: 'rgba(255,255,255,0.12)' }}>
            <ShieldCheck />Open-source retail analytics
          </span>
          <h1>Every outlet, every number - <span className="gradient-text" style={{ backgroundImage: 'linear-gradient(90deg,#a5b4fc,#f0abfc,#7dd3fc)' }}>explained.</span></h1>
          <p className="lead">Sales, stock and customers across your stores, with forecasts you can trust and an assistant that answers in plain English.</p>
          <div className="feature-list">
            {FEATURES.map((f) => (
              <div className="feature" key={f.title}>
                <span className="kpi-icon"><f.icon size={16} /></span>
                <div><b>{f.title}</b><span>{f.text}</span></div>
              </div>
            ))}
          </div>
        </div>
        <div className="stack" style={{ gap: 14 }}>
          <div className="hero-stats">
            <div><b>Multi-outlet</b><span>with role-based access</span></div>
            <div><b>5 models</b><span>compared for every forecast</span></div>
            <div><b>Open source</b><span>no paid APIs required</span></div>
          </div>
          <p className="small" style={{ color: '#7f88a8' }}>Demo data is synthetic, for a fictional chain (Urban Harvest Foods). GST invoices are demos - not for tax filing.</p>
        </div>
      </section>
      <section className="login-form">
        <div className="login-card">
          <div>
            <h1>Welcome back</h1>
            <p className="text-2" style={{ marginTop: 6 }}>{demoAccounts.length ? 'Pick a demo role to explore instantly, or sign in with your account.' : 'Sign in with your ERIS account.'}</p>
          </div>
          {seeding?.running && (
            <div className="alert info"><div className="spinner" style={{ width: 16, height: 16 }} /><div><b>Preparing demo data…</b><p>{seeding.message} This takes about a minute on first start.</p></div></div>
          )}
          {health.isError && <div className="alert critical"><div><b>Cannot reach the ERIS server</b><p>{health.error?.message}</p></div></div>}
          {demoAccounts.length > 0 && (
            <div className="demo-grid demo-accounts" aria-label="Demo accounts">
              {demoAccounts.map((d, i) => (
                <button type="button" key={d.email} className={`demo-account ${busy === d.email ? 'on' : ''}`} disabled={!!busy}
                  onClick={() => { setEmail(d.email); setPassword(d.password); signIn(d.email, d.password, d.email) }}
                  aria-label={`Explore as ${d.role}`}>
                  <span className="initials" style={{ background: AVATAR_TINTS[i % AVATAR_TINTS.length] }}>{initialsOf(d.role)}</span>
                  <span style={{ minWidth: 0 }}><b>{d.role}</b><span>{d.note}</span></span>
                  {busy === d.email ? <span className="spinner go" style={{ width: 16, height: 16 }} /> : <ArrowRight size={16} className="go" />}
                </button>
              ))}
            </div>
          )}
          {demoAccounts.length > 0 && <div className="divider">or use your account</div>}
          <form className="stack" style={{ gap: 12 }} onSubmit={(e) => { e.preventDefault(); signIn(email, password) }}>
            <label className="field"><span>Email</span>
              <input className="input" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" />
            </label>
            <label className="field"><span>Password</span>
              <input className="input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
            </label>
            {error && <div className="alert critical"><div><b>{error}</b></div></div>}
            <button className="btn primary lg block" disabled={!!busy}><LogIn />{busy === 'form' ? 'Signing in…' : 'Sign in'}</button>
          </form>
        </div>
      </section>
    </div>
  )
}
