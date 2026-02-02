import React from 'react';

/**
 * Visually Hidden Component
 * Hides content visually but keeps it accessible to screen readers
 * WCAG 2.4.4 - Link Purpose (In Context)
 */
export const VisuallyHidden = ({ children, as: Component = 'span', ...props }) => {
    return (
        <Component
            className="sr-only"
            {...props}
        >
            {children}
        </Component>
    );
};

/**
 * Announcer Component
 * Live region for screen reader announcements
 * WCAG 4.1.3 - Status Messages
 */
export const Announcer = () => {
    return (
        <div
            id="announcer"
            role="status"
            aria-live="polite"
            aria-atomic="true"
            className="sr-only"
        />
    );
};

/**
 * Focus Trap Component
 * Traps focus within a container (for modals/dialogs)
 */
export const FocusTrap = ({ children, active = true }) => {
    const containerRef = React.useRef(null);

    React.useEffect(() => {
        if (!active || !containerRef.current) return;

        const container = containerRef.current;
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        const handleTabKey = (e) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement?.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement?.focus();
                }
            }
        };

        // Focus first element
        firstElement?.focus();

        container.addEventListener('keydown', handleTabKey);

        return () => {
            container.removeEventListener('keydown', handleTabKey);
        };
    }, [active]);

    return (
        <div ref={containerRef}>
            {children}
        </div>
    );
};

export default VisuallyHidden;
