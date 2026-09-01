export default function HeatCanvas({ title, subtitle, loading, error, empty, emptyMessage, onRetry, children, height = 280 }) {
  if (error) {
    return (
      <div className="heat-canvas">
        {title && <div className="heat-canvas-title">{title}</div>}
        <div className="error-panel">
          <div className="error-title">Failed to load chart</div>
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
      <div className="heat-canvas">
        {title && <div className="heat-canvas-title">{title}</div>}
        <div className="skeleton-chart">
          <div className="shimmer-line skeleton-shimmer" />
          <div className="shimmer-line skeleton-shimmer" />
          <div className="shimmer-line skeleton-shimmer" />
        </div>
      </div>
    );
  }

  if (empty) {
    return (
      <div className="heat-canvas">
        {title && <div className="heat-canvas-title">{title}</div>}
        <div className="empty-state">
          <svg className="empty-state-icon" viewBox="0 0 24 24">
            <path d="M3 3v18h18" />
            <path d="M18.7 8l-5.1 5.2-2.8-2.7-4.8 4.8" />
          </svg>
          <div className="empty-state-title">{emptyMessage || 'No data yet'}</div>
          <div className="empty-state-message">Data will appear once transactions are recorded.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="heat-canvas">
      {title && <div className="heat-canvas-title">{title}</div>}
      <div style={{ height }}>
        {children}
      </div>
    </div>
  );
}
