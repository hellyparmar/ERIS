import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { CalendarDays, Download, FlaskConical, Lightbulb, PackageCheck } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date, formatValue, money, num } from '../lib/format'
import { Badge, Card, DataTable, Delta, Empty, ErrorState, Field, Kpi, PageHead, Seg, Spinner } from '../components/ui'
import { ForecastChart } from '../components/charts'
import { ProductSearch, useCategories } from '../components/pickers'

const SCOPES = [{ value: 'total', label: 'Total sales' }, { value: 'outlet', label: 'Outlet' }, { value: 'category', label: 'Category' }, { value: 'product', label: 'Product' }]
const HORIZONS = [7, 14, 30].map((h) => ({ value: h, label: `${h} days` }))

function toCsv(fc) {
  const rows = [['date', 'forecast', 'lower_80', 'upper_80'], ...fc.forecast.map((f) => [f.date, f.yhat, f.lower, f.upper])]
  const blob = new Blob([rows.map((r) => r.join(',')).join('\n')], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `forecast_${fc.series.scope}_${fc.as_of}.csv`
  a.click()
}

export default function Forecasts() {
  const { outlets, outletId, user } = useApp()
  const cats = useCategories()
  const [params, setParams] = useSearchParams()
  const scope = params.get('scope') || 'total'
  const targetId = params.get('id') ? Number(params.get('id')) : null
  const [horizon, setHorizon] = useState(30)
  const [model, setModel] = useState('auto')
  const [showBacktest, setShowBacktest] = useState(false)
  const [productName, setProductName] = useState(null)
  const models = useQuery({ queryKey: ['fc-models'], queryFn: () => api('/forecast/models'), staleTime: Infinity })

  const myOutlets = user.role === 'admin' ? outlets : outlets.filter((o) => user.outlet_ids.includes(o.id))
  const effectiveTarget = scope === 'outlet' ? (targetId || outletId || myOutlets[0]?.id) : targetId
  const ready = scope === 'total' || !!effectiveTarget
  const qp = { scope, target_id: scope === 'total' ? undefined : effectiveTarget, horizon, model, outlet_id: scope === 'outlet' ? undefined : outletId }
  const q = useQuery({ queryKey: ['forecast', qp], queryFn: () => api('/forecast', { params: qp }), enabled: ready, staleTime: 300_000 })
  const byOutlet = useQuery({ queryKey: ['forecast-outlets', horizon], queryFn: () => api('/forecast/outlets', { params: { horizon } }), enabled: scope === 'total' && user.role === 'admin' && !outletId, staleTime: 300_000 })
  const setScope = (s) => setParams({ scope: s })
  const setTarget = (id) => setParams({ scope, id: String(id) })

  return (
    <>
      <PageHead title="Forecasts" subtitle="Demand and revenue forecasts. Seasonal naive, Holt-Winters, XGBoost, Prophet and an ensemble are back-tested on the latest weeks of every series; the most reliable one is used.">
        <Link className="btn" to="/models"><FlaskConical />Model comparison</Link>
      </PageHead>
      <Card>
        <div className="row" style={{ alignItems: 'flex-end', gap: 14 }}>
          <Field label="Forecast"><Seg options={SCOPES} value={scope} onChange={setScope} label="Scope" /></Field>
          {scope === 'outlet' && (
            <Field label="Outlet">
              <select className="select" value={effectiveTarget || ''} onChange={(e) => setTarget(e.target.value)} disabled={myOutlets.length <= 1}>
                {myOutlets.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
              </select>
            </Field>
          )}
          {scope === 'category' && (
            <Field label="Category">
              <select className="select" value={targetId || ''} onChange={(e) => setTarget(e.target.value)}>
                <option value="">Choose…</option>{(cats.data || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </Field>
          )}
          {scope === 'product' && (
            <Field label={productName ? `Product: ${productName}` : q.data?.series.scope === 'product' ? q.data.series.label.replace('Units - ', 'Product: ') : 'Product'}>
              <div style={{ width: 280 }}><ProductSearch onPick={(p) => { setProductName(p.name); setTarget(p.id) }} placeholder={targetId ? 'Change product…' : 'Search a product…'} /></div>
            </Field>
          )}
          <Field label="Horizon"><Seg options={HORIZONS} value={horizon} onChange={setHorizon} label="Horizon" /></Field>
          <Field label="Model">
            <select className="select" value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="auto">Auto (best in back-test)</option>{(models.data || []).map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
            </select>
          </Field>
        </div>
      </Card>
      {!ready ? <Card><div className="empty"><b>Choose what to forecast</b><div className="small">Pick a {scope} above.</div></div></Card>
        : q.isError && q.error?.status === 400 ? (
          <Card><Empty title="Not enough sales history for this forecast yet" icon={CalendarDays}>
            {q.error.message}. Forecasts become available automatically once enough bills are recorded -
            add past sales on the <Link to="/import?type=sales">Data import</Link> page to start sooner.
          </Empty></Card>)
          : q.isError ? <ErrorState error={q.error} onRetry={q.refetch} />
          : q.isLoading ? <Card><Spinner label="Training and back-testing models… (a few seconds the first time)" /></Card>
            : <Result fc={q.data} showBacktest={showBacktest} setShowBacktest={setShowBacktest} />}
      {scope === 'total' && byOutlet.data?.length > 0 && (
        <Card title={`Outlet outlook - next ${horizon} days`} subtitle="Each outlet forecast with its own best model" flush>
          <DataTable rows={byOutlet.data} columns={[
            { key: 'outlet', label: 'Outlet' },
            { key: 'forecast_total', label: 'Forecast', format: 'currency' },
            { key: 'last_period', label: horizon >= 30 ? 'Last 30 days' : 'Last 7 days', format: 'currency' },
            { key: 'change_pct', label: 'Change', align: 'right', render: (r) => <Delta value={r.change_pct} /> },
            { key: 'model', label: 'Model' }, { key: 'wape', label: 'Back-test error', align: 'right', render: (r) => `${r.wape}%` },
          ]} />
        </Card>
      )}
    </>
  )
}

function Result({ fc, showBacktest, setShowBacktest }) {
  const s = fc.summary
  const isUnits = fc.series.target === 'units'
  const fmt = isUnits ? 'number' : 'currency'
  const val = (v) => (isUnits ? `${num(v)} units` : money(v, { compact: true }))
  const selected = fc.evaluation.find((e) => e.selected)
  const plan = fc.stock_plan
  return (
    <>
      <div className="grid grid-4">
        <Kpi label="Next 7 days" value={val(s.next_7_days)} change={s.change_vs_last_7_pct} hint="vs last 7 days" />
        <Kpi label={`Next ${fc.horizon} days`} value={val(s.horizon_total)} change={s.change_vs_last_30_pct ?? undefined} hint={`≈ ${isUnits ? num(s.avg_daily, 1) : money(s.avg_daily)} per day`} />
        <Kpi label="Peak day" value={date(s.peak_day.date, { weekday: 'short', day: 'numeric', month: 'short' })} hint={formatValue(s.peak_day.yhat, fmt)} />
        <Kpi label="Forecast error (back-test)" value={`${selected.wape}%`} hint={`WAPE · ${selected.label}`} />
      </div>
      <div className="grid grid-3">
        <Card className="span-2" title={fc.series.label} subtitle={`Last ${fc.history.length} days of actuals and ${fc.horizon}-day forecast with 80% range · data to ${date(fc.as_of)}`}
          actions={<>
            <label className="check small"><input type="checkbox" checked={showBacktest} onChange={(e) => setShowBacktest(e.target.checked)} />Show back-test</label>
            <button className="btn sm" onClick={() => toCsv(fc)}><Download />CSV</button>
          </>}>
          <ForecastChart history={fc.history} forecast={fc.forecast} backtest={showBacktest ? fc.backtest : null} format={fmt} />
        </Card>
        <div className="stack" style={{ gap: 16 }}>
          <Card title="What this means">
            <div className="stack">{fc.insights.map((t) => <div key={t} className="row" style={{ alignItems: 'flex-start', flexWrap: 'nowrap' }}><Lightbulb size={16} style={{ flex: 'none', color: 'var(--s4)', marginTop: 2 }} /><span>{t}</span></div>)}</div>
          </Card>
          {fc.events.length > 0 && (
            <Card title="Festivals in this window">
              <div className="stack">{fc.events.map((e) => <div key={e.date} className="row between"><span><CalendarDays size={14} style={{ verticalAlign: -2 }} /> {e.name}</span><span className="small muted">{date(e.date)} · in {e.days_away} days</span></div>)}</div>
            </Card>
          )}
          {plan && (
            <Card title="Stock plan">
              <div className="stack">
                <div className="row between"><span className="muted">In stock</span><b>{num(plan.current_stock)} {plan.unit}</b></div>
                <div className="row between"><span className="muted">Days of cover</span><b>{plan.days_of_cover ?? '-'}</b></div>
                <div className="row between"><span className="muted">Projected stock-out</span><b className={plan.projected_stockout ? 'down' : ''}>{plan.projected_stockout ? date(plan.projected_stockout) : 'Not in window'}</b></div>
                <div className="row between"><span className="muted">Safety stock</span><b>{num(plan.safety_stock)}</b></div>
                <div className="alert info"><PackageCheck /><div><b>{plan.recommended_order_qty > 0 ? `Order ${num(plan.recommended_order_qty)} ${plan.unit}` : plan.reorder_by ? `No order needed yet - reorder by ${date(plan.reorder_by)}` : 'No order needed now'}</b><p>Covers {plan.lead_time_days}-day lead time + 1 week of forecast demand at ~95% service level.</p></div></div>
              </div>
            </Card>
          )}
        </div>
      </div>
      <div className="grid grid-3">
        <Card title="Model leaderboard" subtitle={`Back-tested on the last ${fc.test_days} days (lower error is better)`} flush className="span-2">
          <DataTable rows={[...fc.evaluation].sort((a, b) => (a.wape ?? 999) - (b.wape ?? 999))} sortable={false} columns={[
            { key: 'label', label: 'Model', render: (r) => <span title={r.label}><b>{r.label.split(' (')[0]}</b> {r.selected && <Badge tone="good">used</Badge>}{r.error && <div className="small down">failed: {r.error}</div>}</span> },
            { key: 'wape', label: 'WAPE', align: 'right', render: (r) => (r.wape != null ? `${r.wape}%` : '-') },
            { key: 'smape', label: 'sMAPE', align: 'right', render: (r) => (r.smape != null ? `${r.smape}%` : '-') },
            { key: 'mae', label: 'MAE', align: 'right', render: (r) => (r.mae != null ? formatValue(r.mae, fmt) : '-') },
            { key: 'rmse', label: 'RMSE', align: 'right', render: (r) => (r.rmse != null ? formatValue(r.rmse, fmt) : '-') },
            { key: 'interval_coverage', label: '80% band', align: 'right', render: (r) => (r.interval_coverage != null ? `${r.interval_coverage}%` : '-') },
            { key: 'bias_pct', label: 'Bias', align: 'right', render: (r) => (r.bias_pct != null ? `${r.bias_pct > 0 ? '+' : ''}${r.bias_pct}%` : '-') },
          ]} />
          <p className="small muted" style={{ padding: 12 }}><FlaskConical size={13} style={{ verticalAlign: -2 }} /> WAPE = total absolute error ÷ total actual. 80% band = share of back-test days inside the prediction range (ideal ≈ 80%). Bias &gt; 0 means the model over-forecasts.</p>
          <p className="small muted" style={{ padding: '0 12px 12px' }}>
            Run {fc.run_id ? <Link to={`/models?run=${fc.run_id}`}>#{fc.run_id}</Link> : '(not saved)'} · model version {fc.model_version} · trained on {fc.data_range ? `${date(fc.data_range.start)} – ${date(fc.data_range.end)} (${fc.data_range.days} days)` : '-'} · {fc.features?.length || 0} features
          </p>
        </Card>
        <Card title="Daily forecast" subtitle="With the 80% range" flush>
          <DataTable maxHeight={430} rows={fc.forecast} sortable={false} columns={[
            { key: 'date', label: 'Date', render: (r) => <span className="nowrap">{date(r.date, { weekday: 'short', day: 'numeric', month: 'short' })}</span> },
            { key: 'yhat', label: 'Forecast', format: fmt }, { key: 'lower', label: 'Low', format: fmt }, { key: 'upper', label: 'High', format: fmt },
          ]} />
        </Card>
      </div>
    </>
  )
}
