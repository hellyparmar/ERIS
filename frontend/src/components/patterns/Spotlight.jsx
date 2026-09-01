import { useMemo } from 'react';

const fmtValue = (val) => {
  if (typeof val === 'number') {
    return '₹' + Number(val).toLocaleString('en-IN');
  }
  if (!val && val !== 0) return '';
  return String(val);
};

export default function Spotlight({
  title,
  items = [],
  loading,
  error,
  emptyMessage,
  onRetry,
  heroLabel,
  heroValue,
  secondaries = []
}) {
  // Unify standard and alternative prop configurations
  const normalizedItems = useMemo(() => {
    if (items && items.length > 0) {
      return items.map((it, idx) => ({
        label: it.name || it.label || `Item ${idx + 1}`,
        value: it.revenue !== undefined ? it.revenue : it.value,
        rank: it.rank || (idx + 1)
      }));
    }
    if (heroValue !== undefined && heroValue !== null) {
      return [
        { label: heroLabel || 'Top Performer', value: heroValue, rank: 1 },
        ...(secondaries || []).map((sec, idx) => ({
          label: sec.label || `Secondary ${idx + 1}`,
          value: sec.value,
          rank: idx + 2
        }))
      ];
    }
    return [];
  }, [items, heroLabel, heroValue, secondaries]);

  if (error) {
    return (
      <div className="spotlight" style={{ marginBottom: 'var(--sp-6)' }}>
        {title && <div className="heat-canvas-title" style={{ textAlign: 'left' }}>{title}</div>}
        <div className="error-panel">
          <div className="error-title">Failed to load spotlight</div>
          <div className="error-message">{error}</div>
          {onRetry && (
            <button className="error-retry" onClick={onRetry}>Retry</button>
          )}
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="spotlight" style={{ marginBottom: 'var(--sp-6)' }}>
        {title && <div className="heat-canvas-title" style={{ textAlign: 'left' }}>{title}</div>}
        <div className="skeleton-chart">
          <div className="shimmer-line skeleton-shimmer" />
          <div className="shimmer-line skeleton-shimmer" />
          <div className="shimmer-line skeleton-shimmer" />
        </div>
      </div>
    );
  }

  if (normalizedItems.length === 0) {
    return (
      <div className="spotlight" style={{ marginBottom: 'var(--sp-6)' }}>
        {title && <div className="heat-canvas-title" style={{ textAlign: 'left' }}>{title}</div>}
        <div className="empty-state">
          <svg className="empty-state-icon" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <div className="empty-state-title">{emptyMessage || 'No spotlight items yet'}</div>
          <div className="empty-state-message">Top performing items will display here.</div>
        </div>
      </div>
    );
  }

  // 1 Item: Full-width hero
  if (normalizedItems.length === 1) {
    return (
      <div className="spotlight" style={{ marginBottom: 'var(--sp-6)' }}>
        {title && <div className="heat-canvas-title" style={{ textAlign: 'left' }}>{title}</div>}
        <div style={{ padding: '24px 0', textAlign: 'center' }}>
          <div className="spotlight-hero">
            {fmtValue(normalizedItems[0].value)}
          </div>
          <div style={{ fontFamily: 'var(--font-body)', fontSize: 13, marginTop: 8, color: 'var(--color-ink-muted)' }}>
            {normalizedItems[0].label}
          </div>
        </div>
      </div>
    );
  }

  // 2 Items: 60/40 Split
  if (normalizedItems.length === 2) {
    return (
      <div className="spotlight" style={{ marginBottom: 'var(--sp-6)' }}>
        {title && <div className="heat-canvas-title" style={{ textAlign: 'left' }}>{title}</div>}
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '24px', alignItems: 'center', padding: '24px 0' }}>
          <div style={{ textAlign: 'center' }}>
            <div className="spotlight-hero">
              {fmtValue(normalizedItems[0].value)}
            </div>
            <div style={{ fontFamily: 'var(--font-body)', fontSize: 13, marginTop: 8, color: 'var(--color-ink-muted)' }}>
              {normalizedItems[0].label}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 24, color: 'var(--color-ink)', borderBottom: '1px solid var(--color-divider)', display: 'inline-block', paddingBottom: 4, lineHeight: 1 }}>
              {fmtValue(normalizedItems[1].value)}
            </div>
            <div style={{ fontFamily: 'var(--font-body)', fontSize: 12, marginTop: 6, color: 'var(--color-ink-muted)' }}>
              {normalizedItems[1].label}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 3+ Items: Podium heights & list of secondaries
  return (
    <div className="spotlight" style={{ marginBottom: 'var(--sp-6)' }}>
      {title && <div className="heat-canvas-title" style={{ textAlign: 'left' }}>{title}</div>}
      <div style={{ padding: '24px 0', textAlign: 'center' }}>
        <div className="spotlight-hero">
          {fmtValue(normalizedItems[0].value)}
        </div>
        <div style={{ fontFamily: 'var(--font-body)', fontSize: 13, marginTop: 8, color: 'var(--color-ink-muted)', marginBottom: 24 }}>
          {normalizedItems[0].label}
        </div>

        <div className="spotlight-secondaries">
          {normalizedItems.slice(1).map((sec, idx) => (
            <div key={idx} style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 600 }}>{fmtValue(sec.value)}</div>
              <div style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-ink-muted)', marginTop: 4 }}>
                {sec.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
