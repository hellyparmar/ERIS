import React from 'react';
import PropTypes from 'prop-types';
import '../../styles/eris-components.css';

/**
 * Button Component - Standardised across ERIS
 * Supports variants: primary, secondary, danger, ghost
 * Sizes: sm, md, lg
 */
export const Button = React.forwardRef(({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon: Icon,
  iconRight: IconRight,
  type = 'button',
  className = '',
  style = {},
  'aria-label': ariaLabel,
  ...props
}, ref) => {
  return (
    <button
      ref={ref}
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      aria-busy={loading}
      aria-label={ariaLabel || (typeof children === 'string' ? children : undefined)}
      className={`eris-btn eris-btn--${variant} eris-btn--${size} ${className}`}
      style={{
        transition: 'all var(--duration-fast) cubic-bezier(0.4, 0, 0.2, 1)',
        ...style
      }}
      {...props}
    >
      {loading && <div className="eris-btn__spinner" ref={null} />}
      {!loading && Icon && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} />}
      <span style={{ opacity: loading ? 0 : 1, display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
        {children}
      </span>
      {!loading && IconRight && <IconRight size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} />}
    </button>
  );
});

Button.displayName = 'Button';

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger', 'ghost']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  icon: PropTypes.elementType,
  iconRight: PropTypes.elementType,
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
  className: PropTypes.string,
  style: PropTypes.object,
  'aria-label': PropTypes.string,
};

export default Button;
