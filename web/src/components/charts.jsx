import { useEffect, useId, useState } from 'react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { formatValue, money, num, shortDate, monthLabel } from '../lib/format'

const VARS = ['page', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 'grid', 'axis', 'muted', 'text', 'text-2', 'surface', 'accent',
  'seq-1', 'seq-2', 'seq-3', 'seq-4', 'seq-5', 'seq-6', 'seq-7', 'good', 'bad']

function readColors() {
  const cs = getComputedStyle(document.documentElement)
  return Object.fromEntries(VARS.map((v) => [v, cs.getPropertyValue(`--${v}`).trim()]))
}

/** Resolved theme colours (SVG attributes cannot use CSS variables), refreshed on theme change. */
export function useChartColors() {
  const [colors, setColors] = useState(readColors)
  useEffect(() => {
    const update = () => setColors(readColors())
    const mo = new MutationObserver(update)
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', update)
    return () => { mo.disconnect(); mq.removeEventListener('change', update) }
  }, [])
  return { ...colors, series: [colors.s1, colors.s2, colors.s3, colors.s4, colors.s5, colors.s6, colors.s7, colors.s8] }
}

/** Resolve "var(--name)" to the computed colour (SVG presentation attributes can't use CSS variables). */
const resolve = (color, c) => {
  const m = typeof color === 'string' && color.match(/^var\(--([\w-]+)\)$/)
  return m ? c[m[1]] || color : color
}

export function fmtAxis(format) {
  if (format === 'currency') return (v) => money(v, { compact: true })
  if (format === 'percent' || format === 'percent_plain') return (v) => `${v}%`
  return (v) => (Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(v >= 10000 ? 0 : 1)}k` : num(v))
}

export function dateTick(gran) {
  return (d) => {
    if (typeof d !== 'string' || d.length !== 10) return d
    return gran === 'month' ? monthLabel(d) : shortDate(d)
  }
}

function TipBox({ active, payload, label, format, labelFormat, series }) {
  if (!active || !payload?.length) return null
  const title = labelFormat ? labelFormat(label) : label
  return (
    <div className="chart-tip">
      <div className="t">{title}</div>
      {payload.filter((p) => p.value !== null && p.value !== undefined && !p.dataKey?.startsWith?.('_')).map((p) => {
        const s = series?.find((x) => x.key === p.dataKey)
        return (
          <div className="r" key={p.dataKey}>
            <span className="k"><i className="swatch" style={{ background: p.color || p.stroke || p.fill }} />{s?.label || p.name}</span>
            <b className="tabular">{formatValue(p.value, s?.format || format)}</b>
          </div>
        )
      })}
    </div>
  )
}

export function Legend({ items }) {
  return <div className="legend">{items.map((i) => <span key={i.label}><i className="swatch" style={{ background: i.color, ...(i.dashed ? { background: 'transparent', border: `2px dashed ${i.color}` } : {}) }} />{i.label}</span>)}</div>
}

/** Time series as lines or areas. series: [{key, label, color?, dashed?, format?}] */
export function TrendChart({ data, x = 'date', series, format = 'currency', height = 260, area = true, gran = 'day', compare }) {
  const c = useChartColors()
  const gid = useId().replace(/:/g, '')
  const Chart = area ? AreaChart : LineChart
  const colorOf = (s, i) => resolve(s.color, c) || c.series[i % 8]
  return (
    <div>
      {series.length > 1 && <Legend items={series.map((s, i) => ({ label: s.label, color: colorOf(s, i), dashed: s.dashed }))} />}
      <div style={{ height, marginTop: series.length > 1 ? 8 : 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <Chart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <defs>
              {series.map((s, i) => (
                <linearGradient key={s.key} id={`${gid}-${i}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colorOf(s, i)} stopOpacity={i === 0 ? 0.28 : 0.08} />
                  <stop offset="100%" stopColor={colorOf(s, i)} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid vertical={false} stroke={c.grid} />
            <XAxis dataKey={x} tickFormatter={dateTick(gran)} stroke={c.axis} tickLine={false} minTickGap={24} />
            <YAxis tickFormatter={fmtAxis(format)} stroke={c.axis} tickLine={false} axisLine={false} width={64} />
            <Tooltip content={<TipBox format={format} series={series} labelFormat={(l) => (typeof l === 'string' && l.length === 10 ? (gran === 'month' ? monthLabel(l) : shortDate(l)) : l)} />}
              cursor={{ stroke: c.axis, strokeWidth: 1 }} />
            {series.map((s, i) => area && !s.dashed ? (
              <Area key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={colorOf(s, i)} strokeWidth={2}
                fill={`url(#${gid}-${i})`} fillOpacity={1} dot={false} activeDot={{ r: 5, stroke: c.surface, strokeWidth: 2 }} isAnimationActive={false} />
            ) : (
              <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={colorOf(s, i)} strokeWidth={2}
                strokeDasharray={s.dashed ? '5 4' : undefined} dot={false} activeDot={{ r: 4, stroke: c.surface, strokeWidth: 2 }} isAnimationActive={false} />
            ))}
            {compare}
          </Chart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

