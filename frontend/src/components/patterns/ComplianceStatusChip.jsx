import React from 'react';

export default function ComplianceStatusChip({ status = 'success', level = 'L2' }) {
  // Map status to signal colors & labels
  let dotColor = 'var(--signal-sage, #6FA287)';
  let bgDim = 'var(--signal-sage-dim, rgba(111,162,135,0.12))';
  let label = `${level} Compliance Verified`;

  if (status === 'warning') {
    dotColor = 'var(--signal-amber, #E8A33D)';
    bgDim = 'var(--signal-amber-dim, rgba(232,163,61,0.12))';
    label = `${level} Verification Pending`;
  } else if (status === 'critical' || status === 'danger') {
    dotColor = 'var(--signal-coral, #FF6B5E)';
    bgDim = 'var(--signal-coral-dim, rgba(255,107,94,0.12))';
    label = `${level} Compliance Breach`;
  } else if (status === 'info') {
    dotColor = 'var(--signal-cyan, #2DD4BF)';
    bgDim = 'var(--signal-cyan-dim, rgba(45,212,191,0.12))';
    label = `${level} Audit In Progress`;
  }

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      padding: '4px 10px',
      borderRadius: 'var(--r-sm, 6px)',
      background: 'var(--surface-raised, #21262E)',
      border: '1px solid var(--border, rgba(154,184,196,0.14))',
      fontFamily: 'var(--font-mono, monospace)',
      fontSize: '11px',
      fontWeight: 500,
      color: 'var(--text-secondary, #9AA8B2)',
      userSelect: 'none',
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
    }}>
      {/* Small pulsing status dot */}
      <span style={{
        width: '6px',
        height: '6px',
        borderRadius: '50%',
        background: dotColor,
        boxShadow: `0 0 8px ${dotColor}`,
        animation: 'compliance-pulse 2s infinite ease-in-out'
      }} />

      <span style={{
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        color: 'var(--text-primary, #E7ECEF)'
      }}>
        {label}
      </span>

      <span style={{
        color: 'var(--text-tertiary, #67737D)',
        fontSize: '10px',
        borderLeft: '1px solid var(--border, rgba(154,184,196,0.14))',
        paddingLeft: '8px'
      }}>
        GST-LOK
      </span>

      <style>{`
        @keyframes compliance-pulse {
          0%, 100% { opacity: 0.6; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.2); }
        }
      `}</style>
    </div>
  );
}
