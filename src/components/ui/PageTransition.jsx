import React from 'react';
import { motion } from 'framer-motion';
import { pageVariants } from '../utils/animations';

/**
 * PageTransition Wrapper
 * Wraps page content with smooth transition animations
 */
const PageTransition = ({ children }) => {
    return (
        <motion.div
            initial="initial"
            animate="enter"
            exit="exit"
            variants={pageVariants}
            className="w-full h-full"
        >
            {children}
        </motion.div>
    );
};

export default PageTransition;
