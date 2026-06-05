import React from 'react';

/**
 * PageTransition Wrapper
 * Wraps page content with subtle fade transition
 */
const PageTransition = ({ children }) => {
    return (
        <div className="w-full h-full transition-opacity duration-150 ease">
            {children}
        </div>
    );
};

export default PageTransition;
