/**
 * Enterprise Retail Intelligence System v3.0
 * THEME CONTEXT
 * 
 * Provides Dark Mode state management using React Context API
 * V3.0 Requirement: Dark Mode First Design Strategy
 */

import { createContext, useContext, useEffect, useState, useCallback } from 'react';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
    const [theme, setThemeState] = useState(() => localStorage.getItem('theme') || 'dark');

    useEffect(() => {
        const root = window.document.documentElement;
        const resolved = theme === 'system'
            ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
            : theme;
        root.setAttribute('data-theme', resolved);
        root.classList.toggle('dark', resolved === 'dark');
        root.classList.toggle('light', resolved === 'light');
        localStorage.setItem('theme', theme);
    }, [theme]);

    const toggleTheme = useCallback(() => setThemeState((value) => value === 'dark' ? 'light' : 'dark'), []);
    const setSpecificTheme = useCallback((newTheme) => {
        if (['light', 'dark', 'system'].includes(newTheme)) setThemeState(newTheme);
    }, []);

    const value = {
        theme,
        toggleTheme,
        setTheme: setSpecificTheme,
        isDark: theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
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
