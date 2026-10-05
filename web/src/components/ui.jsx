import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Info, Inbox, X, XCircle } from 'lucide-react'
import { formatValue, pct, titleCase } from '../lib/format'

export function Card({ title, subtitle, actions, children, className = '', flush = false }) {
  return (
    <section className={`card ${flush ? 'flush' : ''} ${className}`}>
      {(title || actions) && (
        <div className="card-head">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && <p>{subtitle}</p>}
          </div>
          {actions && <div className="row">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  )
}

export function PageHead({ title, subtitle, children, eyebrow }) {
  return (
    <div className="page-head">
      <div style={{ minWidth: 0 }}>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {children && <div className="page-actions">{children}</div>}
    </div>
  )
}

export function Delta({ value, inverse = false, suffix = '' }) {
  if (value === null || value === undefined) return <span className="muted small">no comparison</span>
  const good = inverse ? value < 0 : value >= 0
  return <span className={`delta ${good ? 'up' : 'down'}`}>{pct(value)}{suffix}</span>
}

/** Small round arrow next to a headline number: direction of change, coloured by whether it is good. */
export function TrendDot({ value, inverse = false }) {
  if (value === null || value === undefined) return null
  const good = inverse ? value < 0 : value >= 0
  const Icon = value >= 0 ? ArrowUp : ArrowDown
  return <span className={`trend-dot ${good ? 'up' : 'down'}`} aria-hidden="true"><Icon /></span>
}

/** KPI tile: label with the change pill on the right, the headline number, one line of context. */
export function Kpi({ label, value, change, hint, loading, spark, inverse = false }) {
  return (
    <div className="card kpi">
      <div className="kpi-top">
        <div className="kpi-label"><span>{label}</span></div>
        {change !== undefined && change !== null && <Delta value={change} inverse={inverse} />}
      </div>
      <div>
        {loading ? <div className="skeleton" style={{ height: 30, width: '70%' }} /> : (
          <div className="kpi-main"><div className="kpi-value">{value}</div><TrendDot value={change} inverse={inverse} /></div>
        )}
        {hint && <div className="kpi-foot" style={{ marginTop: 6 }}>{hint}</div>}
      </div>
      {spark && <div className="kpi-spark">{spark}</div>}
    </div>
  )
}

/** Share-of-total strip with a two-column legend (value and share per item). */
export function SegmentBar({ items, format = (v) => v, thick = false, legend = true }) {
  const total = items.reduce((a, i) => a + (i.value || 0), 0) || 1
  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className={`seg-bar ${thick ? 'thick' : ''}`} role="img" aria-label={items.map((i) => `${i.label} ${Math.round((i.value / total) * 100)}%`).join(', ')}>
        {items.filter((i) => i.value > 0).map((i) => <i key={i.label} style={{ width: `${(i.value / total) * 100}%`, background: i.color }} title={`${i.label}: ${format(i.value)}`} />)}
      </div>
      {legend && (
        <div className="seg-legend">
          {items.map((i) => (
            <div key={i.label}><span><i className="swatch" style={{ background: i.color }} />{i.label}</span><b>{format(i.value)}</b></div>
          ))}
        </div>
      )}
    </div>
  )
}

/** Half-circle gauge for a 0-100 share (e.g. margin, loyalty share). */
export function Gauge({ value, max = 100, label, caption, color = 'var(--s1)', size = 210 }) {
  const r = 80
  const len = Math.PI * r
  const frac = Math.max(0, Math.min(1, (value || 0) / max))
  return (
    <div className="gauge" style={{ width: size, maxWidth: '100%', margin: '0 auto' }}>
      <svg viewBox="0 0 200 112" width="100%" role="img" aria-label={`${label}: ${caption}`}>
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="var(--surface-3)" strokeWidth="14" strokeLinecap="round" />
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={`${len * frac} ${len}`} />
      </svg>
      <div className="label"><b>{label}</b><span>{caption}</span></div>
    </div>
  )
}

const STATUS = {
  ok: ['good', 'In stock'], low: ['warn', 'Low'], out_of_stock: ['bad', 'Out of stock'], no_stock: ['', 'Not stocked'],
  completed: ['good', 'Completed'], void: ['bad', 'Void'], ordered: ['info', 'Ordered'], partial: ['warn', 'Part-delivered'], closed: ['', 'Closed short'], received: ['good', 'Received'],
  cancelled: ['', 'Cancelled'], overdue: ['bad', 'Overdue'], critical: ['bad', 'Critical'], soon: ['warn', 'Soon'],
  active: ['good', 'Active'], inactive: ['', 'Inactive'], admin: ['info', 'Admin'], manager: ['good', 'Manager'], staff: ['', 'Staff'], viewer: ['', 'Viewer'],
}

export function StatusBadge({ status }) {
  const [tone, label] = STATUS[status] || ['', titleCase(status)]
  return <span className={`badge ${tone}`}>{label}</span>
}

export function Badge({ tone = '', children }) {
  return <span className={`badge ${tone}`}>{children}</span>
}

/** Loading state. After a few seconds it explains why: a free hosted server sleeps and needs ~a minute to wake. */
export function Spinner({ label }) {
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 6000)
    return () => clearTimeout(t)
  }, [])
  return (
    <div className="center">
      <div className="loading">
        <div className="row"><div className="spinner" />{label && <span className="muted">{label}</span>}</div>
        {slow && <div className="hint">Still working… the first request after a quiet period can take up to a minute while the server wakes up.</div>}
      </div>
    </div>
  )
}

