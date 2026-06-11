import React from 'react';
import PropTypes from 'prop-types';
import { X } from 'lucide-react';
import '../../styles/eris-components.css';

/**
 * Badge Component - Pill statuses, labels, metadata markers
 * Variants: success, warning, error, info, neutral
 * Sizes: sm, md, lg
 */
export const Badge = ({
  children,
  label,
  variant = 'neutral',
  size = 'md',
  icon: Icon,
  onDismiss,
  className = '',
  style = {},
  ...props
}) => {
  return (
    <span
      className={`eris-badge eris-badge--${variant} eris-badge--${size} ${className}`}
      style={{
        transition: 'all var(--duration-fast) ease-out',
        ...style
      }}
      {...props}
    >
      {Icon && <Icon size={size === 'sm' ? 10 : size === 'lg' ? 14 : 12} style={{ flexShrink: 0 }} />}
      <span>{children || label}</span>
      {onDismiss && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDismiss();
          }}
          className="eris-badge__close"
          aria-label="Dismiss badge"
        >
          <X size={10} />
        </button>
      )}
    </span>
  );
};

Badge.propTypes = {
  children: PropTypes.node,
  label: PropTypes.string,
  variant: PropTypes.oneOf(['success', 'warning', 'error', 'info', 'neutral']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  icon: PropTypes.elementType,
  onDismiss: PropTypes.func,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default Badge;
