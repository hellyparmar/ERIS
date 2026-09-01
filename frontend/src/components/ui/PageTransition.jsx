import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

/**
 * PageTransition Wrapper
 * Wraps page content with slide+fade or simple fade if reduced motion is enabled.
 */
const PageTransition = ({ children }) => {
    const shouldReduceMotion = useReducedMotion();

    const variants = {
        initial: {
            opacity: 0,
            y: shouldReduceMotion ? 0 : 12,
        },
        animate: {
            opacity: 1,
            y: 0,
            transition: {
                duration: 0.22, // --dur-base (220ms)
                ease: [0.16, 1, 0.3, 1] // --ease-snap: cubic-bezier(0.16, 1, 0.3, 1)
            }
        },
        exit: {
            opacity: 0,
            y: shouldReduceMotion ? 0 : -12,
            transition: {
                duration: 0.12, // --dur-fast (120ms)
                ease: [0.16, 1, 0.3, 1]
            }
        }
    };

    return (
        <motion.div
            variants={variants}
            initial="initial"
            animate="animate"
            exit="exit"
            style={{ width: '100%', height: '100%' }}
        >
            {children}
        </motion.div>
    );
};

export default PageTransition;
