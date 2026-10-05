import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowDown, ArrowRight, ArrowUp, BellRing, Bot, CalendarDays, Receipt, Sparkles, TrendingUp } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date, dateTime, money, num, pct } from '../lib/format'
import { AlertItem, Card, DataTable, Delta, Empty, ErrorState, Gauge, Kpi, PageHead, SegmentBar, SkeletonGrid } from '../components/ui'
import { BarsChart, ForecastChart, TrendChart, useChartColors } from '../components/charts'

const PERIODS = [
  { value: '7d', label: 'Last 7 days', short: 'this week' }, { value: '30d', label: 'Last 30 days', short: 'these 30 days' },
  { value: '90d', label: 'Last 90 days', short: 'these 90 days' }, { value: 'mtd', label: 'Month to date', short: 'this month' },
  { value: 'ytd', label: 'Year to date', short: 'this year' },
]
const ASK = ['Why did revenue change this week?', 'Which products are growing fastest?', 'What should I reorder?']

export default function Dashboard() {
  const { outletId, user, outlets } = useApp()
  const [period, setPeriod] = useState('30d')
  const q = useQuery({ queryKey: ['dashboard', period, outletId], queryFn: () => api('/dashboard', { params: { period, outlet_id: outletId } }) })
  const outletName = outletId ? outlets.find((o) => o.id === outletId)?.name : (user.role === 'admin' ? 'All outlets' : user.outlet_names?.join(', ') || 'My outlets')
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  const p = PERIODS.find((x) => x.value === period)

  return (
    <>
      <PageHead eyebrow={`${greeting}, ${user.full_name.split(' ')[0]} · ${outletName}`} title="Business overview"
        subtitle={q.data ? `${date(q.data.range.start)} – ${date(q.data.range.end)} · compared with ${date(q.data.comparison.start)} – ${date(q.data.comparison.end)}` : 'Your business at a glance'}>
        <select className="pill" value={period} onChange={(e) => setPeriod(e.target.value)} aria-label="Period">
          {PERIODS.map((x) => <option key={x.value} value={x.value}>{x.label}</option>)}
        </select>
      </PageHead>
      {q.isError ? <ErrorState error={q.error} onRetry={q.refetch} /> : q.isLoading ? <SkeletonGrid /> : <Body d={q.data} short={p.short} />}
    </>
  )
}

const upDown = (v, short) => (v === null || v === undefined ? 'No comparison yet' : `${v >= 0 ? 'Up' : 'Down'} ${Math.abs(v).toFixed(1)}% ${short}`)

