import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Pencil, Plus, Search, Trash2, Upload } from 'lucide-react'
import { api, download } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { date, dateTime, money, num } from '../lib/format'
import { Badge, Card, DataTable, Drawer, ErrorState, Field, Modal, PageHead, Pager, Spinner, useDebounced } from '../components/ui'
import { SaleDrawer } from './Sales'

const SEG_TONE = { Champions: 'good', Loyal: 'good', 'Potential Loyalists': 'info', New: 'info', 'Needs Attention': 'warn', 'At Risk': 'bad', Lost: '' }

export default function Customers() {
  const { outletId, isManager } = useApp()
  const [search, setSearch] = useState('')
  const [type, setType] = useState('')
  const [sort, setSort] = useState('spend')
  const [page, setPage] = useState(1)
  const [edit, setEdit] = useState(null)
  const [detail, setDetail] = useState(null)
  const s = useDebounced(search)
  const params = { search: s, customer_type: type, sort, page, page_size: 25 }
  const q = useQuery({ queryKey: ['customers', params], queryFn: () => api('/customers', { params }), placeholderData: (p) => p })
  const seg = useQuery({ queryKey: ['customer-analytics', outletId], queryFn: () => api('/analytics/customers', { params: { outlet_id: outletId, period: '90d' } }) })

  return (
    <>
      <PageHead title="Customers" subtitle="Loyalty customers and business accounts. Bills are linked by phone number.">
        {isManager && <button className="btn" onClick={() => download('/customers/export')}><Download />Export</button>}
        {isManager && <Link to="/import?type=customers" className="btn"><Upload />Import CSV</Link>}
        <button className="btn primary" onClick={() => setEdit({})}><Plus />Add customer</button>
      </PageHead>
      {seg.data && (
        <Card title="Customer segments" subtitle={`RFM analysis of ${num(seg.data.total_customers)} customers over the last 12 months · ${seg.data.repeat.repeat_rate_pct}% repeat rate (90 days)`}>
          <div className="mini-kpis">
            {seg.data.segments.map((x) => (
              <div className="mini-kpi" key={x.segment} title={x.description}>
                <Badge tone={SEG_TONE[x.segment]}>{x.segment}</Badge>
                <div className="v" style={{ marginTop: 6 }}>{num(x.customers)}</div>
                <div className="small muted">{x.revenue_share_pct}% of revenue · {num(x.avg_recency_days)}d since visit</div>
              </div>
            ))}
          </div>
        </Card>
      )}
      <Card flush>
        <div className="row" style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
          <div className="search"><Search /><input className="input" placeholder="Name, phone or email" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} aria-label="Search customers" /></div>
          <select className="select" value={type} onChange={(e) => { setType(e.target.value); setPage(1) }} aria-label="Type"><option value="">All types</option><option value="retail">Retail</option><option value="business">Business</option></select>
          <select className="select" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
            <option value="spend">Highest spend</option><option value="orders">Most visits</option><option value="recent">Most recent</option><option value="new">Newest</option><option value="name">Name</option>
          </select>
        </div>
        {q.isError ? <ErrorState error={q.error} /> : q.isLoading ? <Spinner /> : (
          <>
            <DataTable rows={q.data.items} onRowClick={(r) => setDetail(r.id)} sortable={false} columns={[
              { key: 'name', label: 'Customer', render: (r) => <><b>{r.name}</b>{r.customer_type === 'business' && <> <Badge tone="info">Business</Badge></>}<div className="small muted">{r.city || ''}</div></> },
              { key: 'phone', label: 'Phone' },
              { key: 'orders', label: 'Visits', format: 'number' },
              { key: 'spend', label: 'Total spend', format: 'currency' },
              { key: 'last_purchase', label: 'Last purchase', format: 'date' },
              { key: 'e', label: '', render: (r) => <button className="btn sm icon ghost" aria-label="Edit" onClick={(e) => { e.stopPropagation(); setEdit(r) }}><Pencil /></button> },
            ]} />
            <Pager page={page} pages={q.data.pages} total={q.data.total} onPage={setPage} label="customers" />
          </>
        )}
      </Card>
      {edit && <CustomerForm customer={edit} onClose={() => setEdit(null)} />}
      {detail && <CustomerDrawer id={detail} onClose={() => setDetail(null)} />}
    </>
  )
}

