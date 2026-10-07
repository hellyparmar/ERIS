import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MapPin, Pencil, Plus, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { date, money, num, shortDate } from '../lib/format'
import { Card, DataTable, Delta, Drawer, ErrorState, Field, Kpi, Modal, PageHead, SegmentBar, SkeletonGrid, Spinner, StatusBadge } from '../components/ui'
import { BarsChart, ShareList, TrendChart } from '../components/charts'
import { StateSelect } from '../components/pickers'

export default function Outlets() {
  const { isAdmin, outletId } = useApp()
  const q = useQuery({ queryKey: ['outlets-stats'], queryFn: () => api('/outlets', { params: { with_stats: true } }) })
  const [edit, setEdit] = useState(null)
  const [detail, setDetail] = useState(null)
  const [picked, setPicked] = useState(null)
  const list = q.data || []
  // CSS variables, so each swatch takes the palette of where it sits (the dark card or the page)
  const colors = ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)', 'var(--s5)', 'var(--s6)', 'var(--s7)']
  const colorOf = Object.fromEntries(list.map((o, i) => [o.id, colors[i % colors.length]]))
  const total = list.reduce((a, o) => a + o.stats.revenue_30d, 0)
  const before = list.reduce((a, o) => a + (o.stats.change_pct == null ? o.stats.revenue_30d : o.stats.revenue_30d / (1 + o.stats.change_pct / 100)), 0)
  const ranked = [...list].sort((a, b) => b.stats.revenue_30d - a.stats.revenue_30d)
  const best = ranked[0]
  const selected = picked ?? (list.some((o) => o.id === outletId) ? outletId : best?.id)

  return (
    <>
      <PageHead title="Outlets" subtitle="Last 30 days, compared with the 30 days before.">
        {isAdmin && <button className="btn primary" disabled={list.length >= 7} title={list.length >= 7 ? 'The 7-outlet limit is reached' : undefined}
          onClick={() => setEdit({})}><Plus />Add outlet</button>}
      </PageHead>
      {q.isError ? <ErrorState error={q.error} /> : q.isLoading ? <SkeletonGrid cards={4} rows={1} /> : (
        <>
          <section className="card dark flush">
            <div className="card-head"><div><h2>Sales by outlet</h2><p>Last 30 days</p></div><span className="small muted">Compared to previous 30 days</span></div>
            <div style={{ padding: '4px 18px 18px' }}>
              <div className="row" style={{ gap: 40, alignItems: 'flex-end', marginBottom: 16 }}>
                <div><div className="small muted">Revenue, all outlets</div>
                  <div className="row" style={{ gap: 10 }}><span className="big-number">{money(total, { compact: true })}</span><Delta value={before ? ((total - before) / before) * 100 : null} /></div></div>
                {best && <div><div className="small muted">Best outlet · {best.name}</div>
                  <div className="row" style={{ gap: 10 }}><span className="big-number" style={{ color: 'var(--text-2)' }}>{best.stats.share_pct}%</span><span className="small muted">of revenue</span></div></div>}
              </div>
              <SegmentBar thick legend={false} items={ranked.map((o) => ({ label: o.name, value: o.stats.revenue_30d, color: colorOf[o.id] }))} format={(v) => money(v, { compact: true })} />
            </div>
            <DataTable rows={ranked} sortable={false} onRowClick={(o) => setDetail(o.id)} columns={[
              { key: 'name', label: 'Outlet', render: (o) => <span className="row" style={{ gap: 8, flexWrap: 'nowrap' }}><i className="swatch" style={{ background: colorOf[o.id] }} /><b>{o.name}</b>{!o.is_active && <StatusBadge status="inactive" />}</span> },
              { key: 'city', label: 'City', render: (o) => <span className="muted">{o.city}</span> },
              { key: 'share', label: 'Share', align: 'right', render: (o) => `${o.stats.share_pct}%` },
              { key: 'rev', label: 'Revenue', align: 'right', render: (o) => <span className="row" style={{ gap: 6, justifyContent: 'flex-end', flexWrap: 'nowrap' }}>{money(o.stats.revenue_30d)}<Delta value={o.stats.change_pct} /></span> },
              { key: 'orders', label: 'Bills', align: 'right', render: (o) => num(o.stats.orders_30d) },
              { key: 'basket', label: 'Avg bill', align: 'right', render: (o) => money(o.stats.avg_basket) },
              { key: 'margin', label: 'Margin', align: 'right', render: (o) => `${o.stats.margin_pct}%` },
              { key: 'stock', label: 'Stock value', align: 'right', render: (o) => money(o.stats.stock_value, { compact: true }) },
              { key: 'low', label: 'Low stock', align: 'right', render: (o) => <span className={o.stats.low_stock_items ? 'down' : ''}>{o.stats.low_stock_items}</span> },
              ...(isAdmin ? [{ key: 'edit', label: '', render: (o) => <button className="btn sm icon ghost" aria-label={`Edit ${o.name}`} onClick={(e) => { e.stopPropagation(); setEdit(o) }}><Pencil /></button> }] : []),
            ]} />
          </section>

          <div className="stack" style={{ gap: 4, marginTop: 6 }}>
            <h2 style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em' }}>Outlet details</h2>
          </div>
          <div className="chip-row" role="group" aria-label="Outlet">
            {ranked.map((o) => (
              <button key={o.id} className={`chip ${selected === o.id ? 'on' : ''}`} aria-pressed={selected === o.id} onClick={() => setPicked(o.id)}>
                <i className="dot" style={{ background: colorOf[o.id] }} />{o.name}
              </button>
            ))}
          </div>
          {selected && <OutletDetail id={selected} outlet={list.find((o) => o.id === selected)} onOpen={() => setDetail(selected)} />}
        </>
      )}
      {edit && <OutletForm outlet={edit} onClose={() => setEdit(null)} />}
      {detail && <OutletDrawer id={detail} onClose={() => setDetail(null)} />}
    </>
  )
}

