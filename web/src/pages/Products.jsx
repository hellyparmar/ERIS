import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Pencil, Plus, Search, Tags, Trash2, TrendingUp, Upload } from 'lucide-react'
import { api, download } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { money, num } from '../lib/format'
import { Card, DataTable, Delta, Drawer, ErrorState, Field, Modal, PageHead, Pager, Spinner, StatusBadge, useDebounced } from '../components/ui'
import { TrendChart } from '../components/charts'
import { useCategories, useSuppliers } from '../components/pickers'

export default function Products() {
  const { isManager } = useApp()
  const cats = useCategories()
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [active, setActive] = useState('true')
  const [sort, setSort] = useState('revenue')
  const [page, setPage] = useState(1)
  const [edit, setEdit] = useState(null)
  const [detail, setDetail] = useState(null)
  const [catModal, setCatModal] = useState(false)
  const s = useDebounced(search)
  const params = { search: s, category_id: category, active, sort, page, page_size: 30 }
  const q = useQuery({ queryKey: ['products', params], queryFn: () => api('/products', { params }), placeholderData: (p) => p })

  return (
    <>
      <PageHead title="Products" subtitle="Your catalogue with prices, margins, stock and last-30-day sales.">
        <button className="btn" onClick={() => download('/products/export')}><Download />Export</button>
        {isManager && <>
          <Link to="/import?type=products" className="btn"><Upload />Import CSV</Link>
          <button className="btn" onClick={() => setCatModal(true)}><Tags />Categories</button>
          <button className="btn primary" onClick={() => setEdit({})}><Plus />Add product</button>
        </>}
      </PageHead>
      <Card flush>
        <div className="row" style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
          <div className="search"><Search /><input className="input" placeholder="Name or SKU" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} aria-label="Search products" /></div>
          <select className="select" value={category} onChange={(e) => { setCategory(e.target.value); setPage(1) }} aria-label="Category">
            <option value="">All categories</option>{(cats.data || []).map((c) => <option key={c.id} value={c.id}>{c.name} ({c.products})</option>)}
          </select>
          <select className="select" value={active} onChange={(e) => { setActive(e.target.value); setPage(1) }} aria-label="Status">
            <option value="true">Active</option><option value="false">Inactive</option><option value="">All</option>
          </select>
          <select className="select" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
            <option value="revenue">Sort: revenue (30d)</option><option value="units">Units sold (30d)</option><option value="name">Name</option>
            <option value="sku">SKU</option><option value="price">Price</option><option value="stock">Lowest stock</option>
          </select>
        </div>
        {q.isError ? <ErrorState error={q.error} /> : q.isLoading ? <Spinner /> : (
          <>
            <DataTable rows={q.data.items} onRowClick={(r) => setDetail(r.id)} sortable={false} columns={[
              { key: 'name', label: 'Product', render: (r) => <><b>{r.name}</b><div className="small muted">{r.sku} · {r.category}</div></> },
              { key: 'supplier', label: 'Supplier', render: (r) => r.supplier || <span className="muted">-</span> },
              { key: 'selling_price', label: 'Price', format: 'currency' },
              { key: 'cost_price', label: 'Cost', format: 'currency' },
              { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
              { key: 'tax_rate', label: 'GST', render: (r) => `${r.tax_rate}%`, align: 'right' },
              { key: 'stock', label: 'Stock', format: 'number' },
              { key: 'units_30d', label: 'Sold (30d)', format: 'number' },
              { key: 'revenue_30d', label: 'Revenue (30d)', format: 'currency' },
              ...(isManager ? [{ key: 'e', label: '', render: (r) => <button className="btn sm icon ghost" aria-label={`Edit ${r.name}`} onClick={(e) => { e.stopPropagation(); setEdit(r) }}><Pencil /></button> }] : []),
            ]} />
            <Pager page={page} pages={q.data.pages} total={q.data.total} onPage={setPage} label="products" />
          </>
        )}
      </Card>
      {edit && <ProductForm product={edit} onClose={() => setEdit(null)} />}
      {detail && <ProductDrawer id={detail} onClose={() => setDetail(null)} onEdit={(p) => { setDetail(null); setEdit(p) }} />}
      {catModal && <CategoryModal onClose={() => setCatModal(false)} />}
    </>
  )
}

