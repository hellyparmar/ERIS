import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowDown, ArrowRight, ArrowUp, BellRing, Bot, Receipt, TrendingUp } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date, money, num, pct } from '../lib/format'
import { AlertItem, Card, Delta, Empty, ErrorState, Kpi, PageHead, SkeletonGrid } from '../components/ui'
import { ForecastChart, TrendChart, useChartColors } from '../components/charts'

const PERIODS = [
  { value: '7d', label: 'Last 7 days' }, { value: '30d', label: 'Last 30 days' }, { value: '90d', label: 'Last 90 days' },
  { value: 'mtd', label: 'Month to date' }, { value: 'ytd', label: 'Year to date' },
]
const ASK = ['Why did revenue change this week?', 'What should I reorder?']

export default function Dashboard() {
  const { outletId, user, outlets } = useApp()
  const [period, setPeriod] = useState('30d')
  const q = useQuery({ queryKey: ['dashboard', period, outletId], queryFn: () => api('/dashboard', { params: { period, outlet_id: outletId } }) })
  const outletName = outletId ? outlets.find((o) => o.id === outletId)?.name : (user.role === 'admin' ? 'All outlets' : user.outlet_names?.join(', ') || 'My outlets')

  return (
    <>
      <PageHead title="Overview" subtitle={q.data ? `${outletName} · ${date(q.data.range.start)} – ${date(q.data.range.end)}` : outletName}>
        <select className="pill" value={period} onChange={(e) => setPeriod(e.target.value)} aria-label="Period">
          {PERIODS.map((x) => <option key={x.value} value={x.value}>{x.label}</option>)}
        </select>
      </PageHead>
      {q.isError ? <ErrorState error={q.error} onRetry={q.refetch} /> : q.isLoading ? <SkeletonGrid /> : <Body d={q.data} />}
    </>
  )
}

