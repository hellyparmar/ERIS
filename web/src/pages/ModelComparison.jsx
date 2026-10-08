import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FlaskConical, Play, Trophy } from 'lucide-react'
import { api } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { date, dateTime } from '../lib/format'
import { Badge, Card, DataTable, Drawer, Empty, Kpi, PageHead, Pager, Query, Spinner } from '../components/ui'
import { BarsChart, ForecastChart } from '../components/charts'

const SCOPE_LABELS = { total: 'Whole business', outlet: 'Outlets', category: 'Categories', product: 'Products', 'all series': 'All series' }
const fmtPct = (v) => (v === null || v === undefined ? '-' : `${Number(v).toFixed(1)}%`)

export default function ModelComparison() {
  const [params, setParams] = useSearchParams()
  const runId = params.get('run') ? Number(params.get('run')) : null
  return (
    <>
      <PageHead title="Model comparison"
        subtitle="How accurate each forecasting model is on your data." />
      <Evaluation />
      <RunHistory onOpen={(id) => setParams({ run: String(id) })} />
      {runId && <RunDrawer id={runId} onClose={() => setParams({})} />}
    </>
  )
}

function Evaluation() {
  const { isManager } = useApp()
  const toast = useToast()
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['evaluation-latest'],
    queryFn: () => api('/forecast/evaluations/latest'),
    refetchInterval: (x) => (x.state.data?.job?.running ? 3000 : false),
  })
  const start = useMutation({
    mutationFn: () => api('/forecast/evaluations', { method: 'POST', params: { origins: 2, products: 5 } }),
    onSuccess: () => { toast('Evaluation started - this takes a few minutes', 'success'); q.refetch() },
    onError: (e) => toast(e.message, 'error'),
  })
  const running = q.data?.job?.running
  const wasRunning = useRef(false)
  useEffect(() => {
    if (running) wasRunning.current = true
    else if (wasRunning.current) { wasRunning.current = false; qc.invalidateQueries({ queryKey: ['forecast-runs'] }) }
  }, [running, qc])

  return (
    <Card title="Rolling-origin evaluation"
      subtitle="Each model is trained on data before several cut-off dates and scored on the following 28 days, for the whole business, every outlet, every category and the top products. 'ERIS auto' is the production pipeline (inner back-test, then model choice)."
      actions={isManager && <button className="btn primary" disabled={running || start.isPending} onClick={() => start.mutate()}><Play />{running ? 'Running…' : 'Run evaluation'}</button>}>
      <Query q={q}>{(d) => {
        const job = d.job || {}
        if (running) return <div className="alert info"><div className="spinner" style={{ width: 16, height: 16 }} /><div><b>Evaluation running</b><p>{job.message}</p></div></div>
        if (!d.run) {
          return (
            <Empty title="No evaluation yet" icon={FlaskConical}>
              {isManager ? 'Run an evaluation to compare the models across all series (takes a few minutes).' : 'Ask a manager or admin to run an evaluation.'}
              {job.message && <div className="down">{job.message}</div>}
            </Empty>
          )
        }
        return <EvaluationResult run={d.run} />
      }}</Query>
    </Card>
  )
}

