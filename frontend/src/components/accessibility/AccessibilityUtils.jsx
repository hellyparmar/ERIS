"""
WCAG 2.1 Accessibility Utilities
Comprehensive accessibility support for R - DIOS frontend
"""

import React from 'react';

// ============================================================
// ACCESSIBILITY CONTEXT
// ============================================================

const AccessibilityContext = React.createContext({
    reducedMotion: false,
    highContrast: false,
    fontSize: 'normal',
    screenReader: false,
    setFontSize: () => { },
    setHighContrast: () => { },
});

export const AccessibilityProvider = ({ children }) => {
    const [reducedMotion, setReducedMotion] = React.useState(false);
    const [highContrast, setHighContrast] = React.useState(false);
    const [fontSize, setFontSize] = React.useState('normal');
    const [screenReader, setScreenReader] = React.useState(false);

    React.useEffect(() => {
        // Check system preferences
        const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        const contrastQuery = window.matchMedia('(prefers-contrast: high)');

        setReducedMotion(motionQuery.matches);
        setHighContrast(contrastQuery.matches);

        // Listen for changes
        const handleMotionChange = (e) => setReducedMotion(e.matches);
        const handleContrastChange = (e) => setHighContrast(e.matches);

        motionQuery.addEventListener('change', handleMotionChange);
        contrastQuery.addEventListener('change', handleContrastChange);

        return () => {
            motionQuery.removeEventListener('change', handleMotionChange);
            contrastQuery.removeEventListener('change', handleContrastChange);
        };
    }, []);

    const value = {
        reducedMotion,
        highContrast,
        fontSize,
        screenReader,
        setFontSize,
        setHighContrast: () => setHighContrast(!highContrast),
    };

    return (
        <AccessibilityContext.Provider value={value}>
            {children}
        </AccessibilityContext.Provider>
    );
};

export const useAccessibility = () => React.useContext(AccessibilityContext);

// ============================================================
// SKIP LINKS (WCAG 2.4.1)
// ============================================================

export const SkipLinks = () => {
    return (
        <nav aria-label="Skip navigation" className="skip-links">
            <a href="#main-content" className="skip-link">
                Skip to main content
            </a>
            <a href="#main-navigation" className="skip-link">
                Skip to navigation
            </a>
            <a href="#search" className="skip-link">
                Skip to search
            </a>
        </nav>
    );
};

// ============================================================
// FOCUS TRAP (FOR MODALS)
// ============================================================

export const useFocusTrap = (isActive) => {
    const containerRef = React.useRef(null);

    React.useEffect(() => {
        if (!isActive || !containerRef.current) return;

        const container = containerRef.current;
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        const handleKeyDown = (e) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
        };

        // Focus first element
        firstElement?.focus();

        container.addEventListener('keydown', handleKeyDown);
        return () => container.removeEventListener('keydown', handleKeyDown);
    }, [isActive]);

    return containerRef;
};

// ============================================================
// SCREEN READER ONLY TEXT (WCAG 1.1.1)
// ============================================================

export const ScreenReaderOnly = ({ children }) => (
    <span className="sr-only" style={{
        position: 'absolute',
        width: '1px',
        height: '1px',
        padding: '0',
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        border: '0',
    }}>
        {children}
    </span>
);

// ============================================================
// LIVE REGION (WCAG 4.1.3)
// ============================================================

export const LiveRegion = ({ message, type = 'polite' }) => {
    return (
        <div
            role="status"
            aria-live={type}
            aria-atomic="true"
            className="sr-only"
            style={{
                position: 'absolute',
                width: '1px',
                height: '1px',
                padding: '0',
                margin: '-1px',
                overflow: 'hidden',
                clip: 'rect(0, 0, 0, 0)',
                whiteSpace: 'nowrap',
                border: '0',
            }}
        >
            {message}
        </div>
    );
};

// Custom hook for announcements
export const useAnnounce = () => {
    const [message, setMessage] = React.useState('');

    const announce = (text, delay = 100) => {
        setMessage('');
        setTimeout(() => setMessage(text), delay);
    };

    return { message, announce };
};

