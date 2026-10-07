import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { dateTime } from '../lib/format'
import { Badge, Card, DataTable, Field, PageHead, Pager, Query, useDebounced } from '../components/ui'

const ENTITIES = ['sale', 'product', 'category', 'outlet', 'supplier', 'customer', 'purchase_order', 'stock_level', 'user',
  'organization', 'promotion', 'invoice', 'import', 'database']
const TONE = { create: 'good', update: 'info', delete: 'bad', void: 'bad' }

function Changes({ details }) {
  if (!details) return <span className="muted">-</span>
  const entries = Object.entries(details)
  return (
    <div className="small">
      {entries.slice(0, 4).map(([k, v]) => (
        <div key={k}>
          <b>{k}</b>: {v && typeof v === 'object' && 'from' in v ? <>{String(v.from ?? '∅')} → {String(v.to ?? '∅')}</> : JSON.stringify(v)}
        </div>
      ))}
      {entries.length > 4 && <span className="muted">+{entries.length - 4} more</span>}
    </div>
  )
}

export default function AuditLog() {
  const { outlets } = useApp()
  const [f, setF] = useState({ entity: '', outlet_id: '', start: '', end: '' })
  const [text, setText] = useState('')
  const [page, setPage] = useState(1)
  const q = useDebounced(text)
  const params = { ...f, q, page, page_size: 50 }
  const list = useQuery({ queryKey: ['audit', params], queryFn: () => api('/audit', { params }), placeholderData: (p) => p })
  const set = (k, v) => { setF((x) => ({ ...x, [k]: v })); setPage(1) }
  return (
    <>
      <PageHead title="Audit log" subtitle="Every change to business records, and who made it." />
      <Card>
        <div className="row" style={{ alignItems: 'flex-end', gap: 12 }}>
          <Field label="Record type">
            <select className="select" value={f.entity} onChange={(e) => set('entity', e.target.value)}>
              <option value="">All</option>{ENTITIES.map((e) => <option key={e} value={e}>{e.replace('_', ' ')}</option>)}
            </select>
          </Field>
          <Field label="Outlet">
            <select className="select" value={f.outlet_id} onChange={(e) => set('outlet_id', e.target.value)}>
              <option value="">All</option>{outlets.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
          </Field>
          <Field label="From"><input className="input" type="date" value={f.start} onChange={(e) => set('start', e.target.value)} /></Field>
          <Field label="To"><input className="input" type="date" value={f.end} onChange={(e) => set('end', e.target.value)} /></Field>
          <Field label="Search"><div className="search"><Search /><input className="input" value={text} placeholder="e.g. invoice number, SKU" onChange={(e) => { setText(e.target.value); setPage(1) }} /></div></Field>
        </div>
      </Card>
      <Card flush>
        <Query q={list}>{(d) => (
          <>
            <DataTable rows={d.items} sortable={false} empty="No activity recorded for these filters" columns={[
              { key: 'at', label: 'When', render: (r) => dateTime(r.at) },
              { key: 'user', label: 'User' },
              { key: 'action', label: 'Action', render: (r) => <Badge tone={TONE[r.action.split('.').pop()] || ''}>{r.action}</Badge> },
              { key: 'summary', label: 'What' },
              { key: 'details', label: 'Changes', render: (r) => <Changes details={r.details} /> },
            ]} />
            {d.pages > 1 && <Pager page={page} pages={d.pages} total={d.total} onPage={setPage} label="entries" />}
          </>
        )}</Query>
      </Card>
    </>
  )
}
