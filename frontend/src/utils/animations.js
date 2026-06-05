/**
 * Page Transition Animations
 * Smooth transitions between pages for better UX
 */

export const pageVariants = {
    initial: {
        opacity: 0,
        y: 20,
    },
    enter: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.4,
            ease: [0.6, 0.05, 0.01, 0.9],
        },
    },
    exit: {
        opacity: 0,
        y: -20,
        transition: {
            duration: 0.3,
            ease: [0.6, 0.05, 0.01, 0.9],
        },
    },
};

export const fadeInUp = {
    initial: {
        opacity: 0,
        y: 60,
    },
    animate: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.6,
            ease: [0.6, 0.05, 0.01, 0.9],
        },
    },
};

export const staggerContainer = {
    initial: {},
    animate: {
        transition: {
            staggerChildren: 0.1,
        },
    },
};

export const scaleIn = {
    initial: {
        opacity: 0,
        scale: 0.9,
    },
    animate: {
        opacity: 1,
        scale: 1,
        transition: {
            duration: 0.4,
            ease: [0.6, 0.05, 0.01, 0.9],
        },
    },
};

export const slideInLeft = {
    initial: {
        opacity: 0,
        x: -60,
    },
    animate: {
        opacity: 1,
        x: 0,
        transition: {
            duration: 0.5,
            ease: [0.6, 0.05, 0.01, 0.9],
        },
    },
};

export const slideInRight = {
    initial: {
        opacity: 0,
        x: 60,
    },
    animate: {
        opacity: 1,
        x: 0,
        transition: {
            duration: 0.5,
            ease: [0.6, 0.05, 0.01, 0.9],
        },
    },
};

// Card hover animation
export const cardHover = {
    rest: {
        scale: 1,
        y: 0,
    },
    hover: {
        scale: 1.02,
        y: -4,
        transition: {
            duration: 0.3,
            ease: 'easeOut',
        },
    },
    tap: {
        scale: 0.98,
    },
};

// Button animations
export const buttonTap = {
    scale: 0.95,
    transition: {
        duration: 0.1,
    },
};

export const buttonHover = {
    scale: 1.05,
    y: -2,
    transition: {
        duration: 0.2,
    },
};

// Loading spinner animation
export const spinnerVariants = {
    animate: {
        rotate: 360,
        transition: {
            duration: 1,
            repeat: Infinity,
            ease: 'linear',
        },
    },
};

// Pulse animation for notifications
export const pulseVariants = {
    initial: {
        scale: 1,
    },
    animate: {
        scale: [1, 1.05, 1],
        transition: {
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
        },
    },
};

// Slide in from bottom (for modals/toasts)
export const slideInBottom = {
    initial: {
        y: '100%',
        opacity: 0,
    },
    animate: {
        y: 0,
        opacity: 1,
        transition: {
            duration: 0.4,
            ease: [0.6, 0.05, 0.01, 0.9],
        },
    },
    exit: {
        y: '100%',
        opacity: 0,
        transition: {
            duration: 0.3,
        },
    },
};

// Backdrop animation
export const backdropVariants = {
    initial: {
        opacity: 0,
    },
    animate: {
        opacity: 1,
        transition: {
            duration: 0.3,
        },
    },
    exit: {
        opacity: 0,
        transition: {
            duration: 0.3,
        },
    },
};

// Number counter animation
export const counterVariants = {
    initial: {
        opacity: 0,
        y: 20,
    },
    animate: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.5,
        },
    },
};

// Chart animation
export const chartVariants = {
    initial: {
        opacity: 0,
        scale: 0.95,
    },
    animate: {
        opacity: 1,
        scale: 1,
        transition: {
            duration: 0.6,
            ease: [0.6, 0.05, 0.01, 0.9],
        },
    },
};

// Tooltip animation
export const tooltipVariants = {
    initial: {
        opacity: 0,
        scale: 0.8,
        y: 10,
    },
    animate: {
        opacity: 1,
        scale: 1,
        y: 0,
        transition: {
            duration: 0.2,
        },
    },
    exit: {
        opacity: 0,
        scale: 0.8,
        y: 10,
        transition: {
            duration: 0.15,
        },
    },
};

// Shimmer effect for loading states
export const shimmerVariants = {
    animate: {
        backgroundPosition: ['200% 0', '-200% 0'],
        transition: {
            duration: 2,
            repeat: Infinity,
            ease: 'linear',
        },
    },
};

export default {
    pageVariants,
    fadeInUp,
    staggerContainer,
    scaleIn,
    slideInLeft,
    slideInRight,
    cardHover,
    buttonTap,
    buttonHover,
    spinnerVariants,
    pulseVariants,
    slideInBottom,
    backdropVariants,
    counterVariants,
    chartVariants,
    tooltipVariants,
    shimmerVariants,
};