function EvaluationResult({ run }) {
  const p = run.parameters || {}
  const overall = (run.metrics || []).filter((m) => m.wape !== null)
  const best = [...overall].filter((m) => m.model !== 'auto').sort((a, b) => a.wape - b.wape)[0]
  const auto = overall.find((m) => m.model === 'auto')
  const scopes = Object.keys(Object.values(p.wape_by_scope || {})[0] || {})
  const byScope = Object.entries(p.wape_by_scope || {}).map(([model, v]) => ({ model: overall.find((m) => m.model === model)?.label || model, ...v }))
  const models = overall.map((m) => m.model)
  const bySeries = Object.entries(p.wape_by_series || {}).map(([series, v]) => {
    const winner = Object.entries(v).filter(([m, w]) => m !== 'auto' && w !== null).sort((a, b) => a[1] - b[1])[0]?.[0]
    return { series, ...v, winner }
  })
  return (
    <div className="stack" style={{ gap: 16 }}>
      <div className="grid grid-4">
        <Kpi label="Most accurate single model" value={best?.label || '-'} hint={best ? `${fmtPct(best.wape)} mean WAPE` : ''} icon={Trophy} />
        <Kpi label="ERIS auto-selection" value={fmtPct(auto?.wape)} hint="mean WAPE (what users get)" />
        <Kpi label="80% band coverage" value={fmtPct(p.auto_interval_coverage)} hint="ideal ≈ 80%" />
        <Kpi label="Scope" value={`${p.series} series`} hint={`${p.origins} origins × ${p.horizon} days · ${p.runs} model fits`} />
      </div>
      <div className="grid grid-2">
        <div>
          <h3 className="small muted" style={{ margin: '0 0 6px' }}>Mean WAPE by model (lower is better)</h3>
          <BarsChart data={overall} x="label" series={[{ key: 'wape', label: 'WAPE %' }]} format="percent_plain" horizontal height={200} />
        </div>
        <DataTable rows={overall} sortable={false} columns={[
          { key: 'label', label: 'Model', render: (r) => <><b>{r.label}</b> {r.model === best?.model && <Badge tone="good">best</Badge>}</> },
          { key: 'wape', label: 'WAPE', align: 'right', render: (r) => fmtPct(r.wape) },
          { key: 'smape', label: 'sMAPE', align: 'right', render: (r) => fmtPct(r.smape) },
          { key: 'bias_pct', label: 'Bias', align: 'right', render: (r) => fmtPct(r.bias_pct) },
          { key: 'seconds', label: 'Fit time', align: 'right', render: (r) => (r.seconds != null ? `${r.seconds.toFixed(1)}s` : '-') },
        ]} />
      </div>
      <div className="grid grid-2">
        <div>
          <h3 className="small muted" style={{ margin: '0 0 6px' }}>Mean WAPE by series type</h3>
          <DataTable rows={byScope} sortable={false} columns={[{ key: 'model', label: 'Model' },
            ...scopes.map((s) => ({ key: s, label: SCOPE_LABELS[s] || s, align: 'right', render: (r) => fmtPct(r[s]) }))]} />
        </div>
        <div>
          <h3 className="small muted" style={{ margin: '0 0 6px' }}>How often each model was best / chosen</h3>
          <DataTable rows={models.filter((m) => m !== 'auto').map((m) => ({ model: overall.find((x) => x.model === m)?.label, wins: p.wins?.[m] || 0, chosen: p.chosen?.[m] || 0 }))} sortable={false} columns={[
            { key: 'model', label: 'Model' }, { key: 'wins', label: 'Lowest error (series × origin)', format: 'number' },
            { key: 'chosen', label: 'Chosen by ERIS auto', format: 'number' },
          ]} />
        </div>
      </div>
      {bySeries.length > 0 && (
        <div>
          <h3 className="small muted" style={{ margin: '0 0 6px' }}>WAPE per series</h3>
          <DataTable rows={bySeries} maxHeight={360} columns={[{ key: 'series', label: 'Series' },
            ...models.map((m) => ({ key: m, label: overall.find((x) => x.model === m)?.label.split(' (')[0] || m, align: 'right',
              render: (r) => <span style={r.winner === m ? { fontWeight: 700, color: 'var(--good)' } : undefined}>{fmtPct(r[m])}</span> }))]} />
        </div>
      )}
      <p className="small muted">Evaluation #{run.id} · model version {run.model_version} · {dateTime(run.created_at)} · took {Math.round(run.duration_seconds || 0)}s · data up to {date(run.data_end)}. Accuracy is measured on the synthetic demo dataset.</p>
    </div>
  )
}

