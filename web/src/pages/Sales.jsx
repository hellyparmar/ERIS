import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Ban, Download, Plus, Receipt, Search, Trash2, Upload } from 'lucide-react'
import { api, download } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { dateTime, isoDay, money, num, titleCase } from '../lib/format'
import { Card, DataTable, Drawer, ErrorState, Field, Modal, PageHead, Pager, Spinner, StatusBadge, useDebounced } from '../components/ui'
import { OutletSelect, ProductSearch } from '../components/pickers'

const PAYMENTS = ['cash', 'upi', 'card', 'credit']

export default function Sales() {
  const { outletId } = useApp()
  const [filters, setFilters] = useState({ start: '', end: '', payment_method: '', channel: '', status: '' })
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showNew, setShowNew] = useState(false)
  const [selected, setSelected] = useState(null)
  const s = useDebounced(search)
  const params = { ...filters, search: s, outlet_id: outletId, page, page_size: 25 }
  const q = useQuery({ queryKey: ['sales', params], queryFn: () => api('/sales', { params }), placeholderData: (p) => p })
  const set = (k, v) => { setFilters((f) => ({ ...f, [k]: v })); setPage(1) }

  return (
    <>
      <PageHead title="Sales" subtitle="Every bill across your outlets. Record a sale manually or import sales from a CSV file.">
        <Link to="/import?type=sales" className="btn"><Upload />Import CSV</Link>
        <button className="btn" onClick={() => download('/sales/export', { outlet_id: outletId, start: filters.start || undefined, end: filters.end || undefined })}><Download />Export</button>
        <button className="btn primary" onClick={() => setShowNew(true)}><Plus />New sale</button>
      </PageHead>

      <Card flush>
        <div className="row" style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
          <div className="search"><Search /><input className="input" placeholder="Invoice, customer or phone" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} aria-label="Search sales" /></div>
          <input className="input" type="date" value={filters.start} onChange={(e) => set('start', e.target.value)} aria-label="From date" />
          <input className="input" type="date" value={filters.end} onChange={(e) => set('end', e.target.value)} aria-label="To date" />
          <select className="select" value={filters.payment_method} onChange={(e) => set('payment_method', e.target.value)} aria-label="Payment method">
            <option value="">All payments</option>{PAYMENTS.map((p) => <option key={p} value={p}>{p.toUpperCase()}</option>)}
          </select>
          <select className="select" value={filters.channel} onChange={(e) => set('channel', e.target.value)} aria-label="Channel">
            <option value="">All channels</option><option value="in_store">In store</option><option value="delivery">Delivery</option>
          </select>
          <select className="select" value={filters.status} onChange={(e) => set('status', e.target.value)} aria-label="Status">
            <option value="">All statuses</option><option value="completed">Completed</option><option value="void">Void</option>
          </select>
          {q.data && <span className="small muted" style={{ marginLeft: 'auto' }}>{num(q.data.summary.orders)} bills · <b style={{ color: 'var(--text)' }}>{money(q.data.summary.revenue)}</b> · avg {money(q.data.summary.avg_bill)}</span>}
        </div>
        {q.isError ? <ErrorState error={q.error} onRetry={q.refetch} /> : q.isLoading ? <Spinner /> : (
          <>
            <DataTable rows={q.data.items} onRowClick={(r) => setSelected(r.id)} sortable={false} empty="No sales match these filters" columns={[
              { key: 'invoice_no', label: 'Invoice', render: (r) => <b>{r.invoice_no}</b> },
              { key: 'sold_at', label: 'Date & time', render: (r) => dateTime(r.sold_at) },
              { key: 'outlet', label: 'Outlet' },
              { key: 'customer', label: 'Customer', render: (r) => r.customer || <span className="muted">Walk-in</span> },
              { key: 'payment_method', label: 'Payment', render: (r) => r.payment_method.toUpperCase() },
              { key: 'channel', label: 'Channel', render: (r) => titleCase(r.channel) },
              { key: 'items_count', label: 'Items', format: 'number' },
              { key: 'total', label: 'Amount', format: 'currency' },
              { key: 'status', label: 'Status', format: 'status' },
            ]} />
            <Pager page={page} pages={q.data.pages} total={q.data.total} onPage={setPage} label="bills" />
          </>
        )}
      </Card>
      {showNew && <NewSale onClose={() => setShowNew(false)} onCreated={(sale) => { setShowNew(false); setSelected(sale.id) }} />}
      {selected && <SaleDrawer id={selected} onClose={() => setSelected(null)} />}
    </>
  )
}

