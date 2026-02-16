import React from 'react';
import { motion } from 'framer-motion';
import { Globe, Type } from 'lucide-react';
import { getLanguageName } from '../../lib/languageDetection';

/**
 * LanguageSelector Component
 * Allows switching between native and Roman script input
 */
const LanguageSelector = ({ currentLanguage, scriptMode, onScriptToggle, onLanguageChange }) => {
    const languages = [
        { code: 'en', name: 'English' },
        { code: 'hi', name: 'हिन्दी' },
        { code: 'gu', name: 'ગુજરાતી' },
        { code: 'mr', name: 'मराठी' },
        { code: 'ta', name: 'தமிழ்' },
        { code: 'te', name: 'తెలుగు' },
        { code: 'ur', name: 'اردو' }
    ];

    return (
        <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
            {/* Language Dropdown */}
            <div className="flex items-center gap-2 flex-1">
                <Globe className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <select
                    value={currentLanguage}
                    onChange={(e) => onLanguageChange(e.target.value)}
                    className="flex-1 bg-transparent text-sm text-gray-900 dark:text-white focus:outline-none cursor-pointer"
                >
                    {languages.map(lang => (
                        <option key={lang.code} value={lang.code}>
                            {lang.name}
                        </option>
                    ))}
                </select>
            </div>

            {/* Script Toggle (only for non-English) */}
            {currentLanguage !== 'en' && (
                <>
                    <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={onScriptToggle}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${scriptMode === 'roman'
                            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                            : 'bg-gray-200 dark:bg-white/10 text-gray-700 dark:text-gray-300'
                            }`}
                    >
                        <Type className="w-3.5 h-3.5" />
                        {scriptMode === 'roman' ? 'Roman' : 'Native'}
                    </motion.button>
                </>
            )}
        </div>
    );
};

export default LanguageSelector;
