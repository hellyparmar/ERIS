import { Fragment, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bot, Building2, Database, KeyRound, LogOut, Pencil, Plus, RefreshCw, Trash2, UserCog, Users } from 'lucide-react'
import { api, setSession } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { date, dateTime, num } from '../lib/format'
import { Badge, Card, DataTable, Field, Modal, PageHead, Spinner, StatusBadge, Tabs } from '../components/ui'
import { StateSelect } from '../components/pickers'

export default function Settings() {
  const { isAdmin } = useApp()
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || (isAdmin ? 'organization' : 'profile')
  const setTab = (t) => setParams({ tab: t }, { replace: true })
  const tabs = [
    ...(isAdmin ? [{ id: 'organization', label: 'Organization', icon: Building2 }] : []),
    { id: 'profile', label: 'My profile', icon: UserCog },
    ...(isAdmin ? [{ id: 'users', label: 'Users & roles', icon: Users }] : []),
    { id: 'system', label: 'System & data', icon: Database },
  ]
  return (
    <>
      <PageHead title="Settings" />
      <Tabs tabs={tabs} value={tab} onChange={setTab} />
      {tab === 'organization' && <OrgTab />}
      {tab === 'profile' && <ProfileTab />}
      {tab === 'users' && <UsersTab />}
      {tab === 'system' && <SystemTab />}
    </>
  )
}

function OrgTab() {
  const { org } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const [f, setF] = useState(org)
  const [formFor, setFormFor] = useState(org)
  if (formFor !== org) { setFormFor(org); if (org) setF(org) }
  const save = useMutation({
    mutationFn: () => api('/settings/organization', { method: 'PUT', body: { ...f, low_stock_cover_days: Number(f.low_stock_cover_days) } }),
    onSuccess: () => { toast('Organization saved', 'success'); qc.invalidateQueries({ queryKey: ['org'] }) },
    onError: (e) => toast(e.message, 'error'),
  })
  if (!f) return <Spinner />
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }))
  return (
    <Card title="Business details">
      <form className="form-grid" onSubmit={(e) => { e.preventDefault(); save.mutate() }}>
        <Field label="Business name"><input className="input" value={f.name} onChange={(e) => set('name', e.target.value)} /></Field>
        <Field label="Industry"><input className="input" value={f.industry || ''} onChange={(e) => set('industry', e.target.value)} /></Field>
        <Field label="Email"><input className="input" value={f.email || ''} onChange={(e) => set('email', e.target.value)} /></Field>
        <Field label="Phone"><input className="input" value={f.phone || ''} onChange={(e) => set('phone', e.target.value)} /></Field>
        <Field label="Address" className="full"><input className="input" value={f.address || ''} onChange={(e) => set('address', e.target.value)} /></Field>
        <Field label="GSTIN" hint={f.tax_id_is_demo && f.tax_id === org.tax_id ? 'Synthetic demo GSTIN - invoices are watermarked "DEMO - NOT FOR TAX FILING"' : 'Each outlet uses this PAN with its own state code'}>
          <div className="row" style={{ flexWrap: 'nowrap' }}>
            <input className="input" style={{ flex: 1 }} value={f.tax_id || ''} onChange={(e) => set('tax_id', e.target.value.toUpperCase())} />
            {f.tax_id_is_demo && f.tax_id === org.tax_id && <Badge tone="warn">Demo</Badge>}
          </div>
        </Field>
        <Field label="Home state (GST)"><StateSelect value={f.state_code} onChange={(code, name) => setF((x) => ({ ...x, state_code: code, state: name }))} /></Field>
        <Field label="Time zone"><input className="input" value={f.timezone} onChange={(e) => set('timezone', e.target.value)} /></Field>
        <Field label="Currency code"><input className="input" value={f.currency} onChange={(e) => set('currency', e.target.value.toUpperCase())} /></Field>
        <Field label="Currency symbol"><input className="input" value={f.currency_symbol} onChange={(e) => set('currency_symbol', e.target.value)} /></Field>
        <div className="full"><button className="btn primary" disabled={save.isPending}>Save changes</button></div>
      </form>
    </Card>
  )
}

