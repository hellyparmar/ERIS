import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bot, LogIn } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

export default function Login() {
  const { login } = useApp()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const health = useQuery({ queryKey: ['health'], queryFn: () => api('/health'), refetchInterval: (q) => (q.state.data?.seeding?.running ? 2000 : false) })
  const seeding = health.data?.seeding
  // demo sign-in shortcuts come from the API: none on an install with real data
  const demo = useQuery({ queryKey: ['demo-accounts', Boolean(seeding?.running)], queryFn: () => api('/auth/demo-accounts'), enabled: health.isSuccess })
  const demoAccounts = demo.data || []

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email, password)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-page">
      <section className="login-hero">
        <div className="brand" style={{ padding: 0 }}>
          <div className="brand-mark">E</div>
          <div><b>ERIS</b><small>Enterprise Retail Intelligence System</small></div>
        </div>
        <div className="stack" style={{ gap: 16 }}>
          <h1>Run every outlet from one place - with forecasts and an AI assistant that speaks plain English.</h1>
          <ul>
            <li>Live dashboard of sales, profit and stock across all outlets</li>
            <li>Demand forecasts that pick the most accurate model automatically</li>
            <li>Reorder suggestions, purchase orders and stock transfers</li>
            <li>Ask questions like “Why was Outlet 3 revenue lower this week?” - every answer shows its source</li>
            <li>Unusual days, suspicious bills and the drivers behind every revenue change</li>
          </ul>
          <p className="small" style={{ color: '#c3c2b7' }}>Runs on a synthetic demo dataset for a fictional chain (Urban Harvest Foods). Demo GST invoices only - not for tax filing.</p>
        </div>
        <p className="small" style={{ color: '#898781' }}><Bot size={14} style={{ verticalAlign: -2 }} /> Built with open-source tools: FastAPI, Prophet, XGBoost, React, optional Ollama.</p>
      </section>
      <section className="login-form">
        <form className="login-card" onSubmit={submit}>
          <div>
            <h1>Sign in</h1>
            <p className="text-2" style={{ marginTop: 4 }}>{demoAccounts.length ? 'Use one of the demo accounts or your own login.' : 'Sign in with your ERIS account.'}</p>
          </div>
          {seeding?.running && (
            <div className="alert info"><div className="spinner" style={{ width: 16, height: 16 }} /><div><b>Preparing demo data…</b><p>{seeding.message} This takes about a minute on first start.</p></div></div>
          )}
          {health.isError && <div className="alert critical"><div><b>Cannot reach the API</b><p>Start it with <span className="kbd">uvicorn app.main:app</span> in the api folder.</p></div></div>}
          <label className="field"><span>Email</span>
            <input className="input" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="field"><span>Password</span>
            <input className="input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div className="alert critical"><div><b>{error}</b></div></div>}
          <button className="btn primary" disabled={busy} style={{ height: 40 }}><LogIn />{busy ? 'Signing in…' : 'Sign in'}</button>
          {demoAccounts.length > 0 && <div className="stack demo-accounts" style={{ gap: 6, marginTop: 6 }}>
            <span className="small muted">Demo accounts (click to fill)</span>
            {demoAccounts.map((d) => (
              <button type="button" key={d.email} className="btn" style={{ height: 'auto', padding: '8px 10px', justifyContent: 'space-between' }}
                onClick={() => { setEmail(d.email); setPassword(d.password) }}>
                <span><b>{d.role}</b><br /><span className="small muted">{d.email}</span></span>
                <span className="small muted">{d.note}</span>
              </button>
            ))}
          </div>}
        </form>
      </section>
    </div>
  )
}
