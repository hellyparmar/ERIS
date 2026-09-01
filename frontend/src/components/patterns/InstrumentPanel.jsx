import React, { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';
import CountUp from 'react-countup';

const fmtINR = (val) => {
  if (!val && val !== 0) return '₹0';
  return '₹' + Number(val).toLocaleString('en-IN');
};

const usePrefersReducedMotion = () => {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(media.matches);
    const listener = (e) => setReduced(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, []);
  return reduced;
};

function Sparkline({ data, color }) {
  if (!data || data.length < 2) return null;
  const w = 60, h = 16;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = Math.max(max - min, 1);
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={w} height={h} className="instrument-sparkline" viewBox={`0 0 ${w} ${h}`}>
      <path d={`M ${points}`} fill="none" stroke={color || 'var(--signal-cyan)'} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Section({ label, value, delta, up, danger, format, sparklineData, isPos }) {
  const reducedMotion = usePrefersReducedMotion();
  const duration = reducedMotion ? 0 : (isPos ? 0.12 : 0.48); // --dur-slow (480ms), POS is --dur-fast (120ms)
  const isUp = delta !== null && delta !== undefined ? (up ?? Number(delta) >= 0) : true;
  const numValue = Number(value) || 0;

  return (
    <div className="panel-section">
      <span className="panel-label">
        {label}
        {danger && <span className="status-dot online" style={{ width: 6, height: 6, marginLeft: 6, display: 'inline-block', backgroundColor: 'var(--signal-coral)' }} />}
      </span>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: '8px' }}>
        <div className="panel-value" style={danger ? { color: 'var(--signal-coral)' } : {}}>
          {format ? (
            <CountUp end={numValue} duration={duration} separator="," formattingFn={format} />
          ) : (
            <CountUp end={numValue} duration={duration} separator="," prefix="₹" decimals={0} />
          )}
        </div>
        {sparklineData && <Sparkline data={sparklineData} color={danger ? 'var(--signal-coral)' : 'var(--signal-cyan)'} />}
      </div>
      {delta !== null && delta !== undefined ? (
        <span className={`panel-delta ${isUp ? 'up' : 'down'}`}>
          {isUp ? <ArrowUp size={14} style={{ marginRight: 4 }} /> : <ArrowDown size={14} style={{ marginRight: 4 }} />}
          {Math.abs(Number(delta)).toFixed(1)}%
        </span>
      ) : null}
    </div>
  );
}

export default function InstrumentPanel({ sections, items, loading, error, onRetry }) {
  const dataList = sections || items || [];

  if (error) {
    return (
      <div className="error-panel" style={{ marginBottom: 'var(--sp-6)' }}>
        <div className="error-title">Failed to load metrics</div>
        <div className="error-message">{error}</div>
        {onRetry && (
          <button className="error-retry" onClick={onRetry}>Retry</button>
        )}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="skeleton-panel" style={{ marginBottom: 'var(--sp-6)' }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton-panel-section">
            <div className="shimmer-bar-sm skeleton-shimmer" />
            <div className="shimmer-bar-lg skeleton-shimmer" />
          </div>
        ))}
      </div>
    );
  }

  if (!dataList || dataList.length === 0) {
    return (
      <div className="empty-state" style={{ marginBottom: 'var(--sp-6)' }}>
        <svg className="empty-state-icon" viewBox="0 0 24 24">
          <path d="M3 3v18h18" />
          <path d="M18.7 8l-5.1 5.2-2.8-2.7-4.8 4.8" />
        </svg>
        <div className="empty-state-title">No metrics yet</div>
        <div className="empty-state-message">Data will appear here once available.</div>
      </div>
    );
  }

  return (
    <div className="instrument-panel" role="region" aria-label="Key metrics" style={{ marginBottom: 'var(--sp-6)' }}>
      {dataList.map((s, i) => (
        <Section key={i} {...s} />
      ))}
    </div>
  );
}
