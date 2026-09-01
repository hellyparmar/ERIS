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
    const [theme, setTheme] = useState('dark');

    useEffect(() => {
        const root = window.document.documentElement;
        root.classList.remove('light');
        root.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }, []);

    const toggleTheme = useCallback(() => {}, []);
    const setSpecificTheme = useCallback((newTheme) => {}, []);

    const value = {
        theme: 'dark',
        toggleTheme,
        setTheme: setSpecificTheme,
        isDark: true
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