function OutletDetail({ id, outlet, onOpen }) {
  const q = useQuery({ queryKey: ['outlet', id], queryFn: () => api(`/outlets/${id}`) })
  if (q.isError) return <ErrorState error={q.error} onRetry={q.refetch} />
  if (!q.data) return <SkeletonGrid cards={4} rows={1} />
  const o = q.data
  const k = o.kpis.current
  const ch = o.kpis.change_pct
  const trend = o.trend.map((t) => ({ ...t, basket: t.orders ? Math.round(t.revenue / t.orders) : null, week: shortDate(t.date) }))
  const last = trend[trend.length - 1]
  const prev = trend[trend.length - 2]
  return (
    <>
      <div className="row between">
        <div className="row" style={{ gap: 10 }}>
          <h2 style={{ fontSize: 17 }}>{o.name}</h2>
          <span className="small muted"><MapPin size={12} style={{ verticalAlign: -1 }} /> {o.city} · {o.code}{o.manager_name ? ` · Manager: ${o.manager_name}` : ''}{o.opened_on ? ` · opened ${date(o.opened_on, { month: 'short', year: 'numeric' })}` : ''}</span>
        </div>
        <button className="btn sm" onClick={onOpen}>Products & categories</button>
      </div>
      <div className="grid grid-4">
        <Kpi label="Revenue" value={money(k.revenue, { compact: true })} change={ch.revenue} hint={`${outlet?.stats.share_pct ?? 0}% of all outlets`} />
        <Kpi label="Gross profit" value={money(k.gross_profit, { compact: true })} change={ch.gross_profit} hint={`${k.margin_pct}% margin`} />
        <Kpi label="Bills" value={num(k.orders)} change={ch.orders} hint={`${num(k.items_per_basket, 1)} items per bill`} />
        <Kpi label="Average bill" value={money(k.avg_basket)} change={ch.avg_basket} hint={`${outlet?.stats.low_stock_items ?? 0} products low on stock`} />
      </div>
      <div className="grid grid-2">
        <Card title="Weekly revenue"
          actions={last && <div style={{ textAlign: 'right' }}><div className="small muted">Latest week</div>
            <div className="row" style={{ gap: 8 }}><span className="big-number" style={{ fontSize: 26 }}>{money(last.revenue, { compact: true })}</span>{prev?.revenue > 0 && <Delta value={((last.revenue - prev.revenue) / prev.revenue) * 100} />}</div></div>}>
          <BarsChart data={trend} x="week" series={[{ key: 'revenue', label: 'Revenue' }]} height={230} highlight={(_, i) => i === trend.length - 1} />
        </Card>
        <Card title="Average bill by week"
          actions={last?.basket && <div style={{ textAlign: 'right' }}><div className="small muted">Latest week</div>
            <div className="row" style={{ gap: 8 }}><span className="big-number" style={{ fontSize: 26 }}>{money(last.basket)}</span>{prev?.basket > 0 && <Delta value={((last.basket - prev.basket) / prev.basket) * 100} />}</div></div>}>
          <TrendChart data={trend} gran="week" height={230} series={[{ key: 'basket', label: 'Average bill' }]} />
        </Card>
      </div>
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
    manager_name: outlet.manager_name || '', opened_on: outlet.opened_on || '', is_active: outlet.is_active ?? true,
    state: outlet.state || null, state_code: outlet.state_code || null })
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
        <Field label="State (GST)" hint="Decides the outlet's GSTIN and CGST/SGST vs IGST"><StateSelect value={f.state_code} onChange={(code, name) => setF((x) => ({ ...x, state_code: code, state: name }))} /></Field>
        <Field label="Phone"><input className="input" value={f.phone} onChange={(e) => set('phone', e.target.value)} /></Field>
        <Field label="Address" className="full"><input className="input" value={f.address} onChange={(e) => set('address', e.target.value)} /></Field>
        <Field label="Manager name"><input className="input" value={f.manager_name} onChange={(e) => set('manager_name', e.target.value)} /></Field>
        <Field label="Opened on"><input className="input" type="date" value={f.opened_on} onChange={(e) => set('opened_on', e.target.value)} /></Field>
        <Field label="Status"><select className="select" value={String(f.is_active)} onChange={(e) => set('is_active', e.target.value === 'true')}><option value="true">Active</option><option value="false">Inactive (no new sales)</option></select></Field>
      </div>
    </Modal>
  )
}
