// Number & date formatting (Indian grouping by default, currency symbol from organization settings).
let SYMBOL = '₹'
export const setCurrencySymbol = (s) => { SYMBOL = s || '₹' }

const nf0 = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })
const nf1 = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 })
const nf2 = new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export function money(v, { compact = false, decimals = false } = {}) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '-'
  const n = Number(v)
  const sign = n < 0 ? '-' : ''
  const a = Math.abs(n)
  if (compact && SYMBOL === '₹') {
    if (a >= 1e7) return `${sign}₹${(a / 1e7).toFixed(2)} Cr`
    if (a >= 1e5) return `${sign}₹${(a / 1e5).toFixed(2)} L`
    if (a >= 1e3) return `${sign}₹${(a / 1e3).toFixed(1)}k`
  } else if (compact) {
    if (a >= 1e6) return `${sign}${SYMBOL}${(a / 1e6).toFixed(2)}M`
    if (a >= 1e3) return `${sign}${SYMBOL}${(a / 1e3).toFixed(1)}k`
  }
  return `${sign}${SYMBOL}${(decimals ? nf2 : nf0).format(a)}`
}

export const num = (v, digits = 0) =>
  v === null || v === undefined ? '-' : (digits ? nf1 : nf0).format(Number(v))

export const pct = (v, { signed = true } = {}) =>
  v === null || v === undefined ? '-' : `${signed && v > 0 ? '+' : ''}${Number(v).toFixed(1)}%`

export const date = (d, opts = { day: '2-digit', month: 'short', year: 'numeric' }) =>
  d ? new Date(d.length === 10 ? `${d}T00:00:00` : d).toLocaleDateString('en-IN', opts) : '-'

export const shortDate = (d) => date(d, { day: '2-digit', month: 'short' })
export const monthLabel = (d) => date(d, { month: 'short', year: '2-digit' })
export const dateTime = (d) =>
  d ? new Date(d).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'

export const titleCase = (s) => (s || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export function formatValue(v, format) {
  switch (format) {
    case 'currency': return money(v)
    case 'percent': return pct(v)
    case 'percent_plain': return v === null || v === undefined ? '-' : `${Number(v).toFixed(1)}%`
    case 'number': return typeof v === 'number' ? num(v, Number.isInteger(v) ? 0 : 1) : v ?? '-'
    case 'date': return date(v)
    default: return v ?? '-'
  }
}

export const isoDay = (d) => {
  const x = new Date(d)
  return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`
}