function CustomerForm({ customer, onClose }) {
  const qc = useQueryClient()
  const toast = useToast()
  const { isManager } = useApp()
  const isNew = !customer.id
  const [f, setF] = useState({ name: customer.name || '', phone: customer.phone || '', email: customer.email || '', city: customer.city || '',
    customer_type: customer.customer_type || 'retail', notes: customer.notes || '' })
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }))
  const save = useMutation({
    mutationFn: () => api(isNew ? '/customers' : `/customers/${customer.id}`, { method: isNew ? 'POST' : 'PUT', body: { ...f, phone: f.phone || null, email: f.email || null } }),
    onSuccess: () => { toast('Customer saved', 'success'); qc.invalidateQueries({ queryKey: ['customers'] }); qc.invalidateQueries({ queryKey: ['customer'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  const del = useMutation({
    mutationFn: () => api(`/customers/${customer.id}`, { method: 'DELETE' }),
    onSuccess: () => { toast('Customer deleted', 'success'); qc.invalidateQueries({ queryKey: ['customers'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  return (
    <Modal title={isNew ? 'Add customer' : `Edit ${customer.name}`} onClose={onClose} footer={<>
      {!isNew && isManager && <button className="btn danger" style={{ marginRight: 'auto' }} onClick={() => window.confirm('Delete this customer?') && del.mutate()}><Trash2 />Delete</button>}
      <button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={f.name.trim().length < 2 || save.isPending} onClick={() => save.mutate()}>Save</button>
    </>}>
      <div className="form-grid">
        <Field label="Name" className="full"><input className="input" value={f.name} onChange={(e) => set('name', e.target.value)} /></Field>
        <Field label="Mobile number" hint="Used to link bills"><input className="input" inputMode="tel" value={f.phone} onChange={(e) => set('phone', e.target.value)} /></Field>
        <Field label="Email"><input className="input" type="email" value={f.email} onChange={(e) => set('email', e.target.value)} /></Field>
        <Field label="City"><input className="input" value={f.city} onChange={(e) => set('city', e.target.value)} /></Field>
        <Field label="Type"><select className="select" value={f.customer_type} onChange={(e) => set('customer_type', e.target.value)}><option value="retail">Retail</option><option value="business">Business (can buy on credit)</option></select></Field>
        <Field label="Notes" className="full"><textarea className="input" rows={2} value={f.notes} onChange={(e) => set('notes', e.target.value)} /></Field>
      </div>
    </Modal>
  )
}

function CustomerDrawer({ id, onClose }) {
  const q = useQuery({ queryKey: ['customer', id], queryFn: () => api(`/customers/${id}`) })
  const [sale, setSale] = useState(null)
  const c = q.data
  return (
    <Drawer title={c?.name || 'Customer'} onClose={onClose}>
      {!c ? <Spinner /> : (
        <>
          <div className="grid grid-2">
            <Card><div className="small muted">Total spend</div><div className="kpi-value">{money(c.spend, { compact: true })}</div><div className="kpi-foot">{num(c.orders)} visits · avg {money(c.avg_bill)}</div></Card>
            <Card><div className="small muted">Segment</div><div style={{ margin: '6px 0' }}>{c.segment ? <Badge tone={SEG_TONE[c.segment]}>{c.segment}</Badge> : <span className="muted">Not enough history</span>}</div><div className="kpi-foot">Last visit {date(c.last_purchase)}</div></Card>
          </div>
          <Card><dl className="dl">
            <dt>Phone</dt><dd>{c.phone || '-'}</dd><dt>Email</dt><dd>{c.email || '-'}</dd><dt>City</dt><dd>{c.city || '-'}</dd>
            <dt>Customer since</dt><dd>{date(c.first_purchase || c.created_at)}</dd>
            <dt>Favourites</dt><dd>{c.favourite_products.map((f) => f.name).join(', ') || '-'}</dd>
            {c.notes && <><dt>Notes</dt><dd>{c.notes}</dd></>}
          </dl></Card>
          <Card title="Recent bills" flush>
            <DataTable rows={c.recent_sales} onRowClick={(r) => setSale(r.id)} sortable={false} columns={[
              { key: 'invoice_no', label: 'Invoice' }, { key: 'sold_at', label: 'Date', render: (r) => dateTime(r.sold_at) },
              { key: 'outlet', label: 'Outlet' }, { key: 'total', label: 'Amount', format: 'currency' },
            ]} />
          </Card>
          {sale && <SaleDrawer id={sale} onClose={() => setSale(null)} />}
        </>
      )}
    </Drawer>
  )
}
