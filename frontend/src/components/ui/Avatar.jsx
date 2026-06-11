import React from 'react';
import PropTypes from 'prop-types';
import '../../styles/eris-components.css';

/**
 * Avatar Component - Circular images/initials with status overlays
 * Sizes: xs, sm, md, lg, xl
 * Status: online, offline, away
 */
export const Avatar = ({
  src,
  name = '',
  size = 'md',
  status,
  style = {},
  className = '',
  tooltip = true,
  ...props
}) => {
  const initials = name
    ? name.split(' ').map((n) => n[0]).join('').substring(0, 2).toUpperCase()
    : '??';

  const avatarColors = [
    'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
    'linear-gradient(135deg, #10B981 0%, #059669 100%)',
    'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
    'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)',
    'linear-gradient(135deg, #EC4899 0%, #DB2777 100%)',
  ];

  const colorIndex = name
    ? name.charCodeAt(0) % avatarColors.length
    : 0;

  const bgGradient = avatarColors[colorIndex];

  return (
    <div className="eris-tooltip-wrapper" {...props}>
      <div
        className={`eris-avatar eris-avatar--${size} ${className}`}
        style={{
          background: src ? 'transparent' : bgGradient,
          transition: 'transform var(--duration-fast) ease-out',
          ...style
        }}
      >
        {src ? (
          <img
            src={src}
            alt={name}
            className={`eris-avatar eris-avatar--${size}`}
            style={{ border: 'none' }}
          />
        ) : (
          <span>{initials}</span>
        )}
        {status && (
          <span className={`eris-avatar__status eris-avatar__status--${status}`} />
        )}
      </div>
      {tooltip && name && <div className="eris-tooltip">{name}</div>}
    </div>
  );
};

Avatar.propTypes = {
  src: PropTypes.string,
  name: PropTypes.string,
  size: PropTypes.oneOf(['xs', 'sm', 'md', 'lg', 'xl']),
  status: PropTypes.oneOf(['online', 'offline', 'away']),
  tooltip: PropTypes.bool,
  style: PropTypes.object,
  className: PropTypes.string,
};

export default Avatar;