function RunHistory({ onOpen }) {
  const [page, setPage] = useState(1)
  const q = useQuery({ queryKey: ['forecast-runs', page], queryFn: () => api('/forecast/runs', { params: { page, page_size: 15 } }) })
  return (
    <Card flush title="Forecast run history" >
      <Query q={q}>{(d) => (
        <>
          <DataTable rows={d.items} onRowClick={(r) => onOpen(r.id)} empty="No forecasts yet - open the Forecasts page to create one" columns={[
            { key: 'id', label: 'Run', render: (r) => `#${r.id}` },
            { key: 'created_at', label: 'When', render: (r) => dateTime(r.created_at) },
            { key: 'series', label: 'Series' },
            { key: 'horizon', label: 'Horizon', render: (r) => `${r.horizon} days` },
            { key: 'selected_label', label: 'Chosen model', render: (r) => (r.status === 'ok' ? r.selected_label : <Badge tone="bad">failed</Badge>) },
            { key: 'wape', label: 'Back-test WAPE', align: 'right', render: (r) => fmtPct(r.wape) },
            { key: 'duration_seconds', label: 'Time', align: 'right', render: (r) => (r.duration_seconds != null ? `${r.duration_seconds}s` : '-') },
          ]} />
          {d.pages > 1 && <Pager page={page} pages={d.pages} total={d.total} onPage={setPage} label="runs" />}
        </>
      )}</Query>
    </Card>
  )
}

function RunDrawer({ id, onClose }) {
  const q = useQuery({ queryKey: ['forecast-run', id], queryFn: () => api(`/forecast/runs/${id}`) })
  return (
    <Drawer title={`Forecast run #${id}`} onClose={onClose}>
      {q.isLoading ? <Spinner /> : q.isError ? <div className="down">{q.error.message}</div> : <RunDetail r={q.data} />}
    </Drawer>
  )
}

function RunDetail({ r }) {
  const metrics = (r.metrics || []).filter((m) => m.wape !== undefined)
  const p = r.parameters || {}
  return (
    <div className="stack" style={{ gap: 16 }}>
      <dl className="dl">
        <dt>Series</dt><dd>{r.series} ({r.scope}, {r.target})</dd>
        <dt>Status</dt><dd>{r.status === 'ok' ? <Badge tone="good">ok</Badge> : <><Badge tone="bad">failed</Badge> {r.error}</>}</dd>
        <dt>Data used</dt><dd>{r.data_start ? `${date(r.data_start)} – ${date(r.data_end)}` : '-'}</dd>
        <dt>Horizon</dt><dd>{r.horizon} days</dd>
        <dt>Chosen model</dt><dd>{r.selected_label || '-'}</dd>
        <dt>Selection rule</dt><dd>{p.selection || '-'}</dd>
        <dt>Prediction interval</dt><dd>{p.interval || '-'}</dd>
        <dt>Model version</dt><dd>{r.model_version}</dd>
        <dt>Created</dt><dd>{dateTime(r.created_at)} · {r.duration_seconds}s</dd>
      </dl>
      {r.results?.length > 0 && <ForecastChart history={[]} forecast={r.results.map((x) => ({ date: x.date, yhat: x.yhat, lower: x.lower, upper: x.upper }))} format={r.target === 'units' ? 'number' : 'currency'} height={220} />}
      {metrics.length > 0 && (
        <DataTable rows={metrics} sortable={false} columns={[
          { key: 'label', label: 'Model', render: (m) => <>{m.label} {m.selected && <Badge tone="good">used</Badge>}{m.error && <div className="small down">{m.error}</div>}</> },
          { key: 'wape', label: 'WAPE', align: 'right', render: (m) => fmtPct(m.wape) },
          { key: 'smape', label: 'sMAPE', align: 'right', render: (m) => fmtPct(m.smape) },
          { key: 'mae', label: 'MAE', align: 'right', render: (m) => m.mae ?? '-' },
          { key: 'rmse', label: 'RMSE', align: 'right', render: (m) => m.rmse ?? '-' },
          { key: 'interval_coverage', label: '80% band', align: 'right', render: (m) => fmtPct(m.interval_coverage) },
        ]} />
      )}
      {p.xgboost && <div className="small"><b>XGBoost parameters:</b> <code>{JSON.stringify(p.xgboost)}</code></div>}
      {p.ensemble_members && <div className="small"><b>Ensemble members:</b> {p.ensemble_members.join(' + ')}</div>}
      {r.features?.length > 0 && <div className="small"><b>Features ({r.features.length}):</b> <span className="muted">{r.features.join(', ')}</span></div>}
    </div>
  )
}