function ProfileTab() {
  const { user } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const [name, setName] = useState(user.full_name)
  const [pw, setPw] = useState({ current_password: '', new_password: '', confirm: '' })
  const saveName = useMutation({ mutationFn: () => api('/auth/me', { method: 'PATCH', body: { full_name: name } }), onSuccess: () => { toast('Profile saved', 'success'); qc.invalidateQueries({ queryKey: ['me'] }) }, onError: (e) => toast(e.message, 'error') })
  const savePw = useMutation({
    mutationFn: () => api('/auth/change-password', { method: 'POST', body: { current_password: pw.current_password, new_password: pw.new_password } }),
    onSuccess: (r) => {
      setSession(r.access_token, r.refresh_token)  // other devices are signed out; this one stays signed in
      toast('Password changed - other devices have been signed out', 'success')
      setPw({ current_password: '', new_password: '', confirm: '' })
    },
    onError: (e) => toast(e.message, 'error'),
  })
  const { logout } = useApp()
  const signOutAll = useMutation({
    mutationFn: () => api('/auth/logout-all', { method: 'POST' }),
    onSuccess: () => { toast('Signed out on all devices', 'success'); logout() },
    onError: (e) => toast(e.message, 'error'),
  })
  const mismatch = pw.confirm && pw.new_password !== pw.confirm
  return (
    <div className="grid grid-2">
      <Card title="Profile">
        <form className="stack" onSubmit={(e) => { e.preventDefault(); saveName.mutate() }}>
          <Field label="Full name"><input className="input" value={name} onChange={(e) => setName(e.target.value)} /></Field>
          <dl className="dl"><dt>Email</dt><dd>{user.email}</dd><dt>Role</dt><dd><StatusBadge status={user.role} /></dd><dt>Outlets</dt><dd>{user.role === 'admin' ? 'All outlets' : (user.outlet_names || []).join(', ')}</dd></dl>
          <div className="row">
            <button className="btn primary" disabled={name.trim().length < 2}>Save</button>
            <button type="button" className="btn" onClick={() => window.confirm('Sign out on every device, including this one?') && signOutAll.mutate()}><LogOut />Sign out everywhere</button>
          </div>
        </form>
      </Card>
      <Card title="Change password">
        <form className="stack" onSubmit={(e) => { e.preventDefault(); savePw.mutate() }}>
          <Field label="Current password"><input className="input" type="password" autoComplete="current-password" value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} /></Field>
          <Field label="New password" hint="At least 8 characters"><input className="input" type="password" autoComplete="new-password" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} /></Field>
          <Field label="Confirm new password"><input className="input" type="password" autoComplete="new-password" value={pw.confirm} onChange={(e) => setPw({ ...pw, confirm: e.target.value })} /></Field>
          {mismatch && <span className="down small">Passwords don't match</span>}
          <div><button className="btn primary" disabled={!pw.current_password || pw.new_password.length < 8 || mismatch}><KeyRound />Change password</button></div>
        </form>
      </Card>
    </div>
  )
}

function UsersTab() {
  const q = useQuery({ queryKey: ['users'], queryFn: () => api('/users') })
  const [edit, setEdit] = useState(null)
  return (
    <Card flush title="Team" subtitle="Admins see everything; managers run their outlets; staff bill and check stock; viewers read reports."
      actions={<button className="btn primary" onClick={() => setEdit({})}><Plus />Add user</button>}>
      {q.isLoading ? <Spinner /> : (
        <DataTable rows={q.data} columns={[
          { key: 'full_name', label: 'Name', render: (u) => <><b>{u.full_name}</b><div className="small muted">{u.email}</div></> },
          { key: 'role', label: 'Role', format: 'status' },
          { key: 'outlet_names', label: 'Outlets', render: (u) => (u.role === 'admin' ? <span className="muted">All</span> : (u.outlet_names || []).join(', ')) },
          { key: 'last_login_at', label: 'Last login', render: (u) => (u.last_login_at ? dateTime(u.last_login_at) : <span className="muted">Never</span>) },
          { key: 'is_active', label: 'Status', render: (u) => <StatusBadge status={u.is_active ? 'active' : 'inactive'} /> },
          { key: 'e', label: '', render: (u) => <button className="btn sm icon ghost" aria-label="Edit user" onClick={() => setEdit(u)}><Pencil /></button> },
        ]} />
      )}
      {edit && <UserForm u={edit} onClose={() => setEdit(null)} />}
    </Card>
  )
}

