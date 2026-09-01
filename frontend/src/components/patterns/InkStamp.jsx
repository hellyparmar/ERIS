import React from 'react';

export default function InkStamp({ text = 'GST RESOLVED', status = 'success', size = 'md' }) {
  // Determine colors based on status
  let color = 'var(--signal-sage, #6FA287)';
  let bg = 'rgba(111, 162, 135, 0.08)';
  
  if (status === 'warning') {
    color = 'var(--signal-amber, #E8A33D)';
    bg = 'rgba(232, 163, 61, 0.08)';
  } else if (status === 'danger' || status === 'critical' || status === 'fail') {
    color = 'var(--signal-coral, #FF6B5E)';
    bg = 'rgba(255, 107, 94, 0.08)';
  } else if (status === 'info') {
    color = 'var(--signal-cyan, #2DD4BF)';
    bg = 'rgba(45, 212, 191, 0.08)';
  }

  // Sizing definitions
  const padding = size === 'sm' ? '4px 10px' : size === 'lg' ? '12px 24px' : '8px 18px';
  const fontSize = size === 'sm' ? '10px' : size === 'lg' ? '16px' : '13px';
  const borderWidth = size === 'sm' ? '2px' : '3px';

  return (
    <div style={{
      display: 'inline-block',
      padding,
      fontFamily: 'var(--font-display, "Space Grotesk")',
      fontSize,
      fontWeight: 800,
      textTransform: 'uppercase',
      letterSpacing: '0.15em',
      color,
      background: bg,
      border: `${borderWidth} double ${color}`,
      borderRadius: '4px',
      transform: 'rotate(-8deg)',
      userSelect: 'none',
      mixBlendMode: 'screen', // authentic ink overlay feel on dark mode
      opacity: 0.85,
      textAlign: 'center',
      boxShadow: `0 0 1px ${color}`,
      textShadow: `0 0 1px ${color}`,
      maxWidth: 'fit-content'
    }}>
      <div style={{
        border: `1px solid ${color}`,
        padding: '2px 8px',
        borderRadius: '2px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '2px'
      }}>
        <span>{text}</span>
        <span style={{
          fontSize: '7px',
          letterSpacing: '0.25em',
          fontWeight: 500,
          opacity: 0.7,
          fontFamily: 'var(--font-mono, monospace)',
          marginTop: '2px'
        }}>
          SECURE AUDIT KEY: E-882
        </span>
      </div>
    </div>
  );
}
