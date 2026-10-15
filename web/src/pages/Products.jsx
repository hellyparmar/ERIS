import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Carrot, Download, Pencil, Plus, Search, Tags, Trash2, TrendingUp, Upload, UtensilsCrossed, X } from 'lucide-react'
import { api, download } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { money, num, qty } from '../lib/format'
import { Card, DataTable, Delta, Drawer, ErrorState, Field, Modal, PageHead, Pager, Spinner, StatusBadge, Tabs, useDebounced } from '../components/ui'
import { TrendChart } from '../components/charts'
import { ProductSearch, useCategories, useSuppliers } from '../components/pickers'

const DISH_UNITS = ['plate', 'bowl', 'pcs', 'glass', 'cup', 'can', 'bottle']
const STOCK_UNITS = ['kg', 'L', 'pcs']

/** The menu (dishes and drinks, with their recipes) and the ingredients the kitchens stock. */
export default function Products() {
  const { isManager } = useApp()
  const [params, setParams] = useSearchParams()
  const kind = params.get('tab') === 'ingredients' ? 'ingredient' : 'menu'
  const [edit, setEdit] = useState(null)
  const [detail, setDetail] = useState(null)
  const [catModal, setCatModal] = useState(false)
  const dish = kind === 'menu'
  return (
    <>
      <PageHead title="Menu" subtitle={dish ? 'Dishes, prices and food cost.' : 'What the kitchens stock and buy.'}>
        <button className="btn" onClick={() => download('/products/export')}><Download />Export</button>
        {isManager && <>
          <Link to="/import?type=products" className="btn"><Upload />Import CSV</Link>
          <button className="btn" onClick={() => setCatModal(true)}><Tags />Categories</button>
          <button className="btn primary" onClick={() => setEdit({ kind })}><Plus />{dish ? 'Add dish' : 'Add ingredient'}</button>
        </>}
      </PageHead>
      <Tabs value={dish ? 'menu' : 'ingredients'} onChange={(t) => setParams(t === 'menu' ? {} : { tab: t })} tabs={[
        { id: 'menu', label: 'Dishes', icon: UtensilsCrossed },
        { id: 'ingredients', label: 'Ingredients', icon: Carrot },
      ]} />
      <ItemList key={kind} kind={kind} onOpen={setDetail} onEdit={setEdit} />
      {edit && (edit.kind === 'ingredient' ? <IngredientForm item={edit} onClose={() => setEdit(null)} /> : <DishForm dish={edit} onClose={() => setEdit(null)} />)}
      {detail && <ItemDrawer id={detail} onClose={() => setDetail(null)} onEdit={(p) => { setDetail(null); setEdit(p) }} />}
      {catModal && <CategoryModal kind={kind} onClose={() => setCatModal(false)} />}
    </>
  )
}

