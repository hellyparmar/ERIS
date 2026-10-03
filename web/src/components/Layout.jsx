import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity, BarChart3, Bell, Boxes, Bot, Building2, Contact, FileSpreadsheet, FileText, FlaskConical, History,
  LayoutDashboard, LogOut, Menu, Moon, Package, Receipt, Settings, Store, Sun, TrendingUp, Truck, Upload, Monitor,
} from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date } from '../lib/format'
import { AlertItem } from './ui'

const NAV = [
  { section: 'Overview' },
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/assistant', label: 'AI Assistant', icon: Bot },
  { section: 'Operate' },
  { to: '/sales', label: 'Sales', icon: Receipt },
  { to: '/inventory', label: 'Inventory', icon: Boxes },
  { to: '/products', label: 'Products', icon: Package },
  { to: '/suppliers', label: 'Suppliers & orders', icon: Truck },
  { to: '/customers', label: 'Customers', icon: Contact },
  { to: '/invoices', label: 'Invoices (demo GST)', icon: FileText },
  { section: 'Insights' },
  { to: '/forecasts', label: 'Forecasts', icon: TrendingUp },
  { to: '/models', label: 'Model comparison', icon: FlaskConical },
  { to: '/insights', label: 'Anomalies & drivers', icon: Activity },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/reports', label: 'Reports & export', icon: FileSpreadsheet },
  { section: 'Business' },
  { to: '/outlets', label: 'Outlets', icon: Store },
  { to: '/import', label: 'Data import', icon: Upload, manager: true },
  { to: '/audit', label: 'Audit log', icon: History, admin: true },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function OutletPicker() {
  const { user, outlets, outletId, setOutletId } = useApp()
  if (!user) return null
  const mine = user.role === 'admin' ? outlets : outlets.filter((o) => user.outlet_ids.includes(o.id))
  if (user.role !== 'admin' && mine.length <= 1) {
    return <span className="badge info"><Building2 size={12} />{user.outlet_names?.[0] || 'My outlet'}</span>
  }
  return (
    <select className="select" value={outletId || ''} onChange={(e) => setOutletId(e.target.value ? Number(e.target.value) : null)}
      aria-label="Outlet filter" style={{ maxWidth: 220 }}>
      <option value="">{user.role === 'admin' ? 'All outlets' : 'All my outlets'}</option>
      {mine.map((o) => <option key={o.id} value={o.id}>{o.name}{o.is_active ? '' : ' (inactive)'}</option>)}
    </select>
  )
}

function AlertsBell() {
  const { outletId } = useApp()
  const [open, setOpen] = useState(false)
  const q = useQuery({ queryKey: ['alerts', outletId], queryFn: () => api('/alerts', { params: { outlet_id: outletId } }), staleTime: 120_000 })
  const urgent = (q.data || []).filter((a) => a.severity !== 'info').length
  const navigate = useNavigate()
  return (
    <div style={{ position: 'relative' }}>
      <button className="btn ghost icon" onClick={() => setOpen((o) => !o)} aria-label={`Alerts (${urgent} need attention)`} aria-expanded={open}>
        <Bell />
        {urgent > 0 && <span style={{ position: 'absolute', top: 2, right: 2, background: 'var(--bad)', color: '#fff', borderRadius: 999, fontSize: 10, minWidth: 16, height: 16, display: 'grid', placeItems: 'center', fontWeight: 700 }}>{urgent}</span>}
      </button>
      {open && (
        <>
          <div style={{ position: 'fixed', inset: 0, zIndex: 39 }} onClick={() => setOpen(false)} />
          <div className="card" style={{ position: 'absolute', right: 0, top: 42, width: 360, maxWidth: 'calc(100vw - 32px)', zIndex: 40, maxHeight: 460, overflowY: 'auto' }}>
            <div className="card-head"><h2>Alerts</h2></div>
            <div className="stack">
              {(q.data || []).length === 0 && <span className="muted">No alerts - all good.</span>}
              {(q.data || []).map((a) => (
                <button key={a.id} className="btn ghost" style={{ height: 'auto', padding: 0, textAlign: 'left', display: 'block', whiteSpace: 'normal' }}
                  onClick={() => { setOpen(false); navigate(a.link) }}>
                  <AlertItem alert={a} />
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function ThemeButton() {
  const { theme, setTheme } = useApp()
  const next = { system: 'light', light: 'dark', dark: 'system' }[theme]
  const Icon = theme === 'light' ? Sun : theme === 'dark' ? Moon : Monitor
  return <button className="btn ghost icon" onClick={() => setTheme(next)} aria-label={`Theme: ${theme}. Switch to ${next}`} title={`Theme: ${theme}`}><Icon /></button>
}

export default function Layout() {
  const { user, logout, org, isManager, isAdmin } = useApp()
  const [open, setOpen] = useState(false)
  const location = useLocation()
  useEffect(() => setOpen(false), [location.pathname])
  const sys = useQuery({ queryKey: ['system'], queryFn: () => api('/settings/system'), staleTime: 300_000 })

  return (
    <div className="app">
      <div className={`scrim ${open ? 'open' : ''}`} onClick={() => setOpen(false)} />
      <nav className={`sidebar ${open ? 'open' : ''}`} aria-label="Main">
        <div className="brand">
          <div className="brand-mark">E</div>
          <div><b>ERIS</b><small>Retail Intelligence</small></div>
        </div>
        {NAV.filter((n) => (!n.manager || isManager) && (!n.admin || isAdmin)).map((n) => n.section
          ? <div key={n.section} className="nav-section">{n.section}</div>
          : <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><n.icon />{n.label}</NavLink>)}
        <div className="sidebar-foot">
          {org?.name}
          {sys.data?.data_to && <div>Data to {date(sys.data.data_to)}</div>}
        </div>
      </nav>
      <div className="main">
        <header className="topbar">
          <button className="btn ghost icon menu-btn" onClick={() => setOpen(true)} aria-label="Open menu"><Menu /></button>
          <OutletPicker />
          <div className="spacer" />
          <AlertsBell />
          <ThemeButton />
          <div className="hide-sm" style={{ textAlign: 'right', lineHeight: 1.2 }}>
            <div style={{ fontWeight: 600 }}>{user?.full_name}</div>
            <div className="small muted" style={{ textTransform: 'capitalize' }}>{user?.role}</div>
          </div>
          <button className="btn ghost icon" onClick={logout} aria-label="Sign out" title="Sign out"><LogOut /></button>
        </header>
        <main className="content"><Outlet /></main>
      </div>
    </div>
  )
}
