import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, FileSpreadsheet, FileText } from 'lucide-react'
import { download, api } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { formatValue } from '../lib/format'
import { Card, Empty, PageHead, Query, Seg, Spinner } from '../components/ui'

const PERIODS = [{ value: '7d', label: '7 days' }, { value: '30d', label: '30 days' }, { value: 'mtd', label: 'This month' },
  { value: '90d', label: '90 days' }, { value: 'ytd', label: 'This year' }, { value: '365d', label: '12 months' }]

export default function Reports() {
  const { outletId } = useApp()
  const toast = useToast()
  const list = useQuery({ queryKey: ['reports'], queryFn: () => api('/reports'), staleTime: Infinity })
  const [key, setKey] = useState(null)
  const [period, setPeriod] = useState('30d')
  const active = key || list.data?.[0]?.key
  const meta = list.data?.find((r) => r.key === active)
  const params = { period, outlet_id: outletId }
  const preview = useQuery({ queryKey: ['report', active, params], queryFn: () => api(`/reports/${active}`, { params: { ...params, limit: 100 } }), enabled: !!active })
  const [busy, setBusy] = useState(null)
  const exportAs = async (format) => {
    setBusy(format)
    try { await download(`/reports/${active}/export`, { ...params, format }) } catch (e) { toast(e.message, 'error') } finally { setBusy(null) }
  }
  return (
    <>
      <PageHead title="Reports & export" subtitle="Ready-made reports for your outlets. Preview here, then download as CSV or a formatted Excel workbook (with an 'About this report' sheet)." />
      <Query q={list}>{(reports) => (
        <div className="grid grid-side">
          <Card flush>
            <nav className="stack" style={{ gap: 2, padding: 6 }} aria-label="Reports">
              {reports.map((r) => (
                <button key={r.key} className={`nav-link ${r.key === active ? 'active' : ''}`} style={{ textAlign: 'left', height: 'auto', padding: '8px 10px', display: 'block', whiteSpace: 'normal' }}
                  onClick={() => setKey(r.key)}>
                  <b>{r.title}</b><div className="small muted">{r.description}</div>
                </button>
              ))}
            </nav>
          </Card>
          <Card title={meta?.title} subtitle={meta?.description}
            actions={<>
              {meta?.uses_period && <Seg options={PERIODS} value={period} onChange={setPeriod} label="Period" />}
              <button className="btn" disabled={!!busy} onClick={() => exportAs('csv')}><FileText />{busy === 'csv' ? 'Preparing…' : 'CSV'}</button>
              <button className="btn primary" disabled={!!busy} onClick={() => exportAs('xlsx')}><FileSpreadsheet />{busy === 'xlsx' ? 'Preparing…' : 'Excel'}</button>
            </>}>
            {preview.isLoading ? <Spinner /> : preview.isError ? <div className="down">{preview.error.message}</div> : <Preview p={preview.data} />}
          </Card>
        </div>
      )}</Query>
    </>
  )
}

function Preview({ p }) {
  if (!p.rows.length) return <Empty title="No rows for this selection" icon={Download} />
  const numeric = p.rows[0].map((_, i) => p.rows.every((r) => r[i] === null || typeof r[i] === 'number'))
  return (
    <div className="stack">
      <div className="small muted">
        {p.about.Period} · {p.about.Outlets} · showing {p.rows.length} of {p.total_rows.toLocaleString('en-IN')} rows
        {p.about.Dataset && <> · {p.about.Dataset}</>}
      </div>
      <div className="table-wrap" style={{ maxHeight: 520, overflow: 'auto' }}>
        <table className="table">
          <thead><tr>{p.columns.map((c, i) => <th key={c} className={numeric[i] ? 'num' : ''}>{c}</th>)}</tr></thead>
          <tbody>{p.rows.map((r, j) => (
            <tr key={j}>{r.map((v, i) => <td key={i} className={numeric[i] ? 'num' : ''}>{numeric[i] ? formatValue(v, 'number') : v ?? '-'}</td>)}</tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  )
}