// ============================================================
// ACCESSIBLE BUTTON (WCAG 2.1.1, 4.1.2)
// ============================================================

export const AccessibleButton = ({
    children,
    onClick,
    disabled = false,
    loading = false,
    ariaLabel,
    ariaExpanded,
    ariaControls,
    ariaPressed,
    ...props
}) => {
    const { reducedMotion } = useAccessibility();

    return (
        <button
            onClick={onClick}
            disabled={disabled || loading}
            aria-label={ariaLabel}
            aria-expanded={ariaExpanded}
            aria-controls={ariaControls}
            aria-pressed={ariaPressed}
            aria-busy={loading}
            aria-disabled={disabled}
            className={`accessible-button ${loading ? 'loading' : ''}`}
            style={{
                transition: reducedMotion ? 'none' : 'all 0.2s ease',
            }}
            {...props}
        >
            {loading && <span aria-hidden="true" className="spinner" />}
            {children}
        </button>
    );
};

// ============================================================
// ACCESSIBLE FORM INPUT (WCAG 1.3.1, 3.3.2)
// ============================================================

export const AccessibleInput = ({
    id,
    label,
    type = 'text',
    value,
    onChange,
    error,
    helperText,
    required = false,
    ...props
}) => {
    const errorId = `${id}-error`;
    const helperId = `${id}-helper`;
    const describedBy = [
        error && errorId,
        helperText && helperId
    ].filter(Boolean).join(' ');

    return (
        <div className="form-field">
            <label htmlFor={id} className="form-label">
                {label}
                {required && <span aria-hidden="true" className="required">*</span>}
                {required && <ScreenReaderOnly>required</ScreenReaderOnly>}
            </label>

            <input
                id={id}
                type={type}
                value={value}
                onChange={onChange}
                aria-required={required}
                aria-invalid={!!error}
                aria-describedby={describedBy || undefined}
                className={`form-input ${error ? 'error' : ''}`}
                {...props}
            />

            {helperText && !error && (
                <p id={helperId} className="helper-text">
                    {helperText}
                </p>
            )}

            {error && (
                <p id={errorId} className="error-text" role="alert">
                    <ScreenReaderOnly>Error: </ScreenReaderOnly>
                    {error}
                </p>
            )}
        </div>
    );
};

// ============================================================
// ACCESSIBLE TABLE (WCAG 1.3.1)
// ============================================================

