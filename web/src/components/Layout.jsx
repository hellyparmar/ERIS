import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity, BarChart3, Bell, Boxes, Bot, Building2, Contact, FileSpreadsheet, FileText, FlaskConical, History, LayoutDashboard,
  LifeBuoy, LogOut, Menu, Moon, Package, PanelLeftClose, PanelLeftOpen, Receipt, Settings, Store, Sun, TrendingUp, Truck, Upload,
  Monitor, UserRound,
} from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date } from '../lib/format'
import { AlertItem } from './ui'

const NAV = [
  { section: 'Overview' },
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/assistant', label: 'AI Assistant', icon: Bot, badge: 'AI' },
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
]
const SECTION_OF = {}
let current = null
NAV.forEach((n) => { if (n.section) current = n.section; else SECTION_OF[n.to] = [current, n.label] })
SECTION_OF['/settings'] = ['Account', 'Settings']
SECTION_OF['/help'] = ['Account', 'Help & Support']

function Crumbs() {
  const { pathname } = useLocation()
  const [section, label] = SECTION_OF[pathname] || []
  if (!label) return <div className="crumbs" />
  return <div className="crumbs">{section}<span aria-hidden="true">/</span><b>{label}</b></div>
}

function OutletPicker() {
  const { user, outlets, outletId, setOutletId } = useApp()
  if (!user) return null
  const mine = user.role === 'admin' ? outlets : outlets.filter((o) => user.outlet_ids.includes(o.id))
  if (user.role !== 'admin' && mine.length <= 1) {
    return <span className="pill"><Building2 size={15} />{user.outlet_names?.[0] || 'My outlet'}</span>
  }
  return (
    <select className="pill" value={outletId || ''} onChange={(e) => setOutletId(e.target.value ? Number(e.target.value) : null)}
      aria-label="Outlet filter" style={{ maxWidth: 230 }}>
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
      <button className="btn icon round" onClick={() => setOpen((o) => !o)} aria-label={`Alerts (${urgent} need attention)`} aria-expanded={open}>
        <Bell />
        {urgent > 0 && <span style={{ position: 'absolute', top: -3, right: -3, background: 'var(--bad)', color: '#fff', borderRadius: 999, fontSize: 10, minWidth: 16, height: 16, display: 'grid', placeItems: 'center', fontWeight: 700 }}>{urgent}</span>}
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
  return <button className="btn icon round" onClick={() => setTheme(next)} aria-label={`Theme: ${theme}. Switch to ${next}`} title={`Theme: ${theme}`}><Icon /></button>
}

export const initialsOf = (name = '') => name.replace(/\(.*\)/, '').split(/[^A-Za-z]+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase() || '?'

function UserMenu() {
  const { user, logout } = useApp()
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  return (
    <div style={{ position: 'relative' }}>
      <button className="user-chip" onClick={() => setOpen((o) => !o)} aria-label="Account menu" aria-expanded={open} style={{ cursor: 'pointer' }}>
        <span className="initials">{initialsOf(user?.full_name)}</span>
        <span className="who hide-sm"><b>{user?.full_name}</b><span>{user?.role}</span></span>
      </button>
      {open && (
        <>
          <div style={{ position: 'fixed', inset: 0, zIndex: 39 }} onClick={() => setOpen(false)} />
          <div className="card" style={{ position: 'absolute', right: 0, top: 46, width: 240, zIndex: 40, padding: 8 }}>
            <div style={{ padding: '8px 10px 10px' }}>
              <b>{user?.full_name}</b>
              <div className="small muted">{user?.email}</div>
            </div>
            <button className="btn ghost block" style={{ justifyContent: 'flex-start' }} onClick={() => { setOpen(false); navigate('/settings?tab=profile') }}><UserRound />My profile</button>
            <button className="btn ghost block" style={{ justifyContent: 'flex-start' }} onClick={logout}><LogOut />Sign out</button>
          </div>
        </>
      )}
    </div>
  )
}

/** While the demo data is being generated, say so on every page and refresh the page's data when it is ready. */
function PreparingBanner() {
  const qc = useQueryClient()
  const [was, setWas] = useState(false)
  const health = useQuery({ queryKey: ['health'], queryFn: () => api('/health'), refetchInterval: (q) => (q.state.data?.seeding?.running ? 3000 : false) })
  const running = !!health.data?.seeding?.running
  useEffect(() => {
    if (running) setWas(true)
    else if (was) { setWas(false); qc.invalidateQueries() }
  }, [running, was, qc])
  if (!running) return null
  return (
    <div className="banner" role="status">
      <div className="spinner" />
      <div><b>Preparing the demo data</b><p>{health.data.seeding.message} - pages fill in automatically when it is ready (about a minute).</p></div>
    </div>
  )
}

function readCollapsed() {
  try { return localStorage.getItem('eris.sidebar') === 'collapsed' } catch { return false }
}

export default function Layout() {
  const { org, isManager, isAdmin } = useApp()
  const [open, setOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(readCollapsed)
  const location = useLocation()
  useEffect(() => setOpen(false), [location.pathname])
  const sys = useQuery({ queryKey: ['system'], queryFn: () => api('/settings/system'), staleTime: 300_000 })
  const toggle = () => setCollapsed((c) => {
    try { localStorage.setItem('eris.sidebar', c ? 'open' : 'collapsed') } catch { /* private mode: not remembered */ }
    return !c
  })
  const link = (n) => (
    <NavLink key={n.to} to={n.to} end={n.end} title={collapsed ? n.label : undefined}
      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
      <n.icon aria-hidden="true" /><span>{n.label}</span>{n.badge && <span className="nav-badge">{n.badge}</span>}
    </NavLink>
  )

  return (
    <div className={`app ${collapsed ? 'collapsed' : ''}`}>
      <div className={`scrim ${open ? 'open' : ''}`} onClick={() => setOpen(false)} />
      <nav className={`sidebar ${open ? 'open' : ''}`} aria-label="Main">
        <div className="brand">
          <div className="brand-mark">E</div>
          <div className="brand-text"><b>ERIS</b><small>Retail Intelligence</small></div>
          <button className="btn ghost sm icon collapse-btn" onClick={toggle} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>{collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}</button>
        </div>
        {NAV.filter((n) => (!n.manager || isManager) && (!n.admin || isAdmin)).map((n) => n.section
          ? <div key={n.section} className="nav-section">{n.section}</div> : link(n))}
        <div className="sidebar-foot">
          {link({ to: '/help', label: 'Help & Support', icon: LifeBuoy })}
          {link({ to: '/settings', label: 'Settings', icon: Settings })}
          <div className="sidebar-org">
            <b>{org?.name || 'ERIS'}</b>
            {sys.data?.data_to && <span className="live">Data to {date(sys.data.data_to)}</span>}
          </div>
        </div>
      </nav>
      <div className="main">
        <header className="topbar">
          <button className="btn ghost icon menu-btn" onClick={() => setOpen(true)} aria-label="Open menu"><Menu /></button>
          <Crumbs />
          <div className="spacer" />
          <OutletPicker />
          <AlertsBell />
          <ThemeButton />
          <UserMenu />
        </header>
        <main className="content"><PreparingBanner /><Outlet /></main>
      </div>
    </div>
  )
}
