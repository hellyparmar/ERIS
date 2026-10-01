import { useEffect, useCallback } from 'react';

/**
 * useAnnouncer Hook
 * Announces messages to screen readers
 */
export const useAnnouncer = () => {
    const announce = useCallback((message, priority = 'polite') => {
        const announcer = document.getElementById('announcer');
        if (announcer) {
            // Clear previous message
            announcer.textContent = '';

            // Set priority
            announcer.setAttribute('aria-live', priority);

            // Announce new message (with slight delay for screen readers)
            setTimeout(() => {
                announcer.textContent = message;
            }, 100);
        }
    }, []);

    return { announce };
};

/**
 * useKeyboardShortcut Hook
 * Registers keyboard shortcuts
 */
export const useKeyboardShortcut = (key, callback, options = {}) => {
    const {
        ctrl = false,
        alt = false,
        shift = false,
        enabled = true,
    } = options;

    useEffect(() => {
        if (!enabled) return;

        const handleKeyDown = (e) => {
            const matchesModifiers =
                e.ctrlKey === ctrl &&
                e.altKey === alt &&
                e.shiftKey === shift;

            const matchesKey = e.key.toLowerCase() === key.toLowerCase();

            if (matchesModifiers && matchesKey) {
                e.preventDefault();
                callback(e);
            }
        };

        window.addEventListener('keydown', handleKeyDown);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [key, callback, ctrl, alt, shift, enabled]);
};

/**
 * useFocusManagement Hook
 * Manages focus for accessibility
 */
export const useFocusManagement = () => {
    const focusElement = useCallback((selector) => {
        const element = document.querySelector(selector);
        if (element) {
            element.focus();
        }
    }, []);

    const focusFirst = useCallback((container) => {
        const focusable = container?.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable && focusable.length > 0) {
            focusable[0].focus();
        }
    }, []);

    const saveFocus = useCallback(() => {
        return document.activeElement;
    }, []);

    const restoreFocus = useCallback((element) => {
        if (element && element.focus) {
            element.focus();
        }
    }, []);

    return {
        focusElement,
        focusFirst,
        saveFocus,
        restoreFocus,
    };
};

/**
 * useAriaLive Hook
 * Creates a live region for announcements
 */
export const useAriaLive = (message, priority = 'polite') => {
    const { announce } = useAnnouncer();

    useEffect(() => {
        if (message) {
            announce(message, priority);
        }
    }, [message, priority, announce]);
};

/**
 * useEscapeKey Hook
 * Handles Escape key press
 */
export const useEscapeKey = (callback, enabled = true) => {
    useEffect(() => {
        if (!enabled) return;

        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                callback(e);
            }
        };

        window.addEventListener('keydown', handleEscape);

        return () => {
            window.removeEventListener('keydown', handleEscape);
        };
    }, [callback, enabled]);
};

/**
 * useArrowNavigation Hook
 * Handles arrow key navigation for lists
 */
export const useArrowNavigation = (containerRef, options = {}) => {
    const { orientation = 'vertical', loop = true } = options;

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const handleArrowKey = (e) => {
            const items = Array.from(
                container.querySelectorAll('[role="option"], [role="menuitem"], [role="tab"]')
            );

            const currentIndex = items.indexOf(document.activeElement);
            if (currentIndex === -1) return;

            let nextIndex = currentIndex;

            if (orientation === 'vertical') {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    nextIndex = currentIndex + 1;
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    nextIndex = currentIndex - 1;
                }
            } else {
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    nextIndex = currentIndex + 1;
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    nextIndex = currentIndex - 1;
                }
            }

            // Handle looping
            if (loop) {
                if (nextIndex >= items.length) nextIndex = 0;
                if (nextIndex < 0) nextIndex = items.length - 1;
            } else {
                nextIndex = Math.max(0, Math.min(nextIndex, items.length - 1));
            }

            if (items[nextIndex]) {
                items[nextIndex].focus();
            }
        };

        container.addEventListener('keydown', handleArrowKey);

        return () => {
            container.removeEventListener('keydown', handleArrowKey);
        };
    }, [containerRef, orientation, loop]);
};

export default {
    useAnnouncer,
    useKeyboardShortcut,
    useFocusManagement,
    useAriaLive,
    useEscapeKey,
    useArrowNavigation,
};
