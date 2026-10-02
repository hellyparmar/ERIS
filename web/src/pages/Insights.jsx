import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, AlertTriangle, CheckCircle2, CloudRain, Search } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date, money, pct } from '../lib/format'
import { Badge, Card, DataTable, Delta, Empty, Kpi, PageHead, Query, Seg, StatusBadge } from '../components/ui'
import { BarsChart } from '../components/charts'

const PERIODS = [{ value: '7d', label: '7 days' }, { value: '14d', label: '14 days' }, { value: '30d', label: '30 days' }, { value: 'mtd', label: 'Month to date' }]
const ANOMALY_PERIODS = [{ value: '30d', label: '30 days' }, { value: '90d', label: '90 days' }, { value: '180d', label: '180 days' }, { value: '365d', label: '1 year' }]

export default function Insights() {
  return (
    <>
      <PageHead title="Anomalies & drivers" subtitle="Why revenue changed, and which days or bills look unusual - every number traced back to the data." />
      <Drivers />
      <Anomalies />
    </>
  )
}

function Drivers() {
  const { outletId } = useApp()
  const [period, setPeriod] = useState('7d')
  const q = useQuery({ queryKey: ['drivers', period, outletId], queryFn: () => api('/analytics/drivers', { params: { period, outlet_id: outletId } }) })
  return (
    <Card title="Why did revenue change?" subtitle="This period compared with the period of the same length just before it."
      actions={<Seg options={PERIODS} value={period} onChange={setPeriod} label="Period" />}>
      <Query q={q}>{(d) => (d.insufficient_data
        ? <Empty title="Not enough data">{d.summary.join(' ')}</Empty>
        : <DriverResult d={d} />)}</Query>
    </Card>
  )
}

