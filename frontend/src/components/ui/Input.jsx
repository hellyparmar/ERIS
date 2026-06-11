import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { X, CheckCircle, AlertCircle } from 'lucide-react';
import '../../styles/eris-components.css';

/**
 * Input Component - Form text/number fields
 * Custom border focus states, validations, helper texts
 */
export const Input = React.forwardRef(({
  label,
  value = '',
  onChange,
  placeholder = '',
  type = 'text',
  error,
  valid,
  helperText,
  disabled = false,
  required = false,
  iconLeft: IconLeft,
  iconRight: IconRight,
  onClear,
  id,
  className = '',
  style = {},
  ...props
}, ref) => {
  const [focused, setFocused] = useState(false);
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const errorId = `${inputId}-error`;
  const helperId = `${inputId}-helper`;

  const containerClass = [
    'eris-input-container',
    focused ? 'eris-input-container--focused' : '',
    valid ? 'eris-input-container--valid' : '',
    error ? 'eris-input-container--invalid' : '',
    disabled ? 'eris-input-container--disabled' : ''
  ].filter(Boolean).join(' ');

  return (
    <div className={`eris-input-wrapper ${className}`} style={style}>
      {label && (
        <label htmlFor={inputId} className="eris-input-label">
          {label} {required && <span style={{ color: 'var(--status-error)' }}>*</span>}
        </label>
      )}
      <div className={containerClass}>
        {IconLeft && (
          <span className="eris-input-icon eris-input-icon--left">
            <IconLeft size={16} />
          </span>
        )}
        <input
          ref={ref}
          id={inputId}
          type={type}
          value={value ?? ''}
          onChange={(e) => onChange && onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : helperText ? helperId : undefined}
          className="eris-input"
          {...props}
        />
        {onClear && value && !disabled && (
          <button
            type="button"
            onClick={onClear}
            className="eris-input-clear"
            aria-label="Clear input"
          >
            <X size={14} />
          </button>
        )}
        {valid && !error && (
          <span className="eris-input-icon eris-input-icon--right" style={{ color: 'var(--status-success)' }}>
            <CheckCircle size={16} />
          </span>
        )}
        {error && (
          <span className="eris-input-icon eris-input-icon--right" style={{ color: 'var(--status-error)' }}>
            <AlertCircle size={16} />
          </span>
        )}
        {!valid && !error && IconRight && (
          <span className="eris-input-icon eris-input-icon--right">
            <IconRight size={16} />
          </span>
        )}
      </div>
      {error && (
        <span id={errorId} className="eris-input-error" role="alert">
          {error}
        </span>
      )}
      {!error && helperText && (
        <span id={helperId} className="eris-input-helper">
          {helperText}
        </span>
      )}
    </div>
  );
});

Input.displayName = 'Input';

Input.propTypes = {
  label: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
  type: PropTypes.string,
  error: PropTypes.string,
  valid: PropTypes.bool,
  helperText: PropTypes.string,
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  iconLeft: PropTypes.elementType,
  iconRight: PropTypes.elementType,
  onClear: PropTypes.func,
  id: PropTypes.string,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default Input;
