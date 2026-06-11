import React, { useState } from 'react';
import PropTypes from 'prop-types';
import '../../styles/eris-components.css';

/**
 * Tooltip Component - Interactive info popovers on hover/focus
 * Positions: top, bottom, left, right
 */
export const Tooltip = ({
  children,
  content,
  position = 'top',
  style = {},
  ...props
}) => {
  const [isVisible, setIsVisible] = useState(false);

  const getPositionStyle = () => {
    switch (position) {
      case 'bottom':
        return {
          top: '120%',
          bottom: 'unset',
          left: '50%',
          transform: 'translateX(-50%)',
        };
      case 'left':
        return {
          right: '120%',
          left: 'unset',
          top: '50%',
          bottom: 'unset',
          transform: 'translateY(-50%)',
        };
      case 'right':
        return {
          left: '120%',
          right: 'unset',
          top: '50%',
          bottom: 'unset',
          transform: 'translateY(-50%)',
        };
      case 'top':
      default:
        return {
          bottom: '120%',
          top: 'unset',
          left: '50%',
          transform: 'translateX(-50%)',
        };
    }
  };

  return (
    <div
      className="eris-tooltip-wrapper"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
      {...props}
    >
      {children}
      {content && (
        <div
          className="eris-tooltip"
          role="tooltip"
          style={{
            opacity: isVisible ? 1 : 0,
            pointerEvents: 'none',
            ...getPositionStyle(),
            ...style,
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
};

Tooltip.propTypes = {
  children: PropTypes.node.isRequired,
  content: PropTypes.node.isRequired,
  position: PropTypes.oneOf(['top', 'bottom', 'left', 'right']),
  style: PropTypes.object,
};

export default Tooltip;