function Body({ d, short }) {
  const c = useChartColors()
  const k = d.kpis.current
  const ch = d.kpis.change_pct
  const trend = d.trend.map((t, i) => ({ ...t, previous: d.previous_trend[i]?.revenue ?? null }))
  const gran = d.trend.length > 1 && (new Date(d.trend[1].date) - new Date(d.trend[0].date)) > 2 * 86400000 ? 'week' : 'day'
  const prevTotal = d.previous_trend.reduce((a, t) => a + (t.revenue || 0), 0)
  const fc = d.forecast
  const multi = d.outlets.length > 1
  const cats = d.categories.slice(0, 8)
  const topCat = cats[0]
  const payColors = [c.s1, c.s2, c.s3, c.s4, c.s5, c.s6]

  if (!k.orders) {
    return <Card><Empty title="No sales in this period" icon={Receipt}>Pick a longer period, or record or import sales to see your dashboard.</Empty></Card>
  }
  return (
    <>
      <div className="grid grid-5">
        <Kpi label="Revenue" value={money(k.revenue, { compact: true })} change={ch.revenue} hint={upDown(ch.revenue, short)} />
        <Kpi label="Gross profit" value={money(k.gross_profit, { compact: true })} change={ch.gross_profit} hint={`${k.margin_pct}% margin on net sales`} />
        <Kpi label="Bills" value={num(k.orders)} change={ch.orders} hint={upDown(ch.orders, short)} />
        <Kpi label="Average bill" value={money(k.avg_basket)} change={ch.avg_basket} hint={`${num(k.items_per_basket, 1)} items per bill`} />
        <Kpi label="Units sold" value={num(k.units)} change={ch.units} hint={upDown(ch.units, short)} />
      </div>

      <div className="grid grid-3">
        <Card className="span-2" title="Revenue trend"
          actions={<div className="row" style={{ gap: 22, alignItems: 'flex-end' }}>
            <div><div className="legend"><span><i className="swatch" style={{ background: c.s1 }} />This period</span></div>
              <div className="row" style={{ gap: 8 }}><span className="big-number" style={{ fontSize: 28 }}>{money(k.revenue, { compact: true })}</span><Delta value={ch.revenue} /></div></div>
            <div className="hide-sm"><div className="legend"><span><i className="swatch" style={{ background: c.muted }} />Comparison</span></div>
              <span className="big-number" style={{ fontSize: 28, color: 'var(--text-2)' }}>{money(prevTotal, { compact: true })}</span></div>
          </div>}>
          <p className="small text-2" style={{ marginTop: -6, marginBottom: 10 }}>
            {gran === 'week' ? 'Weekly' : 'Daily'} revenue {ch.revenue >= 0 ? 'up' : 'down'} {pct(Math.abs(ch.revenue ?? 0), { signed: false })} on the comparison period, with bills {ch.orders >= 0 ? 'up' : 'down'} {pct(Math.abs(ch.orders ?? 0), { signed: false })}.
          </p>
          <TrendChart data={trend} gran={gran} height={268} legend={false} series={[{ key: 'revenue', label: 'This period' }, { key: 'previous', label: 'Comparison period', color: 'var(--muted)' }]} />
        </Card>
        <Card title="Sales by category" actions={topCat && <div style={{ textAlign: 'right' }}><div className="small muted">Top category</div><div className="row" style={{ gap: 8, justifyContent: 'flex-end' }}><span className="big-number" style={{ fontSize: 28 }}>{topCat.share_pct}%</span></div></div>}>
          <p className="small text-2" style={{ marginTop: -6, marginBottom: 10 }}>{topCat ? `${topCat.category} leads, ${money(topCat.revenue, { compact: true })} of revenue` : 'Share of revenue'}</p>
          <BarsChart data={cats} x="category" format="currency" height={262} horizontal
            series={[{ key: 'revenue', label: 'Revenue' }]} highlight={(x, i) => i < 3} />
        </Card>
      </div>

      <div className="grid grid-3">
        <Card title="Gross margin" subtitle="Profit after the cost of goods, on sales excluding GST">
          <Gauge value={k.margin_pct} max={50} label={`${k.margin_pct}%`} caption={`${money(k.gross_profit, { compact: true })} gross profit`} />
          <div className="row between small" style={{ marginTop: 14, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
            <span className="muted">Loyalty customers</span><b className="mono">{num(k.identified_customers)} <Delta value={ch.identified_customers} /></b>
          </div>
        </Card>
        <Card title="Payment methods" subtitle="How customers paid this period">
          <div className="stat-row" style={{ marginBottom: 16 }}>
            <div className="s"><span>Bills</span><b>{num(k.orders)}</b></div>
            <div className="s"><span>Avg bill</span><b>{money(k.avg_basket)}</b></div>
            <div className="s"><span>Discounts</span><b>{money(k.discount, { compact: true })}</b></div>
          </div>
          <SegmentBar thick items={d.payments.map((x, i) => ({ label: x.method.toUpperCase(), value: x.revenue, color: payColors[i % payColors.length] }))}
            format={(v) => money(v, { compact: true })} />
        </Card>
        {multi ? (
          <Card title="Sales by outlet" flush>
            <DataTable rows={d.outlets} sortable={false} columns={[
              { key: 'name', label: 'Outlet', render: (r) => <b>{r.name}</b> },
              { key: 'orders', label: 'Bills', align: 'right', render: (r) => <span className="row" style={{ gap: 6, justifyContent: 'flex-end', flexWrap: 'nowrap' }}>{num(r.orders)}<Arrow v={r.change_pct} /></span> },
              { key: 'revenue', label: 'Revenue', format: 'currency' },
            ]} />
          </Card>
        ) : (
          <Card title="Category performance" flush>
            <DataTable rows={cats.slice(0, 6)} sortable={false} columns={[
              { key: 'category', label: 'Category', render: (r) => <b>{r.category}</b> },
              { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
              { key: 'revenue', label: 'Revenue', align: 'right', render: (r) => <span className="row" style={{ gap: 6, justifyContent: 'flex-end', flexWrap: 'nowrap' }}>{money(r.revenue)}<Arrow v={r.change_pct} /></span> },
            ]} />
          </Card>
        )}
      </div>

      <div className="grid grid-3">
        <Card className="dark" title="Next 14 days" subtitle={fc ? `Forecast · ${fc.model_label}` : 'Forecast'}
          actions={<Link to="/forecasts" className="small" style={{ color: 'var(--gold)' }}>Details <ArrowRight size={13} style={{ verticalAlign: -2 }} /></Link>}>
          {fc ? (
            <div className="stack" style={{ gap: 12 }}>
              <div className="row" style={{ gap: 10 }}>
                <span className="big-number">{money(fc.summary.horizon_total, { compact: true })}</span><Delta value={fc.summary.change_vs_last_7_pct} />
              </div>
              <span className="small muted">Next 7 days vs the last 7</span>
              <ForecastChart history={d.trend.slice(-21).map((t) => ({ date: t.date, actual: t.revenue }))} forecast={fc.forecast} height={170} />
              {fc.events.length > 0 && <div className="small text-2"><Sparkles size={13} style={{ verticalAlign: -2, color: 'var(--gold)' }} /> {fc.events.map((e) => `${e.name} (${date(e.date, { day: 'numeric', month: 'short' })})`).join(', ')} ahead</div>}
            </div>
          ) : <Empty title="Not enough history yet" icon={TrendingUp}>Forecasts start after three weeks of sales.</Empty>}
        </Card>
        <Card title="Top products" subtitle="By revenue this period" className="span-2" flush>
          <DataTable rows={d.top_products.map((x, i) => ({ ...x, rank: i + 1 }))} sortable={false} columns={[
            { key: 'name', label: 'Product', render: (r) => <div className="row" style={{ gap: 10, flexWrap: 'nowrap' }}><span className={`rank ${r.rank <= 3 ? 'top' : ''}`}>{r.rank}</span><div><b>{r.name}</b><div className="small muted">{r.category}</div></div></div> },
            { key: 'units', label: 'Units', format: 'number' },
            { key: 'revenue', label: 'Revenue', format: 'currency' },
            { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
            { key: 'share_pct', label: 'Share', format: 'percent_plain' },
          ]} />
        </Card>
      </div>

      <div className="grid grid-3">
        <Card title="Latest bills" flush className="span-2" actions={<Link to="/sales" className="small">All sales <ArrowRight size={13} style={{ verticalAlign: -2 }} /></Link>}>
          <DataTable rows={d.recent_sales} sortable={false} columns={[
            { key: 'invoice_no', label: 'Bill', render: (r) => <><b>{r.invoice_no}</b><div className="small muted">{r.outlet}</div></> },
            { key: 'sold_at', label: 'Time', render: (r) => dateTime(r.sold_at) },
            { key: 'customer', label: 'Customer', render: (r) => r.customer || <span className="muted">Walk-in</span> },
            { key: 'payment_method', label: 'Paid by', render: (r) => <span className="badge">{r.payment_method.toUpperCase()}</span> },
            { key: 'total', label: 'Amount', format: 'currency' },
          ]} />
        </Card>
        <Card title="Needs attention" actions={<BellRing size={16} className="muted" />}>
          <div className="stack">
            {d.alerts.length === 0 && <Empty title="Nothing urgent" icon={BellRing}>Stock, orders and sales look normal.</Empty>}
            {d.alerts.slice(0, 4).map((a) => <Link key={a.id} to={a.link} style={{ color: 'inherit', textDecoration: 'none', fontWeight: 'inherit' }}><AlertItem alert={a} /></Link>)}
          </div>
          <div className="stack" style={{ gap: 6, marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
            <span className="small muted">Ask the assistant</span>
            {ASK.map((x) => <Link key={x} to={`/assistant?q=${encodeURIComponent(x)}`} className="chip"><Bot size={13} />{x}</Link>)}
          </div>
        </Card>
      </div>
      <p className="small muted"><CalendarDays size={13} style={{ verticalAlign: -2 }} /> Revenue includes GST. Gross profit = revenue excluding GST − cost of goods. Changes compare like with like: the same weekdays before, or the same days of last month. Data up to {date(d.data_as_of)}.</p>
    </>
  )
}

function Arrow({ v }) {
  if (v === null || v === undefined) return null
  const Icon = v >= 0 ? ArrowUp : ArrowDown
  return <span className={`trend-dot ${v >= 0 ? 'up' : 'down'}`} title={pct(v)} aria-label={pct(v)}><Icon /></span>
}