export function Empty({ title = 'Nothing here yet', children, icon: Icon = Inbox }) {
  return (
    <div className="empty">
      <span className="empty-icon"><Icon aria-hidden="true" /></span>
      <b>{title}</b>
      {children && <div className="small">{children}</div>}
    </div>
  )
}

/** Placeholder grid shown while a page's first data loads. */
export function SkeletonGrid({ cards = 4, rows = 2 }) {
  return (
    <>
      <div className="grid grid-4">{Array.from({ length: cards }, (_, i) => <div key={i} className="skeleton skeleton-card" />)}</div>
      {Array.from({ length: rows }, (_, i) => <div key={i} className="skeleton" style={{ height: 300, borderRadius: 16 }} />)}
    </>
  )
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="empty">
      <span className="empty-icon" style={{ background: 'var(--bad-soft)', color: 'var(--bad-ink)' }}><XCircle aria-hidden="true" /></span>
      <b>Could not load this data</b>
      <div className="small">{error?.message}</div>
      {onRetry && <button className="btn sm" onClick={onRetry}>Try again</button>}
    </div>
  )
}

export function Query({ q, children, loading }) {
  if (q.isLoading) return loading || <Spinner />
  if (q.isError) return <ErrorState error={q.error} onRetry={q.refetch} />
  return children(q.data)
}

export function Modal({ title, onClose, children, footer, wide = false }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal ${wide ? 'wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-head"><h2>{title}</h2><button className="btn ghost icon" onClick={onClose} aria-label="Close"><X /></button></div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  )
}

export function Drawer({ title, onClose, children, actions }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-head" style={{ background: 'var(--surface)' }}>
          <h2>{title}</h2>
          <div className="row">{actions}<button className="btn ghost icon" onClick={onClose} aria-label="Close"><X /></button></div>
        </div>
        <div className="drawer-body">{children}</div>
      </aside>
    </>
  )
}

export function Tabs({ tabs, value, onChange }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={value === t.id} className={value === t.id ? 'on' : ''} onClick={() => onChange(t.id)}>
          {t.icon && <t.icon size={15} aria-hidden="true" />}{t.label}
        </button>
      ))}
    </div>
  )
}

export function Seg({ options, value, onChange, label }) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} className={value === o.value ? 'on' : ''} aria-pressed={value === o.value} onClick={() => onChange(o.value)}>{o.label}</button>
      ))}
    </div>
  )
}

export function Field({ label, children, hint, className = '' }) {
  return <label className={`field ${className}`}><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>
}

export function AlertItem({ alert }) {
  const Icon = alert.severity === 'info' ? Info : AlertTriangle
  return (
    <div className={`alert ${alert.severity}`}>
      <Icon aria-hidden="true" />
      <div><b>{alert.title}</b><p>{alert.message}</p></div>
    </div>
  )
}

/**
 * Data table with optional client-side sorting.
 * columns: [{ key, label, format, align, render(row), sortable, width }]
 */
export function DataTable({ columns, rows, onRowClick, empty = 'No records found', sortable = true, initialSort, maxHeight }) {
  const [sort, setSort] = useState(initialSort || null)
  const sorted = useMemo(() => {
    if (!sort || !rows) return rows || []
    const { key, dir } = sort
    return [...rows].sort((a, b) => {
      const x = a[key]; const y = b[key]
      if (x === y) return 0
      if (x === null || x === undefined) return 1
      if (y === null || y === undefined) return -1
      return (x > y ? 1 : -1) * (dir === 'asc' ? 1 : -1)
    })
  }, [rows, sort])
  if (!rows?.length) return <Empty title={empty} />
  const isNum = (c) => c.align === 'right' || ['currency', 'number', 'percent', 'percent_plain'].includes(c.format)
  return (
    <div className="table-wrap" style={maxHeight ? { maxHeight, overflowY: 'auto' } : undefined}>
      <table className="table">
        <thead>
          <tr>
            {columns.map((c) => {
              const canSort = sortable && c.sortable !== false && !c.render
              return (
                <th key={c.key} className={`${isNum(c) ? 'num' : ''} ${canSort ? 'sortable' : ''}`} style={{ width: c.width }}
                  onClick={canSort ? () => setSort((s) => ({ key: c.key, dir: s?.key === c.key && s.dir === 'desc' ? 'asc' : 'desc' })) : undefined}
                  aria-sort={sort?.key === c.key ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}>
                  {c.label}{sort?.key === c.key ? (sort.dir === 'asc' ? ' ↑' : ' ↓') : ''}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={r.id ?? i} className={onRowClick ? 'clickable' : ''} onClick={onRowClick ? () => onRowClick(r) : undefined}>
              {columns.map((c) => (
                <td key={c.key} className={isNum(c) ? 'num' : ''}>
                  {c.render ? c.render(r) : c.format === 'status' ? <StatusBadge status={r[c.key]} /> : formatValue(r[c.key], c.format)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Pager({ page, pages, total, onPage, label = 'records' }) {
  return (
    <div className="pager">
      <span>{total?.toLocaleString('en-IN')} {label}</span>
      <div className="row">
        <button className="btn sm icon" disabled={page <= 1} onClick={() => onPage(page - 1)} aria-label="Previous page"><ChevronLeft /></button>
        <span>Page {page} of {pages}</span>
        <button className="btn sm icon" disabled={page >= pages} onClick={() => onPage(page + 1)} aria-label="Next page"><ChevronRight /></button>
      </div>
    </div>
  )
}

export function useDebounced(value, ms = 300) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

export function Meter({ value, max, color = 'var(--s1)' }) {
  const w = max ? Math.max(2, Math.min(100, (value / max) * 100)) : 0
  return <div className="bar-meter" aria-hidden="true"><i style={{ width: `${w}%`, background: color }} /></div>
}