export const AccessibleTable = ({
    caption,
    headers,
    data,
    sortable = false,
    onSort,
    sortColumn,
    sortDirection,
}) => {
    return (
        <div role="region" aria-label={caption} tabIndex="0" className="table-container">
            <table>
                <caption className="sr-only">{caption}</caption>
                <thead>
                    <tr>
                        {headers.map((header, index) => (
                            <th
                                key={index}
                                scope="col"
                                aria-sort={
                                    sortColumn === header.key
                                        ? sortDirection === 'asc'
                                            ? 'ascending'
                                            : 'descending'
                                        : undefined
                                }
                            >
                                {sortable && header.sortable ? (
                                    <button
                                        onClick={() => onSort?.(header.key)}
                                        aria-label={`Sort by ${header.label}`}
                                        className="sort-button"
                                    >
                                        {header.label}
                                        {sortColumn === header.key && (
                                            <span aria-hidden="true">
                                                {sortDirection === 'asc' ? ' ↑' : ' ↓'}
                                            </span>
                                        )}
                                    </button>
                                ) : (
                                    header.label
                                )}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, rowIndex) => (
                        <tr key={rowIndex}>
                            {headers.map((header, cellIndex) => (
                                <td key={cellIndex}>
                                    {cellIndex === 0 ? (
                                        <th scope="row">{row[header.key]}</th>
                                    ) : (
                                        row[header.key]
                                    )}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

// ============================================================
// ACCESSIBLE MODAL (WCAG 2.1.2)
// ============================================================

export const AccessibleModal = ({
    isOpen,
    onClose,
    title,
    children,
}) => {
    const modalRef = useFocusTrap(isOpen);

    React.useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
            document.body.setAttribute('aria-hidden', 'true');
        } else {
            document.body.style.overflow = '';
            document.body.removeAttribute('aria-hidden');
        }

        return () => {
            document.body.style.overflow = '';
            document.body.removeAttribute('aria-hidden');
        };
    }, [isOpen]);

    // Handle escape key
    React.useEffect(() => {
        const handleEscape = (e) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="modal-overlay"
            role="presentation"
            onClick={(e) => e.target === e.currentTarget && onClose()}
        >
            <div
                ref={modalRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="modal-title"
                className="modal-content"
            >
                <header className="modal-header">
                    <h2 id="modal-title">{title}</h2>
                    <button
                        onClick={onClose}
                        aria-label="Close modal"
                        className="close-button"
                    >
                        ×
                    </button>
                </header>
                <div className="modal-body">
                    {children}
                </div>
            </div>
        </div>
    );
};

// ============================================================
// COLOR CONTRAST CHECKER
// ============================================================

export const checkContrast = (foreground, background) => {
    const getLuminance = (hex) => {
        const rgb = hex.match(/\w\w/g).map(x => parseInt(x, 16) / 255);
        const [r, g, b] = rgb.map(c =>
            c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
        );
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };

    const l1 = getLuminance(foreground);
    const l2 = getLuminance(background);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

    return {
        ratio: ratio.toFixed(2),
        passesAA: ratio >= 4.5,
        passesAAA: ratio >= 7,
        passesAALarge: ratio >= 3,
    };
};

// ============================================================
// ACCESSIBLE STYLES (CSS-in-JS)
// ============================================================

export const accessibilityStyles = `
  /* Skip Links */
  .skip-links {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 9999;
  }

  .skip-link {
    position: absolute;
    left: -9999px;
    top: auto;
    width: 1px;
    height: 1px;
    overflow: hidden;
    z-index: 9999;
    padding: 12px 24px;
    background: #1a1a2e;
    color: #ffffff;
    text-decoration: none;
    font-weight: 600;
  }

  .skip-link:focus {
    position: fixed;
    left: 16px;
    top: 16px;
    width: auto;
    height: auto;
    overflow: visible;
    outline: 3px solid #4f46e5;
    outline-offset: 2px;
  }

  /* Focus Styles (WCAG 2.4.7) */
  :focus-visible {
    outline: 3px solid #4f46e5;
    outline-offset: 2px;
  }

  /* Reduced Motion */
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }

  /* High Contrast Mode */
  @media (prefers-contrast: high) {
    .button {
      border: 2px solid currentColor;
    }
    
    .form-input {
      border: 2px solid #000000;
    }

  /* Screen Reader Only */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  /* Required Indicator */
  .required {
    color: #dc2626;
    margin-left: 4px;
  }

  /* Error States */
  .error-text {
    color: #dc2626;
    font-size: 0.875rem;
    margin-top: 4px;
  }

  .form-input.error {
    border-color: #dc2626;
  }

  /* Minimum Touch Target (WCAG 2.5.5) */
  button,
  [role="button"],
  input[type="checkbox"],
  input[type="radio"] {
    min-width: 44px;
    min-height: 44px;
  }

  /* Text Resize Support (WCAG 1.4.4) */
  html {
    font-size: 100%; /* Respects user zoom */
  }

  body {
    line-height: 1.5;
    letter-spacing: 0.01em;
  }

  /* Link Distinction (WCAG 1.4.1) */
  a {
    text-decoration: underline;
  }

  a:hover,
  a:focus {
    text-decoration: none;
  }
`;

export default {
    AccessibilityProvider,
    useAccessibility,
    SkipLinks,
    useFocusTrap,
    ScreenReaderOnly,
    LiveRegion,
    useAnnounce,
    AccessibleButton,
    AccessibleInput,
    AccessibleTable,
    AccessibleModal,
    checkContrast,
    accessibilityStyles,
};
