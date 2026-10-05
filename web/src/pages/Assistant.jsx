import { Fragment, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Activity, ArrowLeft, ArrowUp, Bot, Boxes, Copy, Download, LifeBuoy, Mic, MicOff, RefreshCw, Sheet as Sheet2, Sparkles, SquarePen, Square, Store,
  TrendingUp, Users, X,
} from 'lucide-react'
import { api } from '../lib/api'
import { useToast } from '../lib/app'
import { formatValue } from '../lib/format'
import { Badge, DataTable, PageHead } from '../components/ui'
import { BarsChart, ForecastChart, Heatmap, ShareList, TrendChart } from '../components/charts'

/** Minimal, safe markdown: paragraphs, bullet & numbered lists, **bold**. */
function Markdown({ text }) {
  const inline = (s, key) => s.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? <b key={`${key}-${i}`}>{part.slice(2, -2)}</b> : <Fragment key={`${key}-${i}`}>{part}</Fragment>)
  const blocks = []
  let list = null
  text.split('\n').forEach((raw, i) => {
    const line = raw.trimEnd()
    const bullet = line.match(/^\s*[-•]\s+(.*)/)
    const numbered = line.match(/^\s*\d+\.\s+(.*)/)
    if (bullet || numbered) {
      const type = bullet ? 'ul' : 'ol'
      if (!list || list.type !== type) { list = { type, items: [] }; blocks.push(list) }
      list.items.push(inline((bullet || numbered)[1], i))
    } else if (line.trim() === '') {
      list = null
    } else {
      list = null
      blocks.push({ type: 'p', content: inline(line, i) })
    }
  })
  return (
    <div className="md">
      {blocks.map((b, i) => b.type === 'p' ? <p key={i}>{b.content}</p>
        : b.type === 'ul' ? <ul key={i}>{b.items.map((it, j) => <li key={j}>{it}</li>)}</ul>
          : <ol key={i}>{b.items.map((it, j) => <li key={j}>{it}</li>)}</ol>)}
    </div>
  )
}

function ChartBlock({ b }) {
  const isDate = b.data?.[0] && typeof b.data[0][b.x] === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(b.data[0][b.x])
  if (b.chart === 'pie') return <ShareList rows={b.data} labelKey={b.x} valueKey={b.series[0].key} format={b.format} />
  if (isDate && b.chart !== 'bar') {
    const days = b.data.length > 1 ? (new Date(b.data[1][b.x]) - new Date(b.data[0][b.x])) / 86400000 : 1
    return <TrendChart data={b.data} x={b.x} series={b.series} format={b.format} area={b.chart === 'area'} height={220} gran={days > 20 ? 'month' : 'day'} />
  }
  const horizontal = !isDate && b.data.length > 3 && String(b.data[0][b.x]).length > 6
  return <BarsChart data={b.data} x={b.x} series={b.series} format={b.format} horizontal={horizontal} height={220} />
}

function TableBlock({ b }) {
  const cols = b.columns.map((c) => c.format === 'auto'
    ? { ...c, align: 'right', render: (r) => formatValue(r[c.key], r._format === 'percent_plain' ? 'percent_plain' : r._format || 'number') }
    : c)
  return <DataTable columns={cols} rows={b.rows} maxHeight={360} />
}

function Blocks({ blocks }) {
  return blocks.map((b, i) => (
    <div className="block" key={i}>
      {b.title && b.type !== 'kpis' && <h4>{b.title}</h4>}
      {b.type === 'kpis' && (
        <div className="mini-kpis">
          {b.items.map((k) => (
            <div className="mini-kpi" key={k.label}>
              <div className="small muted">{k.label}</div>
              <div className="v">{formatValue(k.value, k.format)}</div>
              {k.change !== null && k.change !== undefined && <div className={`small ${k.change >= 0 ? 'up' : 'down'}`}>{k.change > 0 ? '+' : ''}{k.change}%</div>}
            </div>
          ))}
        </div>
      )}
      {b.type === 'chart' && <ChartBlock b={b} />}
      {b.type === 'table' && <TableBlock b={b} />}
      {b.type === 'forecast' && <ForecastChart history={b.history} forecast={b.forecast} format={b.format} height={240} />}
      {b.type === 'heatmap' && <Heatmap cells={b.cells} />}
    </div>
  ))
}

const PROMPT_ICONS = [[TrendingUp, 'sky'], [Store, ''], [Boxes, 'amber'], [Activity, 'rose'], [Users, 'emerald'], [Sparkles, 'violet']]

