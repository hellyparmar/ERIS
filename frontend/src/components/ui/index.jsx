import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, X, Check, ChevronDown, AlertCircle, Info, 
  CheckCircle, Loader2, ArrowUpDown, ShieldAlert,
  HelpCircle, MoreVertical
} from 'lucide-react';
import '../../styles/eris-components.css';

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

// ── 1. BUTTON COMPONENT ──
export function Button({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'md', 
  icon: Icon, 
  iconRight: IconRight, 
  disabled = false, 
  loading = false, 
  style = {}, 
  type = 'button',
  className = '',
  ...props
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`eris-btn eris-btn--${variant} eris-btn--${size} ${className}`}
      style={style}
      {...props}
    >
      {loading && <div className="eris-btn__spinner" />}
      {!loading && Icon && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} />}
      <span style={{ opacity: loading ? 0 : 1, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        {children}
      </span>
      {!loading && IconRight && <IconRight size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} />}
    </button>
  );
}

// ── 1B. GRADIENT BUTTON ──
export function GradientButton(props) {
  return <Button {...props} variant="primary" />;
}

// ── 2. INPUT COMPONENT ──
export function Input({
  label,
  value,
  onChange,
  placeholder = '',
  type = 'text',
  error,
  valid,
  helperText,
  disabled = false,
  required = false,
  iconLeft: IconLeft,
  iconRight: IconRight,
  style = {},
  className = '',
  onClear,
  ...props
}) {
  const [focused, setFocused] = useState(false);

  const containerClass = [
    'eris-input-container',
    focused ? 'eris-input-container--focused' : '',
    valid ? 'eris-input-container--valid' : '',
    error ? 'eris-input-container--invalid' : '',
    disabled ? 'eris-input-container--disabled' : ''
  ].filter(Boolean).join(' ');

  return (
    <div className={`eris-input-wrapper ${className}`} style={style}>
      {label && (
        <label className="eris-input-label">
          {label} {required && <span style={{ color: 'var(--accent-red)' }}>*</span>}
        </label>
      )}
      <div className={containerClass}>
        {IconLeft && (
          <span className="eris-input-icon eris-input-icon--left">
            <IconLeft size={16} />
          </span>
        )}
        <input
          type={type}
          value={value ?? ''}
          onChange={(e) => onChange && onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="eris-input"
          {...props}
        />
        {onClear && value && !disabled && (
          <button type="button" onClick={onClear} className="eris-input-clear">
            <X size={14} />
          </button>
        )}
        {valid && !error && (
          <span className="eris-input-icon eris-input-icon--right" style={{ color: 'var(--accent-green)' }}>
            <CheckCircle size={16} />
          </span>
        )}
        {error && (
          <span className="eris-input-icon eris-input-icon--right" style={{ color: 'var(--accent-red)' }}>
            <AlertCircle size={16} />
          </span>
        )}
        {!valid && !error && IconRight && (
          <span className="eris-input-icon eris-input-icon--right">
            <IconRight size={16} />
          </span>
        )}
      </div>
      {error && <span className="eris-input-error">{error}</span>}
      {!error && helperText && <span className="eris-input-helper">{helperText}</span>}
    </div>
  );
}

// ── 3. CUSTOM DROPDOWN / SELECT COMPONENT ──
export function Select({
  label,
  value,
  onChange,
  options = [],
  placeholder = 'Select an option',
  disabled = false,
  required = false,
  error,
  style = {},
  className = '',
  searchable = false
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const wrapperRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = options.find(o => o.value === value);

  const filteredOptions = searchable 
    ? options.filter(o => o.label.toLowerCase().includes(searchTerm.toLowerCase()))
    : options;

  return (
    <div className={`eris-input-wrapper ${className}`} style={style} ref={wrapperRef}>
      {label && (
        <label className="eris-input-label">
          {label} {required && <span style={{ color: 'var(--accent-red)' }}>*</span>}
        </label>
      )}
      <div className="eris-select-wrapper">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
          className="eris-select-trigger"
          style={{
            borderColor: error ? 'var(--accent-red)' : isOpen ? '#8B5CF6' : 'var(--border)',
            boxShadow: isOpen ? '0 0 0 3px rgba(139, 92, 246, 0.15)' : 'none'
          }}
        >
          <span>{selectedOption ? selectedOption.label : placeholder}</span>
          <ChevronDown 
            size={16} 
            className={`eris-select-trigger__chevron ${isOpen ? 'eris-select-trigger__chevron--open' : ''}`} 
          />
        </button>

        {isOpen && (
          <div className="eris-select-dropdown">
            {searchable && (
              <div style={{ padding: '4px 6px', borderBottom: '1px solid var(--border)' }}>
                <input
                  type="text"
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    color: 'var(--text-primary)',
                    fontSize: '12.5px',
                    outline: 'none'
                  }}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            )}
            <div style={{ maxHeight: '180px', overflowY: 'auto', marginTop: searchable ? '4px' : '0' }}>
              {filteredOptions.length === 0 ? (
                <div style={{ padding: '8px 12px', fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center' }}>
                  No options found
                </div>
              ) : (
                filteredOptions.map((opt) => {
                  const isSelected = opt.value === value;
                  return (
                    <div
                      key={opt.value}
                      onClick={() => {
                        onChange && onChange(opt.value);
                        setIsOpen(false);
                        setSearchTerm('');
                      }}
                      className={`eris-select-option ${isSelected ? 'eris-select-option--selected' : ''}`}
                    >
                      <span>{opt.label}</span>
                      {isSelected && <Check size={14} />}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
      {error && <span className="eris-input-error">{error}</span>}
    </div>
  );
}

// ── 4. BADGE COMPONENT ──
export function Badge({
  children,
  variant = 'neutral',
  size = 'md',
  icon: Icon,
  onDismiss,
  className = '',
  style = {}
}) {
  return (
    <span 
      className={`eris-badge eris-badge--${variant} eris-badge--${size} ${className}`}
      style={style}
    >
      {Icon && <Icon size={size === 'sm' ? 10 : size === 'lg' ? 14 : 12} />}
      {children}
      {onDismiss && (
        <button 
          type="button" 
          onClick={(e) => {
            e.stopPropagation();
            onDismiss();
          }} 
          className="eris-badge__close"
        >
          <X size={10} />
        </button>
      )}
    </span>
  );
}

// ── 5. MODAL / DIALOG COMPONENT ──
export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
  width = 520,
  layout = 'center', // 'center' or 'drawer' (side panel)
  className = '',
  style = {}
}) {
  const modalRef = useRef(null);

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && open) {
        onClose && onClose();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const modalStyle = {
    maxWidth: layout === 'drawer' ? '400px' : `${width}px`,
    width: '100%',
    height: layout === 'drawer' ? '100%' : 'auto',
    borderRadius: layout === 'drawer' ? '0' : '16px',
    marginLeft: layout === 'drawer' ? 'auto' : 'unset',
    marginRight: '0',
    animation: layout === 'drawer' ? 'eris-slide-in-right 300ms cubic-bezier(0.16, 1, 0.3, 1)' : 'eris-scale-in 250ms cubic-bezier(0.34, 1.56, 0.64, 1)',
    ...style
  };

  return (
    <div 
      className="eris-modal-overlay" 
      onClick={(e) => e.target === e.currentTarget && onClose && onClose()}
      style={{
        alignItems: layout === 'drawer' ? 'stretch' : 'center',
        justifyContent: layout === 'drawer' ? 'flex-end' : 'center',
        padding: layout === 'drawer' ? '0' : '20px'
      }}
    >
      <div 
        ref={modalRef} 
        className={`eris-modal ${className}`}
        style={modalStyle}
      >
        <div className="eris-modal__header">
          <span className="eris-modal__title">{title}</span>
          <button type="button" onClick={onClose} className="eris-modal__close">
            <X size={18} />
          </button>
        </div>
        <div className="eris-modal__body" style={{ flex: 1 }}>
          {children}
        </div>
        {footer && <div className="eris-modal__footer">{footer}</div>}
      </div>
    </div>
  );
}

// ── 6. CARDS ──
export function Card({
  children,
  variant = 'base', // 'base', 'elevated', 'bordered'
  title,
  titleRight,
  style = {},
  className = '',
  padding = '24px'
}) {
  const cardClass = [
    'eris-card',
    variant === 'elevated' ? 'eris-card--elevated' : '',
    variant === 'bordered' ? 'eris-card--bordered' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={cardClass} style={{ padding, ...style }}>
      {(title || titleRight) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          {title && <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{title}</h3>}
          {titleRight && <div>{titleRight}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export function GlassCard({ children, style = {}, className = '', ...props }) {
  return (
    <Card 
      variant="base" 
      style={{
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        backdropFilter: 'blur(16px)',
        ...style
      }}
      className={className}
      {...props}
    >
      {children}
    </Card>
  );
}

// ── 7. TABLE COMPONENT ──
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
          <Skeleton key={idx} height={48} radius={8} />
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
                          color: isCurrentSort ? '#8B5CF6' : 'var(--text-muted)',
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

// ── 8. SEARCH BARS ──
export function SearchInput({
  value,
  onChange,
  placeholder = 'Search...',
  onClear,
  style = {},
  className = '',
  debounceMs = 300,
  onDebouncedSearch
}) {
  const [localVal, setLocalVal] = useState(value || '');

  useEffect(() => {
    setLocalVal(value || '');
  }, [value]);

  useEffect(() => {
    if (!onDebouncedSearch) return;
    const timer = setTimeout(() => {
      onDebouncedSearch(localVal);
    }, debounceMs);
    return () => clearTimeout(timer);
  }, [localVal, debounceMs, onDebouncedSearch]);

  const handleInputChange = (e) => {
    const val = e.target.value;
    setLocalVal(val);
    if (onChange) onChange(val);
  };

  const handleClear = () => {
    setLocalVal('');
    if (onChange) onChange('');
    if (onClear) onClear();
    if (onDebouncedSearch) onDebouncedSearch('');
  };

  return (
    <div className={`eris-search-bar ${className}`} style={style}>
      <Search size={16} style={{ color: 'var(--text-muted)', marginRight: 10, flexShrink: 0 }} />
      <input
        type="text"
        value={localVal}
        onChange={handleInputChange}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '10px 0',
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: 'var(--text-primary)',
          fontSize: '14px'
        }}
      />
      {localVal && (
        <button 
          type="button" 
          onClick={handleClear} 
          className="eris-input-clear"
          style={{ marginLeft: 6 }}
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

// ── 9. AVATARS ──
export function Avatar({
  src,
  name = '',
  size = 'md',
  status, // 'online', 'offline', 'away'
  style = {},
  className = '',
  tooltip = true
}) {
  const initials = name
    ? name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
    : '??';

  const avatarColors = [
    'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)', // Gold
    'linear-gradient(135deg, #10B981 0%, #059669 100%)', // Emerald
    'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)', // Blue
    'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)', // Violet
    'linear-gradient(135deg, #EC4899 0%, #DB2777 100%)'  // Pink
  ];

  // Determine a stable background color based on name string
  const colorIndex = name 
    ? name.charCodeAt(0) % avatarColors.length 
    : 0;

  const bgGradient = avatarColors[colorIndex];

  return (
    <div className="eris-tooltip-wrapper">
      <div 
        className={`eris-avatar eris-avatar--${size} ${className}`}
        style={{
          background: src ? 'transparent' : bgGradient,
          ...style
        }}
      >
        {src ? (
          <img 
            src={src} 
            alt={name} 
            className={`eris-avatar eris-avatar--${size}`} 
            style={{ border: 'none' }}
          />
        ) : (
          <span>{initials}</span>
        )}
        {status && (
          <span className={`eris-avatar__status eris-avatar__status--${status}`} />
        )}
      </div>
      {tooltip && name && <div className="eris-tooltip">{name}</div>}
    </div>
  );
}

// ── 10. STATUS COMPONENT ──
export function StatusIndicator({
  status = 'pending', // 'paid', 'pending', 'failed', 'processing'
  text = '',
  pulse = false,
  className = '',
  style = {}
}) {
  const statusConfig = {
    paid: { color: 'var(--accent-green)', label: 'Paid', icon: CheckCircle, variant: 'success' },
    success: { color: 'var(--accent-green)', label: 'Success', icon: CheckCircle, variant: 'success' },
    pending: { color: 'var(--accent-amber)', label: 'Pending', icon: Info, variant: 'warning' },
    warning: { color: 'var(--accent-amber)', label: 'Warning', icon: Info, variant: 'warning' },
    failed: { color: 'var(--accent-red)', label: 'Failed', icon: AlertCircle, variant: 'error' },
    error: { color: 'var(--accent-red)', label: 'Error', icon: AlertCircle, variant: 'error' },
    processing: { color: '#3B82F6', label: 'Processing', icon: Loader2, variant: 'info' }
  };

  const config = statusConfig[status.toLowerCase()] || statusConfig.pending;
  const StatusIcon = config.icon;

  return (
    <Badge 
      variant={config.variant}
      size="md"
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '4px 10px',
        animation: pulse ? 'eris-pulse 2s infinite ease-in-out' : 'none',
        ...style
      }}
    >
      <StatusIcon size={12} className={status === 'processing' ? 'eris-btn__spinner' : ''} />
      <span>{text || config.label}</span>
    </Badge>
  );
}

export function StatusDot({ status = 'offline', size = 8 }) {
  const colors = {
    online: 'var(--accent-green)',
    offline: 'var(--text-muted)',
    warning: 'var(--accent-amber)',
    error: 'var(--accent-red)'
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

// ── 11. TOOLTIP COMPONENT ──
export function Tooltip({
  children,
  content,
  position = 'top', // 'top', 'bottom', 'left', 'right'
  style = {}
}) {
  return (
    <div className="eris-tooltip-wrapper">
      {children}
      {content && (
        <div 
          className="eris-tooltip" 
          style={{
            bottom: position === 'top' ? '120%' : 'unset',
            top: position === 'bottom' ? '120%' : 'unset',
            left: '50%',
            transform: 'translateX(-50%)',
            ...style
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
}

// ── 12. LOADING STATES & PROGRESS BARS ──
export function Spinner({ size = 18, color = 'currentColor', className = '' }) {
  return (
    <Loader2 
      size={size} 
      className={`eris-btn__spinner ${className}`} 
      style={{ color }} 
    />
  );
}

export function Skeleton({ width = '100%', height = 20, radius = 6, style = {} }) {
  return (
    <div 
      className="eris-shimmer"
      style={{
        width,
        height: typeof height === 'number' ? `${height}px` : height,
        borderRadius: `${radius}px`,
        ...style
      }}
    />
  );
}

export function ProgressBar({
  progress = 0, // 0 to 100
  color = '#8B5CF6',
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
          background: 'var(--bg-muted)', 
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
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>
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
      <Spinner size={size === 'sm' ? 24 : size === 'lg' ? 48 : 36} color="#8B5CF6" />
      <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>{message}</span>
    </div>
  );
}

// ── 13. EMPTY STATE ──
export function EmptyState({
  icon: Icon = Info,
  title = 'No items found',
  subtitle = 'Try refining your search or filter options',
  action
}) {
  return (
    <div className="eris-empty-state">
      <div className="eris-empty-state__icon">
        <Icon size={48} strokeWidth={1.5} />
      </div>
      <h3 className="eris-empty-state__title">{title}</h3>
      <p className="eris-empty-state__subtitle">{subtitle}</p>
      {action && <div style={{ marginTop: 8 }}>{action}</div>}
    </div>
  );
}

// ── 14. ERROR STATES ──
export function ErrorBanner({
  message = 'An unexpected error occurred. Please try again.',
  onDismiss,
  className = '',
  style = {}
}) {
  const [visible, setVisible] = useState(true);
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
          style={{ color: 'var(--accent-red)' }}
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

export function SectionLabel({ children, style = {} }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8, ...style }}>
      {children}
    </div>
  );
}

export function Divider({ style = {} }) {
  return <div style={{ height: 1, background: 'var(--border-sm)', ...style }} />;
}

// ── METRIC CARD & HERO CARD ──
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function MetricCard({ title, value, trend, trendLabel, subtitle, icon: Icon, color = 'accent', style = {} }) {
  const isUp = trend > 0;
  const isDown = trend < 0;
  const TrendIcon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;

  const colorMap = {
    accent:  { i: 'var(--accent)',   b: 'rgba(139, 92, 246, 0.15)',  border: 'rgba(139, 92, 246, 0.2)' },
    success: { i: 'var(--accent-green)',  b: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.2)' },
    warning: { i: 'var(--accent-amber)',  b: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.2)' },
    danger:  { i: 'var(--accent-red)',   b: 'rgba(239, 68, 68, 0.15)',  border: 'rgba(239, 68, 68, 0.2)' },
    info:    { i: '#3B82F6',     b: 'rgba(59, 130, 246, 0.15)',    border: 'rgba(59, 130, 246, 0.2)' },
  };
  const c = colorMap[color] || colorMap.accent;

  return (
    <div
      className="eris-card"
      style={{
        padding: '18px 20px',
        ...style,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
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
            color: isUp ? 'var(--accent-green)' : isDown ? 'var(--accent-red)' : 'var(--text-muted)',
            background: isUp ? 'rgba(16, 185, 129, 0.1)' : isDown ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-muted)'
          }}>
            <TrendIcon size={11} />
            {Math.abs(trend)}%
          </span>
        )}
        {(trendLabel || subtitle) && (
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{trendLabel || subtitle}</span>
        )}
      </div>
    </div>
  );
}

export function HeroCard({ title, value, trend, trendLabel, icon: Icon, gradient = 'linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%)', style = {} }) {
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
      boxShadow: '0 8px 32px rgba(0,0,0,0.35)',
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