function DriverResult({ d }) {
  const SHORT = { traffic: 'Bills', basket: 'Avg bill', calendar: 'Calendar', promotions: 'Promotions', stockouts: 'Stockouts', weather: 'Rain', anomalies: 'Unusual days' }
  const drivers = d.drivers.map((x) => ({ ...x, short: SHORT[x.key] || x.label }))
  return (
    <div className="stack" style={{ gap: 16 }}>
      <div className="grid grid-4">
        <Kpi label="Revenue" value={money(d.revenue[0], { compact: true })} change={d.change_pct} hint={`vs ${money(d.revenue[1], { compact: true })}`} />
        <Kpi label="Bills" value={d.bills[0].toLocaleString('en-IN')} change={d.bills[1] ? ((d.bills[0] - d.bills[1]) / d.bills[1]) * 100 : null} />
        <Kpi label="Average bill" value={money(d.avg_bill[0])} change={d.avg_bill[1] ? ((d.avg_bill[0] - d.avg_bill[1]) / d.avg_bill[1]) * 100 : null} />
        <Kpi label="Change" value={money(d.change, { compact: true })} hint={`${date(d.period.start)} – ${date(d.period.end)} vs ${date(d.comparison.start)} – ${date(d.comparison.end)}`} />
      </div>
      <div className="grid grid-2">
        <div className="stack">
          <h3 className="small muted" style={{ margin: 0 }}>In plain words</h3>
          <ul style={{ margin: 0, paddingLeft: 18 }}>{d.summary.map((s) => <li key={s} style={{ marginBottom: 4 }}>{s}</li>)}</ul>
          <p className="small muted">Bills and average bill add up exactly to the change. The other drivers are estimates; weather is an association measured on the past year, not proof of cause.</p>
        </div>
        <div>
          <h3 className="small muted" style={{ margin: '0 0 6px' }}>Estimated contribution of each driver</h3>
          <BarsChart data={drivers} x="short" series={[{ key: 'effect', label: 'Effect' }]} horizontal height={240}
            colorBy={(row, c) => (row.effect >= 0 ? c.good : c.bad)} />
        </div>
      </div>
      <DataTable rows={drivers} sortable={false} columns={[
        { key: 'label', label: 'Driver' },
        { key: 'effect', label: 'Effect', format: 'currency' },
        { key: 'detail', label: 'Evidence', render: (r) => <span className="small">{r.detail}</span> },
      ]} />
      <div className="grid grid-2">
        {d.outlets.length > 1 && (
          <div>
            <h3 className="small muted" style={{ margin: '0 0 6px' }}>By outlet</h3>
            <DataTable rows={d.outlets} columns={[
              { key: 'outlet', label: 'Outlet' }, { key: 'current', label: 'This period', format: 'currency' },
              { key: 'previous', label: 'Before', format: 'currency' }, { key: 'change', label: 'Change', format: 'currency' },
              { key: 'change_pct', label: '%', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
            ]} />
          </div>
        )}
        <div>
          <h3 className="small muted" style={{ margin: '0 0 6px' }}>By category</h3>
          <DataTable rows={d.categories} columns={[
            { key: 'category', label: 'Category' }, { key: 'current', label: 'This period', format: 'currency' },
            { key: 'change', label: 'Change', format: 'currency' },
            { key: 'change_pct', label: '%', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
          ]} />
        </div>
      </div>
      <div className="grid grid-3">
        <Card title="Promotions">
          <div className="small stack">
            <div>Estimated uplift: <b>{money(d.promotions.current.uplift)}</b> (before: {money(d.promotions.previous.uplift)})</div>
            <div>Discount given: {money(d.promotions.current.discount_given)}</div>
            <div className="muted">{d.promotions.current.running.join(', ') || 'No promotions running'}</div>
          </div>
        </Card>
        <Card title="Stockouts">
          <div className="small stack">
            <div>Estimated lost sales: <b>{money(d.stockouts.current.lost_revenue)}</b> (before: {money(d.stockouts.previous.lost_revenue)})</div>
            <div>{d.stockouts.current.events} stockout event(s), {d.stockouts.current.product_days} product-days</div>
            <div className="muted">{d.stockouts.current.top.map((t) => t.product).join(', ')}</div>
          </div>
        </Card>
        <Card title="Weather">
          <div className="small stack">
            {d.weather.rain_mm_per_day ? <>
              <div><CloudRain size={14} style={{ verticalAlign: -2 }} /> Rain {d.weather.rain_mm_per_day[0]} vs {d.weather.rain_mm_per_day[1]} mm/day</div>
              <div>Heavy-rain days: {d.weather.heavy_rain_days[0]} vs {d.weather.heavy_rain_days[1]}</div>
              <div className="muted">Revenue moves about {pct(d.weather.pct_per_10mm)} per extra 10 mm of rain (association).</div>
            </> : <div className="muted">{d.weather.note || 'No weather data'}</div>}
          </div>
        </Card>
      </div>
    </div>
  )
}

function Anomalies() {
  const { outletId } = useApp()
  const [period, setPeriod] = useState('90d')
  const q = useQuery({ queryKey: ['anomalies', period, outletId], queryFn: () => api('/anomalies', { params: { period, outlet_id: outletId } }) })
  return (
    <Card title="Unusual days and suspicious bills" subtitle="Daily revenue per outlet compared with its expected level for that weekday (robust z-score). Heavy-rain dips and festivals are shown as context."
      actions={<Seg options={ANOMALY_PERIODS} value={period} onChange={setPeriod} label="Period" />}>
      <Query q={q}>{(d) => <AnomalyResult d={d} />}</Query>
    </Card>
  )
}

function AnomalyResult({ d }) {
  const incidents = d.anomalies.filter((a) => !a.explained_by)
  const context = d.anomalies.filter((a) => a.explained_by)
  const ev = d.evaluation
  return (
    <div className="stack" style={{ gap: 16 }}>
      <div className="grid grid-4">
        <Kpi label="Unusual outlet-days" value={incidents.length} icon={AlertTriangle} />
        <Kpi label="Explained by context" value={context.length} hint="heavy rain or festival" icon={CloudRain} />
        <Kpi label="Suspicious bill lines" value={d.suspicious_lines.length} icon={Search} hint="likely typing errors" />
        <Kpi label="Detector check" value={ev ? `${Math.round((ev.recall || 0) * 100)}% found` : 'n/a'} icon={CheckCircle2}
          hint={ev ? `precision ${ev.precision}, recall ${ev.recall} vs ${ev.labelled} injected anomalies` : 'no labelled anomalies in this period'} />
      </div>
      {d.anomalies.length === 0
        ? <Empty title="No unusual days" icon={Activity}>Sales stayed within their normal range in this period.</Empty>
        : <DataTable rows={d.anomalies} maxHeight={420} columns={[
          { key: 'day', label: 'Date', format: 'date' },
          { key: 'outlet', label: 'Outlet' },
          { key: 'actual', label: 'Actual', format: 'currency' },
          { key: 'expected', label: 'Expected', format: 'currency' },
          { key: 'change_pct', label: 'Change', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
          { key: 'severity', label: 'Severity', render: (r) => (r.explained_by ? <Badge>{r.explained_by}</Badge> : <StatusBadge status={r.severity} />) },
          { key: 'explanation', label: 'Evidence', render: (r) => <span className="small">{r.explanation}</span> },
        ]} />}
      {d.suspicious_lines.length > 0 && (
        <div>
          <h3 className="small muted" style={{ margin: '0 0 6px' }}>Suspicious bill lines (quantity far above normal)</h3>
          <DataTable rows={d.suspicious_lines} columns={[
            { key: 'day', label: 'Date', format: 'date' }, { key: 'invoice_no', label: 'Bill' }, { key: 'outlet', label: 'Outlet' },
            { key: 'product', label: 'Product' }, { key: 'quantity', label: 'Qty', format: 'number' },
            { key: 'typical_quantity', label: 'Typical', format: 'number' }, { key: 'line_total', label: 'Amount', format: 'currency' },
          ]} />
        </div>
      )}
      {ev && (
        <details>
          <summary className="small"><b>Detector quality on the synthetic data</b> - {ev.true_positives} of {ev.labelled} injected anomalies found, {ev.false_positives} other day(s) flagged (F1 {ev.f1 ?? '-'})</summary>
          <div className="grid grid-2" style={{ marginTop: 10 }}>
            <DataTable rows={Object.entries(ev.by_kind).map(([kind, v]) => ({ kind: kind.replace('_', ' '), ...v }))} sortable={false} columns={[
              { key: 'kind', label: 'Injected anomaly type' }, { key: 'labelled', label: 'Injected', format: 'number' }, { key: 'detected', label: 'Found', format: 'number' },
            ]} />
            <DataTable rows={ev.labels} maxHeight={260} columns={[
              { key: 'day', label: 'Date', format: 'date' }, { key: 'kind', label: 'Type' },
              { key: 'description', label: 'What was injected', render: (r) => <span className="small">{r.description}</span> },
              { key: 'detected', label: 'Found', render: (r) => (r.detected ? <Badge tone="good">yes</Badge> : <Badge tone="warn">no</Badge>) },
            ]} />
          </div>
        </details>
      )}
    </div>
  )
}
