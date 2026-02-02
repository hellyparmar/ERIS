/**
 * Enterprise Retail Intelligence System v3.0
 * THEME CONTEXT
 * 
 * Provides Dark Mode state management using React Context API
 * V3.0 Requirement: Dark Mode First Design Strategy
 */

import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { APP_CONFIG } from '../lib/constants';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
    // Initialize from localStorage or default to dark mode
    const [theme, setTheme] = useState(() => {
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem('theme');
            return stored || APP_CONFIG.defaultTheme;
        }
        return APP_CONFIG.defaultTheme;
    });

    // Update DOM and localStorage when theme changes
    useEffect(() => {
        const root = window.document.documentElement;

        // Remove existing theme classes
        root.classList.remove('light', 'dark');

        // Add new theme class
        root.classList.add(theme);

        // Persist to localStorage
        localStorage.setItem('theme', theme);
    }, [theme]);

    // Toggle theme between light and dark
    // Using useCallback for performance (V3.0 Standard)
    const toggleTheme = useCallback(() => {
        setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
    }, []);

    // Set specific theme
    const setSpecificTheme = useCallback((newTheme) => {
        if (newTheme === 'light' || newTheme === 'dark') {
            setTheme(newTheme);
        }
    }, []);

    const value = {
        theme,
        toggleTheme,
        setTheme: setSpecificTheme,
        isDark: theme === 'dark'
    };

    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    );
};

// Custom hook for accessing theme context
export const useTheme = () => {
    const context = useContext(ThemeContext);

    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }

    return context;
};

export default ThemeContext;
