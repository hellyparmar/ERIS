import { useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Download, FileSpreadsheet, FileUp, PenLine, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, download } from '../lib/api'
import { useToast } from '../lib/app'
import { titleCase } from '../lib/format'
import { Card, DataTable, PageHead, Spinner } from '../components/ui'

const LABELS = { sales: 'Sales / bills', products: 'Products', customers: 'Customers', suppliers: 'Suppliers', inventory: 'Stock count' }
const MANUAL = { sales: '/sales', products: '/products', customers: '/customers', suppliers: '/suppliers', inventory: '/inventory' }

export default function DataImport() {
  const [params, setParams] = useSearchParams()
  const kind = params.get('type') || 'sales'
  const types = useQuery({ queryKey: ['import-types'], queryFn: () => api('/imports'), staleTime: Infinity })
  const t = types.data?.find((x) => x.kind === kind)
  return (
    <>
      <PageHead title="Data import" subtitle="Bring in data from spreadsheets, POS exports or other systems. Every file is checked before anything is saved." />
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
              <span className="small muted">* required. Column names are not case-sensitive. CSV files from Excel / Google Sheets work (comma, semicolon or tab separated).</span>
            </div>
          )}
        </Card>
        <Card title="Templates & manual entry">
          <div className="stack">
            <button className="btn" onClick={() => download(`/imports/templates/${kind}`)}><Download />Download {LABELS[kind].toLowerCase()} template</button>
            <Link className="btn" to={MANUAL[kind]}><PenLine />Enter {LABELS[kind].toLowerCase()} manually</Link>
            <span className="small muted">Fill the template in Excel or Google Sheets and save as CSV.</span>
          </div>
        </Card>
      </div>
      {types.isLoading ? <Spinner /> : <Uploader key={kind} kind={kind} />}
    </>
  )
}

function Uploader({ kind }) {
  const qc = useQueryClient()
  const toast = useToast()
  const input = useRef(null)
  const [file, setFile] = useState(null)
  const [updateStock, setUpdateStock] = useState(false)
  const [result, setResult] = useState(null)
  const [drag, setDrag] = useState(false)
  const run = useMutation({
    mutationFn: (dryRun) => {
      const form = new FormData()
      form.append('file', file)
      return api(`/imports/${kind}`, { method: 'POST', form, params: { dry_run: dryRun, update_stock: updateStock } })
    },
    onSuccess: (r) => {
      setResult(r)
      if (r.committed) { toast(r.message, 'success'); qc.invalidateQueries() }
    },
    onError: (e) => toast(e.message, 'error'),
  })
  const pick = (f) => { setFile(f); setResult(null) }
  return (
    <Card title="2. Upload and check">
      <div className="stack">
        <div onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); if (e.dataTransfer.files[0]) pick(e.dataTransfer.files[0]) }}
          onClick={() => input.current?.click()} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && input.current?.click()}
          style={{ border: `2px dashed ${drag ? 'var(--accent)' : 'var(--border-strong)'}`, borderRadius: 12, padding: 28, textAlign: 'center', cursor: 'pointer', background: drag ? 'var(--accent-soft)' : 'transparent' }}>
          <FileUp size={28} style={{ color: 'var(--muted)' }} />
          <div><b>{file ? file.name : 'Drop a CSV file here or click to choose'}</b></div>
          <div className="small muted">{file ? `${(file.size / 1024).toFixed(1)} KB` : 'Max 15 MB / 50,000 rows'}</div>
          <input ref={input} type="file" accept=".csv,text/csv" hidden onChange={(e) => e.target.files[0] && pick(e.target.files[0])} />
        </div>
        {kind === 'sales' && (
          <label className="check"><input type="checkbox" checked={updateStock} onChange={(e) => setUpdateStock(e.target.checked)} />
            Reduce stock for these sales <span className="small muted">(leave off when importing past sales that are already reflected in your stock count)</span></label>
        )}
        <div className="row">
          <button className="btn" disabled={!file || run.isPending} onClick={() => run.mutate(true)}>Check file</button>
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

function Result({ r }) {
  const ok = r.error_count === 0
  return (
    <div className="stack">
      <div className={`alert ${ok ? 'info' : 'critical'}`}>
        {ok ? <CheckCircle2 /> : <XCircle />}
        <div>
          <b>{r.message}</b>
          <p>{r.total_rows} rows read{r.bills ? ` · ${r.bills} bills` : ''} · {r.created} {r.dry_run ? 'to create' : 'created'} · {r.updated} {r.dry_run ? 'to update' : 'updated'} · {r.error_count} with errors</p>
        </div>
      </div>
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
