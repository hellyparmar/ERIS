/**
 * Enterprise Retail Intelligence System v3.0
 * LAYOUT - HEADER
 * 
 * Top navigation bar with theme toggle and language selector
 * V3.0 Standard: Explicit icon imports, performance-optimized
 */

import { Moon, Sun, Globe } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import { useLanguage } from '../../hooks/useLanguage';
import Button from '../ui/Button';
import { useCallback } from 'react';

const Header = () => {
    const { theme, toggleTheme } = useTheme();
    const { language, changeLanguage, availableLanguages, t } = useLanguage();

    // Performance optimization: useCallback for event handlers (V3.0 Standard)
    const handleThemeToggle = useCallback(() => {
        toggleTheme();
    }, [toggleTheme]);

    const handleLanguageChange = useCallback((e) => {
        changeLanguage(e.target.value);
    }, [changeLanguage]);

    return (
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
            <div className="flex items-center justify-between px-6 py-4">
                {/* Left: Title */}
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Enterprise Retail Intelligence
                    </h1>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        R-DIOS v3.0 Analytics Platform
                    </p>
                </div>

                {/* Right: Controls */}
                <div className="flex items-center gap-4">
                    {/* Language Selector */}
                    <div className="flex items-center gap-2">
                        <Globe className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                        <select
                            value={language}
                            onChange={handleLanguageChange}
                            className="bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {availableLanguages.map(({ code, name }) => (
                                <option key={code} value={code}>
                                    {name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Theme Toggle */}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleThemeToggle}
                        aria-label="Toggle theme"
                    >
                        {theme === 'dark' ? (
                            <Sun className="w-5 h-5" />
                        ) : (
                            <Moon className="w-5 h-5" />
                        )}
                    </Button>
                </div>
            </div>
        </header>
    );
};

export default Header;