/** Vertical or horizontal bars for categories. */
export function BarsChart({ data, x, series, format = 'currency', height = 260, horizontal = false, colorBy }) {
  const c = useChartColors()
  const colorOf = (s, i) => resolve(s.color, c) || c.series[i % 8]
  const labelWidth = horizontal ? Math.min(170, Math.max(80, ...data.map((d) => String(d[x]).length * 6.4))) : 0
  return (
    <div>
      {series.length > 1 && <Legend items={series.map((s, i) => ({ label: s.label, color: colorOf(s, i) }))} />}
      <div style={{ height: horizontal ? Math.max(height, data.length * 30 + 30) : height, marginTop: series.length > 1 ? 8 : 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout={horizontal ? 'vertical' : 'horizontal'} margin={{ top: 8, right: 12, bottom: 0, left: 0 }} barGap={2}>
            <CartesianGrid vertical={horizontal} horizontal={!horizontal} stroke={c.grid} />
            {horizontal ? (
              <>
                <XAxis type="number" tickFormatter={fmtAxis(format)} stroke={c.axis} tickLine={false} />
                <YAxis type="category" dataKey={x} width={labelWidth} stroke={c.axis} tickLine={false} interval={0} />
              </>
            ) : (
              <>
                <XAxis dataKey={x} stroke={c.axis} tickLine={false} interval="preserveStartEnd" minTickGap={8} />
                <YAxis tickFormatter={fmtAxis(format)} stroke={c.axis} tickLine={false} axisLine={false} width={64} />
              </>
            )}
            <Tooltip content={<TipBox format={format} series={series} />} cursor={{ fill: c.grid, opacity: 0.5 }} />
            {series.map((s, i) => (
              <Bar key={s.key} dataKey={s.key} name={s.label} fill={colorOf(s, i)} radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}
                maxBarSize={horizontal ? 18 : 42} isAnimationActive={false}>
                {colorBy && data.map((d, j) => <Cell key={j} fill={colorBy(d, c)} />)}
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

/** Share of total as a ranked horizontal meter list (clearer than a pie). */
export function ShareList({ rows, labelKey, valueKey, format = 'currency', extra }) {
  const c = useChartColors()
  const max = Math.max(...rows.map((r) => r[valueKey] || 0), 1)
  const total = rows.reduce((a, r) => a + (r[valueKey] || 0), 0) || 1
  return (
    <div className="stack" style={{ gap: 10 }}>
      {rows.map((r, i) => (
        <div key={r[labelKey]} className="stack" style={{ gap: 4 }}>
          <div className="row between small">
            <span><i className="swatch" style={{ background: c.series[i % 8], marginRight: 6 }} />{r[labelKey]}</span>
            <span className="tabular"><b>{formatValue(r[valueKey], format)}</b> <span className="muted">· {((r[valueKey] / total) * 100).toFixed(0)}%</span>{extra && <> · {extra(r)}</>}</span>
          </div>
          <div className="bar-meter"><i style={{ width: `${(r[valueKey] / max) * 100}%`, background: c.series[i % 8] }} /></div>
        </div>
      ))}
    </div>
  )
}

/** History + forecast with an 80% band; optional back-test overlay. */
export function ForecastChart({ history, forecast, backtest, format = 'currency', height = 320 }) {
  const c = useChartColors()
  const bt = Object.fromEntries((backtest || []).map((b) => [b.date, b.predicted]))
  const data = [
    ...history.map((h) => ({ date: h.date, actual: h.actual, backtest: bt[h.date] ?? null })),
    ...forecast.map((f) => ({ date: f.date, forecast: f.yhat, band: [f.lower, f.upper] })),
  ]
  if (history.length && forecast.length) {
    const last = data[history.length - 1]
    last.forecast = last.actual // connect the lines
  }
  const today = forecast[0]?.date
  return (
    <div>
      <Legend items={[{ label: 'Actual', color: c.s1 }, { label: 'Forecast', color: c.s2 }, { label: '80% range', color: c.s2 + '33' },
        ...(backtest?.length ? [{ label: 'Back-test prediction', color: c.s7, dashed: true }] : [])]} />
      <div style={{ height, marginTop: 8 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke={c.grid} />
            <XAxis dataKey="date" tickFormatter={dateTick('day')} stroke={c.axis} tickLine={false} minTickGap={28} />
            <YAxis tickFormatter={fmtAxis(format)} stroke={c.axis} tickLine={false} axisLine={false} width={64} />
            <Tooltip cursor={{ stroke: c.axis }} content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const row = payload[0].payload
              return (
                <div className="chart-tip">
                  <div className="t">{shortDate(label)}</div>
                  {row.actual != null && <div className="r"><span className="k"><i className="swatch" style={{ background: c.s1 }} />Actual</span><b>{formatValue(row.actual, format)}</b></div>}
                  {row.backtest != null && <div className="r"><span className="k"><i className="swatch" style={{ background: c.s7 }} />Back-test</span><b>{formatValue(row.backtest, format)}</b></div>}
                  {row.band && <div className="r"><span className="k"><i className="swatch" style={{ background: c.s2 }} />Forecast</span><b>{formatValue(row.forecast, format)}</b></div>}
                  {row.band && <div className="r"><span className="k">80% range</span><span className="tabular">{formatValue(row.band[0], format)} – {formatValue(row.band[1], format)}</span></div>}
                </div>
              )
            }} />
            <Area dataKey="band" stroke="none" fill={c.s2} fillOpacity={0.16} isAnimationActive={false} />
            <Line dataKey="actual" stroke={c.s1} strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line dataKey="forecast" stroke={c.s2} strokeWidth={2} dot={false} isAnimationActive={false} />
            {backtest?.length > 0 && <Line dataKey="backtest" stroke={c.s7} strokeWidth={2} strokeDasharray="5 4" dot={false} isAnimationActive={false} />}
            {today && <ReferenceLine x={today} stroke={c.axis} strokeDasharray="3 3" label={{ value: 'Forecast →', position: 'insideTopLeft', fill: c.muted, fontSize: 11 }} />}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

/** Weekday x hour heatmap on a single-hue sequential ramp. */
export function Heatmap({ cells, format = 'currency', valueKey = 'revenue' }) {
  const c = useChartColors()
  const [hover, setHover] = useState(null)
  if (!cells?.length) return null
  const hours = [...new Set(cells.map((x) => x.hour))].sort((a, b) => a - b)
  const map = new Map(cells.map((x) => [`${x.weekday}-${x.hour}`, x]))
  const max = Math.max(...cells.map((x) => x[valueKey]))
  const ramp = [c['seq-1'], c['seq-2'], c['seq-3'], c['seq-4'], c['seq-5'], c['seq-6'], c['seq-7']]
  const colorFor = (v) => ramp[Math.min(ramp.length - 1, Math.floor((v / max) * ramp.length))]
  return (
    <div>
      <div className="heatmap" style={{ gridTemplateColumns: `36px repeat(${hours.length}, minmax(18px, 1fr))` }}>
        <span />
        {hours.map((h) => <span key={h} className="lbl" style={{ justifyContent: 'center' }}>{h % 3 === 0 ? `${h}:00` : ''}</span>)}
        {DAYS.map((d, wi) => (
          <div key={d} style={{ display: 'contents' }}>
            <span className="lbl">{d}</span>
            {hours.map((h) => {
              const cell = map.get(`${wi}-${h}`)
              const v = cell?.[valueKey] || 0
              return <div key={h} className="cell" style={{ background: v ? colorFor(v) : c.grid }}
                onMouseEnter={() => setHover({ d, h, v, o: cell?.orders })} onMouseLeave={() => setHover(null)}
                title={`${d} ${h}:00 - ${formatValue(v, format)} avg per week`} />
            })}
          </div>
        ))}
      </div>
      <div className="row between small muted" style={{ marginTop: 8 }}>
        <span>{hover ? <>{hover.d} {hover.h}:00–{hover.h + 1}:00 · <b style={{ color: 'var(--text)' }}>{formatValue(hover.v, format)}</b> avg per week · {hover.o} bills</> : 'Hover a cell for details'}</span>
        <span className="row" style={{ gap: 4 }}>Low{ramp.map((r) => <i key={r} className="swatch" style={{ background: r }} />)}High</span>
      </div>
    </div>
  )
}

export function Sparkline({ data, k = 'revenue', color, height = 46 }) {
  const c = useChartColors()
  const gid = useId().replace(/:/g, '')
  const stroke = resolve(color, c) || c.s1
  return (
    <div style={{ height }} aria-hidden="true">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity={0.25} />
              <stop offset="100%" stopColor={stroke} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey={k} stroke={stroke} fill={`url(#${gid})`} strokeWidth={2} dot={false} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
