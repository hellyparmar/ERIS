import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { X } from 'lucide-react';
import '../../styles/eris-components.css';

/**
 * Modal Component - Centered or slide-out overlay drawers
 * Accessibility features: ESC key navigation, backdrop close, title focus
 */
export const Modal = ({
  open,
  onClose,
  title,
  children,
  footer,
  width = 520,
  layout = 'center', // 'center' or 'drawer'
  className = '',
  style = {},
  ...props
}) => {
  const modalRef = useRef(null);

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && open) {
        onClose && onClose();
      }
    }
    if (open) {
      window.addEventListener('keydown', handleKeyDown);
      // Prevent body scrolling
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [open, onClose]);

  if (!open) return null;

  const modalStyle = {
    maxWidth: layout === 'drawer' ? '400px' : `${width}px`,
    width: '100%',
    height: layout === 'drawer' ? '100%' : 'auto',
    borderRadius: layout === 'drawer' ? '0' : '16px',
    marginLeft: layout === 'drawer' ? 'auto' : 'unset',
    marginRight: '0',
    animation: layout === 'drawer' 
      ? 'eris-slide-in-right var(--duration-normal) cubic-bezier(0.16, 1, 0.3, 1)' 
      : 'eris-scale-in var(--duration-normal) cubic-bezier(0.34, 1.56, 0.64, 1)',
    ...style
  };

  return (
    <div
      className="eris-modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose && onClose()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      style={{
        alignItems: layout === 'drawer' ? 'stretch' : 'center',
        justifyContent: layout === 'drawer' ? 'flex-end' : 'center',
        padding: layout === 'drawer' ? '0' : 'var(--space-4)',
        transition: 'opacity var(--duration-fast) ease-out',
      }}
      {...props}
    >
      <div
        ref={modalRef}
        className={`eris-modal ${className}`}
        style={modalStyle}
      >
        <div className="eris-modal__header">
          <span id="modal-title" className="eris-modal__title">{title}</span>
          <button
            type="button"
            onClick={onClose}
            className="eris-modal__close"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>
        <div className="eris-modal__body" style={{ flex: 1 }}>
          {children}
        </div>
        {footer && <div className="eris-modal__footer">{footer}</div>}
      </div>
    </div>
  );
};

Modal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  footer: PropTypes.node,
  width: PropTypes.number,
  layout: PropTypes.oneOf(['center', 'drawer']),
  className: PropTypes.string,
  style: PropTypes.object,
};

export default Modal;
