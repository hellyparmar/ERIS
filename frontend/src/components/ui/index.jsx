import { useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/* ── MetricCard ─────────────────────────────────────────────
   Two variants:
   - variant="hero": Colored gradient background, white text (like Apexify Total Income)
   - variant="default": Surface background with colored icon area
   ───────────────────────────────────────────────────────── */
export function MetricCard({
  title, value, subtitle, trend, trendLabel,
  icon: Icon, variant = 'default', gradient = 'var(--hero-gradient)',
  color = 'accent', sparkline = null, style = {}
}) {
  const colorMap = {
    accent:  { icon: 'var(--accent)',   bg: 'var(--accent-soft)',  border: 'var(--accent-border)' },
    success: { icon: 'var(--success)',  bg: 'var(--success-soft)', border: 'rgba(0,196,124,0.2)' },
    warning: { icon: 'var(--warning)',  bg: 'var(--warning-soft)', border: 'rgba(245,166,35,0.2)' },
    danger:  { icon: 'var(--danger)',   bg: 'var(--danger-soft)',  border: 'rgba(255,77,106,0.2)' },
    info:    { icon: 'var(--info)',     bg: 'var(--info-soft)',    border: 'rgba(59,158,255,0.2)' },
  };
  const c = colorMap[color] || colorMap.accent;
  const isUp = trend > 0;
  const isDown = trend < 0;
  const TrendIcon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;

  if (variant === 'hero') {
    return (
      <div style={{
        background: gradient, borderRadius: 'var(--radius-xl)',
        padding: '22px 24px', position: 'relative', overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.35)', ...style,
      }}>
        {/* Decorative circle */}
        <div style={{
          position: 'absolute', right: -20, top: -20,
          width: 120, height: 120, borderRadius: '50%',
          background: 'rgba(255,255,255,0.08)',
        }} />
        <div style={{
          position: 'absolute', right: 20, bottom: -30,
          width: 80, height: 80, borderRadius: '50%',
          background: 'rgba(255,255,255,0.05)',
        }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.7)' }}>{title}</span>
            {Icon && (
              <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} color="white" />
              </div>
            )}
          </div>
          <div style={{ fontSize: 30, fontWeight: 700, color: 'white', letterSpacing: '-0.03em', marginBottom: 10 }}>{value ?? '—'}</div>
          {trend !== undefined && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 3, background: 'rgba(255,255,255,0.18)', borderRadius: 'var(--radius-full)', padding: '3px 8px' }}>
                <TrendIcon size={11} color="white" />
                <span style={{ fontSize: 12, fontWeight: 600, color: 'white' }}>{Math.abs(trend)}%</span>
              </div>
              {trendLabel && <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.65)' }}>{trendLabel}</span>}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
        padding: '18px 20px', border: '1px solid var(--border-sm)',
        boxShadow: 'var(--shadow-sm)', transition: 'all var(--transition-base)', ...style,
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-md)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-sm)'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{title}</span>
        </div>
        {Icon && (
          <div style={{ width: 36, height: 36, borderRadius: 'var(--radius-md)', background: c.bg, border: `1px solid ${c.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Icon size={17} color={c.icon} />
          </div>
        )}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.03em', marginBottom: 8 }}>{value ?? '—'}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {trend !== undefined && (
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 3,
            fontSize: 12, fontWeight: 600,
            color: isUp ? 'var(--success)' : isDown ? 'var(--danger)' : 'var(--text-muted)',
            background: isUp ? 'var(--success-soft)' : isDown ? 'var(--danger-soft)' : 'var(--bg-overlay)',
            padding: '2px 7px', borderRadius: 'var(--radius-full)',
          }}>
            <TrendIcon size={11} />
            {Math.abs(trend)}%
          </span>
        )}
        {(trendLabel || subtitle) && (
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{trendLabel || subtitle}</span>
        )}
      </div>
      {sparkline && <div style={{ marginTop: 12 }}>{sparkline}</div>}
    </div>
  );
}

/* ── PageHeader ─────────────────────────────────────────── */
export function PageHeader({ title, subtitle, actions, breadcrumb }) {
  return (
    <div style={{ marginBottom: 28 }}>
      {breadcrumb && (
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
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

/* ── Card ───────────────────────────────────────────────── */
export function Card({ children, padding = '20px', title, titleRight, style = {} }) {
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-sm)',
      borderRadius: 'var(--radius-lg)', padding, boxShadow: 'var(--shadow-sm)', ...style,
    }}>
      {title && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{title}</span>
          {titleRight && <div>{titleRight}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

/* ── Badge ──────────────────────────────────────────────── */
export function Badge({ children, variant = 'default', size = 'sm' }) {
  const styles = {
    default: { bg: 'var(--bg-overlay)', color: 'var(--text-secondary)', border: 'var(--border-md)' },
    accent:  { bg: 'var(--accent-soft)', color: 'var(--accent)', border: 'var(--accent-border)' },
    success: { bg: 'var(--success-soft)', color: 'var(--success)', border: 'rgba(0,196,124,0.2)' },
    warning: { bg: 'var(--warning-soft)', color: 'var(--warning)', border: 'rgba(245,166,35,0.2)' },
    danger:  { bg: 'var(--danger-soft)', color: 'var(--danger)', border: 'rgba(255,77,106,0.2)' },
    info:    { bg: 'var(--info-soft)', color: 'var(--info)', border: 'rgba(59,158,255,0.2)' },
  };
  const s = styles[variant] || styles.default;
  const padding = size === 'xs' ? '1px 5px' : '3px 8px';
  const fontSize = size === 'xs' ? 10 : 11;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', padding,
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
      borderRadius: 'var(--radius-full)', fontSize, fontWeight: 600,
      letterSpacing: '0.04em', textTransform: 'uppercase', whiteSpace: 'nowrap',
    }}>
      {children}
    </span>
  );
}

/* ── Button ─────────────────────────────────────────────── */
export function Button({ children, onClick, variant = 'primary', size = 'md', icon: Icon, iconRight: IconRight, disabled = false, loading = false, style = {}, type = 'button' }) {
  const [hov, setHov] = useState(false);
  const sizes = {
    xs: { padding: '4px 10px', fontSize: 12, iconSize: 13 },
    sm: { padding: '6px 12px', fontSize: 13, iconSize: 14 },
    md: { padding: '8px 16px', fontSize: 14, iconSize: 15 },
    lg: { padding: '11px 22px', fontSize: 15, iconSize: 16 },
  };
  const variants = {
    primary: { bg: hov ? 'var(--accent-hover)' : 'var(--accent)', color: 'white', border: 'transparent' },
    secondary: { bg: hov ? 'var(--bg-hover)' : 'var(--bg-overlay)', color: 'var(--text-primary)', border: 'var(--border-md)' },
    ghost: { bg: hov ? 'var(--bg-hover)' : 'transparent', color: 'var(--text-secondary)', border: 'transparent' },
    danger: { bg: hov ? 'rgba(255,77,106,0.2)' : 'var(--danger-soft)', color: 'var(--danger)', border: 'rgba(255,77,106,0.2)' },
    success: { bg: hov ? 'rgba(0,196,124,0.2)' : 'var(--success-soft)', color: 'var(--success)', border: 'rgba(0,196,124,0.2)' },
  };
  const v = variants[variant] || variants.secondary;
  const sz = sizes[size] || sizes.md;
  return (
    <button
      type={type} onClick={onClick} disabled={disabled || loading}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: sz.padding, fontSize: sz.fontSize, fontWeight: 600,
        borderRadius: 'var(--radius-md)', border: `1px solid ${v.border}`,
        background: v.bg, color: v.color,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'all var(--transition-fast)',
        outline: 'none', lineHeight: 1, whiteSpace: 'nowrap', ...style,
      }}
    >
      {loading ? <Spinner size={sz.iconSize} /> : Icon && <Icon size={sz.iconSize} />}
      {children}
      {!loading && IconRight && <IconRight size={sz.iconSize} />}
    </button>
  );
}

export function GradientButton({ children, onClick, type = 'button', disabled = false, style = {}, className = '', variant = 'primary', ...props }) {
  const variants = {
    primary: {
      background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))',
      color: 'white',
      border: '1px solid transparent',
    },
    secondary: {
      background: 'var(--bg-surface)',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-sm)',
    },
  };
  const v = variants[variant] || variants.primary;
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        padding: '12px 18px',
        borderRadius: '12px',
        fontWeight: 700,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 180ms ease',
        opacity: disabled ? 0.6 : 1,
        ...v,
        ...style,
      }}
      {...props}
    >
      {children}
    </button>
  );
}

export function GlassCard({ children, className = '', style = {}, title, ...props }) {
  return (
    <div
      className={className}
      style={{
        background: 'rgba(255, 255, 255, 0.18)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        backdropFilter: 'blur(18px)',
        borderRadius: '18px',
        boxShadow: '0 20px 50px rgba(15, 23, 42, 0.08)',
        padding: 20,
        overflow: 'hidden',
        ...style,
      }}
      {...props}
    >
      {title && <div style={{ marginBottom: 12, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{title}</div>}
      {children}
    </div>
  );
}

/* ── Spinner ─────────────────────────────────────────────── */
export function Spinner({ size = 16, color = 'currentColor' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 0.8s linear infinite' }}>
      <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="2.5" strokeOpacity="0.2" />
      <path d="M12 2a10 10 0 0 1 10 10" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

/* ── Skeleton ────────────────────────────────────────────── */
export function Skeleton({ width = '100%', height = 20, radius = 6, style = {} }) {
  return (
    <div style={{
      width, height, borderRadius: radius,
      background: `linear-gradient(90deg, var(--bg-overlay) 25%, var(--bg-hover) 50%, var(--bg-overlay) 75%)`,
      backgroundSize: '400px 100%',
      animation: 'shimmer 1.4s ease-in-out infinite',
      ...style,
    }} />
  );
}

/* ── StatusDot ───────────────────────────────────────────── */
export function StatusDot({ status = 'offline', size = 8 }) {
  const colors = {
    online: 'var(--success)', offline: 'var(--text-muted)',
    warning: 'var(--warning)', error: 'var(--danger)',
  };
  return <span style={{ display: 'inline-block', width: size, height: size, borderRadius: '50%', background: colors[status] || colors.offline, flexShrink: 0 }} />;
}

/* ── Table ───────────────────────────────────────────────── */
export function Table({ headers, children, style = {} }) {
  return (
    <div style={{ overflowX: 'auto', ...style }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} style={{
                padding: '10px 14px', textAlign: h.align || 'left',
                fontSize: 11, fontWeight: 600, letterSpacing: '0.08em',
                textTransform: 'uppercase', color: 'var(--text-muted)',
                borderBottom: '1px solid var(--border-sm)',
                background: 'var(--bg-elevated)', whiteSpace: 'nowrap',
              }}>{h.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function TableRow({ children, onClick, style = {} }) {
  const [hov, setHov] = useState(false);
  return (
    <tr
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? 'var(--bg-overlay)' : 'transparent',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'background var(--transition-fast)',
        ...style,
      }}
    >
      {children}
    </tr>
  );
}

export function Td({ children, align = 'left', style = {} }) {
  return (
    <td style={{
      padding: '12px 14px', textAlign: align,
      borderBottom: '1px solid var(--border-xs)',
      color: 'var(--text-primary)', verticalAlign: 'middle', ...style,
    }}>
      {children}
    </td>
  );
}

/* ── EmptyState ──────────────────────────────────────────── */
export function EmptyState({ icon: Icon, title, subtitle, action }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 20px', gap: 12, textAlign: 'center' }}>
      {Icon && <Icon size={40} color="var(--text-muted)" strokeWidth={1.5} />}
      <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-secondary)', marginTop: 4 }}>{title}</div>
      {subtitle && <div style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 320 }}>{subtitle}</div>}
      {action && <div style={{ marginTop: 8 }}>{action}</div>}
    </div>
  );
}

/* ── SectionLabel ────────────────────────────────────────── */
export function SectionLabel({ children, style = {} }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8, ...style }}>
      {children}
    </div>
  );
}

/* ── Divider ─────────────────────────────────────────────── */
export function Divider({ style = {} }) {
  return <div style={{ height: 1, background: 'var(--border-sm)', ...style }} />;
}
