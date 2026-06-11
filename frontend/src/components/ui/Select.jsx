import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { ChevronDown, Check, Search } from 'lucide-react';
import '../../styles/eris-components.css';

/**
 * Custom Styled Select Dropdown component
 * Meets accessibility standards for keyboard interactions and ARIA roles.
 */
export const Select = ({
  label,
  value,
  onChange,
  options = [],
  placeholder = 'Select an option',
  disabled = false,
  required = false,
  error,
  searchable = false,
  className = '',
  style = {},
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const wrapperRef = useRef(null);
  const searchInputRef = useRef(null);
  const triggerRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = options.find((o) => o.value === value);
  const filteredOptions = searchable
    ? options.filter((o) => o.label.toLowerCase().includes(searchTerm.toLowerCase()))
    : options;

  useEffect(() => {
    if (isOpen) {
      setFocusedIndex(-1);
      if (searchable && searchInputRef.current) {
        setTimeout(() => searchInputRef.current.focus(), 50);
      }
    }
  }, [isOpen, searchable]);

  const handleKeyDown = (e) => {
    if (disabled) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else {
        setFocusedIndex((prev) => (prev < filteredOptions.length - 1 ? prev + 1 : 0));
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (isOpen) {
        setFocusedIndex((prev) => (prev > 0 ? prev - 1 : filteredOptions.length - 1));
      }
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else if (focusedIndex >= 0 && focusedIndex < filteredOptions.length) {
        onChange && onChange(filteredOptions[focusedIndex].value);
        setIsOpen(false);
        setSearchTerm('');
        triggerRef.current?.focus();
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      triggerRef.current?.focus();
    }
  };

  return (
    <div className={`eris-input-wrapper ${className}`} style={style} ref={wrapperRef}>
      {label && (
        <span className="eris-input-label">
          {label} {required && <span style={{ color: 'var(--status-error)' }}>*</span>}
        </span>
      )}
      <div className="eris-select-wrapper" onKeyDown={handleKeyDown}>
        <button
          ref={triggerRef}
          type="button"
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          onClick={() => setIsOpen(!isOpen)}
          className="eris-select-trigger"
          style={{
            borderColor: error ? 'var(--status-error)' : isOpen ? 'var(--accent-violet)' : 'var(--border-subtle)',
            boxShadow: isOpen ? '0 0 0 3px rgba(139, 92, 246, 0.15)' : 'none',
          }}
        >
          <span>{selectedOption ? selectedOption.label : placeholder}</span>
          <ChevronDown
            size={16}
            className={`eris-select-trigger__chevron ${isOpen ? 'eris-select-trigger__chevron--open' : ''}`}
          />
        </button>

        {isOpen && (
          <div className="eris-select-dropdown" role="listbox">
            {searchable && (
              <div style={{ display: 'flex', alignItems: 'center', padding: '4px 6px', borderBottom: '1px solid var(--border-subtle)' }} onClick={(e) => e.stopPropagation()}>
                <Search size={14} style={{ color: 'var(--text-tertiary)', marginRight: 6 }} />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 4px',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-primary)',
                    fontSize: '12.5px',
                    outline: 'none',
                  }}
                />
              </div>
            )}
            <div style={{ maxHeight: '180px', overflowY: 'auto', marginTop: searchable ? '4px' : '0' }}>
              {filteredOptions.length === 0 ? (
                <div style={{ padding: '8px 12px', fontSize: '13px', color: 'var(--text-tertiary)', textAlign: 'center' }}>
                  No options found
                </div>
              ) : (
                filteredOptions.map((opt, index) => {
                  const isSelected = opt.value === value;
                  const isFocused = index === focusedIndex;
                  return (
                    <div
                      key={opt.value}
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => {
                        onChange && onChange(opt.value);
                        setIsOpen(false);
                        setSearchTerm('');
                        triggerRef.current?.focus();
                      }}
                      className={`eris-select-option ${isSelected ? 'eris-select-option--selected' : ''}`}
                      style={{
                        background: isFocused ? 'var(--surface-tertiary)' : 'transparent',
                      }}
                    >
                      <span>{opt.label}</span>
                      {isSelected && <Check size={14} />}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
      {error && <span className="eris-input-error">{error}</span>}
    </div>
  );
};

Select.propTypes = {
  label: PropTypes.string,
  value: PropTypes.any,
  onChange: PropTypes.func,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      value: PropTypes.any.isRequired,
    })
  ).isRequired,
  placeholder: PropTypes.string,
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  error: PropTypes.string,
  searchable: PropTypes.bool,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default Select;
