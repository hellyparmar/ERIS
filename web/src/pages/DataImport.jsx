import { useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, Download, FileSpreadsheet, FileUp, PenLine, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, download } from '../lib/api'
import { useToast } from '../lib/app'
import { dateTime, titleCase } from '../lib/format'
import { Badge, Card, DataTable, PageHead, Pager, Query, Spinner } from '../components/ui'

const LABELS = { sales: 'Sales / bills', products: 'Products', customers: 'Customers', suppliers: 'Suppliers', inventory: 'Stock count' }
const MANUAL = { sales: '/sales', products: '/products', customers: '/customers', suppliers: '/suppliers', inventory: '/inventory' }

export default function DataImport() {
  const [params, setParams] = useSearchParams()
  const kind = params.get('type') || 'sales'
  const types = useQuery({ queryKey: ['import-types'], queryFn: () => api('/imports'), staleTime: Infinity })
  const t = types.data?.find((x) => x.kind === kind)
  return (
    <>
      <PageHead title="Data import" subtitle="Upload CSV files. Every file is checked before anything is saved." />
      <div className="grid grid-3">
        <Card title="1. What are you importing?" className="span-2">
          <div className="row">
            {Object.entries(LABELS).map(([k, label]) => (
              <button key={k} className={`btn ${kind === k ? 'primary' : ''}`} onClick={() => setParams({ type: k })}><FileSpreadsheet />{label}</button>
            ))}
          </div>
          {t && (
            <div className="stack" style={{ marginTop: 14 }}>
              <p className="text-2">{t.help}</p>
              <div className="small"><b>Columns:</b> {t.columns.map((c) => <span key={c} className="kbd" style={{ marginRight: 4, display: 'inline-block', marginBottom: 4 }}>{c}{t.required.includes(c) ? '*' : ''}</span>)}</div>
              <span className="small muted">* required</span>
            </div>
          )}
        </Card>
        <Card title="Templates & manual entry">
          <div className="stack">
            <button className="btn" onClick={() => download(`/imports/templates/${kind}`)}><Download />Empty template</button>
            <button className="btn" onClick={() => download(`/imports/samples/${kind}`)}><Download />Sample file (valid)</button>
            <button className="btn" onClick={() => download(`/imports/samples/${kind}`, { with_errors: true })}><AlertTriangle />Sample with mistakes</button>
            <Link className="btn" to={MANUAL[kind]}><PenLine />Enter {LABELS[kind].toLowerCase()} manually</Link>
          </div>
        </Card>
      </div>
      {types.isLoading ? <Spinner /> : <Uploader key={kind} kind={kind} />}
      <History kind={kind} />
    </>
  )
}