function UserForm({ u, onClose }) {
  const { outlets, user: me } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const isNew = !u.id
  const [f, setF] = useState({ email: u.email || '', full_name: u.full_name || '', role: u.role || 'staff', outlet_ids: u.outlet_ids || [], is_active: u.is_active ?? true, password: '' })
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }))
  const toggleOutlet = (id) => set('outlet_ids', f.outlet_ids.includes(id) ? f.outlet_ids.filter((x) => x !== id) : [...f.outlet_ids, id])
  const save = useMutation({
    mutationFn: () => {
      const body = { full_name: f.full_name, role: f.role, outlet_ids: f.role === 'admin' ? [] : f.outlet_ids }
      if (isNew) return api('/users', { method: 'POST', body: { ...body, email: f.email, password: f.password } })
      return api(`/users/${u.id}`, { method: 'PATCH', body: { ...body, is_active: f.is_active, ...(f.password ? { password: f.password } : {}) } })
    },
    onSuccess: () => { toast('User saved', 'success'); qc.invalidateQueries({ queryKey: ['users'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  return (
    <Modal title={isNew ? 'Add user' : `Edit ${u.full_name}`} onClose={onClose} footer={<>
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn primary" disabled={save.isPending || (isNew && f.password.length < 8) || (f.role !== 'admin' && !f.outlet_ids.length)} onClick={() => save.mutate()}>Save</button>
    </>}>
      <div className="form-grid">
        <Field label="Full name"><input className="input" value={f.full_name} onChange={(e) => set('full_name', e.target.value)} /></Field>
        <Field label="Email"><input className="input" type="email" value={f.email} disabled={!isNew} onChange={(e) => set('email', e.target.value)} /></Field>
        <Field label="Role">
          <select className="select" value={f.role} onChange={(e) => set('role', e.target.value)} disabled={u.id === me.id}>
            <option value="admin">Admin - everything, all outlets</option>
            <option value="manager">Manager - runs assigned outlets</option>
            <option value="staff">Staff - billing & stock lookup</option>
            <option value="viewer">Viewer - read-only reports & insights</option>
          </select>
        </Field>
        <Field label={isNew ? 'Password' : 'Reset password'} hint={isNew ? 'At least 8 characters' : 'Leave empty to keep current'}>
          <input className="input" type="password" autoComplete="new-password" value={f.password} onChange={(e) => set('password', e.target.value)} />
        </Field>
        <fieldset className="field full" style={{ border: 0, padding: 0, margin: 0 }}>
          <span>Outlets {f.role === 'admin' ? '(admins see all outlets)' : '(choose one or more)'}</span>
          <div className="row" style={{ gap: 12 }}>
            {outlets.map((o) => (
              <label key={o.id} className="row small" style={{ gap: 6 }}>
                <input type="checkbox" disabled={f.role === 'admin'} checked={f.role === 'admin' || f.outlet_ids.includes(o.id)} onChange={() => toggleOutlet(o.id)} />
                {o.name}{o.is_active ? '' : ' (inactive)'}
              </label>
            ))}
          </div>
        </fieldset>
        {!isNew && <Field label="Status"><select className="select" value={String(f.is_active)} disabled={u.id === me.id} onChange={(e) => set('is_active', e.target.value === 'true')}><option value="true">Active</option><option value="false">Deactivated</option></select></Field>}
      </div>
    </Modal>
  )
}

function SystemTab() {
  const { isAdmin, logout } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const q = useQuery({ queryKey: ['system-full'], queryFn: () => api('/settings/system'), refetchInterval: (x) => (x.state.data?.seeding?.running ? 2000 : false) })
  const regen = useMutation({
    mutationFn: () => api('/settings/demo-data', { method: 'POST' }),
    onSuccess: (r) => { toast(r.message, 'success'); q.refetch() },
    onError: (e) => toast(e.message, 'error'),
  })
  const clear = useMutation({
    mutationFn: () => api('/settings/clear-transactions', { method: 'POST' }),
    onSuccess: () => { toast('Sales, stock, purchase orders and customers cleared', 'success'); qc.invalidateQueries() },
    onError: (e) => toast(e.message, 'error'),
  })
  const wasRunning = useRef(false)
  useEffect(() => {
    if (q.data?.seeding?.running) wasRunning.current = true
    else if (wasRunning.current && q.data) { wasRunning.current = false; toast('Demo data ready - please sign in again', 'success'); logout() }
  }, [q.data, logout, toast])
  if (q.isLoading) return <Spinner />
  const d = q.data
  const ai = d.assistant
  return (
    <div className="grid grid-2">
      <Card title="Data">
        <dl className="dl">
          <dt>Database</dt><dd>{d.database}</dd>
          <dt>Sales history</dt><dd>{d.data_from ? `${date(d.data_from)} – ${date(d.data_to)}` : 'No sales yet'}</dd>
          {Object.entries(d.counts).map(([k, v]) => <Fragment key={k}><dt>{k.replace('_', ' ')}</dt><dd>{num(v)}</dd></Fragment>)}
          <dt>Sales by source</dt><dd>{Object.entries(d.sales_by_source).map(([k, v]) => `${k}: ${num(v)}`).join(' · ') || '-'}</dd>
          {d.dataset && <>
            <dt>Demo dataset</dt>
            <dd>Synthetic - generator v{d.dataset.generator_version}, seed {d.dataset.random_seed}, {date(d.dataset.period_start)} – {date(d.dataset.period_end)}, generated {dateTime(d.dataset.generated_at)}</dd>
          </>}
        </dl>
      </Card>
      <Card title="AI assistant engine">
        <div className="stack">
          <div className="row"><Bot size={18} /><b>Built-in analytics engine</b><Badge tone="good">active</Badge></div>
          <p className="small text-2">Understands questions about sales, stock, customers and forecasts and answers from your live data - works offline, no API keys.</p>
          <div className="row"><Bot size={18} /><b>Local LLM (Ollama)</b><Badge tone={ai.available ? 'good' : ''}>{ai.available ? ai.model : 'not connected'}</Badge></div>
          {!ai.available && (
            <div className="small text-2">
              Optional: for free-form questions and advice, install <a href="https://ollama.com" target="_blank" rel="noreferrer">Ollama</a> (free, runs on your computer) and run:
              <pre className="code" style={{ marginTop: 6 }}>ollama pull llama3.2:3b</pre>
              <span className="muted">{ai.error}</span>
            </div>
          )}
          <div className="small muted">Forecast models: {d.forecast_models.join(', ')}</div>
        </div>
      </Card>
      {isAdmin && (
        <Card title="Demo data & reset" className="span-2">
          <div className="stack">
            {d.seeding?.running && <div className="alert info"><div className="spinner" style={{ width: 16, height: 16 }} /><div><b>Generating demo data…</b><p>{d.seeding.message}</p></div></div>}
            <div className="row between">
              <div><b>Regenerate demo organization</b><p className="small text-2">Replaces ALL data with a fresh synthetic demo (5 outlets, two years of bills, seed 42 - the same seed always gives the same data). Takes about a minute; you'll be signed out.</p></div>
              <button className="btn" disabled={regen.isPending || d.seeding?.running} onClick={() => window.confirm('This deletes ALL data and users and regenerates the demo. Continue?') && regen.mutate()}><RefreshCw />Regenerate demo</button>
            </div>
            <div className="row between">
              <div><b>Start fresh with your own data</b><p className="small text-2">Deletes sales, stock levels, purchase orders and customers. Keeps outlets, products, suppliers and users - then import your data.</p></div>
              <button className="btn danger" disabled={clear.isPending} onClick={() => window.confirm('Delete all sales, stock, purchase orders and customers? This cannot be undone.') && clear.mutate()}><Trash2 />Clear transactions</button>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
