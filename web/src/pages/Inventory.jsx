import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeftRight, Boxes, ClipboardList, Download, History, PackagePlus, Search, SlidersHorizontal } from 'lucide-react'
import { api, download } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { dateTime, money, num, titleCase } from '../lib/format'
import { Badge, Card, DataTable, ErrorState, Field, Kpi, Modal, PageHead, Pager, Spinner, StatusBadge, Tabs, useDebounced } from '../components/ui'
import { OutletSelect, ProductSearch, useCategories } from '../components/pickers'

export default function Inventory() {
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || 'stock'
  const { isManager } = useApp()
  const [transfer, setTransfer] = useState(false)
  return (
    <>
      <PageHead title="Inventory" subtitle="Stock on hand at every outlet, with days of cover based on recent demand.">
        {isManager && <button className="btn" onClick={() => setTransfer(true)}><ArrowLeftRight />Transfer stock</button>}
      </PageHead>
      <Tabs value={tab} onChange={(t) => setParams({ tab: t })} tabs={[
        { id: 'stock', label: 'Stock levels', icon: Boxes },
        { id: 'reorder', label: 'Reorder suggestions', icon: ClipboardList },
        { id: 'movements', label: 'Stock movements', icon: History },
      ]} />
      {tab === 'stock' && <StockTab initialStatus={params.get('status') || ''} />}
      {tab === 'reorder' && <ReorderTab />}
      {tab === 'movements' && <MovementsTab />}
      {transfer && <TransferModal onClose={() => setTransfer(false)} />}
    </>
  )
}

function StockTab({ initialStatus }) {
  const { outletId, isManager } = useApp()
  const cats = useCategories()
  const [status, setStatus] = useState(initialStatus)
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [adjust, setAdjust] = useState(null)
  useEffect(() => setStatus(initialStatus), [initialStatus])
  const s = useDebounced(search)
  const params = { outlet_id: outletId, status, category_id: category, search: s, page, page_size: 30 }
  const q = useQuery({ queryKey: ['inventory', params], queryFn: () => api('/inventory', { params }), placeholderData: (p) => p })
  const sum = q.data?.summary
  return (
    <>
      <div className="grid grid-4">
        <Kpi label="Stock value (at cost)" value={sum ? money(sum.stock_value, { compact: true }) : '…'} hint={sum ? `${num(sum.lines)} stock lines` : ''} />
        <Kpi label="Out of stock" value={sum ? num(sum.out_of_stock) : '…'} hint="items that normally sell" />
        <Kpi label="Below reorder level" value={sum ? num(sum.low) : '…'} hint="reorder soon" />
        <Kpi label="Filter" value={<span style={{ fontSize: 15 }}>{status ? titleCase(status) : 'All items'}</span>} hint={outletId ? 'one outlet' : 'all outlets'} />
      </div>
      <Card flush>
        <div className="row" style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
          <div className="search"><Search /><input className="input" placeholder="Product or SKU" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} aria-label="Search stock" /></div>
          <select className="select" value={category} onChange={(e) => { setCategory(e.target.value); setPage(1) }} aria-label="Category">
            <option value="">All categories</option>{(cats.data || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select className="select" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }} aria-label="Stock status">
            <option value="">All statuses</option><option value="attention">Needs attention</option><option value="out_of_stock">Out of stock</option>
            <option value="low">Low</option><option value="ok">In stock</option>
          </select>
          <button className="btn" style={{ marginLeft: 'auto' }} onClick={() => download('/inventory/export', { outlet_id: outletId })}><Download />Export</button>
        </div>
        {q.isError ? <ErrorState error={q.error} /> : q.isLoading ? <Spinner /> : (
          <>
            <DataTable rows={q.data.items} sortable={false} empty="No stock lines match" columns={[
              { key: 'product', label: 'Product', render: (r) => <><b>{r.product}</b><div className="small muted">{r.sku} · {r.category}</div></> },
              { key: 'outlet', label: 'Outlet' },
              { key: 'quantity', label: 'In stock', align: 'right', render: (r) => <span className="tabular">{num(r.quantity, 1)} <span className="muted small">{r.unit}</span></span> },
              { key: 'reorder_level', label: 'Reorder at', format: 'number' },
              { key: 'avg_daily_demand', label: 'Sells / day', format: 'number' },
              { key: 'days_of_cover', label: 'Days of cover', align: 'right', render: (r) => r.days_of_cover === null ? <span className="muted">-</span> : <span className={r.days_of_cover < 3 ? 'down' : ''}>{num(r.days_of_cover, 1)}</span> },
              { key: 'stock_value', label: 'Value', format: 'currency' },
              { key: 'status', label: 'Status', format: 'status' },
              ...(isManager ? [{ key: 'act', label: '', render: (r) => <button className="btn sm" onClick={() => setAdjust(r)}><SlidersHorizontal />Adjust</button> }] : []),
            ]} />
            <Pager page={page} pages={q.data.pages} total={q.data.total} onPage={setPage} label="stock lines" />
          </>
        )}
      </Card>
      {adjust && <AdjustModal row={adjust} onClose={() => setAdjust(null)} />}
    </>
  )
}

