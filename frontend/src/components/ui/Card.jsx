import React from 'react';
import PropTypes from 'prop-types';
import '../../styles/eris-components.css';

/**
 * Card Component - Structured content containers
 * Variants: base, elevated, bordered
 */
export const Card = ({
  children,
  variant = 'base',
  title,
  titleRight,
  style = {},
  className = '',
  padding = 'var(--space-6)',
  onClick,
  ...props
}) => {
  const cardClass = [
    'eris-card',
    variant === 'elevated' ? 'eris-card--elevated' : '',
    variant === 'bordered' ? 'eris-card--bordered' : '',
    onClick ? 'cursor-pointer hover:shadow-lg' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div
      onClick={onClick}
      className={cardClass}
      style={{
        padding,
        transition: 'all var(--duration-normal) cubic-bezier(0.4, 0, 0.2, 1)',
        ...style
      }}
      {...props}
    >
      {(title || titleRight) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
          {title && (
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              {title}
            </h3>
          )}
          {titleRight && <div>{titleRight}</div>}
        </div>
      )}
      {children}
    </div>
  );
};

Card.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['base', 'elevated', 'bordered']),
  title: PropTypes.string,
  titleRight: PropTypes.node,
  style: PropTypes.object,
  className: PropTypes.string,
  padding: PropTypes.string,
  onClick: PropTypes.func,
};

export default Card;
