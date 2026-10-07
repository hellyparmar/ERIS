import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, Package, Store, Users } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date, money, num, titleCase } from '../lib/format'
import { Badge, Card, DataTable, Delta, ErrorState, Kpi, PageHead, Seg, Spinner, Tabs } from '../components/ui'
import { BarsChart, Heatmap, ShareList, TrendChart } from '../components/charts'

const PERIODS = [{ value: '30d', label: '30D' }, { value: '90d', label: '90D' }, { value: '180d', label: '6M' }, { value: '365d', label: '1Y' }]

export default function Analytics() {
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || 'sales'
  const [period, setPeriod] = useState('90d')
  return (
    <>
      <PageHead title="Analytics" subtitle="Sales patterns, products, outlets and customers.">
        <Seg options={PERIODS} value={period} onChange={setPeriod} label="Period" />
      </PageHead>
      <Tabs value={tab} onChange={(t) => setParams({ tab: t })} tabs={[
        { id: 'sales', label: 'Sales patterns', icon: BarChart3 }, { id: 'products', label: 'Products', icon: Package },
        { id: 'outlets', label: 'Outlets', icon: Store }, { id: 'customers', label: 'Customers', icon: Users },
      ]} />
      {tab === 'sales' && <SalesTab period={period} />}
      {tab === 'products' && <ProductsTab period={period} />}
      {tab === 'outlets' && <OutletsTab period={period} />}
      {tab === 'customers' && <CustomersTab period={period} />}
    </>
  )
}

function useAnalytics(kind, period, extra = {}) {
  const { outletId } = useApp()
  const p = { period, outlet_id: kind === 'outlets' ? undefined : outletId, ...extra }
  return useQuery({ queryKey: ['analytics', kind, p], queryFn: () => api(`/analytics/${kind}`, { params: p }), placeholderData: (x) => x })
}

function Loader({ q, children }) {
  if (q.isError) return <ErrorState error={q.error} onRetry={q.refetch} />
  if (!q.data) return <Spinner />
  return children(q.data)
}

function SalesTab({ period }) {
  const [gran, setGran] = useState('auto')
  const q = useAnalytics('sales', period, { granularity: gran })
  return <Loader q={q}>{(d) => {
    const k = d.kpis.current
    const ch = d.kpis.change_pct
    return (
      <>
        <div className="grid grid-4">
          <Kpi label="Revenue" value={money(k.revenue, { compact: true })} change={ch.revenue} hint={`${money(k.avg_daily_revenue, { compact: true })} per day`} />
          <Kpi label="Bills" value={num(k.orders)} change={ch.orders} />
          <Kpi label="Average bill" value={money(k.avg_basket)} change={ch.avg_basket} hint={`${k.items_per_basket} items`} />
          <Kpi label="Gross margin" value={`${k.margin_pct}%`} hint={`${money(k.discount, { compact: true })} given as discounts`} />
        </div>
        <Card title="Revenue and gross profit" subtitle={`${date(d.range.start)} – ${date(d.range.end)}, by ${d.granularity}`}
          actions={<Seg options={[{ value: 'auto', label: 'Auto' }, { value: 'day', label: 'Day' }, { value: 'week', label: 'Week' }, { value: 'month', label: 'Month' }]} value={gran} onChange={setGran} label="Granularity" />}>
          <TrendChart data={d.series} gran={d.granularity} series={[{ key: 'revenue', label: 'Revenue' }, { key: 'profit', label: 'Gross profit' }]} height={300} />
        </Card>
        <div className="grid grid-3">
          <Card title="When do customers shop?" subtitle="Average revenue by weekday and hour" className="span-2">
            <Heatmap cells={d.heatmap.cells} />
          </Card>
          <div className="stack" style={{ gap: 16 }}>
            <Card title="Payment methods"><ShareList rows={d.payments.map((p) => ({ ...p, method: p.method.toUpperCase() }))} labelKey="method" valueKey="revenue" /></Card>
            <Card title="Channels"><ShareList rows={d.channels.map((c) => ({ ...c, channel: titleCase(c.channel) }))} labelKey="channel" valueKey="revenue" extra={(r) => `avg ${money(r.avg_basket)}`} /></Card>
          </div>
        </div>
        <Card title="Bill size distribution" subtitle="Number of bills by bill value (₹)">
          <BarsChart data={d.baskets} x="band" series={[{ key: 'orders', label: 'Bills' }]} format="number" height={220} />
        </Card>
      </>
    )
  }}</Loader>
}

