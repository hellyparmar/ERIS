import React from 'react';
import { 
  ArrowUpDown, ShieldAlert, X, Info, CheckCircle, Loader2
} from 'lucide-react';
import '../../styles/eris-components.css';

// ── IMPORT CORE COMPONENTS FROM INDIVIDUAL FILES ──
import { Button } from './Button';
import { Input } from './Input';
import { Select } from './Select';
import { Badge } from './Badge';
import { Card } from './Card';
import { Modal } from './Modal';
import { Avatar } from './Avatar';
import { StatusBadge } from './StatusBadge';
import { Tooltip } from './Tooltip';
import { Spinner } from './Spinner';
import { SkeletonLoader } from './SkeletonLoader';
import { EmptyState } from './EmptyState';

// ── RE-EXPORT FROM MASTER FILE ──
export { Button, Button as default } from './Button';
export { Input } from './Input';
export { Select } from './Select';
export { Badge } from './Badge';
export { Card } from './Card';
export { Modal } from './Modal';
export { Avatar } from './Avatar';
export { StatusBadge } from './StatusBadge';
export { Tooltip } from './Tooltip';
export { Spinner } from './Spinner';
export { SkeletonLoader } from './SkeletonLoader';
export { EmptyState } from './EmptyState';

// Helper aliases
export { default as GradientButton } from './GradientButton';
export { default as GlassCard } from './GlassCard';
export { default as SearchInput } from './SearchInput';
export { default as StatCard } from './StatCard';
export { default as ActionButton } from './ActionButton';
export { default as LoadingSkeleton } from './LoadingSkeleton';


// ── UTILS: FORMATTERS ──
export const fmt = {
  inr: (v) => {
    if (v == null || isNaN(v)) return '—';
    if (v >= 10000000) return `₹${(v/10000000).toFixed(2)} Cr`;
    if (v >= 100000)   return `₹${(v/100000).toFixed(2)} L`;
    if (v >= 1000)     return `₹${(v/1000).toFixed(1)}k`;
    return `₹${Number(v).toLocaleString('en-IN')}`;
  },
  num: (v) => {
    if (v == null || isNaN(v)) return '—';
    if (v >= 10000000) return `${(v/10000000).toFixed(1)}Cr`;
    if (v >= 100000)   return `${(v/100000).toFixed(1)}L`;
    if (v >= 1000)     return `${(v/1000).toFixed(1)}k`;
    return String(v);
  },
  pct: (v, sign = true) => {
    if (v == null || isNaN(v)) return '—';
    const s = sign && v > 0 ? '+' : '';
    return `${s}${Number(v).toFixed(1)}%`;
  },
  date: (d) => {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  },
  ago: (d) => {
    if (!d) return '—';
    const m = Math.floor((Date.now() - new Date(d).getTime()) / 60000);
    if (m < 1)  return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  },
};

