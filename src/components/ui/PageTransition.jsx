import React from 'react';
import { pageVariants } from '../utils/animations';

/**
 * PageTransition Wrapper
 * Wraps page content with smooth transition animations
 */
const PageTransition = ({ children }) => {
    return (
        <div
            initial="initial"
            animate="enter"
            exit="exit"
            
            className="w-full h-full"
        >
            {children}
        </div>
    );
};

export default PageTransition;