export function SaleDrawer({ id, onClose }) {
  const { isManager } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const q = useQuery({ queryKey: ['sale', id], queryFn: () => api(`/sales/${id}`) })
  const voidM = useMutation({
    mutationFn: (reason) => api(`/sales/${id}/void`, { method: 'POST', body: { reason } }),
    onSuccess: () => { toast('Sale voided and stock restored', 'success'); qc.invalidateQueries() },
    onError: (e) => toast(e.message, 'error'),
  })
  const doVoid = () => {
    const reason = window.prompt('Why is this sale being voided? (e.g. entered twice, customer returned items)')
    if (reason && reason.trim().length >= 3) voidM.mutate(reason.trim())
  }
  const s = q.data
  return (
    <Drawer title={s ? `Bill ${s.invoice_no}` : 'Bill'} onClose={onClose}
      actions={s && isManager && s.status === 'completed' && <button className="btn danger sm" onClick={doVoid} disabled={voidM.isPending}><Ban />Void</button>}>
      {!s ? <Spinner /> : (
        <>
          <Card>
            <dl className="dl">
              <dt>Status</dt><dd><StatusBadge status={s.status} /> {s.notes && <span className="small muted">{s.notes}</span>}</dd>
              <dt>Date</dt><dd>{dateTime(s.sold_at)}</dd>
              <dt>Outlet</dt><dd>{s.outlet}</dd>
              <dt>Customer</dt><dd>{s.customer ? `${s.customer} · ${s.customer_phone || ''}` : 'Walk-in'}</dd>
              <dt>Payment</dt><dd>{s.payment_method.toUpperCase()} · {titleCase(s.channel)}</dd>
              <dt>Source</dt><dd>{titleCase(s.source)}</dd>
            </dl>
          </Card>
          <Card flush>
            <DataTable rows={s.items} sortable={false} columns={[
              { key: 'product', label: 'Item', render: (r) => <><b>{r.product}</b><div className="small muted">{r.sku} · GST {r.tax_rate}%</div></> },
              { key: 'quantity', label: 'Qty', format: 'number' },
              { key: 'unit_price', label: 'Price', format: 'currency' },
              { key: 'discount', label: 'Discount', format: 'currency' },
              { key: 'line_total', label: 'Total', format: 'currency' },
            ]} />
          </Card>
          <Card>
            <dl className="dl" style={{ gridTemplateColumns: '1fr auto' }}>
              <dt>Subtotal</dt><dd className="right tabular">{money(s.subtotal, { decimals: true })}</dd>
              <dt>Discount</dt><dd className="right tabular">− {money(s.discount, { decimals: true })}</dd>
              <dt>Includes tax (GST)</dt><dd className="right tabular">{money(s.tax_amount, { decimals: true })}</dd>
              <dt><b>Total paid</b></dt><dd className="right tabular"><b>{money(s.total, { decimals: true })}</b></dd>
            </dl>
          </Card>
        </>
      )}
    </Drawer>
  )
}

