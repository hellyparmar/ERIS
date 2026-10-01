import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, ClipboardList, Pencil, Plus, Trash2, Truck, XCircle } from 'lucide-react'
import { api } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { date, money, num } from '../lib/format'
import { Badge, Card, DataTable, Drawer, ErrorState, Field, Modal, PageHead, Pager, Spinner, StatusBadge, Tabs } from '../components/ui'
import { OutletSelect, ProductSearch, useSuppliers } from '../components/pickers'

export default function Suppliers() {
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || 'suppliers'
  const { isManager } = useApp()
  const [edit, setEdit] = useState(null)
  const [newPO, setNewPO] = useState(false)
  return (
    <>
      <PageHead title="Suppliers & purchase orders" subtitle="Who you buy from, what's on order and when it arrives.">
        {isManager && <button className="btn" onClick={() => setEdit({})}><Plus />Add supplier</button>}
        {isManager && <button className="btn primary" onClick={() => setNewPO(true)}><ClipboardList />New purchase order</button>}
      </PageHead>
      <Tabs value={tab} onChange={(t) => setParams({ tab: t })} tabs={[{ id: 'suppliers', label: 'Suppliers', icon: Truck }, { id: 'orders', label: 'Purchase orders', icon: ClipboardList }]} />
      {tab === 'suppliers' ? <SupplierList onEdit={setEdit} /> : <OrderList />}
      {edit && <SupplierForm supplier={edit} onClose={() => setEdit(null)} />}
      {newPO && <NewPO onClose={() => setNewPO(false)} onCreated={() => { setNewPO(false); setParams({ tab: 'orders' }) }} />}
    </>
  )
}

function SupplierList({ onEdit }) {
  const q = useSuppliers()
  const [detail, setDetail] = useState(null)
  const { isManager } = useApp()
  if (q.isLoading) return <Spinner />
  if (q.isError) return <ErrorState error={q.error} />
  return (
    <>
      <Card flush>
        <DataTable rows={q.data} onRowClick={(r) => setDetail(r.id)} columns={[
          { key: 'name', label: 'Supplier', render: (r) => <><b>{r.name}</b><div className="small muted">{r.contact_person} · {r.city}</div></> },
          { key: 'phone', label: 'Phone', sortable: false },
          { key: 'lead_time_days', label: 'Lead time', render: (r) => `${r.lead_time_days} day${r.lead_time_days === 1 ? '' : 's'}`, align: 'right' },
          { key: 'payment_terms', label: 'Terms' },
          { key: 'products', label: 'Products', format: 'number' },
          { key: 'open_orders', label: 'Open POs', format: 'number' },
          { key: 'open_order_value', label: 'On order', format: 'currency' },
          { key: 'purchases_90d', label: 'Bought (90d)', format: 'currency' },
          { key: 'is_active', label: 'Status', render: (r) => <StatusBadge status={r.is_active ? 'active' : 'inactive'} /> },
          ...(isManager ? [{ key: 'e', label: '', render: (r) => <button className="btn sm icon ghost" aria-label="Edit" onClick={(e) => { e.stopPropagation(); onEdit(r) }}><Pencil /></button> }] : []),
        ]} />
      </Card>
      {detail && <SupplierDrawer id={detail} onClose={() => setDetail(null)} />}
    </>
  )
}

function SupplierDrawer({ id, onClose }) {
  const q = useQuery({ queryKey: ['supplier', id], queryFn: () => api(`/suppliers/${id}`) })
  const s = q.data
  return (
    <Drawer title={s?.name || 'Supplier'} onClose={onClose}>
      {!s ? <Spinner /> : (
        <>
          <Card><dl className="dl">
            <dt>Contact</dt><dd>{s.contact_person || '-'}</dd><dt>Phone</dt><dd>{s.phone || '-'}</dd><dt>Email</dt><dd>{s.email || '-'}</dd>
            <dt>City</dt><dd>{s.city || '-'}</dd><dt>Lead time</dt><dd>{s.lead_time_days} days</dd><dt>Payment terms</dt><dd>{s.payment_terms || '-'}</dd>
            <dt>On-time delivery</dt><dd>{s.on_time_rate_pct === null ? '-' : `${s.on_time_rate_pct}% of recent orders`}</dd>
            {s.notes && <><dt>Notes</dt><dd>{s.notes}</dd></>}
          </dl></Card>
          <Card title={`Products (${s.products.length})`} flush>
            <DataTable rows={s.products} sortable={false} columns={[{ key: 'name', label: 'Product', render: (p) => <>{p.name} <span className="small muted">{p.sku}</span></> }, { key: 'cost_price', label: 'Cost', format: 'currency' }]} />
          </Card>
          <Card title="Recent purchase orders" flush>
            <DataTable rows={s.recent_orders} sortable={false} columns={[
              { key: 'po_number', label: 'PO' }, { key: 'outlet', label: 'Outlet' }, { key: 'order_date', label: 'Date', format: 'date' },
              { key: 'total_cost', label: 'Value', format: 'currency' }, { key: 'status', label: 'Status', format: 'status' },
            ]} />
          </Card>
        </>
      )}
    </Drawer>
  )
}

