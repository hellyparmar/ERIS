import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bot, LineChart, LogIn, PackageCheck } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

const FEATURES = [
  { icon: LineChart, text: 'Forecasts for every store, product and category' },
  { icon: PackageCheck, text: 'Stock, reorders and purchase orders in one place' },
  { icon: Bot, text: 'Ask questions in plain English, with sources' },
]

export default function Login() {
  const { login } = useApp()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const health = useQuery({ queryKey: ['health'], queryFn: () => api('/health'), refetchInterval: (q) => (q.state.data?.seeding?.running ? 2000 : false) })
  const seeding = health.data?.seeding
  // demo sign-ins come from the API: none on an install with real data
  const demo = useQuery({ queryKey: ['demo-accounts', Boolean(seeding?.running)], queryFn: () => api('/auth/demo-accounts'), enabled: health.isSuccess })
  const demoAccounts = demo.data || []
  const picked = demoAccounts.find((d) => d.email === email)

  const choose = (mail) => {
    const d = demoAccounts.find((x) => x.email === mail)
    setEmail(mail)
    setPassword(d ? d.password : '')
    setError(null)
  }
  const signIn = async (e) => {
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
        <div className="brand">
          <div className="brand-mark">E</div>
          <div><b>ERIS</b><small>Retail intelligence for multi-store grocers</small></div>
        </div>
        <div className="stack" style={{ gap: 18 }}>
          <h1>Every store, every number, <span style={{ color: '#F2C46A' }}>explained.</span></h1>
          <div className="feature-list">
            {FEATURES.map((f) => <div className="feature" key={f.text}><f.icon size={16} /><span>{f.text}</span></div>)}
          </div>
        </div>
        <p className="small" style={{ color: '#BCAE9E' }}>Demo data is synthetic, for a fictional supermarket chain.</p>
      </section>

      <section className="login-form">
        <form className="login-card" onSubmit={signIn}>
          <div>
            <h1>Sign in</h1>
            <p className="text-2" style={{ marginTop: 6 }}>{demoAccounts.length ? 'Pick a demo account or use your own.' : 'Use your ERIS account.'}</p>
          </div>
          {seeding?.running && (
            <div className="alert info"><div className="spinner" style={{ width: 16, height: 16 }} /><div><b>Preparing demo data…</b><p>{seeding.message}</p></div></div>
          )}
          {health.isError && <div className="alert critical"><div><b>Cannot reach the ERIS server</b><p>{health.error?.message}</p></div></div>}
          {demoAccounts.length > 0 && (
            <label className="field"><span>Demo account</span>
              <select className="select" value={picked ? picked.email : ''} onChange={(e) => choose(e.target.value)} aria-label="Demo account">
                <option value="">Choose a role…</option>
                {demoAccounts.map((d) => <option key={d.email} value={d.email}>{d.role} · {d.note}</option>)}
              </select>
            </label>
          )}
          <label className="field"><span>Email</span>
            <input className="input" type="email" autoComplete="username" required value={email} list="demo-emails"
              onChange={(e) => { const v = e.target.value; if (demoAccounts.some((d) => d.email === v)) choose(v); else setEmail(v) }}
              placeholder="you@company.com" />
            <datalist id="demo-emails">{demoAccounts.map((d) => <option key={d.email} value={d.email}>{d.role}</option>)}</datalist>
          </label>
          <label className="field"><span>Password</span>
            <input className="input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div className="alert critical"><div><b>{error}</b></div></div>}
          <button className="btn primary lg block" disabled={busy}><LogIn />{busy ? 'Signing in…' : 'Sign in'}</button>
        </form>
      </section>
    </div>
  )
}