function Uploader({ kind }) {
  const qc = useQueryClient()
  const toast = useToast()
  const input = useRef(null)
  const [file, setFile] = useState(null)
  const [updateStock, setUpdateStock] = useState(false)
  const [skipDuplicates, setSkipDuplicates] = useState(true)
  const [inspect, setInspect] = useState(null)
  const [mapping, setMapping] = useState({})
  const [result, setResult] = useState(null)
  const [drag, setDrag] = useState(false)
  const inspectM = useMutation({
    mutationFn: (f) => {
      const form = new FormData()
      form.append('file', f)
      return api(`/imports/${kind}/inspect`, { method: 'POST', form })
    },
    onSuccess: (r) => { setInspect(r); setMapping(r.mapping) },
    onError: (e) => { toast(e.message, 'error'); setFile(null) },
  })
  const run = useMutation({
    mutationFn: (dryRun) => {
      const form = new FormData()
      form.append('file', file)
      form.append('mapping', JSON.stringify(mapping))
      return api(`/imports/${kind}`, { method: 'POST', form, params: { dry_run: dryRun, update_stock: updateStock, skip_duplicates: skipDuplicates } })
    },
    onSuccess: (r) => {
      setResult(r)
      qc.invalidateQueries({ queryKey: ['import-history'] })
      if (r.committed) { toast(r.message, 'success'); qc.invalidateQueries() }
    },
    onError: (e) => toast(e.message, 'error'),
  })
  const pick = (f) => { setFile(f); setResult(null); setInspect(null); inspectM.mutate(f) }
  const setCol = (col, header) => { setMapping((m) => ({ ...m, [col]: header || null })); setResult(null) }
  const missing = inspect ? inspect.required.filter((c) => !mapping[c] && !(c === 'outlet_code' && (mapping.outlet || mapping.outlet_name)) && !(c === 'sku' && (mapping.product || mapping.product_name))) : []
  return (
    <Card title="2. Upload, match columns and check">
      <div className="stack">
        <div onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); if (e.dataTransfer.files[0]) pick(e.dataTransfer.files[0]) }}
          onClick={() => input.current?.click()} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && input.current?.click()}
          style={{ border: `2px dashed ${drag ? 'var(--accent)' : 'var(--border-strong)'}`, borderRadius: 12, padding: 28, textAlign: 'center', cursor: 'pointer', background: drag ? 'var(--accent-soft)' : 'transparent' }}>
          <FileUp size={28} style={{ color: 'var(--muted)' }} />
          <div><b>{file ? file.name : 'Drop a CSV file here or click to choose'}</b></div>
          <div className="small muted">{file ? `${(file.size / 1024).toFixed(1)} KB${inspect ? ` · ${inspect.rows.toLocaleString('en-IN')} rows · ${inspect.headers.length} columns` : ''}` : 'CSV only (save Excel files as CSV) · max 15 MB / 50,000 rows'}</div>
          <input ref={input} type="file" accept=".csv,.txt,.tsv,text/csv" hidden onChange={(e) => e.target.files[0] && pick(e.target.files[0])} />
        </div>
        {inspectM.isPending && <Spinner label="Reading the file…" />}
        {inspect && (
          <div className="stack">
            <b>Match your columns</b>
            <span className="small muted">Check the suggested matches.</span>
            <div className="form-grid">
              {inspect.columns.map((col) => (
                <label key={col} className="field">
                  <span>{col}{inspect.required.includes(col) ? ' *' : ''}</span>
                  <select className="select" value={mapping[col] || ''} onChange={(e) => setCol(col, e.target.value)}>
                    <option value="">- not in file -</option>
                    {inspect.headers.map((h) => <option key={h} value={h}>{h}</option>)}
                  </select>
                </label>
              ))}
            </div>
            {missing.length > 0 && <div className="alert warning"><AlertTriangle /><div><b>Required fields not matched: {missing.join(', ')}</b><p>Choose the column that holds them.</p></div></div>}
            {inspect.sample.length > 0 && (
              <Card title="First rows of your file" flush>
                <DataTable rows={inspect.sample.map((r, i) => ({ ...r, id: i }))} sortable={false}
                  columns={Object.keys(inspect.sample[0]).map((k) => ({ key: k, label: k }))} />
              </Card>
            )}
          </div>
        )}
        {kind === 'sales' && (
          <>
            <label className="check"><input type="checkbox" checked={updateStock} onChange={(e) => setUpdateStock(e.target.checked)} />
              Reduce stock for these sales <span className="small muted">(off for past sales already in your stock count)</span></label>
            <label className="check"><input type="checkbox" checked={skipDuplicates} onChange={(e) => { setSkipDuplicates(e.target.checked); setResult(null) }} />
              Skip bills that are already in ERIS </label>
          </>
        )}
        <div className="row">
          <button className="btn" disabled={!inspect || missing.length > 0 || run.isPending} onClick={() => run.mutate(true)}>Check file (dry run)</button>
          <button className="btn primary" disabled={!file || run.isPending || !result || result.dry_run === false || result.error_count > 0} onClick={() => run.mutate(false)}>
            Import {result && result.dry_run && !result.error_count ? `${result.created + result.updated} record(s)` : ''}
          </button>
          {run.isPending && <div className="spinner" />}
        </div>
        {result && <Result r={result} />}
      </div>
    </Card>
  )
}

