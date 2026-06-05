import React from 'react';
import './SkipLinks.css';

/**
 * Skip Navigation Links
 * Allows keyboard users to skip repetitive content
 * WCAG 2.4.1 - Bypass Blocks
 */
const SkipLinks = () => {
    return (
        <div className="skip-links" role="navigation" aria-label="Skip links">
            <a href="#main-content" className="skip-link">
                Skip to main content
            </a>
            <a href="#navigation" className="skip-link">
                Skip to navigation
            </a>
            <a href="#search" className="skip-link">
                Skip to search
            </a>
        </div>
    );
};

export default SkipLinks;