function ItemList({ kind, onOpen, onEdit }) {
  const { isManager } = useApp()
  const dish = kind === 'menu'
  const cats = useCategories(kind)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState(dish ? 'revenue' : 'name')
  const [page, setPage] = useState(1)
  const s = useDebounced(search)
  const params = { kind, search: s, category_id: category, active: 'true', sort, page, page_size: 30 }
  const q = useQuery({ queryKey: ['products', params], queryFn: () => api('/products', { params }), placeholderData: (p) => p })
  const edit = isManager ? [{ key: 'e', label: '', render: (r) => <button className="btn sm icon ghost" aria-label={`Edit ${r.name}`} onClick={(e) => { e.stopPropagation(); onEdit(r) }}><Pencil /></button> }] : []
  const columns = dish ? [
    { key: 'name', label: 'Dish', render: (r) => <><b>{r.name}</b><div className="small muted">{r.sku} · {r.category}</div></> },
    { key: 'selling_price', label: 'Price', format: 'currency' },
    { key: 'cost_price', label: 'Food cost', render: (r) => <>{money(r.cost_price)} <span className="muted small">· {r.food_cost_pct}%</span></>, align: 'right' },
    { key: 'units_30d', label: 'Ordered (30d)', format: 'number' },
    { key: 'revenue_30d', label: 'Revenue (30d)', format: 'currency' },
    ...edit,
  ] : [
    { key: 'name', label: 'Ingredient', render: (r) => <><b>{r.name}</b><div className="small muted">{r.sku} · {r.category}</div></> },
    { key: 'supplier', label: 'Supplier', render: (r) => r.supplier || <span className="muted">-</span> },
    { key: 'cost_price', label: 'Cost', render: (r) => <>{money(r.cost_price, { decimals: true })} <span className="muted small">/ {r.unit}</span></>, align: 'right' },
    { key: 'stock', label: 'In stock', render: (r) => `${qty(r.stock)} ${r.unit}`, align: 'right' },
    { key: 'units_30d', label: 'Used (30d)', render: (r) => `${qty(r.units_30d)} ${r.unit}`, align: 'right' },
    ...edit,
  ]
  return (
    <Card flush>
      <div className="row" style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
        <div className="search"><Search /><input className="input" placeholder="Name or code" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} aria-label={dish ? 'Search dishes' : 'Search ingredients'} /></div>
        <select className="select" value={category} onChange={(e) => { setCategory(e.target.value); setPage(1) }} aria-label="Category">
          <option value="">All categories</option>{(cats.data || []).map((c) => <option key={c.id} value={c.id}>{c.name} ({c.products})</option>)}
        </select>
        <select className="select" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
          {dish ? <>
            <option value="revenue">Sort: revenue (30d)</option><option value="units">Most ordered</option>
            <option value="food_cost">Highest food cost %</option><option value="price">Price</option><option value="name">Name</option>
          </> : <>
            <option value="name">Sort: name</option><option value="units">Most used</option><option value="stock">Lowest stock</option>
          </>}
        </select>
      </div>
      {q.isError ? <ErrorState error={q.error} /> : q.isLoading ? <Spinner /> : (
        <>
          <DataTable rows={q.data.items} onRowClick={(r) => onOpen(r.id)} sortable={false} columns={columns} />
          <Pager page={page} pages={q.data.pages} total={q.data.total} onPage={setPage} label={dish ? 'dishes' : 'ingredients'} />
        </>
      )}
    </Card>
  )
}

function useSave(item, onClose, label) {
  const qc = useQueryClient()
  const toast = useToast()
  const isNew = !item.id
  const done = (msg) => { toast(msg, 'success'); qc.invalidateQueries({ queryKey: ['products'] }); qc.invalidateQueries({ queryKey: ['product'] }); qc.invalidateQueries({ queryKey: ['categories'] }); onClose() }
  const save = useMutation({
    mutationFn: (body) => api(isNew ? '/products' : `/products/${item.id}`, { method: isNew ? 'POST' : 'PUT', body }),
    onSuccess: () => done(isNew ? `${label} added` : `${label} saved`),
    onError: (e) => toast(e.message, 'error'),
  })
  const del = useMutation({
    mutationFn: () => api(`/products/${item.id}`, { method: 'DELETE' }),
    onSuccess: (r) => done(r.message || `${label} deleted`),
    onError: (e) => toast(e.message, 'error'),
  })
  return { save, del, isNew }
}