// ── TABLE COMPONENT ──
export function Table({
  headers = [],
  rows = [],
  onSort,
  sortField,
  sortDirection,
  loading = false,
  emptyMessage = 'No data available',
  renderRow,
  style = {},
  className = ''
}) {
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '16px 0' }}>
        {[1, 2, 3, 4, 5].map((idx) => (
          <SkeletonLoader key={idx} variant="table" />
        ))}
      </div>
    );
  }

  return (
    <div className={`eris-table-container ${className}`} style={style}>
      <table className="eris-table">
        <thead>
          <tr>
            {headers.map((h, i) => {
              const isSortable = h.sortable;
              const isCurrentSort = sortField === h.key;
              return (
                <th
                  key={i}
                  onClick={() => isSortable && onSort && onSort(h.key)}
                  className="eris-table__th"
                  style={{
                    textAlign: h.align || 'left',
                    cursor: isSortable ? 'pointer' : 'default',
                  }}
                >
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <span>{h.label}</span>
                    {isSortable && (
                      <ArrowUpDown 
                        size={12} 
                        style={{ 
                          color: isCurrentSort ? '#8B5CF6' : 'var(--text-tertiary)',
                          opacity: isCurrentSort ? 1 : 0.4 
                        }} 
                      />
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={headers.length} style={{ textAlign: 'center', padding: '48px 24px' }}>
                <EmptyState title="No items found" subtitle={emptyMessage} />
              </td>
            </tr>
          ) : (
            rows.map((row, rIdx) => {
              if (renderRow) return renderRow(row, rIdx);
              return (
                <tr key={rIdx} className="eris-table__tr">
                  {headers.map((h, cIdx) => (
                    <td 
                      key={cIdx} 
                      className="eris-table__td"
                      style={{ textAlign: h.align || 'left' }}
                    >
                      {h.render ? h.render(row[h.key], row) : (row[h.key] ?? '—')}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

export function TableRow({ children, onClick, className = '', style = {} }) {
  return (
    <tr 
      onClick={onClick} 
      className={`eris-table__tr ${className}`} 
      style={{ cursor: onClick ? 'pointer' : 'default', ...style }}
    >
      {children}
    </tr>
  );
}

export function Td({ children, align = 'left', className = '', style = {} }) {
  return (
    <td 
      className={`eris-table__td ${className}`} 
      style={{ textAlign: align, ...style }}
    >
      {children}
    </td>
  );
}

// ── STATUS INDICATOR ──
export function StatusIndicator({
  status = 'pending',
  text = '',
  pulse = false,
  className = '',
  style = {}
}) {
  return (
    <StatusBadge 
      status={status}
      text={text}
      pulse={pulse}
      className={className}
      style={style}
    />
  );
}

export function StatusDot({ status = 'offline', size = 8 }) {
  const colors = {
    online: 'var(--status-success)',
    offline: 'var(--text-tertiary)',
    warning: 'var(--status-warning)',
    error: 'var(--status-error)'
  };
  return (
    <span 
      style={{ 
        display: 'inline-block', 
        width: size, 
        height: size, 
        borderRadius: '50%', 
        background: colors[status] || colors.offline,
        flexShrink: 0 
      }} 
    />
  );
}

// ── SKELETON / LOADING NOTICES ──
export function Skeleton({ width = '100%', height = 20, radius = 6, style = {} }) {
  return (
    <SkeletonLoader 
      width={width} 
      height={typeof height === 'number' ? `${height}px` : height} 
      radius={`${radius}px`}
      style={style}
    />
  );
}

export function ProgressBar({
  progress = 0,
  color = 'var(--accent-violet)',
  height = 6,
  showLabel = false,
  style = {},
  className = ''
}) {
  const clampedProgress = Math.min(100, Math.max(0, progress));
  return (
    <div className={className} style={{ width: '100%', ...style }}>
      <div 
        style={{ 
          background: 'var(--surface-tertiary)', 
          borderRadius: 999, 
          height, 
          overflow: 'hidden', 
          position: 'relative' 
        }}
      >
        <div
          style={{
            height: '100%',
            background: color,
            width: `${clampedProgress}%`,
            transition: 'width 300ms ease-out',
            borderRadius: 999
          }}
        />
      </div>
      {showLabel && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
          <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 600 }}>
            {Math.round(clampedProgress)}%
          </span>
        </div>
      )}
    </div>
  );
}

export function LoadingNotice({ message = 'Loading...', size = 'md' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 20px', gap: 12 }}>
      <Spinner size={size} color="var(--accent-violet)" />
      <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>{message}</span>
    </div>
  );
}

// ── ERROR STATES ──
export function ErrorBanner({
  message = 'An unexpected error occurred. Please try again.',
  onDismiss,
  className = '',
  style = {}
}) {
  const [visible, setVisible] = React.useState(true);
  if (!visible) return null;

  return (
    <div className={`eris-error-banner ${className}`} style={style}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <ShieldAlert size={18} style={{ flexShrink: 0 }} />
        <span>{message}</span>
      </div>
      {onDismiss && (
        <button 
          type="button" 
          onClick={() => {
            setVisible(false);
            onDismiss();
          }} 
          className="eris-input-clear"
          style={{ color: 'var(--status-error)' }}
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

// ── MISCELLANEOUS LAYOUT ──
export function PageHeader({ title, subtitle, actions, breadcrumb }) {
  return (
    <div style={{ marginBottom: 'var(--space-6)' }}>
      {breadcrumb && (
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
          {breadcrumb}
        </div>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1.2 }}>{title}</h1>
          {subtitle && <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{subtitle}</p>}
        </div>
        {actions && <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexShrink: 0 }}>{actions}</div>}
      </div>
    </div>
  );
}

export function SectionLabel({ children, style = {} }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 8, ...style }}>
      {children}
    </div>
  );
}
export function Divider({ style = {} }) {
  return <div style={{ height: 1, background: 'var(--border-subtle)', ...style }} />;
}

// ── METRIC CARD & HERO CARD ──
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function MetricCard({ title, value, trend, trendLabel, subtitle, icon: Icon, color = 'accent', style = {} }) {
  const isUp = trend > 0;
  const isDown = trend < 0;
  const TrendIcon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;

  const colorMap = {
    accent:  { i: 'var(--accent-violet)',   b: 'rgba(139, 92, 246, 0.15)',  border: 'rgba(139, 92, 246, 0.2)' },
    success: { i: 'var(--status-success)',  b: 'rgba(34, 197, 94, 0.15)', border: 'rgba(34, 197, 94, 0.2)' },
    warning: { i: 'var(--status-warning)',  b: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.2)' },
    danger:  { i: 'var(--status-error)',   b: 'rgba(239, 68, 68, 0.15)',  border: 'rgba(239, 68, 68, 0.2)' },
    info:    { i: 'var(--status-info)',     b: 'rgba(59, 130, 246, 0.15)',    border: 'rgba(59, 130, 246, 0.2)' },
  };
  const c = colorMap[color] || colorMap.accent;

  return (
    <Card
      style={{
        padding: '18px 20px',
        ...style,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
          {title}
        </span>
        {Icon && (
          <div style={{ 
            width: 36, 
            height: 36, 
            borderRadius: '8px', 
            background: c.b, 
            border: `1px solid ${c.border}`, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            flexShrink: 0 
          }}>
            {typeof Icon === 'function' ? <Icon size={17} color={c.i} /> : Icon}
          </div>
        )}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.03em', marginBottom: 8 }}>
        {value ?? '—'}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {trend !== undefined && (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 3,
            fontSize: 12,
            fontWeight: 600,
            borderRadius: '99px',
            padding: '2px 7px',
            color: isUp ? 'var(--status-success)' : isDown ? 'var(--status-error)' : 'var(--text-secondary)',
            background: isUp ? 'rgba(34, 197, 94, 0.1)' : isDown ? 'rgba(239, 68, 68, 0.1)' : 'var(--surface-tertiary)'
          }}>
            <TrendIcon size={11} />
            {Math.abs(trend)}%
          </span>
        )}
        {(trendLabel || subtitle) && (
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{trendLabel || subtitle}</span>
        )}
      </div>
    </Card>
  );
}

export function HeroCard({ title, value, trend, trendLabel, icon: Icon, gradient = 'linear-gradient(135deg, var(--accent-violet) 0%, var(--accent-cyan) 100%)', style = {} }) {
  const isUp = trend > 0;
  const isDown = trend < 0;
  const TrendIcon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;

  return (
    <div style={{ 
      background: gradient, 
      borderRadius: 14, 
      padding: '22px 24px',
      position: 'relative', 
      overflow: 'hidden',
      boxShadow: 'var(--shadow-md)',
      ...style
    }}>
      <div style={{ position: 'absolute', right: -20, top: -20, width: 120, height: 120, borderRadius: '50%', background: 'rgba(255,255,255,0.08)', pointerEvents: 'none' }}/>
      <div style={{ position: 'absolute', right: 20, bottom: -30, width: 80, height: 80, borderRadius: '50%', background: 'rgba(255,255,255,0.05)', pointerEvents: 'none' }}/>
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.72)' }}>
            {title}
          </span>
          {Icon && (
            <div style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(255,255,255,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {typeof Icon === 'function' ? <Icon size={16} color="white" /> : Icon}
            </div>
          )}
        </div>
        <div style={{ fontSize: 30, fontWeight: 700, color: 'white', letterSpacing: '-0.03em', marginBottom: 10 }}>
          {value ?? '—'}
        </div>
        {trend !== undefined && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, background: 'rgba(255,255,255,0.18)', borderRadius: 99, padding: '3px 8px', fontSize: 12, fontWeight: 600, color: 'white' }}>
              <TrendIcon size={11}/>{Math.abs(trend)}%
            </span>
            {trendLabel && <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.65)' }}>{trendLabel}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
