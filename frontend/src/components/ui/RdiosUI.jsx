// ═══════════════════════════════════════════════════════
// R-DIOS UI COMPONENT LIBRARY
// All colors via CSS variables — zero hardcoded hex values
// ═══════════════════════════════════════════════════════
import { useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

// ── formatters (inline so pages only need one import) ───
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
  pct: (v, sign=true) => {
    if (v == null || isNaN(v)) return '—';
    const s = sign && v > 0 ? '+' : '';
    return `${s}${Number(v).toFixed(1)}%`;
  },
  date: (d) => {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-IN',
      { day:'2-digit', month:'short', year:'numeric' });
  },
  ago: (d) => {
    if (!d) return '—';
    const m = Math.floor((Date.now()-new Date(d).getTime())/60000);
    if (m < 1)  return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m/60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h/24)}d ago`;
  },
};

// ── Card ─────────────────────────────────────────────────
export function Card({ children, style={}, padding='20px', title, action }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-sm)',
      borderRadius: 12, padding, ...style,
    }}>
      {(title || action) && (
        <div style={{ display:'flex', justifyContent:'space-between',
          alignItems:'center', marginBottom:16 }}>
          {title && <span style={{ fontSize:13, fontWeight:600,
            color:'var(--text-primary)' }}>{title}</span>}
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

// ── HeroCard (gradient background, white text) ────────────
export function HeroCard({ title, value, trend, trendLabel, icon:Icon, gradient='linear-gradient(135deg,#6C5CE7 0%,#3D2FA8 100%)' }) {
  const isUp = trend > 0, isDn = trend < 0;
  const TI = isUp ? TrendingUp : isDn ? TrendingDown : Minus;
  return (
    <div style={{ background:gradient, borderRadius:14, padding:'22px 24px',
      position:'relative', overflow:'hidden',
      boxShadow:'0 8px 32px rgba(0,0,0,0.35)' }}>
      <div style={{ position:'absolute', right:-20, top:-20, width:120,
        height:120, borderRadius:'50%', background:'rgba(255,255,255,0.08)',
        pointerEvents:'none' }}/>
      <div style={{ position:'absolute', right:20, bottom:-30, width:80,
        height:80, borderRadius:'50%', background:'rgba(255,255,255,0.05)',
        pointerEvents:'none' }}/>
      <div style={{ position:'relative', zIndex:1 }}>
        <div style={{ display:'flex', justifyContent:'space-between',
          alignItems:'flex-start', marginBottom:16 }}>
          <span style={{ fontSize:11, fontWeight:600, letterSpacing:'0.1em',
            textTransform:'uppercase', color:'rgba(255,255,255,0.72)' }}>{title}</span>
          {Icon && (
            <div style={{ width:32, height:32, borderRadius:8,
              background:'rgba(255,255,255,0.18)',
              display:'flex', alignItems:'center', justifyContent:'center' }}>
              <Icon size={16} color="white" />
            </div>
          )}
        </div>
        <div style={{ fontSize:30, fontWeight:700, color:'white',
          letterSpacing:'-0.03em', marginBottom:10 }}>{value ?? '—'}</div>
        {trend !== undefined && (
          <div style={{ display:'flex', alignItems:'center', gap:6 }}>
            <span style={{ display:'inline-flex', alignItems:'center', gap:3,
              background:'rgba(255,255,255,0.18)', borderRadius:99,
              padding:'3px 8px', fontSize:12, fontWeight:600, color:'white' }}>
              <TI size={11}/>{Math.abs(trend)}%
            </span>
            {trendLabel && <span style={{ fontSize:12, color:'rgba(255,255,255,0.65)' }}>{trendLabel}</span>}
          </div>
        )}
      </div>
    </div>
  );
}

// ── MetricCard (surface background) ──────────────────────
export function MetricCard({ title, value, trend, trendLabel, subtitle, icon:Icon, color='accent' }) {
  const C = { accent:{i:'var(--accent)',b:'var(--accent-soft)'},
    success:{i:'var(--success)',b:'var(--success-soft)'},
    warning:{i:'var(--warning)',b:'var(--warning-soft)'},
    danger:{i:'var(--danger)',b:'var(--danger-soft)'},
    info:{i:'var(--info)',b:'var(--info-soft)'} };
  const c = C[color] || C.accent;
  const isUp = trend > 0, isDn = trend < 0;
  const TI = isUp ? TrendingUp : isDn ? TrendingDown : Minus;
  const [hov, setHov] = useState(false);
  return (
    <div style={{ background:'var(--bg-surface)', border:`1px solid ${hov?'var(--border-md)':'var(--border-sm)'}`,
      borderRadius:12, padding:'18px 20px',
      transition:'border-color 0.15s, box-shadow 0.15s',
      boxShadow: hov ? '0 4px 20px rgba(0,0,0,0.3)' : '0 1px 4px rgba(0,0,0,0.2)' }}
      onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}>
      <div style={{ display:'flex', justifyContent:'space-between',
        alignItems:'flex-start', marginBottom:14 }}>
        <span style={{ fontSize:11, fontWeight:600, letterSpacing:'0.08em',
          textTransform:'uppercase', color:'var(--text-muted)' }}>{title}</span>
        {Icon && (
          <div style={{ width:36, height:36, borderRadius:9, background:c.b,
            display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
            <Icon size={17} color={c.i}/>
          </div>
        )}
      </div>
      <div style={{ fontSize:28, fontWeight:700, color:'var(--text-primary)',
        letterSpacing:'-0.03em', marginBottom:8 }}>{value ?? '—'}</div>
      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
        {trend !== undefined && (
          <span style={{ display:'inline-flex', alignItems:'center', gap:3,
            fontSize:12, fontWeight:600, borderRadius:99, padding:'2px 7px',
            color: isUp?'var(--success)':isDn?'var(--danger)':'var(--text-muted)',
            background: isUp?'var(--success-soft)':isDn?'var(--danger-soft)':'var(--bg-overlay)' }}>
            <TI size={11}/>{Math.abs(trend)}%
          </span>
        )}
        {(trendLabel||subtitle) && (
          <span style={{ fontSize:12, color:'var(--text-muted)' }}>{trendLabel||subtitle}</span>
        )}
      </div>
    </div>
  );
}

// ── PageHeader ────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between',
      alignItems:'flex-start', marginBottom:28 }}>
      <div>
        <h1 style={{ fontSize:26, fontWeight:700, color:'var(--text-primary)',
          letterSpacing:'-0.02em', margin:0, lineHeight:1.2 }}>{title}</h1>
        {subtitle && <p style={{ fontSize:13, color:'var(--text-secondary)',
          marginTop:4, marginBottom:0 }}>{subtitle}</p>}
      </div>
      {actions && (
        <div style={{ display:'flex', gap:10, alignItems:'center',
          flexShrink:0 }}>{actions}</div>
      )}
    </div>
  );
}

// ── Badge ─────────────────────────────────────────────────
export function Badge({ children, variant='default', size='sm' }) {
  const V = {
    default: { bg:'var(--bg-overlay)', color:'var(--text-secondary)', border:'var(--border-md)' },
    accent:  { bg:'var(--accent-soft)', color:'var(--accent)', border:'var(--accent-border)' },
    success: { bg:'var(--success-soft)', color:'var(--success)', border:'rgba(0,196,124,0.2)' },
    warning: { bg:'var(--warning-soft)', color:'var(--warning)', border:'rgba(245,166,35,0.2)' },
    danger:  { bg:'var(--danger-soft)',  color:'var(--danger)',  border:'rgba(255,77,106,0.2)' },
    info:    { bg:'var(--info-soft)',    color:'var(--info)',    border:'rgba(59,158,255,0.2)' },
  };
  const s = V[variant] || V.default;
  return (
    <span style={{ display:'inline-flex', alignItems:'center',
      padding: size==='xs'?'1px 5px':'3px 8px',
      background:s.bg, color:s.color, border:`1px solid ${s.border}`,
      borderRadius:99, fontSize:size==='xs'?10:11,
      fontWeight:600, letterSpacing:'0.04em',
      textTransform:'uppercase', whiteSpace:'nowrap' }}>
      {children}
    </span>
  );
}

// ── Btn ───────────────────────────────────────────────────
export function Btn({ children, onClick, variant='primary', size='md',
  icon:Icon, disabled=false, loading=false, style={}, type='button' }) {
  const [hov, setHov] = useState(false);
  const SZ = { xs:{p:'4px 10px',fs:12}, sm:{p:'6px 12px',fs:13},
    md:{p:'8px 16px',fs:14}, lg:{p:'11px 22px',fs:15} };
  const V = {
    primary:   { bg: hov?'#7D70F0':'#6C5CE7', color:'white', bdr:'transparent' },
    secondary: { bg: hov?'var(--bg-hover)':'var(--bg-overlay)', color:'var(--text-primary)', bdr:'var(--border-md)' },
    ghost:     { bg: hov?'var(--bg-hover)':'transparent', color:'var(--text-secondary)', bdr:'transparent' },
    danger:    { bg: hov?'rgba(255,77,106,0.22)':'var(--danger-soft)', color:'var(--danger)', bdr:'rgba(255,77,106,0.2)' },
    success:   { bg: hov?'rgba(0,196,124,0.22)':'var(--success-soft)', color:'var(--success)', bdr:'rgba(0,196,124,0.2)' },
  };
  const v = V[variant]||V.secondary, sz = SZ[size]||SZ.md;
  return (
    <button type={type} onClick={onClick}
      disabled={disabled||loading}
      onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}
      style={{ display:'inline-flex', alignItems:'center', gap:6,
        padding:sz.p, fontSize:sz.fs, fontWeight:600, borderRadius:8,
        border:`1px solid ${v.bdr}`, background:v.bg, color:v.color,
        cursor:disabled||loading?'not-allowed':'pointer',
        opacity:disabled?0.5:1, transition:'all 0.15s', outline:'none',
        lineHeight:1, whiteSpace:'nowrap', ...style }}>
      {loading
        ? <svg width={sz.fs} height={sz.fs} viewBox="0 0 24 24" fill="none"
            style={{ animation:'spin 0.8s linear infinite' }}>
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeOpacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
          </svg>
        : Icon && <Icon size={sz.fs+1}/>
      }
      {children}
    </button>
  );
}

// ── Skeleton ──────────────────────────────────────────────
export function Skeleton({ w='100%', h=20, r=6 }) {
  return (
    <div style={{ width:w, height:h, borderRadius:r,
      background:'linear-gradient(90deg,var(--bg-overlay) 25%,var(--bg-hover) 50%,var(--bg-overlay) 75%)',
      backgroundSize:'400px 100%',
      animation:'shimmer 1.4s ease-in-out infinite' }}/>
  );
}

// ── Table ─────────────────────────────────────────────────
export function Table({ cols, rows, loading, empty='No data' }) {
  if (loading) return (
    <div style={{ display:'flex', flexDirection:'column', gap:8, padding:'8px 0' }}>
      {[1,2,3,4,5].map(i=><Skeleton key={i} h={44} r={6}/>)}
    </div>
  );
  return (
    <div style={{ overflowX:'auto' }}>
      <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
        <thead>
          <tr>
            {cols.map((c,i)=>(
              <th key={i} style={{ padding:'10px 14px',
                textAlign:c.align||'left', fontSize:11, fontWeight:600,
                letterSpacing:'0.08em', textTransform:'uppercase',
                color:'var(--text-muted)', background:'var(--bg-elevated)',
                borderBottom:'1px solid var(--border-sm)',
                whiteSpace:'nowrap' }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length===0
            ? <tr><td colSpan={cols.length} style={{ padding:'48px 20px',
                textAlign:'center', color:'var(--text-muted)', fontSize:14 }}>{empty}</td></tr>
            : rows.map((row,ri)=>(
                <tr key={ri}
                  style={{ transition:'background 0.1s' }}
                  onMouseEnter={e=>e.currentTarget.style.background='var(--bg-overlay)'}
                  onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
                  {cols.map((c,ci)=>(
                    <td key={ci} style={{ padding:'12px 14px',
                      textAlign:c.align||'left',
                      borderBottom:'1px solid var(--border-sm)',
                      color:'var(--text-primary)', verticalAlign:'middle' }}>
                      {c.render ? c.render(row[c.key], row) : (row[c.key] ?? '—')}
                    </td>
                  ))}
                </tr>
              ))
          }
        </tbody>
      </table>
    </div>
  );
}

// ── Input ─────────────────────────────────────────────────
export function Input({ label, value, onChange, placeholder, type='text',
  error, required, style={} }) {
  const [foc, setFoc] = useState(false);
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
      {label && (
        <label style={{ fontSize:13, fontWeight:500, color:'var(--text-secondary)' }}>
          {label}{required&&<span style={{ color:'var(--danger)', marginLeft:3 }}>*</span>}
        </label>
      )}
      <input type={type} value={value} onChange={e=>onChange(e.target.value)}
        placeholder={placeholder} required={required}
        onFocus={()=>setFoc(true)} onBlur={()=>setFoc(false)}
        style={{ padding:'10px 14px', background:'var(--bg-overlay)',
          border:`1px solid ${error?'var(--danger)':foc?'var(--accent)':'var(--border-md)'}`,
          borderRadius:8, color:'var(--text-primary)', fontSize:14,
          outline:'none', fontFamily:'inherit', width:'100%', ...style }}/>
      {error && <span style={{ fontSize:12, color:'var(--danger)' }}>{error}</span>}
    </div>
  );
}

// ── Select ────────────────────────────────────────────────
export function Select({ label, value, onChange, options=[], required, style={} }) {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
      {label && (
        <label style={{ fontSize:13, fontWeight:500, color:'var(--text-secondary)' }}>
          {label}{required&&<span style={{ color:'var(--danger)', marginLeft:3 }}>*</span>}
        </label>
      )}
      <select value={value} onChange={e=>onChange(e.target.value)} required={required}
        style={{ padding:'10px 14px', background:'var(--bg-overlay)',
          border:'1px solid var(--border-md)', borderRadius:8,
          color:'var(--text-primary)', fontSize:14,
          outline:'none', fontFamily:'inherit', cursor:'pointer', ...style }}>
        {options.map(o=>(
          <option key={o.value} value={o.value}
            style={{ background:'var(--bg-elevated)' }}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

// ── Modal ─────────────────────────────────────────────────
export function Modal({ open, onClose, title, children, width=480 }) {
  if (!open) return null;
  return (
    <div style={{ position:'fixed', inset:0, zIndex:1000,
      background:'rgba(0,0,0,0.65)', display:'flex',
      alignItems:'center', justifyContent:'center', padding:20 }}
      onClick={e=>e.target===e.currentTarget&&onClose()}>
      <div style={{ background:'var(--bg-elevated)', border:'1px solid var(--border-md)',
        borderRadius:16, padding:28, width:'100%', maxWidth:width,
        boxShadow:'0 24px 64px rgba(0,0,0,0.6)',
        animation:'fadeIn 0.2s ease' }}>
        <div style={{ display:'flex', justifyContent:'space-between',
          alignItems:'center', marginBottom:20 }}>
          <span style={{ fontSize:17, fontWeight:700, color:'var(--text-primary)' }}>{title}</span>
          <button onClick={onClose} style={{ background:'none', border:'none',
            cursor:'pointer', color:'var(--text-muted)', fontSize:20, lineHeight:1,
            padding:4 }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ── StatusDot ─────────────────────────────────────────────
export function StatusDot({ status='offline', size=8 }) {
  const C = { online:'var(--success)', offline:'var(--text-muted)',
    warning:'var(--warning)', error:'var(--danger)' };
  return <span style={{ display:'inline-block', width:size, height:size,
    borderRadius:'50%', background:C[status]||C.offline, flexShrink:0 }}/>;
}

// ── EmptyState ────────────────────────────────────────────
export function EmptyState({ icon:Icon, title, subtitle, action }) {
  return (
    <div style={{ display:'flex', flexDirection:'column', alignItems:'center',
      justifyContent:'center', padding:'60px 20px', gap:12, textAlign:'center' }}>
      {Icon && <Icon size={40} color="var(--text-muted)" strokeWidth={1.5}/>}
      <div style={{ fontSize:15, fontWeight:600,
        color:'var(--text-secondary)', marginTop:4 }}>{title}</div>
      {subtitle && <div style={{ fontSize:13, color:'var(--text-muted)',
        maxWidth:320 }}>{subtitle}</div>}
      {action && <div style={{ marginTop:8 }}>{action}</div>}
    </div>
  );
}

// ── InfoBanner ────────────────────────────────────────────
export function InfoBanner({ children, variant='info' }) {
  const V = {
    info:    { bg:'var(--info-soft)',    color:'var(--info)',    bdr:'rgba(59,158,255,0.2)' },
    warning: { bg:'var(--warning-soft)', color:'var(--warning)', bdr:'rgba(245,166,35,0.2)' },
    danger:  { bg:'var(--danger-soft)',  color:'var(--danger)',  bdr:'rgba(255,77,106,0.2)' },
    success: { bg:'var(--success-soft)', color:'var(--success)', bdr:'rgba(0,196,124,0.2)' },
  };
  const v = V[variant]||V.info;
  return (
    <div style={{ padding:'10px 16px', background:v.bg,
      border:`1px solid ${v.bdr}`, borderRadius:8,
      fontSize:13, color:v.color, marginBottom:16 }}>
      {children}
    </div>
  );
}
