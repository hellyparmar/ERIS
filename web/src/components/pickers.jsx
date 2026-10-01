import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { money, num } from '../lib/format'
import { useDebounced } from './ui'

/** Typeahead product search; calls onPick(product). */
export function ProductSearch({ onPick, placeholder = 'Search product name or SKU…', autoFocus = false }) {
  const [text, setText] = useState('')
  const [open, setOpen] = useState(false)
  const q = useDebounced(text, 200)
  const res = useQuery({
    queryKey: ['product-search', q],
    queryFn: () => api('/products', { params: { search: q, page_size: 8, sort: 'revenue' } }),
    enabled: open,
    staleTime: 30_000,
  })
  return (
    <div style={{ position: 'relative' }}>
      <div className="search">
        <Search />
        <input className="input" style={{ width: '100%' }} value={text} placeholder={placeholder} autoFocus={autoFocus}
          onChange={(e) => { setText(e.target.value); setOpen(true) }} onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)} aria-label="Search products" />
      </div>
      {open && res.data?.items?.length > 0 && (
        <div className="card" style={{ position: 'absolute', left: 0, right: 0, top: 38, zIndex: 10, padding: 4, maxHeight: 300, overflowY: 'auto' }}>
          {res.data.items.map((p) => (
            <button type="button" key={p.id} className="btn ghost" style={{ width: '100%', justifyContent: 'space-between', height: 'auto', padding: '7px 8px' }}
              onMouseDown={(e) => { e.preventDefault(); onPick(p); setText(''); setOpen(false) }}>
              <span style={{ textAlign: 'left' }}><b>{p.name}</b><br /><span className="small muted">{p.sku} · {p.category} · stock {num(p.stock)}</span></span>
              <span className="tabular">{money(p.selling_price)}</span>
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

export function useCategories() {
  return useQuery({ queryKey: ['categories'], queryFn: () => api('/categories'), staleTime: 300_000 })
}

export function useSuppliers() {
  return useQuery({ queryKey: ['suppliers'], queryFn: () => api('/suppliers'), staleTime: 120_000 })
}
