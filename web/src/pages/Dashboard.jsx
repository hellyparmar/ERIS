import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { IndianRupee, Percent, Receipt, ShoppingBasket, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date, dateTime, money, num } from '../lib/format'
import { AlertItem, Card, DataTable, Delta, ErrorState, Kpi, PageHead, Seg, Spinner } from '../components/ui'
import { BarsChart, ForecastChart, ShareList, TrendChart } from '../components/charts'

const PERIODS = [
  { value: '7d', label: '7D' }, { value: '30d', label: '30D' }, { value: '90d', label: '90D' },
  { value: 'mtd', label: 'MTD' }, { value: 'ytd', label: 'YTD' },
]

export default function Dashboard() {
  const { outletId, user, outlets } = useApp()
  const [period, setPeriod] = useState('30d')
  const q = useQuery({ queryKey: ['dashboard', period, outletId], queryFn: () => api('/dashboard', { params: { period, outlet_id: outletId } }) })
  const outletName = outletId ? outlets.find((o) => o.id === outletId)?.name : 'All outlets'
  const greeting = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <>
      <PageHead title={`${greeting}, ${user.full_name.split(' ')[0]}`}
        subtitle={q.data ? `${outletName} · ${date(q.data.range.start)} – ${date(q.data.range.end)} · data up to ${date(q.data.data_as_of)}` : outletName}>
        <Seg options={PERIODS} value={period} onChange={setPeriod} label="Period" />
      </PageHead>
      {q.isError ? <ErrorState error={q.error} onRetry={q.refetch} /> : q.isLoading ? <Spinner label="Crunching numbers…" /> : <Body d={q.data} period={period} />}
    </>
  )
}

function Body({ d }) {
  const k = d.kpis.current
  const ch = d.kpis.change_pct
  const trend = d.trend.map((t, i) => ({ ...t, previous: d.previous_trend[i]?.revenue ?? null }))
  const gran = d.trend.length > 1 && (new Date(d.trend[1].date) - new Date(d.trend[0].date)) > 2 * 86400000 ? 'week' : 'day'
  const fc = d.forecast
  return (
    <>
      <div className="grid grid-4">
        <Kpi label="Revenue" icon={IndianRupee} value={money(k.revenue, { compact: true })} change={ch.revenue} hint="vs previous period" />
        <Kpi label="Bills" icon={Receipt} value={num(k.orders)} change={ch.orders} hint={`${num(k.items_per_basket, 1)} items per bill`} />
        <Kpi label="Average bill" icon={ShoppingBasket} value={money(k.avg_basket)} change={ch.avg_basket} hint={`${num(k.identified_customers)} loyalty customers`} />
        <Kpi label="Gross profit" icon={Percent} value={money(k.gross_profit, { compact: true })} change={ch.gross_profit} hint={`${k.margin_pct}% margin`} />
      </div>

      <div className="grid grid-3">
        <Card className="span-2" title="Revenue trend" subtitle={`Daily revenue compared with the previous ${d.range.days} days`}>
          <TrendChart data={trend} gran={gran} series={[{ key: 'revenue', label: 'This period' }, { key: 'previous', label: 'Previous period', dashed: true, color: 'var(--muted)' }]} />
        </Card>
        <Card title="Next 14 days" subtitle={fc ? fc.model_label : 'Forecast'}
          actions={<Link to="/forecasts" className="small">Details →</Link>}>
          {fc ? (
            <div className="stack">
              <div>
                <div className="kpi-value">{money(fc.summary.horizon_total, { compact: true })}</div>
                <div className="kpi-foot"><Delta value={fc.summary.change_vs_last_7_pct} /> next 7 days vs last 7</div>
              </div>
              <ForecastChart history={d.trend.slice(-21).map((t) => ({ date: t.date, actual: t.revenue }))} forecast={fc.forecast} height={170} />
              {fc.events.length > 0 && <div className="small muted"><Sparkles size={13} style={{ verticalAlign: -2 }} /> {fc.events.map((e) => `${e.name} (${date(e.date, { day: 'numeric', month: 'short' })})`).join(', ')} in the window</div>}
            </div>
          ) : <span className="muted">Not enough history to forecast yet.</span>}
        </Card>
      </div>

      <div className="grid grid-3">
        {d.outlets.length > 1 && (
          <Card title="Outlet performance" subtitle="Revenue this period" className="span-2">
            <BarsChart data={d.outlets} x="name" horizontal series={[{ key: 'revenue', label: 'Revenue' }]} height={220} />
            <DataTable rows={d.outlets} sortable={false} columns={[
              { key: 'name', label: 'Outlet' }, { key: 'orders', label: 'Bills', format: 'number' },
              { key: 'avg_basket', label: 'Avg bill', format: 'currency' }, { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
              { key: 'change_pct', label: 'vs previous', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
            ]} />
          </Card>
        )}
        <Card title="Needs attention" subtitle="Live alerts" className={d.outlets.length > 1 ? '' : 'span-2'}>
          <div className="stack">
            {d.alerts.length === 0 && <span className="muted">Nothing urgent. 🎉</span>}
            {d.alerts.map((a) => <Link key={a.id} to={a.link} style={{ color: 'inherit', textDecoration: 'none' }}><AlertItem alert={a} /></Link>)}
          </div>
        </Card>
      </div>

      <div className="grid grid-3">
        <Card title="Top products" subtitle="By revenue" className="span-2" flush>
          <DataTable rows={d.top_products} sortable={false} columns={[
            { key: 'name', label: 'Product', render: (r) => <><b>{r.name}</b><div className="small muted">{r.category}</div></> },
            { key: 'units', label: 'Units', format: 'number' },
            { key: 'revenue', label: 'Revenue', format: 'currency' },
            { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
            { key: 'share_pct', label: 'Share', format: 'percent_plain' },
          ]} />
        </Card>
        <Card title="Sales by category">
          <ShareList rows={d.categories.slice(0, 8)} labelKey="category" valueKey="revenue" />
        </Card>
      </div>

      <div className="grid grid-2">
        <Card title="Payment methods">
          <ShareList rows={d.payments.map((p) => ({ ...p, method: p.method.toUpperCase() }))} labelKey="method" valueKey="revenue" extra={(r) => `${num(r.orders)} bills`} />
        </Card>
        <Card title="Latest bills" flush actions={<Link to="/sales" className="small">All sales →</Link>}>
          <DataTable rows={d.recent_sales} sortable={false} columns={[
            { key: 'invoice_no', label: 'Invoice', render: (r) => <><b>{r.invoice_no}</b><div className="small muted">{r.outlet}</div></> },
            { key: 'sold_at', label: 'Time', render: (r) => dateTime(r.sold_at) },
            { key: 'customer', label: 'Customer', render: (r) => r.customer || <span className="muted">Walk-in</span> },
            { key: 'total', label: 'Amount', format: 'currency' },
          ]} />
        </Card>
      </div>
      <p className="small muted">Revenue includes tax; gross profit = revenue excluding tax − cost of goods. Changes compare with the previous period of equal length.</p>
    </>
  )
}