function History({ kind }) {
  const [page, setPage] = useState(1)
  const q = useQuery({ queryKey: ['import-history', kind, page], queryFn: () => api('/imports/history', { params: { kind, page, page_size: 10 } }) })
  const tone = { committed: 'good', validated: 'info', rejected: 'bad', failed: 'bad', running: 'warn' }
  return (
    <Card title="Import history"  flush>
      <Query q={q}>{(d) => (
        <>
          <DataTable rows={d.items} sortable={false} empty="No imports yet" columns={[
            { key: 'created_at', label: 'When', render: (r) => dateTime(r.created_at) },
            { key: 'filename', label: 'File' },
            { key: 'user', label: 'By' },
            { key: 'status', label: 'Result', render: (r) => <Badge tone={tone[r.status]}>{r.dry_run && r.status !== 'rejected' ? 'checked' : r.status}{r.dry_run ? ' (dry run)' : ''}</Badge> },
            { key: 'total_rows', label: 'Rows', format: 'number' },
            { key: 'created', label: 'Created', format: 'number' },
            { key: 'updated', label: 'Updated', format: 'number' },
            { key: 'errors', label: 'Errors', format: 'number' },
            { key: 'report', label: '', render: (r) => (r.errors > 0 || r.status === 'committed'
              ? <button className="btn sm" onClick={() => download(`/imports/history/${r.id}/errors.csv`)}><Download />Report</button> : null) },
          ]} />
          {d.pages > 1 && <Pager page={page} pages={d.pages} total={d.total} onPage={setPage} label="imports" />}
        </>
      )}</Query>
    </Card>
  )
}

function Result({ r }) {
  const ok = r.error_count === 0
  return (
    <div className="stack">
      <div className={`alert ${ok ? 'info' : 'critical'}`}>
        {ok ? <CheckCircle2 /> : <XCircle />}
        <div>
          <b>{r.message}</b>
          <p>{r.total_rows} rows read{r.bills ? ` · ${r.bills} bills` : ''} · {r.created} {r.dry_run ? 'to create' : 'created'} · {r.updated} {r.dry_run ? 'to update' : 'updated'} · {r.error_count} with errors{r.skipped_duplicates ? ` · ${r.skipped_duplicates} duplicate bill(s) skipped` : ''}</p>
        </div>
        {r.job_id && (r.error_count > 0 || r.warnings?.length > 0) && <button className="btn sm" onClick={() => download(`/imports/history/${r.job_id}/errors.csv`)}><Download />Error report</button>}
      </div>
      {r.warnings?.length > 0 && (
        <Card title="Warnings (not blocking)" flush>
          <DataTable rows={r.warnings.map((e, i) => ({ ...e, id: i }))} maxHeight={200} columns={[{ key: 'row', label: 'Row', format: 'number', width: 70 }, { key: 'message', label: 'Note' }]} />
        </Card>
      )}
      {r.errors.length > 0 && (
        <Card title="Rows to fix" subtitle="Row numbers match your spreadsheet (row 1 is the header)" flush>
          <DataTable rows={r.errors.map((e, i) => ({ ...e, id: i }))} maxHeight={300} columns={[{ key: 'row', label: 'Row', format: 'number', width: 70 }, { key: 'message', label: 'Problem' }]} />
        </Card>
      )}
      {r.preview.length > 0 && (
        <Card title={r.dry_run ? 'Preview' : 'Imported (first rows)'} flush>
          <DataTable rows={r.preview.map((p, i) => ({ ...p, id: i }))} columns={Object.keys(r.preview[0]).map((k) => ({ key: k, label: titleCase(k) }))} />
        </Card>
      )}
    </div>
  )
}