function AdjustModal({ row, onClose }) {
  const qc = useQueryClient()
  const toast = useToast()
  const [mode, setMode] = useState('set')
  const [quantity, setQuantity] = useState(row.quantity)
  const [reason, setReason] = useState('adjustment')
  const [note, setNote] = useState('')
  const [reorder, setReorder] = useState(row.reorder_level)
  const m = useMutation({
    mutationFn: async () => {
      if (Number(reorder) !== row.reorder_level) await api(`/inventory/${row.id}`, { method: 'PATCH', body: { reorder_level: Number(reorder) } })
      if (!(mode === 'set' && Number(quantity) === row.quantity)) {
        await api('/inventory/adjust', { method: 'POST', body: { outlet_id: row.outlet_id, product_id: row.product_id, mode, quantity: Number(quantity), reason, note: note || null } })
      }
    },
    onSuccess: () => { toast('Stock updated', 'success'); qc.invalidateQueries({ queryKey: ['inventory'] }); qc.invalidateQueries({ queryKey: ['alerts'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  const after = mode === 'set' ? Number(quantity) : mode === 'add' ? row.quantity + Number(quantity) : row.quantity - Number(quantity)
  return (
    <Modal title={`Adjust stock - ${row.product}`} onClose={onClose} footer={<>
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn primary" disabled={m.isPending || after < 0 || Number.isNaN(after)} onClick={() => m.mutate()}>Save</button>
    </>}>
      <p className="text-2">{row.outlet} · currently <b>{num(row.quantity, 1)} {row.unit}</b></p>
      <div className="form-grid">
        <Field label="Change">
          <select className="select" value={mode} onChange={(e) => { setMode(e.target.value); setQuantity(e.target.value === 'set' ? row.quantity : 0) }}>
            <option value="set">Set counted quantity (stock-take)</option><option value="add">Add stock</option><option value="remove">Remove stock</option>
          </select>
        </Field>
        <Field label="Quantity"><input className="input" type="number" min="0" step="any" value={quantity} onChange={(e) => setQuantity(e.target.value)} /></Field>
        <Field label="Reason">
          <select className="select" value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="adjustment">Stock count / correction</option><option value="damage">Damaged / expired</option><option value="purchase">Received without PO</option>
          </select>
        </Field>
        <Field label="Reorder level" hint="Alert when stock falls to this"><input className="input" type="number" min="0" step="any" value={reorder} onChange={(e) => setReorder(e.target.value)} /></Field>
        <Field label="Note" className="full"><input className="input" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional" /></Field>
      </div>
      <p className={after < 0 ? 'down' : 'muted'}>New quantity: <b>{Number.isNaN(after) ? '-' : num(after, 1)}</b>{after < 0 && ' - cannot go below zero'}</p>
    </Modal>
  )
}

function TransferModal({ onClose }) {
  const { outletId } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const [from, setFrom] = useState(outletId)
  const [to, setTo] = useState(null)
  const [product, setProduct] = useState(null)
  const [qty, setQty] = useState(1)
  const m = useMutation({
    mutationFn: () => api('/inventory/transfer', { method: 'POST', body: { from_outlet_id: from, to_outlet_id: to, product_id: product.id, quantity: Number(qty) } }),
    onSuccess: () => { toast('Stock transferred', 'success'); qc.invalidateQueries({ queryKey: ['inventory'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  return (
    <Modal title="Transfer stock between outlets" onClose={onClose} footer={<>
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn primary" disabled={!from || !to || from === to || !product || !(qty > 0) || m.isPending} onClick={() => m.mutate()}>Transfer</button>
    </>}>
      <div className="form-grid">
        <Field label="From outlet"><OutletSelect value={from} onChange={setFrom} /></Field>
        <Field label="To outlet"><OutletSelect value={to} onChange={setTo} includeInactive={false} /></Field>
      </div>
      <Field label="Product">{product ? <div className="row"><Badge tone="info">{product.name}</Badge><button className="btn sm" onClick={() => setProduct(null)}>Change</button></div> : <ProductSearch onPick={setProduct} />}</Field>
      <Field label="Quantity"><input className="input" type="number" min="0.1" step="any" value={qty} onChange={(e) => setQty(e.target.value)} /></Field>
      {from && to && from === to && <p className="down small">Choose two different outlets.</p>}
    </Modal>
  )
}

function ReorderTab() {
  const { outletId, isManager } = useApp()
  const qc = useQueryClient()
  const toast = useToast()
  const q = useQuery({ queryKey: ['reorder', outletId], queryFn: () => api('/inventory/reorder-suggestions', { params: { outlet_id: outletId } }) })
  const [picked, setPicked] = useState({})
  const rows = useMemo(() => (q.data?.items || []).map((r) => ({ ...r, id: `${r.outlet_id}-${r.product_id}` })), [q.data])
  useEffect(() => {
    setPicked(Object.fromEntries(rows.map((r) => [r.id, { on: r.urgency === 'critical', qty: r.suggested_qty }])))
  }, [rows])
  const chosen = rows.filter((r) => picked[r.id]?.on && picked[r.id]?.qty > 0)
  const cost = chosen.reduce((a, r) => a + picked[r.id].qty * r.unit_cost, 0)
  const m = useMutation({
    mutationFn: () => api('/inventory/reorder', { method: 'POST', body: { lines: chosen.map((r) => ({ outlet_id: r.outlet_id, product_id: r.product_id, quantity: Number(picked[r.id].qty) })) } }),
    onSuccess: (res) => { toast(`Created ${res.created.length} purchase order(s): ${res.created.join(', ')}`, 'success'); qc.invalidateQueries() },
    onError: (e) => toast(e.message, 'error'),
  })
  if (q.isLoading) return <Spinner />
  if (q.isError) return <ErrorState error={q.error} />
  return (
    <Card flush title="What to order now" subtitle="Based on the last 28 days of demand (trend-adjusted), supplier lead times, safety stock and orders already on the way."
      actions={isManager && rows.length > 0 && <button className="btn primary" disabled={!chosen.length || m.isPending} onClick={() => m.mutate()}><PackagePlus />Create {chosen.length} PO line{chosen.length === 1 ? '' : 's'} · {money(cost)}</button>}>
      {rows.length === 0 ? <div className="empty"><Boxes /><b>Nothing to reorder</b><div className="small">Stock covers expected demand plus supplier lead times.</div></div> : (
        <DataTable rows={rows} sortable={false} columns={[
          { key: 'pick', label: '', render: (r) => <input type="checkbox" aria-label={`Order ${r.product}`} checked={!!picked[r.id]?.on} disabled={!isManager}
            onChange={(e) => setPicked((p) => ({ ...p, [r.id]: { ...p[r.id], on: e.target.checked } }))} /> },
          { key: 'product', label: 'Product', render: (r) => <><b>{r.product}</b><div className="small muted">{r.supplier || 'No supplier'} · lead time {r.lead_time_days}d</div></> },
          { key: 'outlet', label: 'Outlet' },
          { key: 'current_stock', label: 'In stock', format: 'number' },
          { key: 'on_order', label: 'On order', format: 'number' },
          { key: 'avg_daily_demand', label: 'Sells / day', format: 'number' },
          { key: 'days_of_cover', label: 'Days left', format: 'number' },
          { key: 'qty', label: 'Order qty', align: 'right', render: (r) => <input className="input" type="number" min="0" style={{ width: 80 }} value={picked[r.id]?.qty ?? r.suggested_qty} disabled={!isManager}
            onChange={(e) => setPicked((p) => ({ ...p, [r.id]: { on: true, qty: Number(e.target.value) } }))} aria-label="Order quantity" /> },
          { key: 'estimated_cost', label: 'Est. cost', format: 'currency' },
          { key: 'urgency', label: 'Urgency', render: (r) => <StatusBadge status={r.urgency} /> },
        ]} />
      )}
    </Card>
  )
}

function MovementsTab() {
  const { outletId } = useApp()
  const [reason, setReason] = useState('')
  const [page, setPage] = useState(1)
  const params = { outlet_id: outletId, reason, page, page_size: 30 }
  const q = useQuery({ queryKey: ['movements', params], queryFn: () => api('/inventory/movements', { params }), placeholderData: (p) => p })
  return (
    <Card flush>
      <div className="row" style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
        <select className="select" value={reason} onChange={(e) => { setReason(e.target.value); setPage(1) }} aria-label="Reason">
          <option value="">All movements</option>
          {['sale', 'sale_void', 'purchase', 'adjustment', 'damage', 'transfer_in', 'transfer_out', 'import'].map((r) => <option key={r} value={r}>{titleCase(r)}</option>)}
        </select>
        <span className="small muted">Every stock change is recorded with who made it and why.</span>
      </div>
      {q.isLoading ? <Spinner /> : q.isError ? <ErrorState error={q.error} /> : (
        <>
          <DataTable rows={q.data.items} sortable={false} columns={[
            { key: 'created_at', label: 'When', render: (r) => dateTime(r.created_at) },
            { key: 'product', label: 'Product' }, { key: 'outlet', label: 'Outlet' },
            { key: 'reason', label: 'Reason', render: (r) => titleCase(r.reason) },
            { key: 'change', label: 'Change', align: 'right', render: (r) => <span className={r.change >= 0 ? 'up' : 'down'}>{r.change > 0 ? '+' : ''}{num(r.change, 1)}</span> },
            { key: 'balance_after', label: 'Balance', format: 'number' },
            { key: 'reference', label: 'Reference', render: (r) => <>{r.reference}{r.note && <div className="small muted">{r.note}</div>}</> },
            { key: 'user', label: 'By' },
          ]} />
          <Pager page={page} pages={q.data.pages} total={q.data.total} onPage={setPage} label="movements" />
        </>
      )}
    </Card>
  )
}