function NewSale({ onClose, onCreated }) {
  const { outletId, outlets, isManager } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const [outlet, setOutlet] = useState(outletId || outlets.find((o) => o.is_active)?.id || null)
  const [lines, setLines] = useState([])
  const [form, setForm] = useState({ payment_method: 'upi', channel: 'in_store', customer_phone: '', customer_name: '', bill_discount: 0, when: '' })
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const addProduct = (p) => setLines((ls) => {
    const ex = ls.find((l) => l.product.id === p.id)
    return ex ? ls.map((l) => (l === ex ? { ...l, quantity: l.quantity + 1 } : l)) : [...ls, { product: p, quantity: 1, unit_price: p.selling_price, discount: 0 }]
  })
  const updateLine = (i, k, v) => setLines((ls) => ls.map((l, j) => (j === i ? { ...l, [k]: v } : l)))
  const totals = useMemo(() => {
    const gross = lines.reduce((a, l) => a + (Number(l.quantity) || 0) * (Number(l.unit_price) || 0), 0)
    const disc = lines.reduce((a, l) => a + (Number(l.discount) || 0), 0) + (Number(form.bill_discount) || 0)
    return { gross, disc, total: Math.max(0, gross - disc), items: lines.reduce((a, l) => a + (Number(l.quantity) || 0), 0) }
  }, [lines, form.bill_discount])

  const m = useMutation({
    mutationFn: () => api('/sales', { method: 'POST', body: {
      outlet_id: outlet, payment_method: form.payment_method, channel: form.channel,
      customer_phone: form.customer_phone || null, customer_name: form.customer_name || null,
      bill_discount: Number(form.bill_discount) || 0, sold_at: form.when ? `${form.when}:00`.slice(0, 19) : null, // local time, as entered
      items: lines.map((l) => ({ product_id: l.product.id, quantity: Number(l.quantity), unit_price: Number(l.unit_price), discount: Number(l.discount) || 0 })),
    } }),
    onSuccess: (sale) => { toast(`Bill ${sale.invoice_no} saved - ${money(sale.total)}`, 'success'); qc.invalidateQueries(); onCreated(sale) },
    onError: (e) => toast(e.message, 'error'),
  })

  return (
    <Modal title="New sale" onClose={onClose} wide footer={<>
      <span className="muted" style={{ marginRight: 'auto' }}>{num(totals.items)} items · discount {money(totals.disc)}</span>
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn primary" disabled={!outlet || !lines.length || m.isPending} onClick={() => m.mutate()}><Receipt />Save bill · {money(totals.total, { decimals: true })}</button>
    </>}>
      <div className="form-grid">
        <Field label="Outlet"><OutletSelect value={outlet} onChange={setOutlet} required /></Field>
        <Field label="Date & time" hint={isManager ? 'Leave empty for now' : 'Staff can record today’s sales'}>
          <input className="input" type="datetime-local" value={form.when} max={`${isoDay(new Date())}T23:59`} onChange={(e) => set('when', e.target.value)} />
        </Field>
      </div>
      <Field label="Add items"><ProductSearch onPick={addProduct} autoFocus /></Field>
      {lines.length > 0 ? (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Item</th><th className="num">Qty</th><th className="num">Price</th><th className="num">Discount (₹)</th><th className="num">Amount</th><th /></tr></thead>
            <tbody>
              {lines.map((l, i) => (
                <tr key={l.product.id}>
                  <td><b>{l.product.name}</b><div className="small muted">In stock: {num(l.product.stock)}</div></td>
                  <td className="num"><input className="input" type="number" min="0.1" step="any" style={{ width: 72 }} value={l.quantity} onChange={(e) => updateLine(i, 'quantity', e.target.value)} aria-label="Quantity" /></td>
                  <td className="num"><input className="input" type="number" min="0" step="any" style={{ width: 90 }} value={l.unit_price} onChange={(e) => updateLine(i, 'unit_price', e.target.value)} aria-label="Unit price" /></td>
                  <td className="num"><input className="input" type="number" min="0" step="any" style={{ width: 80 }} value={l.discount} onChange={(e) => updateLine(i, 'discount', e.target.value)} aria-label="Discount" /></td>
                  <td className="num">{money((Number(l.quantity) || 0) * (Number(l.unit_price) || 0) - (Number(l.discount) || 0), { decimals: true })}</td>
                  <td><button className="btn ghost sm icon" onClick={() => setLines((ls) => ls.filter((_, j) => j !== i))} aria-label="Remove"><Trash2 /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <p className="muted small">Search above to add products to the bill.</p>}
      <div className="form-grid">
        <Field label="Customer phone" hint="Optional - links the bill to a loyalty customer (created if new)">
          <input className="input" inputMode="tel" value={form.customer_phone} onChange={(e) => set('customer_phone', e.target.value)} placeholder="10-digit mobile" />
        </Field>
        <Field label="Customer name"><input className="input" value={form.customer_name} onChange={(e) => set('customer_name', e.target.value)} placeholder="Optional" /></Field>
        <Field label="Payment method">
          <select className="select" value={form.payment_method} onChange={(e) => set('payment_method', e.target.value)}>
            {PAYMENTS.map((p) => <option key={p} value={p}>{p === 'credit' ? 'Credit (pay later)' : p.toUpperCase()}</option>)}
          </select>
        </Field>
        <Field label="Channel">
          <select className="select" value={form.channel} onChange={(e) => set('channel', e.target.value)}>
            <option value="in_store">In store</option><option value="delivery">Home delivery</option>
          </select>
        </Field>
        <Field label="Bill discount (₹)"><input className="input" type="number" min="0" step="any" value={form.bill_discount} onChange={(e) => set('bill_discount', e.target.value)} /></Field>
      </div>
      <p className="small muted">Prices include GST. Stock is reduced automatically; the sale is blocked if an item doesn't have enough stock.</p>
    </Modal>
  )
}