function SupplierForm({ supplier, onClose }) {
  const qc = useQueryClient()
  const toast = useToast()
  const isNew = !supplier.id
  const [f, setF] = useState({ name: supplier.name || '', contact_person: supplier.contact_person || '', phone: supplier.phone || '', email: supplier.email || '',
    city: supplier.city || '', lead_time_days: supplier.lead_time_days ?? 3, payment_terms: supplier.payment_terms || '', notes: supplier.notes || '', is_active: supplier.is_active ?? true })
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }))
  const save = useMutation({
    mutationFn: () => api(isNew ? '/suppliers' : `/suppliers/${supplier.id}`, { method: isNew ? 'POST' : 'PUT', body: { ...f, lead_time_days: Number(f.lead_time_days) } }),
    onSuccess: () => { toast('Supplier saved', 'success'); qc.invalidateQueries({ queryKey: ['suppliers'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  const del = useMutation({
    mutationFn: () => api(`/suppliers/${supplier.id}`, { method: 'DELETE' }),
    onSuccess: (r) => { toast(r.message || 'Supplier deleted', 'success'); qc.invalidateQueries({ queryKey: ['suppliers'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  return (
    <Modal title={isNew ? 'Add supplier' : `Edit ${supplier.name}`} onClose={onClose} footer={<>
      {!isNew && <button className="btn danger" style={{ marginRight: 'auto' }} onClick={() => window.confirm('Delete this supplier?') && del.mutate()}><Trash2 />Delete</button>}
      <button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={!f.name.trim() || save.isPending} onClick={() => save.mutate()}>Save</button>
    </>}>
      <div className="form-grid">
        <Field label="Name" className="full"><input className="input" value={f.name} onChange={(e) => set('name', e.target.value)} /></Field>
        <Field label="Contact person"><input className="input" value={f.contact_person} onChange={(e) => set('contact_person', e.target.value)} /></Field>
        <Field label="Phone"><input className="input" value={f.phone} onChange={(e) => set('phone', e.target.value)} /></Field>
        <Field label="Email"><input className="input" type="email" value={f.email} onChange={(e) => set('email', e.target.value)} /></Field>
        <Field label="City"><input className="input" value={f.city} onChange={(e) => set('city', e.target.value)} /></Field>
        <Field label="Lead time (days)" hint="Order to delivery - used for reorder planning"><input className="input" type="number" min="0" max="90" value={f.lead_time_days} onChange={(e) => set('lead_time_days', e.target.value)} /></Field>
        <Field label="Payment terms"><input className="input" value={f.payment_terms} onChange={(e) => set('payment_terms', e.target.value)} placeholder="e.g. Net 30" /></Field>
        <Field label="Notes" className="full"><textarea className="input" rows={2} value={f.notes} onChange={(e) => set('notes', e.target.value)} /></Field>
        <Field label="Status"><select className="select" value={String(f.is_active)} onChange={(e) => set('is_active', e.target.value === 'true')}><option value="true">Active</option><option value="false">Inactive</option></select></Field>
      </div>
    </Modal>
  )
}

function OrderList() {
  const { outletId } = useApp()
  const [status, setStatus] = useState('ordered')
  const [page, setPage] = useState(1)
  const [detail, setDetail] = useState(null)
  const params = { status, outlet_id: outletId, page, page_size: 25 }
  const q = useQuery({ queryKey: ['pos', params], queryFn: () => api('/purchase-orders', { params }), placeholderData: (p) => p })
  return (
    <Card flush>
      <div className="row" style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
        <select className="select" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }} aria-label="Status">
          <option value="ordered">Open</option><option value="overdue">Overdue</option><option value="received">Received</option><option value="cancelled">Cancelled</option><option value="">All</option>
        </select>
      </div>
      {q.isLoading ? <Spinner /> : q.isError ? <ErrorState error={q.error} /> : (
        <>
          <DataTable rows={q.data.items} onRowClick={(r) => setDetail(r.id)} sortable={false} empty="No purchase orders" columns={[
            { key: 'po_number', label: 'PO', render: (r) => <b>{r.po_number}</b> },
            { key: 'supplier', label: 'Supplier' }, { key: 'outlet', label: 'Outlet' },
            { key: 'order_date', label: 'Ordered', format: 'date' },
            { key: 'expected_date', label: 'Expected', render: (r) => <span className={r.overdue ? 'down' : ''}>{date(r.expected_date)}</span> },
            { key: 'items_count', label: 'Lines', format: 'number' }, { key: 'total_cost', label: 'Value', format: 'currency' },
            { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.overdue ? 'overdue' : r.status} /> },
          ]} />
          <Pager page={page} pages={q.data.pages} total={q.data.total} onPage={setPage} label="orders" />
        </>
      )}
      {detail && <PODrawer id={detail} onClose={() => setDetail(null)} />}
    </Card>
  )
}

function PODrawer({ id, onClose }) {
  const { isManager } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const q = useQuery({ queryKey: ['po', id], queryFn: () => api(`/purchase-orders/${id}`) })
  const [received, setReceived] = useState(null)
  const po = q.data
  const qty = (i) => received?.[i.product_id] ?? i.quantity
  const receive = useMutation({
    mutationFn: () => api(`/purchase-orders/${id}/receive`, { method: 'POST', body: { items: po.items.map((i) => ({ product_id: i.product_id, quantity: Number(qty(i)) })) } }),
    onSuccess: () => { toast('Goods received - stock updated', 'success'); qc.invalidateQueries() },
    onError: (e) => toast(e.message, 'error'),
  })
  const cancel = useMutation({
    mutationFn: () => api(`/purchase-orders/${id}/cancel`, { method: 'POST' }),
    onSuccess: () => { toast('Purchase order cancelled', 'success'); qc.invalidateQueries() },
    onError: (e) => toast(e.message, 'error'),
  })
  const open = po?.status === 'ordered'
  return (
    <Drawer title={po ? po.po_number : 'Purchase order'} onClose={onClose} actions={po && isManager && open && <>
      <button className="btn sm danger" onClick={() => window.confirm('Cancel this purchase order?') && cancel.mutate()}><XCircle />Cancel</button>
      <button className="btn sm primary" onClick={() => receive.mutate()} disabled={receive.isPending}><CheckCircle2 />Receive goods</button>
    </>}>
      {!po ? <Spinner /> : (
        <>
          <Card><dl className="dl">
            <dt>Status</dt><dd><StatusBadge status={po.overdue ? 'overdue' : po.status} /></dd>
            <dt>Supplier</dt><dd>{po.supplier}</dd><dt>Deliver to</dt><dd>{po.outlet}</dd>
            <dt>Ordered</dt><dd>{date(po.order_date)}</dd><dt>Expected</dt><dd>{date(po.expected_date)}</dd>
            {po.received_date && <><dt>Received</dt><dd>{date(po.received_date)}</dd></>}
            {po.notes && <><dt>Notes</dt><dd>{po.notes}</dd></>}
          </dl></Card>
          <Card flush title={open ? 'Items - adjust quantities if the delivery differs' : 'Items'}>
            <DataTable rows={po.items} sortable={false} columns={[
              { key: 'product', label: 'Product', render: (i) => <><b>{i.product}</b><div className="small muted">{i.sku}</div></> },
              { key: 'quantity', label: open ? 'Received qty' : 'Quantity', align: 'right', render: (i) => open && isManager
                ? <input className="input" type="number" min="0" step="any" style={{ width: 84 }} value={qty(i)} aria-label="Received quantity"
                    onChange={(e) => setReceived((r) => ({ ...(r || {}), [i.product_id]: e.target.value }))} />
                : `${num(i.quantity, 1)} ${i.unit}` },
              { key: 'unit_cost', label: 'Unit cost', format: 'currency' },
              { key: 'line_total', label: 'Total', format: 'currency' },
            ]} />
            <div className="pager"><span>Order value</span><b style={{ color: 'var(--text)' }}>{money(po.total_cost, { decimals: true })}</b></div>
          </Card>
        </>
      )}
    </Drawer>
  )
}

function NewPO({ onClose, onCreated }) {
  const { outletId } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const sups = useSuppliers()
  const [supplier, setSupplier] = useState('')
  const [outlet, setOutlet] = useState(outletId)
  const [expected, setExpected] = useState('')
  const [lines, setLines] = useState([])
  const add = (p) => setLines((ls) => (ls.some((l) => l.product.id === p.id) ? ls : [...ls, { product: p, quantity: 10, unit_cost: p.cost_price }]))
  const total = lines.reduce((a, l) => a + Number(l.quantity || 0) * Number(l.unit_cost || 0), 0)
  const m = useMutation({
    mutationFn: () => api('/purchase-orders', { method: 'POST', body: { supplier_id: Number(supplier), outlet_id: outlet, expected_date: expected || null,
      items: lines.map((l) => ({ product_id: l.product.id, quantity: Number(l.quantity), unit_cost: Number(l.unit_cost) })) } }),
    onSuccess: (po) => { toast(`Purchase order ${po.po_number} created`, 'success'); qc.invalidateQueries({ queryKey: ['pos'] }); qc.invalidateQueries({ queryKey: ['suppliers'] }); onCreated() },
    onError: (e) => toast(e.message, 'error'),
  })
  return (
    <Modal title="New purchase order" wide onClose={onClose} footer={<>
      <span className="muted" style={{ marginRight: 'auto' }}>Order value {money(total, { decimals: true })}</span>
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn primary" disabled={!supplier || !outlet || !lines.length || m.isPending} onClick={() => m.mutate()}>Create order</button>
    </>}>
      <div className="form-grid">
        <Field label="Supplier">
          <select className="select" value={supplier} onChange={(e) => setSupplier(e.target.value)}>
            <option value="">Choose…</option>{(sups.data || []).filter((s) => s.is_active).map((s) => <option key={s.id} value={s.id}>{s.name} ({s.lead_time_days}d)</option>)}
          </select>
        </Field>
        <Field label="Deliver to outlet"><OutletSelect value={outlet} onChange={setOutlet} /></Field>
        <Field label="Expected delivery" hint="Defaults to today + supplier lead time"><input className="input" type="date" value={expected} onChange={(e) => setExpected(e.target.value)} /></Field>
      </div>
      <Field label="Add products"><ProductSearch onPick={add} /></Field>
      {lines.length > 0 && (
        <div className="table-wrap"><table className="table">
          <thead><tr><th>Product</th><th className="num">Quantity</th><th className="num">Unit cost</th><th className="num">Total</th><th /></tr></thead>
          <tbody>{lines.map((l, i) => (
            <tr key={l.product.id}>
              <td><b>{l.product.name}</b>{l.product.supplier && String(l.product.supplier_id) !== supplier && <div><Badge tone="warn">usually from {l.product.supplier}</Badge></div>}</td>
              <td className="num"><input className="input" type="number" min="0.1" step="any" style={{ width: 84 }} value={l.quantity} onChange={(e) => setLines((ls) => ls.map((x, j) => (j === i ? { ...x, quantity: e.target.value } : x)))} aria-label="Quantity" /></td>
              <td className="num"><input className="input" type="number" min="0" step="any" style={{ width: 90 }} value={l.unit_cost} onChange={(e) => setLines((ls) => ls.map((x, j) => (j === i ? { ...x, unit_cost: e.target.value } : x)))} aria-label="Unit cost" /></td>
              <td className="num">{money(Number(l.quantity) * Number(l.unit_cost), { decimals: true })}</td>
              <td><button className="btn ghost sm icon" aria-label="Remove" onClick={() => setLines((ls) => ls.filter((_, j) => j !== i))}><Trash2 /></button></td>
            </tr>))}
          </tbody>
        </table></div>
      )}
      <p className="small muted">Tip: the Inventory → Reorder tab creates purchase orders automatically from demand.</p>
    </Modal>
  )
}