function useSpeech(onText) {
  const [listening, setListening] = useState(false)
  const recRef = useRef(null)
  const SR = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)
  const toggle = () => {
    if (!SR) return
    if (listening) { recRef.current?.stop(); return }
    const rec = new SR()
    rec.lang = 'en-IN'
    rec.interimResults = false
    rec.onresult = (e) => onText(e.results[0][0].transcript)
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
    recRef.current = rec
    rec.start()
    setListening(true)
  }
  return { supported: !!SR, listening, toggle }
}

/** Where an answer came from: data source, filters, timing, model version and caveats. */
function Provenance({ p }) {
  if (!p) return null
  const f = p.filters || {}
  return (
    <details className="provenance">
      <summary>
        Source &amp; method · {p.query_ms} ms{p.model_version ? ` · model v${p.model_version}` : ''}
        {p.notes?.length > 0 && <> · <span className="warn-ink">{p.notes.length} note{p.notes.length > 1 ? 's' : ''}</span></>}
      </summary>
      <dl>
        {p.data_source && <><dt>Data</dt><dd>{p.data_source}</dd></>}
        {f.outlets && <><dt>Outlets</dt><dd>{f.outlets}</dd></>}
        {f.periods?.length > 0 && <><dt>Periods</dt><dd>{f.periods.join('; ')}</dd></>}
        {f.category && <><dt>Category</dt><dd>{f.category}</dd></>}
        {f.products?.length > 0 && <><dt>Products</dt><dd>{f.products.join(', ')}</dd></>}
        {f.horizon_days && <><dt>Horizon</dt><dd>{f.horizon_days} days</dd></>}
        {p.sources?.length > 0 && <><dt>Sources</dt><dd>{p.sources.join('; ')}</dd></>}
        <dt>Method</dt><dd>{p.method} · engine: {p.engine}{p.forecast_run_id ? ` · forecast run #${p.forecast_run_id}` : ''}</dd>
        {p.notes?.length > 0 && <><dt>Notes</dt><dd>{p.notes.map((n) => <div key={n}>{n}</div>)}</dd></>}
      </dl>
    </details>
  )
}

const cellText = (c, r) => (c.format === 'auto' ? formatValue(r[c.key], r._format || 'number') : formatValue(r[c.key], c.format))
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

