import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, ArrowUp, BookOpen, Bot, Boxes, FileText, LineChart, Receipt, ShieldCheck, Sparkles, Upload } from 'lucide-react'
import { api } from '../lib/api'
import { useApp } from '../lib/app'
import { date, num } from '../lib/format'
import { Card, PageHead } from '../components/ui'

// Each topic is answered by the assistant from the project documentation (docs/knowledge), with its source shown.
const TOPICS = [
  { icon: Upload, title: 'Importing your data', q: 'How do I import sales from a CSV file?' },
  { icon: LineChart, title: 'How forecasts are made', q: 'How is the forecasting model chosen?' },
  { icon: Receipt, title: 'Recording a sale', q: 'How do I record a sale?' },
  { icon: Boxes, title: 'Reorder suggestions', q: 'How are reorder suggestions calculated?' },
  { icon: FileText, title: 'GST invoices', q: 'How is GST calculated on the demo invoices?' },
  { icon: BookOpen, title: 'What the numbers mean', q: 'What does WAPE mean?' },
]

const ROLES = [
  ['Admin', 'Everything: all outlets, users, settings, imports and the audit log.'],
  ['Manager', 'Their outlets: billing, stock, purchase orders, imports and reports.'],
  ['Staff', 'Billing and stock at their outlet.'],
  ['Viewer', 'Read-only dashboards, analytics, forecasts and the assistant.'],
]

const LINKS = [
  ['/', 'Dashboard'], ['/sales', 'Sales & billing'], ['/inventory', 'Inventory'], ['/forecasts', 'Forecasts'],
  ['/insights', 'Anomalies & drivers'], ['/reports', 'Reports & export'], ['/import', 'Data import'], ['/settings', 'Settings'],
]

export default function Help() {
  const navigate = useNavigate()
  const { user } = useApp()
  const [text, setText] = useState('')
  const sys = useQuery({ queryKey: ['system'], queryFn: () => api('/settings/system'), staleTime: 300_000 })
  const ask = (q) => navigate(`/assistant?q=${encodeURIComponent(q)}`)
  const s = sys.data

  return (
    <>
      <PageHead title="Help & Support" subtitle="Answers come from the ERIS documentation, through the assistant, with their source shown." />
      <Card className="hero">
        <div className="stack" style={{ gap: 14, maxWidth: 760 }}>
          <div className="row" style={{ gap: 12 }}>
            <span className="avatar"><Bot /></span>
            <div><h2 style={{ fontSize: 18, color: 'var(--text)' }}>How can we help, {user.full_name.split(' ')[0]}?</h2>
              <p className="small muted">Ask about a feature, a number on a page, or how to do something.</p></div>
          </div>
          <form className="composer" style={{ margin: 0, boxShadow: 'var(--shadow-xs)' }} onSubmit={(e) => { e.preventDefault(); if (text.trim()) ask(text.trim()) }}>
            <textarea rows={1} value={text} onChange={(e) => setText(e.target.value)} placeholder="e.g. How do I transfer stock between outlets?" aria-label="Ask for help"
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (text.trim()) ask(text.trim()) } }} />
            <div className="bar"><span className="tag"><Sparkles />AI Assistant</span>
              <button className="btn send" disabled={!text.trim()} aria-label="Ask"><ArrowUp /></button></div>
          </form>
        </div>
      </Card>

      <div className="grid grid-3">
        {TOPICS.map((t) => (
          <button key={t.title} className="prompt-card" onClick={() => ask(t.q)}>
            <span className="row" style={{ justifyContent: 'space-between' }}><span className="kpi-icon amber"><t.icon size={16} /></span><ArrowRight size={15} className="muted" /></span>
            <b>{t.title}</b><span className="small muted">{t.q}</span>
          </button>
        ))}
      </div>

      <div className="grid grid-3">
        <Card title="Your workspace" subtitle="What this installation is running on">
          {s ? (
            <dl className="dl">
              <dt>Data</dt><dd>{s.data_from ? `${date(s.data_from)} – ${date(s.data_to)}` : 'No sales yet'}</dd>
              <dt>Sales</dt><dd className="mono">{num(s.counts.sales)} bills · {num(s.counts.sale_items)} lines</dd>
              <dt>Catalogue</dt><dd>{num(s.counts.outlets)} outlets · {num(s.counts.products)} products · {num(s.counts.customers)} customers</dd>
              <dt>Database</dt><dd>{s.database}</dd>
              <dt>Forecasting</dt><dd>{s.forecast_models.length} models available</dd>
              <dt>Assistant</dt><dd>{s.assistant?.available ? `Local LLM (${s.assistant.model})` : 'Built-in analytics engine'}</dd>
              {s.dataset && <><dt>Dataset</dt><dd>{s.dataset.data_source === 'synthetic' ? 'Synthetic demo (seeded, reproducible)' : s.dataset.data_source}</dd></>}
            </dl>
          ) : <div className="skeleton" style={{ height: 170 }} />}
        </Card>
        <Card title="Who can do what" subtitle={`You are signed in as ${user.role}`}>
          <div className="stack" style={{ gap: 0 }}>
            {ROLES.map(([r, d]) => (
              <div key={r} className="list-row">
                <span className={`badge ${r.toLowerCase() === user.role ? 'info' : ''}`}><ShieldCheck />{r}</span>
                <span className="small text-2">{d}</span>
              </div>
            ))}
          </div>
        </Card>
        <Card title="Go to" subtitle="Pages people look for most">
          <div className="chip-row">
            {LINKS.map(([to, label]) => <Link key={to} to={to} className="chip">{label}<ArrowRight size={13} /></Link>)}
          </div>
          <p className="small muted" style={{ marginTop: 16 }}>Demo data is synthetic, for a fictional chain. GST invoices are demos and not for tax filing.</p>
        </Card>
      </div>
    </>
  )
}
