import { Fragment, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bot, Mic, MicOff, Send, Trash2, User } from 'lucide-react'
import { api } from '../lib/api'
import { useToast } from '../lib/app'
import { formatValue } from '../lib/format'
import { Badge, Card, DataTable, PageHead } from '../components/ui'
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

export default function Assistant() {
  const qc = useQueryClient()
  const toast = useToast()
  const [input, setInput] = useState('')
  const [pending, setPending] = useState(null)
  const logRef = useRef(null)
  const history = useQuery({ queryKey: ['chat-history'], queryFn: () => api('/assistant/history', { params: { limit: 60 } }), staleTime: Infinity })
  const status = useQuery({ queryKey: ['assistant-status'], queryFn: () => api('/assistant/status'), staleTime: 60_000 })

  const send = useMutation({
    mutationFn: (message) => api('/assistant/chat', { method: 'POST', body: { message } }),
    onMutate: (message) => setPending(message),
    onSuccess: (res, message) => {
      qc.setQueryData(['chat-history'], (old = []) => [...old, { id: `u${Date.now()}`, role: 'user', content: message },
        { id: `a${Date.now()}`, role: 'assistant', content: res.answer, ...res }])
    },
    onError: (e) => toast(e.message, 'error'),
    onSettled: () => setPending(null),
  })
  const clear = useMutation({
    mutationFn: () => api('/assistant/history', { method: 'DELETE' }),
    onSuccess: () => qc.setQueryData(['chat-history'], []),
  })
  const speech = useSpeech((t) => setInput(t))

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [history.data, pending])

  const ask = (text) => {
    const t = (text ?? input).trim()
    if (!t || send.isPending) return
    setInput('')
    send.mutate(t)
  }
  const msgs = history.data || []
  const llm = status.data?.llm
  const lastSuggestions = [...msgs].reverse().find((m) => m.role === 'assistant')?.suggestions

  return (
    <>
      <PageHead title="AI Assistant" subtitle="Ask about sales, stock, customers and forecasts in plain English - answers come from your live data.">
        <Badge tone={llm?.available ? 'good' : 'info'}>{llm?.available ? `Local LLM: ${llm.model}` : 'Built-in analytics engine'}</Badge>
        <button className="btn" onClick={() => clear.mutate()} disabled={!msgs.length}><Trash2 />Clear chat</button>
      </PageHead>
      <Card flush className="chat">
        <div className="chat-log" ref={logRef} aria-live="polite">
          {msgs.length === 0 && !pending && (
            <div className="empty" style={{ margin: 'auto' }}>
              <Bot />
              <b>Hi! I'm your retail assistant.</b>
              <div className="small" style={{ maxWidth: 520 }}>Try one of these questions, or type your own. You can mention an outlet, product, category or time period.</div>
              <div className="chips" style={{ justifyContent: 'center', marginTop: 8 }}>
                {(status.data?.suggestions || []).map((s) => <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>)}
              </div>
            </div>
          )}
          {msgs.map((m) => m.role === 'user' ? (
            <div className="msg user" key={m.id}><div className="bubble">{m.content}</div><div className="avatar"><User /></div></div>
          ) : (
            <div className="msg bot" key={m.id}>
              <div className="avatar"><Bot /></div>
              <div className="bubble">
                <Markdown text={m.content} />
                {m.blocks?.length > 0 && <Blocks blocks={m.blocks} />}
              </div>
            </div>
          ))}
          {pending && (
            <>
              <div className="msg user"><div className="bubble">{pending}</div><div className="avatar"><User /></div></div>
              <div className="msg bot"><div className="avatar"><Bot /></div><div className="bubble row"><div className="spinner" style={{ width: 16, height: 16 }} /><span className="muted">Analysing your data…</span></div></div>
            </>
          )}
        </div>
        <div>
          {lastSuggestions?.length > 0 && !pending && (
            <div className="chips" style={{ padding: '10px 12px 0', background: 'var(--surface)' }}>
              {lastSuggestions.map((s) => <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>)}
            </div>
          )}
          <form className="chat-input" onSubmit={(e) => { e.preventDefault(); ask() }}>
            <input className="input" placeholder="e.g. Which outlet grew the most last month?" value={input} maxLength={500}
              onChange={(e) => setInput(e.target.value)} aria-label="Ask a question" autoFocus />
            {speech.supported && (
              <button type="button" className={`btn icon ${speech.listening ? 'primary' : ''}`} onClick={speech.toggle} aria-label={speech.listening ? 'Stop listening' : 'Speak your question'} style={{ height: 42, width: 42 }}>
                {speech.listening ? <MicOff /> : <Mic />}
              </button>
            )}
            <button className="btn primary" disabled={!input.trim() || send.isPending} style={{ height: 42 }}><Send />Ask</button>
          </form>
        </div>
      </Card>
    </>
  )
}
