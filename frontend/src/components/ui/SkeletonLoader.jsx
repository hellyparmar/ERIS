import React from 'react';
import PropTypes from 'prop-types';
import '../../styles/eris-components.css';

/**
 * SkeletonLoader Component - Content loading placeholders
 * Shapes: text, avatar, card, table
 */
export const SkeletonLoader = ({
  variant = 'text',
  count = 1,
  width = '100%',
  height,
  radius,
  className = '',
  style = {},
  ...props
}) => {
  const defaultHeight = {
    text: '16px',
    avatar: '40px',
    card: '180px',
    table: '48px'
  };

  const defaultRadius = {
    text: '9999px',
    avatar: '50%',
    card: '12px',
    table: '6px'
  };

  const finalHeight = height || defaultHeight[variant] || '16px';
  const finalRadius = radius || defaultRadius[variant] || '6px';
  const finalWidth = variant === 'avatar' ? finalHeight : width;

  return (
    <>
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className={`eris-shimmer ${className}`}
          style={{
            width: finalWidth,
            height: finalHeight,
            borderRadius: finalRadius,
            marginBottom: count > 1 && idx < count - 1 ? 'var(--space-2)' : '0',
            transition: 'all var(--duration-fast) ease-out',
            ...style
          }}
          {...props}
        />
      ))}
    </>
  );
};

SkeletonLoader.propTypes = {
  variant: PropTypes.oneOf(['text', 'avatar', 'card', 'table']),
  count: PropTypes.number,
  width: PropTypes.string,
  height: PropTypes.string,
  radius: PropTypes.string,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default SkeletonLoader;
