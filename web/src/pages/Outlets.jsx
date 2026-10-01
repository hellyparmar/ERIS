import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MapPin, Pencil, Plus, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { date, money, num } from '../lib/format'
import { Card, DataTable, Delta, Drawer, ErrorState, Field, Modal, PageHead, Spinner, StatusBadge } from '../components/ui'
import { ShareList, TrendChart } from '../components/charts'

export default function Outlets() {
  const { isAdmin } = useApp()
  const q = useQuery({ queryKey: ['outlets-stats'], queryFn: () => api('/outlets', { params: { with_stats: true } }) })
  const [edit, setEdit] = useState(null)
  const [detail, setDetail] = useState(null)
  return (
    <>
      <PageHead title="Outlets" subtitle="Your stores at a glance - last 30 days.">
        {isAdmin && <button className="btn primary" onClick={() => setEdit({})}><Plus />Add outlet</button>}
      </PageHead>
      {q.isError ? <ErrorState error={q.error} /> : q.isLoading ? <Spinner /> : (
        <div className="grid grid-3">
          {q.data.map((o) => (
            <section key={o.id} className="card" style={{ cursor: 'pointer' }} onClick={() => setDetail(o.id)} tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setDetail(o.id)} aria-label={`Open ${o.name}`}>
              <div className="card-head">
                <div><h2>{o.name}</h2><p><MapPin size={12} style={{ verticalAlign: -1 }} /> {o.city} · {o.code}</p></div>
                <div className="row">
                  {!o.is_active && <StatusBadge status="inactive" />}
                  {isAdmin && <button className="btn sm icon ghost" aria-label="Edit outlet" onClick={(e) => { e.stopPropagation(); setEdit(o) }}><Pencil /></button>}
                </div>
              </div>
              <div className="kpi-value">{money(o.stats.revenue_30d, { compact: true })}</div>
              <div className="kpi-foot"><Delta value={o.stats.change_pct} /> vs previous 30 days · {o.stats.share_pct}% of total</div>
              <div className="grid grid-3" style={{ marginTop: 14, gap: 8 }}>
                <div><div className="small muted">Bills</div><b>{num(o.stats.orders_30d)}</b></div>
                <div><div className="small muted">Avg bill</div><b>{money(o.stats.avg_basket)}</b></div>
                <div><div className="small muted">Margin</div><b>{o.stats.margin_pct}%</b></div>
                <div><div className="small muted">Stock value</div><b>{money(o.stats.stock_value, { compact: true })}</b></div>
                <div><div className="small muted">Low stock</div><b className={o.stats.low_stock_items ? 'down' : ''}>{o.stats.low_stock_items}</b></div>
                <div><div className="small muted">Team</div><b>{o.stats.users}</b></div>
              </div>
              <p className="small muted" style={{ marginTop: 10 }}>{o.manager_name ? `Manager: ${o.manager_name}` : 'No manager set'}{o.opened_on && ` · opened ${date(o.opened_on, { month: 'short', year: 'numeric' })}`}</p>
            </section>
          ))}
        </div>
      )}
      {edit && <OutletForm outlet={edit} onClose={() => setEdit(null)} />}
      {detail && <OutletDrawer id={detail} onClose={() => setDetail(null)} />}
    </>
  )
}

function OutletDrawer({ id, onClose }) {
  const q = useQuery({ queryKey: ['outlet', id], queryFn: () => api(`/outlets/${id}`) })
  const o = q.data
  return (
    <Drawer title={o?.name || 'Outlet'} onClose={onClose}>
      {!o ? <Spinner /> : (
        <>
          <Card><dl className="dl">
            <dt>Address</dt><dd>{o.address || '-'}</dd><dt>Phone</dt><dd>{o.phone || '-'}</dd><dt>Manager</dt><dd>{o.manager_name || '-'}</dd>
            <dt>Revenue (30d)</dt><dd>{money(o.kpis.current.revenue)} <Delta value={o.kpis.change_pct.revenue} /></dd>
            <dt>Gross profit</dt><dd>{money(o.kpis.current.gross_profit)} ({o.kpis.current.margin_pct}%)</dd>
          </dl></Card>
          <Card title="Weekly revenue (90 days)"><TrendChart data={o.trend} series={[{ key: 'revenue', label: 'Revenue' }]} height={180} /></Card>
          <Card title="Category mix (30 days)"><ShareList rows={o.categories} labelKey="category" valueKey="revenue" /></Card>
          <Card title="Top products (30 days)" flush>
            <DataTable rows={o.top_products} sortable={false} columns={[{ key: 'name', label: 'Product' }, { key: 'units', label: 'Units', format: 'number' }, { key: 'revenue', label: 'Revenue', format: 'currency' }]} />
          </Card>
        </>
      )}
    </Drawer>
  )
}

function OutletForm({ outlet, onClose }) {
  const qc = useQueryClient()
  const toast = useToast()
  const isNew = !outlet.id
  const [f, setF] = useState({ code: outlet.code || '', name: outlet.name || '', city: outlet.city || '', address: outlet.address || '', phone: outlet.phone || '',
    manager_name: outlet.manager_name || '', opened_on: outlet.opened_on || '', is_active: outlet.is_active ?? true })
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }))
  const refresh = () => { qc.invalidateQueries({ queryKey: ['outlets'] }); qc.invalidateQueries({ queryKey: ['outlets-stats'] }) }
  const save = useMutation({
    mutationFn: () => api(isNew ? '/outlets' : `/outlets/${outlet.id}`, { method: isNew ? 'POST' : 'PUT', body: { ...f, opened_on: f.opened_on || null } }),
    onSuccess: () => { toast(isNew ? 'Outlet created - every product starts at zero stock' : 'Outlet saved', 'success'); refresh(); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  const del = useMutation({
    mutationFn: () => api(`/outlets/${outlet.id}`, { method: 'DELETE' }),
    onSuccess: (r) => { toast(r.message || 'Outlet deleted', 'success'); refresh(); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  return (
    <Modal title={isNew ? 'Add outlet' : `Edit ${outlet.name}`} onClose={onClose} footer={<>
      {!isNew && <button className="btn danger" style={{ marginRight: 'auto' }} onClick={() => window.confirm('Delete this outlet? Outlets with sales are deactivated instead.') && del.mutate()}><Trash2 />Delete</button>}
      <button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={save.isPending} onClick={() => save.mutate()}>Save</button>
    </>}>
      <div className="form-grid">
        <Field label="Code" hint="Short unique code, e.g. MUM-AND"><input className="input" value={f.code} onChange={(e) => set('code', e.target.value.toUpperCase())} /></Field>
        <Field label="Name"><input className="input" value={f.name} onChange={(e) => set('name', e.target.value)} /></Field>
        <Field label="City"><input className="input" value={f.city} onChange={(e) => set('city', e.target.value)} /></Field>
        <Field label="Phone"><input className="input" value={f.phone} onChange={(e) => set('phone', e.target.value)} /></Field>
        <Field label="Address" className="full"><input className="input" value={f.address} onChange={(e) => set('address', e.target.value)} /></Field>
        <Field label="Manager name"><input className="input" value={f.manager_name} onChange={(e) => set('manager_name', e.target.value)} /></Field>
        <Field label="Opened on"><input className="input" type="date" value={f.opened_on} onChange={(e) => set('opened_on', e.target.value)} /></Field>
        <Field label="Status"><select className="select" value={String(f.is_active)} onChange={(e) => set('is_active', e.target.value === 'true')}><option value="true">Active</option><option value="false">Inactive (no new sales)</option></select></Field>
      </div>
    </Modal>
  )
}
