import React from 'react';

/**
 * DataCard Component
 * General-purpose card for displaying charts, tables, or other content
 * 
 * @param {Object} props
 * @param {string} props.title - Card title
 * @param {string} props.subtitle - Optional subtitle
 * @param {Object} props.actionButton - Optional action button {label: string, onClick: function, variant?: 'primary'|'secondary'}
 * @param {React.ReactNode} props.children - Card content (charts, tables, etc.)
 * @returns {JSX.Element}
 */
export default function DataCard({
  title,
  subtitle,
  actionButton,
  children,
}) {
  const handleButtonClick = actionButton?.onClick || (() => {});
  const buttonVariant = actionButton?.variant || 'primary';

  const buttonStyle = {
    padding: '6px 14px',
    borderRadius: '8px',
    border: 'none',
    fontSize: '13px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontFamily: "'Inter', sans-serif",
  };

  const primaryButtonStyle = {
    ...buttonStyle,
    backgroundColor: 'var(--accent-teal)',
    color: 'white',
  };

  const secondaryButtonStyle = {
    ...buttonStyle,
    backgroundColor: 'var(--bg-card)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-light)',
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: '12px',
        padding: '20px',
        boxShadow: 'var(--shadow-card)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      {(title || actionButton) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            marginBottom: '16px',
            gap: '16px',
          }}
        >
          {/* Title Section */}
          <div style={{ flex: 1 }}>
            {title && (
              <h3
                style={{
                  fontSize: '14px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  margin: '0 0 4px 0',
                }}
              >
                {title}
              </h3>
            )}
            {subtitle && (
              <p
                style={{
                  fontSize: '12px',
                  fontWeight: 400,
                  color: 'var(--text-muted)',
                  margin: 0,
                }}
              >
                {subtitle}
              </p>
            )}
          </div>

          {/* Action Button */}
          {actionButton && (
            <button
              onClick={handleButtonClick}
              style={buttonVariant === 'primary' ? primaryButtonStyle : secondaryButtonStyle}
              onMouseEnter={(e) => {
                if (buttonVariant === 'primary') {
                  e.currentTarget.style.backgroundColor = 'var(--accent-teal-light)';
                } else {
                  e.currentTarget.style.backgroundColor = '#F3F4F6';
                }
              }}
              onMouseLeave={(e) => {
                if (buttonVariant === 'primary') {
                  e.currentTarget.style.backgroundColor = 'var(--accent-teal)';
                } else {
                  e.currentTarget.style.backgroundColor = 'var(--bg-card)';
                }
              }}
            >
              {actionButton.label}
            </button>
          )}
        </div>
      )}

      {/* Content */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
        }}
      >
        {children}
      </div>
    </div>
  );
}