function ProductsTab({ period }) {
  const q = useAnalytics('products', period)
  return <Loader q={q}>{(d) => (
    <>
      <div className="grid grid-3">
        {['A', 'B', 'C'].map((cls) => (
          <Kpi key={cls} label={`Class ${cls} products`} value={`${d.summary[cls].products} products`}
            hint={`${d.summary[cls].share_pct}% of revenue · ${{ A: 'protect stock, never run out', B: 'review regularly', C: 'candidates for promotion or delisting' }[cls]}`} />
        ))}
      </div>
      <div className="grid grid-2">
        <Card title="Category performance" flush>
          <DataTable rows={d.categories} columns={[
            { key: 'category', label: 'Category' }, { key: 'revenue', label: 'Revenue', format: 'currency' },
            { key: 'share_pct', label: 'Share', format: 'percent_plain' }, { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
            { key: 'change_pct', label: 'Change', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
          ]} />
        </Card>
        <Card title="Gross profit by category">
          <BarsChart data={d.categories} x="category" horizontal series={[{ key: 'profit', label: 'Gross profit' }]} />
        </Card>
      </div>
      <Card title="Frequently bought together" subtitle="Pairs bought together more often than chance" flush>
        <DataTable rows={d.affinity} columns={[
          { key: 'product_a', label: 'Product' }, { key: 'product_b', label: 'Bought with' },
          { key: 'bills_together', label: 'Bills together', format: 'number' }, { key: 'support_pct', label: 'Support', format: 'percent_plain' },
          { key: 'confidence_pct', label: 'Confidence', format: 'percent_plain' }, { key: 'lift', label: 'Lift', align: 'right', render: (r) => `${r.lift}×` },
        ]} />
      </Card>
      <Card title="ABC analysis" subtitle="A = top 80% of revenue, B = next 15%, C = the rest" flush>
        <DataTable maxHeight={520} rows={d.products} columns={[
          { key: 'class', label: 'Class', render: (r) => <Badge tone={r.class === 'A' ? 'good' : r.class === 'B' ? 'info' : 'warn'}>{r.class}</Badge> },
          { key: 'name', label: 'Product', render: (r) => <><b>{r.name}</b><div className="small muted">{r.category}</div></> },
          { key: 'units', label: 'Units', format: 'number' }, { key: 'revenue', label: 'Revenue', format: 'currency' },
          { key: 'margin_pct', label: 'Margin', format: 'percent_plain' }, { key: 'share_pct', label: 'Share', format: 'percent_plain' },
          { key: 'cumulative_pct', label: 'Cumulative', format: 'percent_plain' },
          { key: 'change_pct', label: 'vs previous', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
        ]} />
        {d.not_sold.length > 0 && <p className="small" style={{ padding: 12 }}><b>Not sold in this period:</b> {d.not_sold.map((x) => x.name).join(', ')}</p>}
      </Card>
    </>
  )}</Loader>
}

function OutletsTab({ period }) {
  const q = useAnalytics('outlets', period)
  return <Loader q={q}>{(d) => (
    <>
      <Card title="Revenue by outlet over time" subtitle={`By ${d.granularity}`}>
        <TrendChart data={d.series} gran={d.granularity} area={false} series={d.outlets.map((o) => ({ key: o.name, label: o.name }))} height={320} />
      </Card>
      <Card title="Outlet comparison" flush>
        <DataTable rows={d.outlets} columns={[
          { key: 'name', label: 'Outlet', render: (r) => <><b>{r.name}</b><div className="small muted">{r.city}</div></> },
          { key: 'revenue', label: 'Revenue', format: 'currency' }, { key: 'share_pct', label: 'Share', format: 'percent_plain' },
          { key: 'orders', label: 'Bills', format: 'number' }, { key: 'avg_basket', label: 'Avg bill', format: 'currency' },
          { key: 'avg_daily_revenue', label: 'Per day', format: 'currency' }, { key: 'profit', label: 'Gross profit', format: 'currency' },
          { key: 'margin_pct', label: 'Margin', format: 'percent_plain' },
          { key: 'change_pct', label: 'vs previous', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
        ]} />
      </Card>
    </>
  )}</Loader>
}

function CustomersTab({ period }) {
  const q = useAnalytics('customers', period)
  return <Loader q={q}>{(d) => (
    <>
      <div className="grid grid-4">
        <Kpi label="Active loyalty customers" value={num(d.repeat.customers)} hint="in this period" />
        <Kpi label="Repeat rate" value={`${d.repeat.repeat_rate_pct}%`} hint="came back more than once" />
        <Kpi label="Bills linked to customers" value={`${d.repeat.identified_order_share_pct}%`} hint="rest are walk-ins" />
        <Kpi label="Customers analysed (12m)" value={num(d.total_customers)} hint="RFM segmentation" />
      </div>
      <div className="grid grid-2">
        <Card title="RFM segments" subtitle="Last 12 months" flush>
          <DataTable rows={d.segments} columns={[
            { key: 'segment', label: 'Segment', render: (r) => <><b>{r.segment}</b><div className="small muted">{r.description}</div></> },
            { key: 'customers', label: 'Customers', format: 'number' }, { key: 'revenue_share_pct', label: 'Revenue share', format: 'percent_plain' },
            { key: 'avg_orders', label: 'Avg visits', format: 'number' }, { key: 'avg_recency_days', label: 'Days since visit', format: 'number' },
          ]} />
        </Card>
        <Card title="Customers by segment">
          <BarsChart data={d.segments} x="segment" horizontal series={[{ key: 'customers', label: 'Customers' }]} format="number" />
        </Card>
      </div>
      <Card title="Top customers this period" flush>
        <DataTable rows={d.top} columns={[
          { key: 'name', label: 'Customer' }, { key: 'type', label: 'Type', render: (r) => titleCase(r.type) }, { key: 'phone', label: 'Phone' },
          { key: 'orders', label: 'Visits', format: 'number' }, { key: 'spend', label: 'Spend', format: 'currency' }, { key: 'last_purchase', label: 'Last visit', format: 'date' },
        ]} />
      </Card>
    </>
  )}</Loader>
}
