import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '../../hooks/useTheme';

/**
 * ThemeToggle Component
 * Animated toggle button for switching between light and dark modes
 * Persists user preference to localStorage
 */
const ThemeToggle = ({ className = "" }) => {
    const { theme, toggleTheme, isDark } = useTheme();

    return (
        <motion.button
            onClick={toggleTheme}
            className={`relative p-2 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors ${className}`}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
        >
            <motion.div
                initial={false}
                animate={{
                    rotate: isDark ? 0 : 180,
                    scale: isDark ? 1 : 0
                }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="absolute inset-0 flex items-center justify-center"
            >
                <Moon className="w-5 h-5 text-foreground" />
            </motion.div>

            <motion.div
                initial={false}
                animate={{
                    rotate: isDark ? 180 : 0,
                    scale: isDark ? 0 : 1
                }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="absolute inset-0 flex items-center justify-center"
            >
                <Sun className="w-5 h-5 text-foreground" />
            </motion.div>

            {/* Invisible placeholder to maintain button size */}
            <div className="w-5 h-5 opacity-0">
                <Sun className="w-5 h-5" />
            </div>
        </motion.button>
    );
};

export default ThemeToggle;