function ProductForm({ product, onClose }) {
  const qc = useQueryClient()
  const toast = useToast()
  const cats = useCategories()
  const sups = useSuppliers()
  const isNew = !product.id
  const [f, setF] = useState({
    sku: product.sku || '', name: product.name || '', category_id: product.category_id || '', supplier_id: product.supplier_id || '',
    unit: product.unit || 'pcs', cost_price: product.cost_price ?? '', selling_price: product.selling_price ?? '',
    tax_rate: product.tax_rate ?? 5, reorder_level: product.reorder_level ?? 10, is_active: product.is_active ?? true,
    hsn_code: product.hsn_code || '',
  })
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }))
  const save = useMutation({
    mutationFn: () => api(isNew ? '/products' : `/products/${product.id}`, { method: isNew ? 'POST' : 'PUT', body: {
      ...f, category_id: Number(f.category_id), supplier_id: f.supplier_id ? Number(f.supplier_id) : null,
      cost_price: Number(f.cost_price), selling_price: Number(f.selling_price), tax_rate: Number(f.tax_rate), reorder_level: Number(f.reorder_level),
      hsn_code: f.hsn_code.trim() || null,
    } }),
    onSuccess: () => { toast(isNew ? 'Product added to every outlet' : 'Product saved', 'success'); qc.invalidateQueries({ queryKey: ['products'] }); qc.invalidateQueries({ queryKey: ['categories'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  const del = useMutation({
    mutationFn: () => api(`/products/${product.id}`, { method: 'DELETE' }),
    onSuccess: (r) => { toast(r.message || 'Product deleted', 'success'); qc.invalidateQueries({ queryKey: ['products'] }); onClose() },
    onError: (e) => toast(e.message, 'error'),
  })
  const net = Number(f.selling_price) / (1 + Number(f.tax_rate) / 100)
  const margin = net ? ((net - Number(f.cost_price)) / net) * 100 : 0
  return (
    <Modal title={isNew ? 'Add product' : `Edit ${product.name}`} onClose={onClose} footer={<>
      {!isNew && <button className="btn danger" style={{ marginRight: 'auto' }} onClick={() => window.confirm('Delete this product? Products with history are deactivated instead.') && del.mutate()}><Trash2 />Delete</button>}
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn primary" disabled={save.isPending} onClick={() => save.mutate()}>Save</button>
    </>}>
      <form className="form-grid" onSubmit={(e) => { e.preventDefault(); save.mutate() }}>
        <Field label="SKU"><input className="input" value={f.sku} onChange={(e) => set('sku', e.target.value.toUpperCase())} required /></Field>
        <Field label="Name"><input className="input" value={f.name} onChange={(e) => set('name', e.target.value)} required /></Field>
        <Field label="Category">
          <select className="select" value={f.category_id} onChange={(e) => set('category_id', e.target.value)} required>
            <option value="">Choose…</option>{(cats.data || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Supplier">
          <select className="select" value={f.supplier_id} onChange={(e) => set('supplier_id', e.target.value)}>
            <option value="">None</option>{(sups.data || []).filter((s) => s.is_active).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </Field>
        <Field label="Unit" hint="pcs, kg, pack, bottle…"><input className="input" value={f.unit} onChange={(e) => set('unit', e.target.value)} /></Field>
        <Field label="GST rate %">
          <select className="select" value={f.tax_rate} onChange={(e) => set('tax_rate', e.target.value)}>{[0, 5, 12, 18, 28].map((t) => <option key={t} value={t}>{t}%</option>)}</select>
        </Field>
        <Field label="HSN code" hint="4-8 digits, printed on GST invoices"><input className="input" inputMode="numeric" maxLength={8} value={f.hsn_code} onChange={(e) => set('hsn_code', e.target.value.replace(/\D/g, ''))} /></Field>
        <Field label="Cost price (₹)"><input className="input" type="number" min="0" step="any" value={f.cost_price} onChange={(e) => set('cost_price', e.target.value)} required /></Field>
        <Field label="Selling price incl. GST (₹)" hint={f.selling_price && f.cost_price ? `Margin ${margin.toFixed(1)}% after tax` : ''}>
          <input className="input" type="number" min="0" step="any" value={f.selling_price} onChange={(e) => set('selling_price', e.target.value)} required />
        </Field>
        <Field label="Default reorder level" hint="Used for new outlets"><input className="input" type="number" min="0" step="any" value={f.reorder_level} onChange={(e) => set('reorder_level', e.target.value)} /></Field>
        <Field label="Status">
          <select className="select" value={String(f.is_active)} onChange={(e) => set('is_active', e.target.value === 'true')}><option value="true">Active</option><option value="false">Inactive (hidden from billing)</option></select>
        </Field>
      </form>
    </Modal>
  )
}

function ProductDrawer({ id, onClose, onEdit }) {
  const { isManager } = useApp()
  const q = useQuery({ queryKey: ['product', id], queryFn: () => api(`/products/${id}`) })
  const p = q.data
  return (
    <Drawer title={p?.name || 'Product'} onClose={onClose} actions={p && isManager && <button className="btn sm" onClick={() => onEdit(p)}><Pencil />Edit</button>}>
      {!p ? <Spinner /> : (
        <>
          <div className="grid grid-2">
            <Card><div className="small muted">Sold in last 30 days</div><div className="kpi-value">{num(p.last_30_days.units)} <span className="small muted">{p.unit}</span></div>
              <div className="kpi-foot"><Delta value={p.previous_30_days.units ? ((p.last_30_days.units - p.previous_30_days.units) / p.previous_30_days.units) * 100 : null} /> vs previous 30 days</div></Card>
            <Card><div className="small muted">Revenue (30d)</div><div className="kpi-value">{money(p.last_30_days.revenue, { compact: true })}</div>
              <div className="kpi-foot">{p.margin_pct}% margin · {money(p.selling_price)} each</div></Card>
          </div>
          <Card title="Weekly units sold" actions={<Link className="small" to={`/forecasts?scope=product&id=${p.id}`}><TrendingUp size={13} /> Forecast</Link>}>
            <TrendChart data={p.trend} series={[{ key: 'units', label: 'Units' }]} format="number" height={180} gran="day" />
          </Card>
          <Card title={`Stock - ${num(p.total_stock)} ${p.unit} in total`} flush>
            <DataTable rows={p.stock_by_outlet} sortable={false} columns={[
              { key: 'outlet', label: 'Outlet' }, { key: 'quantity', label: 'In stock', format: 'number' },
              { key: 'avg_daily_demand', label: 'Sells / day', format: 'number' }, { key: 'days_of_cover', label: 'Days of cover', format: 'number' },
              { key: 'status', label: 'Status', format: 'status' },
            ]} />
          </Card>
          {p.bought_with.length > 0 && (
            <Card title="Frequently bought with" subtitle="Lift = how much more often they're bought together than by chance">
              <div className="stack">{p.bought_with.map((b) => {
                const other = b.product_a_id === p.id ? b.product_b : b.product_a
                return <div className="row between" key={other}><span>{other}</span><span className="small muted">{b.lift}× lift · {b.bills_together} bills</span></div>
              })}</div>
            </Card>
          )}
          <Card><dl className="dl">
            <dt>SKU</dt><dd>{p.sku}</dd><dt>Category</dt><dd>{p.category}</dd><dt>Supplier</dt><dd>{p.supplier || '-'}</dd>
            <dt>Cost / price</dt><dd>{money(p.cost_price, { decimals: true })} / {money(p.selling_price, { decimals: true })} (GST {p.tax_rate}%{p.hsn_code ? `, HSN ${p.hsn_code}` : ''})</dd>
            <dt>Status</dt><dd><StatusBadge status={p.is_active ? 'active' : 'inactive'} /></dd>
          </dl></Card>
        </>
      )}
    </Drawer>
  )
}

function CategoryModal({ onClose }) {
  const qc = useQueryClient()
  const toast = useToast()
  const cats = useCategories()
  const [name, setName] = useState('')
  const refresh = () => qc.invalidateQueries({ queryKey: ['categories'] })
  const add = useMutation({ mutationFn: () => api('/categories', { method: 'POST', body: { name } }), onSuccess: () => { setName(''); refresh() }, onError: (e) => toast(e.message, 'error') })
  const rename = useMutation({ mutationFn: ({ id, n }) => api(`/categories/${id}`, { method: 'PUT', body: { name: n } }), onSuccess: refresh, onError: (e) => toast(e.message, 'error') })
  const del = useMutation({ mutationFn: (id) => api(`/categories/${id}`, { method: 'DELETE' }), onSuccess: refresh, onError: (e) => toast(e.message, 'error') })
  return (
    <Modal title="Categories" onClose={onClose}>
      <form className="row" onSubmit={(e) => { e.preventDefault(); if (name.trim()) add.mutate() }}>
        <input className="input" style={{ flex: 1 }} placeholder="New category name" value={name} onChange={(e) => setName(e.target.value)} />
        <button className="btn primary" disabled={!name.trim()}><Plus />Add</button>
      </form>
      <DataTable rows={cats.data || []} sortable={false} columns={[
        { key: 'name', label: 'Category' }, { key: 'products', label: 'Products', format: 'number' },
        { key: 'a', label: '', render: (c) => <div className="row" style={{ justifyContent: 'flex-end' }}>
          <button className="btn sm" onClick={() => { const n = window.prompt('Rename category', c.name); if (n && n.trim()) rename.mutate({ id: c.id, n: n.trim() }) }}>Rename</button>
          <button className="btn sm danger" disabled={c.products > 0} title={c.products ? 'Move its products first' : ''} onClick={() => del.mutate(c.id)}>Delete</button>
        </div> },
      ]} />
    </Modal>
  )
}
