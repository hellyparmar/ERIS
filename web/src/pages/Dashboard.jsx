import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BellRing, Bot, CalendarDays, IndianRupee, Percent, Receipt, ShoppingBasket, Sparkles, Store, TrendingUp } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date, dateTime, money, num } from '../lib/format'
import { AlertItem, Card, DataTable, Delta, Empty, ErrorState, Kpi, PageHead, Seg, SkeletonGrid } from '../components/ui'
import { BarsChart, ForecastChart, ShareList, Sparkline, TrendChart } from '../components/charts'

const PERIODS = [
  { value: '7d', label: '7D' }, { value: '30d', label: '30D' }, { value: '90d', label: '90D' },
  { value: 'mtd', label: 'MTD' }, { value: 'ytd', label: 'YTD' },
]

export default function Dashboard() {
  const { outletId, user, outlets } = useApp()
  const [period, setPeriod] = useState('30d')
  const q = useQuery({ queryKey: ['dashboard', period, outletId], queryFn: () => api('/dashboard', { params: { period, outlet_id: outletId } }) })
  const outletName = outletId ? outlets.find((o) => o.id === outletId)?.name : (user.role === 'admin' ? 'All outlets' : user.outlet_names?.join(', ') || 'My outlets')
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <>
      <PageHead eyebrow={<><Store size={13} />{outletName}</>} title={`${greeting}, ${user.full_name.split(' ')[0]}`}
        subtitle={q.data ? `${date(q.data.range.start)} – ${date(q.data.range.end)} · compared with ${date(q.data.comparison.start)} – ${date(q.data.comparison.end)} · data up to ${date(q.data.data_as_of)}` : 'Your business at a glance'}>
        <Seg options={PERIODS} value={period} onChange={setPeriod} label="Period" />
      </PageHead>
      {q.isError ? <ErrorState error={q.error} onRetry={q.refetch} /> : q.isLoading ? <SkeletonGrid /> : <Body d={q.data} />}
    </>
  )
}

