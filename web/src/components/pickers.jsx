import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { money } from '../lib/format'
import { useDebounced } from './ui'

/** Typeahead search over the menu (kind="menu", most-ordered first) or the ingredients (kind="ingredient");
 * calls onPick(item). */
export function ProductSearch({ onPick, kind = 'menu', placeholder, autoFocus = false }) {
  const [text, setText] = useState('')
  const [open, setOpen] = useState(false)
  const closing = useRef(null) // a pending close after blur, cancelled if the field is used again
  const show = () => { clearTimeout(closing.current); setOpen(true) }
  const q = useDebounced(text, 200)
  const dish = kind === 'menu'
  const res = useQuery({
    queryKey: ['product-search', kind, q],
    queryFn: () => api('/products', { params: dish ? { search: q, kind, page_size: 8, sort: 'revenue' }
      : { search: q, kind, page_size: 8, fields: 'basic' } }),
    enabled: open,
    staleTime: 30_000,
  })
  const label = dish ? 'Search dishes' : 'Search ingredients'
  return (
    <div style={{ position: 'relative' }}>
      <div className="search">
        <Search />
        <input className="input" style={{ width: '100%' }} value={text} placeholder={placeholder || `${label} by name or code…`} autoFocus={autoFocus}
          onChange={(e) => { setText(e.target.value); show() }} onFocus={show}
          onBlur={() => { closing.current = setTimeout(() => setOpen(false), 150) }} aria-label={label} />
      </div>
      {open && res.data?.items?.length > 0 && (
        <div className="card" style={{ position: 'absolute', left: 0, right: 0, top: 38, zIndex: 10, padding: 4, maxHeight: 300, overflowY: 'auto' }}>
          {res.data.items.map((p) => (
            <button type="button" key={p.id} className="btn ghost" style={{ width: '100%', justifyContent: 'space-between', height: 'auto', padding: '7px 8px' }}
              onMouseDown={(e) => { e.preventDefault(); onPick(p); setText(''); setOpen(false) }}>
              <span style={{ textAlign: 'left' }}><b>{p.name}</b><br /><span className="small muted">{p.sku} · {p.category}{dish ? '' : ` · per ${p.unit}`}</span></span>
              <span className="tabular">{money(dish ? p.selling_price : p.cost_price)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export function OutletSelect({ value, onChange, allowAll = false, required = false, includeInactive = false }) {
  const { outlets, user } = useApp()
  const list = outlets.filter((o) => includeInactive || o.is_active)
  return (
    <select className="select" value={value || ''} required={required} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
      disabled={user.role !== 'admin' && list.length <= 1}>
      {allowAll && <option value="">All outlets</option>}
      {!allowAll && !value && <option value="">Choose outlet…</option>}
      {list.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
    </select>
  )
}

/** Categories; kind="menu" or "ingredient" keeps the ones holding that kind of item. */
export function useCategories(kind) {
  return useQuery({ queryKey: ['categories', kind || 'all'], queryFn: () => api('/categories', { params: { kind } }), staleTime: 300_000 })
}

export function useSuppliers() {
  return useQuery({ queryKey: ['suppliers'], queryFn: () => api('/suppliers'), staleTime: 120_000 })
}

export function useGstStates() {
  return useQuery({ queryKey: ['gst-states'], queryFn: () => api('/settings/gst-states'), staleTime: Infinity })
}

/** GST state picker; onChange(code, name). */
export function StateSelect({ value, onChange, placeholder = 'Choose state…' }) {
  const states = useGstStates()
  return (
    <select className="select" value={value || ''} onChange={(e) => {
      const s = (states.data || []).find((x) => x.code === e.target.value)
      onChange(s?.code || null, s?.name || null)
    }}>
      <option value="">{placeholder}</option>
      {(states.data || []).map((s) => <option key={s.code} value={s.code}>{s.code} - {s.name}</option>)}
    </select>
  )
}