/** A table answer laid out as a spreadsheet, with copy (paste into Excel / Sheets) and CSV download. */
function Sheet({ sheet, onClose }) {
  const toast = useToast()
  const { title, columns, rows } = sheet
  const matrix = [columns.map((c) => c.label), ...rows.map((r) => columns.map((c) => {
    const v = r[c.key]
    return typeof v === 'number' ? v : (v ?? '')
  }))]
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(matrix.map((row) => row.join('\t')).join('\n'))
      toast('Copied - paste it into Excel or Google Sheets', 'success')
    } catch { toast('Copy is not allowed in this browser', 'error') }
  }
  const download = () => {
    const esc = (v) => (/[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v))
    const blob = new Blob([matrix.map((row) => row.map(esc).join(',')).join('\n') + '\n'], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${(title || 'eris-table').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.csv`
    a.click()
    URL.revokeObjectURL(a.href)
  }
  const blank = Math.max(0, 14 - rows.length - 1)
  return (
    <aside className="sheet" aria-label={`Spreadsheet: ${title}`}>
      <div className="sheet-head">
        <button className="btn ghost sm icon" onClick={onClose} aria-label="Close spreadsheet"><X /></button>
        <h2>{title || 'Table'}</h2>
        <button className="btn sm" onClick={copy}><Copy />Copy</button>
        <button className="btn sm" onClick={download}><Download />CSV</button>
      </div>
      <div className="sheet-grid">
        <table>
          <thead><tr><th className="rn" />{columns.map((c, i) => <th key={c.key}>{LETTERS[i] || i + 1}</th>)}</tr></thead>
          <tbody>
            <tr className="hdr"><td className="rn">1</td>{columns.map((c) => <td key={c.key}>{c.label}</td>)}</tr>
            {rows.map((r, i) => (
              <tr key={i}><td className="rn">{i + 2}</td>
                {columns.map((c) => <td key={c.key} className={typeof r[c.key] === 'number' ? 'n' : ''}>{cellText(c, r)}</td>)}</tr>
            ))}
            {Array.from({ length: blank }, (_, i) => <tr key={`b${i}`}><td className="rn">{rows.length + 2 + i}</td>{columns.map((c) => <td key={c.key} />)}</tr>)}
          </tbody>
        </table>
      </div>
    </aside>
  )
}

const dayGroup = (iso) => {
  if (!iso) return 'Today'
  const d = new Date(iso)
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const days = Math.floor((today - new Date(d.getFullYear(), d.getMonth(), d.getDate())) / 86400000)
  return days <= 0 ? 'Today' : days === 1 ? 'Yesterday' : days < 7 ? 'Last 7 days' : 'Earlier'
}

const wantsSheet = (q) => /\b(spread ?sheet|sheet|excel|csv|table)\b/i.test(q || '')
const firstTable = (m) => (m.blocks || []).find((b) => b.type === 'table')

export default function Assistant() {
  const qc = useQueryClient()
  const toast = useToast()
  const [input, setInput] = useState('')
  const [pending, setPending] = useState(null)
  const [sheet, setSheet] = useState(null)
  const [focus, setFocus] = useState(null)
  const logRef = useRef(null)
  const history = useQuery({ queryKey: ['chat-history'], queryFn: () => api('/assistant/history', { params: { limit: 80 } }), staleTime: Infinity })
  const status = useQuery({ queryKey: ['assistant-status'], queryFn: () => api('/assistant/status'), staleTime: 60_000 })

  const send = useMutation({
    mutationFn: (message) => api('/assistant/chat', { method: 'POST', body: { message } }),
    onMutate: (message) => setPending(message),
    onSuccess: (res, message) => {
      const now = new Date().toISOString()
      const reply = { id: `a${Date.now()}`, role: 'assistant', content: res.answer, created_at: now, ...res }
      qc.setQueryData(['chat-history'], (old = []) => [...old, { id: `u${Date.now()}`, role: 'user', content: message, created_at: now }, reply])
      const table = firstTable(reply)
      if (table && wantsSheet(message)) setSheet({ title: table.title || message, columns: table.columns, rows: table.rows })
    },
    onError: (e) => toast(e.message, 'error'),
    onSettled: () => setPending(null),
  })
  const clear = useMutation({
    mutationFn: () => api('/assistant/history', { method: 'DELETE' }),
    onSuccess: () => { qc.setQueryData(['chat-history'], []); setSheet(null) },
  })
  const speech = useSpeech((t) => setInput(t))
  const [params, setParams] = useSearchParams()
  const linked = params.get('q')

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [history.data, pending])

  const ask = (text) => {
    const t = (text ?? input).trim()
    if (!t || send.isPending) return
    setInput('')
    send.mutate(t)
  }
  // a question linked from another page (e.g. the dashboard or Help) is asked once the history has loaded
  useEffect(() => {
    if (linked && history.isSuccess && !send.isPending) {
      setParams({}, { replace: true })
      send.mutate(linked)
    }
  }, [linked, history.isSuccess]) // eslint-disable-line react-hooks/exhaustive-deps
  const msgs = history.data || []
  const llm = status.data?.llm
  const lastSuggestions = [...msgs].reverse().find((m) => m.role === 'assistant')?.suggestions
  const questions = msgs.map((m, i) => ({ ...m, i })).filter((m) => m.role === 'user').reverse()
  const groups = ['Today', 'Yesterday', 'Last 7 days', 'Earlier'].map((g) => [g, questions.filter((m) => dayGroup(m.created_at) === g)]).filter(([, l]) => l.length)
  const jump = (id) => {
    setFocus(id)
    document.getElementById(`m-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  const copy = async (text) => {
    try { await navigator.clipboard.writeText(text.replace(/\*\*/g, '')); toast('Answer copied', 'success') } catch { toast('Copy is not allowed in this browser', 'error') }
  }

  return (
    <>
      <PageHead title="AI Assistant" subtitle="Answers about sales, stock, customers and forecasts from tested analyses of your data, each with its source.">
        <Badge tone={llm?.available ? 'good' : 'info'}><Sparkles />{llm?.available ? `Local LLM: ${llm.model}` : 'Built-in analytics engine'}</Badge>
        <button className="btn sm only-narrow" onClick={() => clear.mutate()} disabled={!msgs.length}><SquarePen />New chat</button>
      </PageHead>
      <div className={`ai-shell ${sheet ? 'with-sheet' : ''}`}>
        <nav className="ai-list" aria-label="Conversations">
          <Link to="/" className="action" style={{ textDecoration: 'none' }}><ArrowLeft />Back to dashboard</Link>
          <button className="action" onClick={() => clear.mutate()} disabled={!msgs.length} title="Start over (clears this conversation)"><SquarePen />New chat</button>
          <Link to="/help" className="action" style={{ textDecoration: 'none' }}><LifeBuoy />Help topics</Link>
          {groups.map(([g, list]) => (
            <div key={g}>
              <div className="group">{g}</div>
              {list.map((m) => <button key={m.id} className={`conv ${focus === m.id ? 'on' : ''}`} onClick={() => jump(m.id)} title={m.content}>{m.content}</button>)}
            </div>
          ))}
          {!groups.length && <div className="group">Your questions appear here</div>}
          <div className="engine" style={{ marginTop: 'auto' }}>
            <b>{llm?.available ? 'Local language model' : 'Built-in engine'}</b>
            {llm?.available ? `${llm.model} words the answers; numbers come from ERIS analyses.` : 'Answers come straight from ERIS analyses - no data leaves this server.'}
          </div>
        </nav>

        <section className="chat">
          <div className="chat-log" ref={logRef} aria-live="polite">
            {msgs.length === 0 && !pending && (
              <div className="empty" style={{ margin: 'auto', gap: 14 }}>
                <span className="avatar" style={{ width: 52, height: 52, borderRadius: 16 }}><Bot style={{ width: 26, height: 26 }} /></span>
                <div>
                  <h2 style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em' }}>How can I help with the business today?</h2>
                  <div className="small" style={{ maxWidth: 560, marginTop: 6 }}>Mention an outlet, product, category or period - for example “last month at Indiranagar”. Ask for a spreadsheet and table answers open as one.</div>
                </div>
                <div className="prompt-grid">
                  {(status.data?.suggestions || []).map((x, i) => {
                    const [Icon, tone] = PROMPT_ICONS[i % PROMPT_ICONS.length]
                    return (
                      <button key={x} className="prompt-card" onClick={() => ask(x)}>
                        <span className={`kpi-icon ${tone}`}><Icon size={15} /></span>
                        <b>{x}</b>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
            {msgs.map((m, i) => m.role === 'user' ? (
              <div className="msg user" key={m.id} id={`m-${m.id}`}><div className="bubble">{m.content}</div></div>
            ) : (
              <div className="msg bot" key={m.id}>
                <div className="bubble">
                  <Markdown text={m.content} />
                  {m.blocks?.length > 0 && <Blocks blocks={m.blocks} />}
                  <Provenance p={m.provenance} />
                </div>
                <div className="msg-actions">
                  <button className="btn ghost icon" onClick={() => copy(m.content)} aria-label="Copy answer" title="Copy answer"><Copy /></button>
                  {msgs[i - 1]?.role === 'user' && <button className="btn ghost icon" onClick={() => ask(msgs[i - 1].content)} disabled={send.isPending}
                    aria-label="Regenerate answer" title="Run this question again on the latest data"><RefreshCw /></button>}
                  {firstTable(m) && <button className="btn ghost text" onClick={() => {
                    const t = firstTable(m)
                    setSheet({ title: t.title || msgs[i - 1]?.content, columns: t.columns, rows: t.rows })
                  }}><Sheet2 />Open as spreadsheet</button>}
                </div>
              </div>
            ))}
            {pending && (
              <>
                <div className="msg user"><div className="bubble">{pending}</div></div>
                <div className="msg bot"><div className="thinking"><span className="avatar" style={{ width: 26, height: 26, borderRadius: 8 }}><Bot style={{ width: 14, height: 14 }} /></span>
                  <span className="typing" aria-hidden="true"><i /><i /><i /></span>Analysing your data…</div></div>
              </>
            )}
          </div>
          <div>
            {lastSuggestions?.length > 0 && !pending && (
              <div className="chips" style={{ padding: '0 clamp(10px, 3vw, 40px) 10px' }}>
                {lastSuggestions.map((x) => <button key={x} className="chip" onClick={() => ask(x)}>{x}</button>)}
              </div>
            )}
            <form className="composer" onSubmit={(e) => { e.preventDefault(); ask() }}>
              <textarea rows={1} placeholder="How can I help you? e.g. Why was Indiranagar revenue lower this week?" value={input} maxLength={500}
                onChange={(e) => setInput(e.target.value)} aria-label="Ask a question" autoFocus
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask() } }} />
              <div className="bar">
                <span className="tag"><Sparkles />AI Assistant</span>
                {speech.supported && (
                  <button type="button" className={`btn ghost sm icon ${speech.listening ? 'gold' : ''}`} onClick={speech.toggle}
                    aria-label={speech.listening ? 'Stop listening' : 'Speak your question'} style={{ marginLeft: 'auto' }}>
                    {speech.listening ? <MicOff /> : <Mic />}
                  </button>
                )}
                <button className="btn send" disabled={!input.trim() || send.isPending} aria-label="Ask" style={speech.supported ? { marginLeft: 0 } : undefined}>
                  {send.isPending ? <Square size={13} fill="currentColor" /> : <ArrowUp />}
                </button>
              </div>
            </form>
          </div>
        </section>

        {sheet && <Sheet sheet={sheet} onClose={() => setSheet(null)} />}
      </div>
    </>
  )
}
