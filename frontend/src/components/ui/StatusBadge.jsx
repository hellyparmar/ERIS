import React from 'react';
import PropTypes from 'prop-types';
import { CheckCircle, Info, AlertTriangle, Loader2 } from 'lucide-react';
import '../../styles/eris-components.css';

/**
 * StatusBadge Component - Highly distinct badge for operation/transaction status
 * Supports states: paid, success, pending, warning, failed, error, processing
 */
export const StatusBadge = ({
  status = 'pending',
  text = '',
  pulse = false,
  className = '',
  style = {},
  ...props
}) => {
  const statusConfig = {
    paid: { color: 'var(--status-success)', bg: 'rgba(34, 197, 94, 0.12)', border: 'rgba(34, 197, 94, 0.25)', label: 'Paid', icon: CheckCircle },
    success: { color: 'var(--status-success)', bg: 'rgba(34, 197, 94, 0.12)', border: 'rgba(34, 197, 94, 0.25)', label: 'Success', icon: CheckCircle },
    pending: { color: 'var(--status-warning)', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.25)', label: 'Pending', icon: Info },
    warning: { color: 'var(--status-warning)', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.25)', label: 'Warning', icon: Info },
    failed: { color: 'var(--status-error)', bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.25)', label: 'Failed', icon: AlertTriangle },
    error: { color: 'var(--status-error)', bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.25)', label: 'Error', icon: AlertTriangle },
    processing: { color: 'var(--status-info)', bg: 'rgba(59, 130, 246, 0.12)', border: 'rgba(59, 130, 246, 0.25)', label: 'Processing', icon: Loader2 }
  };

  const config = statusConfig[status.toLowerCase()] || statusConfig.pending;
  const IconComponent = config.icon;
  const isProcessing = status.toLowerCase() === 'processing';

  return (
    <span
      className={`eris-badge ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '5px 12px',
        fontSize: '11px',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        borderRadius: '9999px',
        color: config.color,
        background: config.bg,
        border: `1px solid ${config.border}`,
        animation: pulse ? 'eris-pulse 2s infinite ease-in-out' : isProcessing ? 'none' : 'eris-scale-in 200ms ease-out',
        ...style
      }}
      {...props}
    >
      <IconComponent 
        size={12} 
        className={isProcessing ? 'eris-btn__spinner' : ''} 
        style={{ animationDuration: isProcessing ? '0.8s' : '0s' }}
      />
      <span>{text || config.label}</span>
    </span>
  );
};

StatusBadge.propTypes = {
  status: PropTypes.oneOf(['paid', 'success', 'pending', 'warning', 'failed', 'error', 'processing']),
  text: PropTypes.string,
  pulse: PropTypes.bool,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default StatusBadge;