function Body({ d }) {
  const k = d.kpis.current
  const ch = d.kpis.change_pct
  const trend = d.trend.map((t, i) => ({ ...t, previous: d.previous_trend[i]?.revenue ?? null, basket: t.orders ? t.revenue / t.orders : null }))
  const gran = d.trend.length > 1 && (new Date(d.trend[1].date) - new Date(d.trend[0].date)) > 2 * 86400000 ? 'week' : 'day'
  const fc = d.forecast
  const best = [...d.outlets].sort((a, b) => b.revenue - a.revenue)[0]
  const urgent = d.alerts.filter((a) => a.severity !== 'info').length

  if (!k.orders) {
    return <Card><Empty title="No sales in this period" icon={Receipt}>Pick a longer period, or record or import sales to see your dashboard.</Empty></Card>
  }
  return (
    <>
      <div className="grid grid-4">
        <Kpi label="Revenue" icon={IndianRupee} tone="" value={money(k.revenue, { compact: true })} change={ch.revenue}
          hint={`${money(k.revenue / Math.max(1, d.range.days), { compact: true })} per day on average`} spark={<Sparkline data={trend} k="revenue" color="var(--s1)" />} />
        <Kpi label="Bills" icon={Receipt} tone="sky" value={num(k.orders)} change={ch.orders}
          hint={`${num(k.items_per_basket, 1)} items per bill`} spark={<Sparkline data={trend} k="orders" color="var(--s3)" />} />
        <Kpi label="Average bill" icon={ShoppingBasket} tone="amber" value={money(k.avg_basket)} change={ch.avg_basket}
          hint={`${num(k.identified_customers)} loyalty customers shopped`} spark={<Sparkline data={trend} k="basket" color="var(--s4)" />} />
        <Kpi label="Gross profit" icon={Percent} tone="emerald" value={money(k.gross_profit, { compact: true })} change={ch.gross_profit}
          hint={`${k.margin_pct}% margin on net sales`} spark={<Sparkline data={trend} k="profit" color="var(--s6)" />} />
      </div>

      <div className="grid grid-3">
        <Card className="span-2" title="Revenue trend" subtitle={`${gran === 'week' ? 'Weekly' : 'Daily'} revenue, this period vs the comparison period`}>
          <TrendChart data={trend} gran={gran} height={290} series={[{ key: 'revenue', label: 'This period' }, { key: 'previous', label: 'Comparison period', dashed: true, color: 'var(--muted)' }]} />
        </Card>
        <Card className="hero" title="Next 14 days" subtitle={fc ? `Forecast · ${fc.model_label}` : 'Forecast'}
          actions={<Link to="/forecasts" className="small">Details <ArrowRight size={13} style={{ verticalAlign: -2 }} /></Link>}>
          {fc ? (
            <div className="stack" style={{ gap: 12 }}>
              <div>
                <div className="big-number">{money(fc.summary.horizon_total, { compact: true })}</div>
                <div className="kpi-foot" style={{ marginTop: 6 }}><Delta value={fc.summary.change_vs_last_7_pct} /> next 7 days vs the last 7</div>
              </div>
              <ForecastChart history={d.trend.slice(-21).map((t) => ({ date: t.date, actual: t.revenue }))} forecast={fc.forecast} height={170} />
              {fc.events.length > 0 && <div className="small text-2"><Sparkles size={13} style={{ verticalAlign: -2, color: 'var(--accent)' }} /> {fc.events.map((e) => `${e.name} (${date(e.date, { day: 'numeric', month: 'short' })})`).join(', ')} ahead</div>}
            </div>
          ) : <Empty title="Not enough history yet" icon={TrendingUp}>Forecasts start after three weeks of sales.</Empty>}
        </Card>
      </div>

      <div className="grid grid-3">
        {d.outlets.length > 1 ? (
          <Card title="Outlet performance" subtitle={best ? `${best.name} leads with ${money(best.revenue, { compact: true })}` : 'Revenue this period'} className="span-2">
            <BarsChart data={d.outlets} x="name" horizontal series={[{ key: 'revenue', label: 'Revenue' }]} height={210} />
            <div style={{ marginTop: 10 }}>
              <DataTable rows={d.outlets} sortable={false} columns={[
                { key: 'name', label: 'Outlet', render: (r) => <b>{r.name}</b> }, { key: 'orders', label: 'Bills', format: 'number' },
                { key: 'avg_basket', label: 'Avg bill', format: 'currency' }, { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
                { key: 'change_pct', label: 'vs comparison', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
              ]} />
            </div>
          </Card>
        ) : (
          <Card title="Payment methods" subtitle="Share of revenue" className="span-2">
            <ShareList rows={d.payments.map((p) => ({ ...p, method: p.method.toUpperCase() }))} labelKey="method" valueKey="revenue" extra={(r) => `${num(r.orders)} bills`} />
          </Card>
        )}
        <Card title="Needs attention" subtitle={urgent ? `${urgent} item${urgent === 1 ? '' : 's'} to act on` : 'All clear'}
          actions={<BellRing size={16} className="muted" />}>
          <div className="stack">
            {d.alerts.length === 0 && <Empty title="Nothing urgent" icon={BellRing}>Stock, orders and sales look normal.</Empty>}
            {d.alerts.map((a) => <Link key={a.id} to={a.link} style={{ color: 'inherit', textDecoration: 'none', fontWeight: 'inherit' }}><AlertItem alert={a} /></Link>)}
          </div>
        </Card>
      </div>

      <div className="grid grid-3">
        <Card title="Top products" subtitle="By revenue this period" className="span-2" flush>
          <DataTable rows={d.top_products.map((p, i) => ({ ...p, rank: i + 1 }))} sortable={false} columns={[
            { key: 'name', label: 'Product', render: (r) => <div className="row" style={{ gap: 10, flexWrap: 'nowrap' }}><span className="rank">{r.rank}</span><div><b>{r.name}</b><div className="small muted">{r.category}</div></div></div> },
            { key: 'units', label: 'Units', format: 'number' },
            { key: 'revenue', label: 'Revenue', format: 'currency' },
            { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
            { key: 'share_pct', label: 'Share', format: 'percent_plain' },
          ]} />
        </Card>
        <Card title="Sales by category" subtitle="Share of revenue">
          <ShareList rows={d.categories.slice(0, 8)} labelKey="category" valueKey="revenue" />
        </Card>
      </div>

      <div className="grid grid-3">
        {d.outlets.length > 1 && (
          <Card title="Payment methods" subtitle="Share of revenue">
            <ShareList rows={d.payments.map((p) => ({ ...p, method: p.method.toUpperCase() }))} labelKey="method" valueKey="revenue" extra={(r) => `${num(r.orders)} bills`} />
          </Card>
        )}
        <Card title="Latest bills" flush className={d.outlets.length > 1 ? 'span-2' : 'span-2'} actions={<Link to="/sales" className="small">All sales <ArrowRight size={13} style={{ verticalAlign: -2 }} /></Link>}>
          <DataTable rows={d.recent_sales} sortable={false} columns={[
            { key: 'invoice_no', label: 'Bill', render: (r) => <><b>{r.invoice_no}</b><div className="small muted">{r.outlet}</div></> },
            { key: 'sold_at', label: 'Time', render: (r) => dateTime(r.sold_at) },
            { key: 'customer', label: 'Customer', render: (r) => r.customer || <span className="muted">Walk-in</span> },
            { key: 'payment_method', label: 'Paid by', render: (r) => <span className="badge">{r.payment_method.toUpperCase()}</span> },
            { key: 'total', label: 'Amount', format: 'currency' },
          ]} />
        </Card>
        {d.outlets.length <= 1 && (
          <Card className="hero" title="Ask the assistant" subtitle="Plain-English questions, answered from your data">
            <div className="stack">
              {['Why did revenue change this week?', 'Which products are growing fastest?', 'What should I reorder?'].map((q) => (
                <Link key={q} to={`/assistant?q=${encodeURIComponent(q)}`} className="chip" style={{ textDecoration: 'none' }}><Bot size={13} style={{ verticalAlign: -2, marginRight: 6 }} />{q}</Link>
              ))}
            </div>
          </Card>
        )}
      </div>
      <p className="small muted"><CalendarDays size={13} style={{ verticalAlign: -2 }} /> Revenue includes GST. Gross profit = revenue excluding GST − cost of goods. Changes compare like with like: the same weekdays before, or the same days of last month.</p>
    </>
  )
}
