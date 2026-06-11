import React from 'react';
import PropTypes from 'prop-types';
import { Loader2 } from 'lucide-react';
import '../../styles/eris-components.css';

/**
 * Spinner Component - Standardised rotating progress indicators
 * Sizes: sm, md, lg
 */
export const Spinner = ({
  size = 'md',
  color = 'var(--accent-violet)',
  className = '',
  style = {},
  ...props
}) => {
  const pixelSizes = {
    sm: 16,
    md: 24,
    lg: 40
  };

  const dim = pixelSizes[size] || pixelSizes.md;

  return (
    <Loader2
      size={dim}
      className={`eris-btn__spinner ${className}`}
      style={{
        color,
        animationDuration: '0.8s',
        ...style
      }}
      {...props}
    />
  );
};

Spinner.propTypes = {
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  color: PropTypes.string,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default Spinner;