function DishForm({ dish, onClose }) {
  const cats = useCategories('menu')
  const detail = useQuery({ queryKey: ['product', dish.id], queryFn: () => api(`/products/${dish.id}`), enabled: Boolean(dish.id) })
  const { save, del, isNew } = useSave(dish, onClose, 'Dish')
  const [f, setF] = useState({
    sku: dish.sku || '', name: dish.name || '', category_id: dish.category_id || '', unit: dish.unit || 'plate',
    selling_price: dish.selling_price ?? '', tax_rate: dish.tax_rate ?? 5, is_active: dish.is_active ?? true,
  })
  const [lines, setLines] = useState(null) // null = not loaded yet (editing) -> use the saved recipe
  const recipe = lines ?? (detail.data?.recipe || []).map((r) => ({ ingredient_id: r.ingredient_id, name: r.ingredient, unit: r.unit, unit_cost: r.unit_cost, quantity: r.quantity }))
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }))
  const setLine = (i, patch) => setLines(recipe.map((l, k) => (k === i ? { ...l, ...patch } : l)))
  const cost = recipe.reduce((a, l) => a + (Number(l.quantity) || 0) * (l.unit_cost || 0), 0)
  const net = Number(f.selling_price) / (1 + Number(f.tax_rate) / 100)
  const submit = () => save.mutate({
    kind: 'menu', ...f, category_id: Number(f.category_id), supplier_id: null, cost_price: Math.round(cost * 100) / 100,
    selling_price: Number(f.selling_price), tax_rate: Number(f.tax_rate), reorder_level: 0, hsn_code: dish.hsn_code || '996331',
    recipe: recipe.filter((l) => Number(l.quantity) > 0).map((l) => ({ ingredient_id: l.ingredient_id, quantity: Number(l.quantity) })),
  })
  return (
    <Modal wide title={isNew ? 'Add dish' : `Edit ${dish.name}`} onClose={onClose} footer={<>
      {!isNew && <button className="btn danger" style={{ marginRight: 'auto' }} onClick={() => window.confirm('Delete this dish? Dishes with sales are taken off the menu instead.') && del.mutate()}><Trash2 />Delete</button>}
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn primary" disabled={save.isPending || (!isNew && detail.isLoading)} onClick={submit}>Save</button>
    </>}>
      <form className="form-grid" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <Field label="Code"><input className="input" value={f.sku} onChange={(e) => set('sku', e.target.value.toUpperCase())} required placeholder="e.g. STR-009" /></Field>
        <Field label="Name"><input className="input" value={f.name} onChange={(e) => set('name', e.target.value)} required /></Field>
        <Field label="Menu category">
          <select className="select" value={f.category_id} onChange={(e) => set('category_id', e.target.value)} required>
            <option value="">Choose…</option>{(cats.data || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Served as">
          <select className="select" value={f.unit} onChange={(e) => set('unit', e.target.value)}>{DISH_UNITS.map((u) => <option key={u}>{u}</option>)}</select>
        </Field>
        <Field label="Menu price incl. GST (₹)"><input className="input" type="number" min="1" step="any" value={f.selling_price} onChange={(e) => set('selling_price', e.target.value)} required /></Field>
        <Field label="Status">
          <select className="select" value={String(f.is_active)} onChange={(e) => set('is_active', e.target.value === 'true')}><option value="true">On the menu</option><option value="false">Off the menu</option></select>
        </Field>
      </form>
      <div className="stack" style={{ gap: 8, marginTop: 14 }}>
        <div className="row between">
          <h4 style={{ margin: 0 }}>Recipe <span className="muted small" style={{ fontWeight: 400 }}>· per portion</span></h4>
          <span className="small">Food cost <b>{money(cost, { decimals: true })}</b>{net > 0 && <span className="muted"> · {((cost / net) * 100).toFixed(1)}% of price</span>}</span>
        </div>
        {recipe.length === 0 && <p className="small muted" style={{ margin: 0 }}>Add the ingredients one portion uses - every sale then draws them from the kitchen's stock.</p>}
        {recipe.map((l, i) => (
          <div className="row" key={l.ingredient_id} style={{ flexWrap: 'nowrap' }}>
            <span style={{ flex: 1, minWidth: 0 }}>{l.name}</span>
            <input className="input" type="number" min="0" step="any" style={{ width: 96 }} value={l.quantity} aria-label={`${l.name} quantity`}
              onChange={(e) => setLine(i, { quantity: e.target.value })} />
            <span className="muted small" style={{ width: 28 }}>{l.unit}</span>
            <span className="small tabular" style={{ width: 70, textAlign: 'right' }}>{money((Number(l.quantity) || 0) * l.unit_cost, { decimals: true })}</span>
            <button type="button" className="btn sm icon ghost" aria-label={`Remove ${l.name}`} onClick={() => setLines(recipe.filter((_, k) => k !== i))}><X /></button>
          </div>
        ))}
        <ProductSearch kind="ingredient" placeholder="Add an ingredient…" onPick={(p) => recipe.some((l) => l.ingredient_id === p.id) || setLines([...recipe, { ingredient_id: p.id, name: p.name, unit: p.unit, unit_cost: p.cost_price, quantity: '' }])} />
      </div>
    </Modal>
  )
}

function IngredientForm({ item, onClose }) {
  const cats = useCategories('ingredient')
  const sups = useSuppliers()
  const { save, del, isNew } = useSave(item, onClose, 'Ingredient')
  const [f, setF] = useState({
    sku: item.sku || '', name: item.name || '', category_id: item.category_id || '', supplier_id: item.supplier_id || '',
    unit: item.unit || 'kg', cost_price: item.cost_price ?? '', reorder_level: item.reorder_level ?? 0, is_active: item.is_active ?? true,
  })
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }))
  const submit = () => save.mutate({
    kind: 'ingredient', ...f, category_id: Number(f.category_id), supplier_id: f.supplier_id ? Number(f.supplier_id) : null,
    cost_price: Number(f.cost_price), selling_price: 0, tax_rate: 0, reorder_level: Number(f.reorder_level), hsn_code: null,
  })
  return (
    <Modal title={isNew ? 'Add ingredient' : `Edit ${item.name}`} onClose={onClose} footer={<>
      {!isNew && <button className="btn danger" style={{ marginRight: 'auto' }} onClick={() => window.confirm('Delete this ingredient? Ingredients with history are deactivated instead.') && del.mutate()}><Trash2 />Delete</button>}
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn primary" disabled={save.isPending} onClick={submit}>Save</button>
    </>}>
      <form className="form-grid" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <Field label="Code"><input className="input" value={f.sku} onChange={(e) => set('sku', e.target.value.toUpperCase())} required placeholder="e.g. ING-039" /></Field>
        <Field label="Name"><input className="input" value={f.name} onChange={(e) => set('name', e.target.value)} required /></Field>
        <Field label="Store category">
          <select className="select" value={f.category_id} onChange={(e) => set('category_id', e.target.value)} required>
            <option value="">Choose…</option>{(cats.data || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Supplier">
          <select className="select" value={f.supplier_id} onChange={(e) => set('supplier_id', e.target.value)}>
            <option value="">None</option>{(sups.data || []).filter((s) => s.is_active).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </Field>
        <Field label="Unit"><select className="select" value={f.unit} onChange={(e) => set('unit', e.target.value)}>{STOCK_UNITS.map((u) => <option key={u}>{u}</option>)}</select></Field>
        <Field label={`Cost per ${f.unit} (₹)`}><input className="input" type="number" min="0" step="any" value={f.cost_price} onChange={(e) => set('cost_price', e.target.value)} required /></Field>
        <Field label="Default reorder level" hint={`In ${f.unit}, for new kitchens`}><input className="input" type="number" min="0" step="any" value={f.reorder_level} onChange={(e) => set('reorder_level', e.target.value)} /></Field>
        <Field label="Status">
          <select className="select" value={String(f.is_active)} onChange={(e) => set('is_active', e.target.value === 'true')}><option value="true">In use</option><option value="false">Not in use</option></select>
        </Field>
      </form>
    </Modal>
  )
}

function ItemDrawer({ id, onClose, onEdit }) {
  const { isManager } = useApp()
  const q = useQuery({ queryKey: ['product', id], queryFn: () => api(`/products/${id}`) })
  const p = q.data
  return (
    <Drawer title={p?.name || 'Item'} onClose={onClose} actions={p && isManager && <button className="btn sm" onClick={() => onEdit(p)}><Pencil />Edit</button>}>
      {!p ? <Spinner /> : p.kind === 'ingredient' ? <IngredientDetail p={p} /> : <DishDetail p={p} />}
    </Drawer>
  )
}

function DishDetail({ p }) {
  const prev = p.previous_30_days.units
  return (
    <>
      <div className="grid grid-2">
        <Card><div className="small muted">Ordered in the last 30 days</div><div className="kpi-value">{num(p.last_30_days.units)}</div>
          <div className="kpi-foot"><Delta value={prev ? ((p.last_30_days.units - prev) / prev) * 100 : null} /> vs previous 30 days</div></Card>
        <Card><div className="small muted">Revenue (30d)</div><div className="kpi-value">{money(p.last_30_days.revenue, { compact: true })}</div>
          <div className="kpi-foot">{money(p.selling_price)} · food cost {p.food_cost_pct}%</div></Card>
      </div>
      <Card title="Orders per week" actions={<Link className="small" to={`/forecasts?scope=product&id=${p.id}`}><TrendingUp size={13} /> Forecast</Link>}>
        <TrendChart data={p.trend} series={[{ key: 'units', label: 'Orders' }]} format="number" height={170} gran="day" />
      </Card>
      <Card title={`Recipe - ${money(p.cost_price, { decimals: true })} per portion`} flush>
        <DataTable rows={p.recipe} sortable={false} empty="No recipe yet - edit the dish to add one" columns={[
          { key: 'ingredient', label: 'Ingredient' },
          { key: 'quantity', label: 'Per portion', render: (r) => `${qty(r.quantity)} ${r.unit}`, align: 'right' },
          { key: 'cost', label: 'Cost', format: 'currency' },
        ]} />
      </Card>
      {p.portions_by_outlet.length > 0 && (
        <Card title="Portions the kitchens can make now" flush>
          <DataTable rows={p.portions_by_outlet} sortable={false} columns={[
            { key: 'outlet', label: 'Restaurant' }, { key: 'portions', label: 'Portions', format: 'number' },
            { key: 'limited_by', label: 'Runs short first' },
          ]} />
        </Card>
      )}
      {p.bought_with.length > 0 && (
        <Card title="Often ordered with">
          <div className="stack">{p.bought_with.map((b) => {
            const other = b.product_a_id === p.id ? b.product_b : b.product_a
            return <div className="row between" key={other}><span>{other}</span><span className="small muted">{b.lift}× lift · {b.bills_together} bills</span></div>
          })}</div>
        </Card>
      )}
    </>
  )
}

function IngredientDetail({ p }) {
  return (
    <>
      <div className="grid grid-2">
        <Card><div className="small muted">In stock (all kitchens)</div><div className="kpi-value">{qty(p.total_stock)} <span className="small muted">{p.unit}</span></div>
          <div className="kpi-foot">Uses about {qty(p.avg_daily_use)} {p.unit} a day</div></Card>
        <Card><div className="small muted">Cost</div><div className="kpi-value">{money(p.cost_price, { decimals: true })}</div>
          <div className="kpi-foot">per {p.unit} · {p.supplier || 'no supplier set'}</div></Card>
      </div>
      <Card title="Stock by kitchen" flush>
        <DataTable rows={p.stock_by_outlet} sortable={false} columns={[
          { key: 'outlet', label: 'Restaurant' }, { key: 'quantity', label: 'In stock', render: (r) => `${qty(r.quantity)} ${p.unit}`, align: 'right' },
          { key: 'avg_daily_demand', label: 'Uses / day', format: 'number' }, { key: 'days_of_cover', label: 'Days of cover', format: 'number' },
          { key: 'status', label: 'Status', format: 'status' },
        ]} />
      </Card>
      <Card title={`Used in ${p.used_in.length} dish${p.used_in.length === 1 ? '' : 'es'}`}>
        <div className="stack">{p.used_in.map((d) => <div className="row between" key={d.id}><span>{d.name}</span><span className="small muted">{qty(d.quantity)} {p.unit} each</span></div>)}</div>
      </Card>
      <Card><dl className="dl">
        <dt>Code</dt><dd>{p.sku}</dd><dt>Category</dt><dd>{p.category}</dd>
        <dt>Status</dt><dd><StatusBadge status={p.is_active ? 'active' : 'inactive'} /></dd>
      </dl></Card>
    </>
  )
}

function CategoryModal({ kind, onClose }) {
  const qc = useQueryClient()
  const toast = useToast()
  const cats = useCategories(kind)
  const [name, setName] = useState('')
  const refresh = () => qc.invalidateQueries({ queryKey: ['categories'] })
  const add = useMutation({ mutationFn: () => api('/categories', { method: 'POST', body: { name } }), onSuccess: () => { setName(''); refresh() }, onError: (e) => toast(e.message, 'error') })
  const rename = useMutation({ mutationFn: ({ id, n }) => api(`/categories/${id}`, { method: 'PUT', body: { name: n } }), onSuccess: refresh, onError: (e) => toast(e.message, 'error') })
  const del = useMutation({ mutationFn: (id) => api(`/categories/${id}`, { method: 'DELETE' }), onSuccess: refresh, onError: (e) => toast(e.message, 'error') })
  return (
    <Modal title={kind === 'menu' ? 'Menu categories' : 'Store categories'} onClose={onClose}>
      <form className="row" onSubmit={(e) => { e.preventDefault(); if (name.trim()) add.mutate() }}>
        <input className="input" style={{ flex: 1 }} placeholder="New category name" value={name} onChange={(e) => setName(e.target.value)} />
        <button className="btn primary" disabled={!name.trim()}><Plus />Add</button>
      </form>
      <DataTable rows={cats.data || []} sortable={false} columns={[
        { key: 'name', label: 'Category' }, { key: 'products', label: kind === 'menu' ? 'Dishes' : 'Ingredients', format: 'number' },
        { key: 'a', label: '', render: (c) => <div className="row" style={{ justifyContent: 'flex-end' }}>
          <button className="btn sm" onClick={() => { const n = window.prompt('Rename category', c.name); if (n && n.trim()) rename.mutate({ id: c.id, n: n.trim() }) }}>Rename</button>
          <button className="btn sm danger" disabled={c.products > 0} title={c.products ? 'Move its items first' : ''} onClick={() => del.mutate(c.id)}>Delete</button>
        </div> },
      ]} />
    </Modal>
  )
}