function Body({ d }) {
  const c = useChartColors()
  const k = d.kpis.current
  const ch = d.kpis.change_pct
  const trend = d.trend.map((t, i) => ({ ...t, previous: d.previous_trend[i]?.revenue ?? null }))
  const gran = d.trend.length > 1 && (new Date(d.trend[1].date) - new Date(d.trend[0].date)) > 2 * 86400000 ? 'week' : 'day'
  const fc = d.forecast
  const multi = d.outlets.length > 1

  if (!k.orders) {
    return <Card><Empty title="No sales in this period" icon={Receipt}>Pick a longer period, or record or import sales.</Empty></Card>
  }
  return (
    <>
      <div className="grid grid-4">
        <Kpi label="Revenue" value={money(k.revenue, { compact: true })} change={ch.revenue} hint="vs the previous period" />
        <Kpi label="Gross profit" value={money(k.gross_profit, { compact: true })} change={ch.gross_profit} hint={`${k.margin_pct}% margin`} />
        <Kpi label="Bills" value={num(k.orders)} change={ch.orders} hint={`${num(k.items_per_basket, 1)} items per bill`} />
        <Kpi label="Average bill" value={money(k.avg_basket)} change={ch.avg_basket} hint="vs the previous period" />
      </div>

      <div className="grid grid-3">
        <Card className="span-2" title="Revenue"
          actions={<div className="legend">
            <span><i className="swatch" style={{ background: c.s1 }} />This period</span>
            <span><i className="swatch" style={{ background: c.muted }} />Previous period</span>
          </div>}>
          <TrendChart data={trend} gran={gran} height={270} legend={false}
            series={[{ key: 'revenue', label: 'This period' }, { key: 'previous', label: 'Previous period', color: 'var(--muted)' }]} />
        </Card>
        <Card className="dark" title="Next 14 days" actions={<Link to="/forecasts" className="small" style={{ color: 'var(--gold)' }}>Forecasts <ArrowRight size={13} style={{ verticalAlign: -2 }} /></Link>}>
          {fc ? (
            <div className="stack" style={{ gap: 10 }}>
              <div className="row" style={{ gap: 10 }}>
                <span className="big-number">{money(fc.summary.horizon_total, { compact: true })}</span>
                <Delta value={fc.summary.change_vs_last_7_pct} />
              </div>
              <span className="small muted">Expected revenue · next 7 days vs last 7</span>
              <ForecastChart history={d.trend.slice(-21).map((t) => ({ date: t.date, actual: t.revenue }))} forecast={fc.forecast} height={190} />
            </div>
          ) : <Empty title="Not enough history yet" icon={TrendingUp}>Forecasts start after three weeks of sales.</Empty>}
        </Card>
      </div>

      <div className="grid grid-3">
        {multi ? (
          <Card title="Outlets" actions={<Link to="/outlets" className="small">Details <ArrowRight size={13} style={{ verticalAlign: -2 }} /></Link>}>
            <RankList rows={d.outlets.map((o) => ({ key: o.outlet_id, name: o.name, value: o.revenue, change: o.change_pct }))} />
          </Card>
        ) : (
          <Card title="Categories" actions={<Link to="/analytics" className="small">Details <ArrowRight size={13} style={{ verticalAlign: -2 }} /></Link>}>
            <RankList rows={d.categories.slice(0, 6).map((x) => ({ key: x.category, name: x.category, value: x.revenue, change: x.change_pct }))} />
          </Card>
        )}
        <Card title="Top products" actions={<Link to="/products" className="small">All products <ArrowRight size={13} style={{ verticalAlign: -2 }} /></Link>}>
          <div className="stack" style={{ gap: 0 }}>
            {d.top_products.slice(0, 6).map((p, i) => (
              <div key={p.product_id ?? p.name} className="list-row">
                <span className={`rank ${i < 3 ? 'top' : ''}`}>{i + 1}</span>
                <div style={{ minWidth: 0, flex: 1 }}><b className="small" style={{ fontWeight: 550 }}>{p.name}</b><div className="small muted">{num(p.units)} sold</div></div>
                <span className="mono small">{money(p.revenue, { compact: true })}</span>
              </div>
            ))}
          </div>
        </Card>
        <Card title="Needs attention" actions={<BellRing size={16} className="muted" />}>
          <div className="stack">
            {d.alerts.length === 0 && <Empty title="Nothing urgent" icon={BellRing}>Stock, orders and sales look normal.</Empty>}
            {d.alerts.slice(0, 3).map((a) => <Link key={a.id} to={a.link} style={{ color: 'inherit', textDecoration: 'none', fontWeight: 'inherit' }}><AlertItem alert={a} /></Link>)}
          </div>
          <div className="chip-row" style={{ marginTop: 12 }}>
            {ASK.map((x) => <Link key={x} to={`/assistant?q=${encodeURIComponent(x)}`} className="chip"><Bot size={13} />{x}</Link>)}
          </div>
        </Card>
      </div>
    </>
  )
}

/** Name, value and change for a short ranked list (outlets or categories). */
function RankList({ rows }) {
  const max = Math.max(...rows.map((r) => r.value), 1)
  return (
    <div className="stack" style={{ gap: 12 }}>
      {rows.map((r) => (
        <div key={r.key} className="stack" style={{ gap: 5 }}>
          <div className="row between small" style={{ flexWrap: 'nowrap' }}>
            <span style={{ fontWeight: 550 }}>{r.name}</span>
            <span className="row" style={{ gap: 8, flexWrap: 'nowrap' }}><span className="mono">{money(r.value, { compact: true })}</span><Arrow v={r.change} /></span>
          </div>
          <div className="bar-meter"><i style={{ width: `${(r.value / max) * 100}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

function Arrow({ v }) {
  if (v === null || v === undefined) return null
  const Icon = v >= 0 ? ArrowUp : ArrowDown
  return <span className={`trend-dot ${v >= 0 ? 'up' : 'down'}`} title={pct(v)} aria-label={pct(v)}><Icon /></span>
}
