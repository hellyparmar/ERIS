import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

/**
 * ThemeToggle Component
 * Animated toggle button for switching between light and dark modes
 * Persists user preference to localStorage
 */
const ThemeToggle = ({ className = "" }) => {
    const { theme, toggleTheme, isDark } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className={`relative p-2 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors ${className}`}
            }
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
        >
            <div
                
                className="absolute inset-0 flex items-center justify-center"
            >
                <Moon className="w-5 h-5 text-foreground" />
            </div>

            <div
                
                className="absolute inset-0 flex items-center justify-center"
            >
                <Sun className="w-5 h-5 text-foreground" />
            </div>

            {/* Invisible placeholder to maintain button size */}
            <div className="w-5 h-5 opacity-0">
                <Sun className="w-5 h-5" />
            </div>
        </button>
    );
};

export default ThemeToggle;
