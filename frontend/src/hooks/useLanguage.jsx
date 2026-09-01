/**
 * Enterprise Retail Intelligence System v3.0
 * LANGUAGE CONTEXT & HOOK
 * 
 * Provides multilingual support using React Context API
 * V3.0 Intelligence Engine: Auto-Language Detection
 */

import { createContext, useContext, useState, useCallback, useMemo } from 'react';
import { APP_CONFIG, TRANSLATIONS } from '../lib/constants';

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
    // Initialize from localStorage or default language
    const [language, setLanguage] = useState(() => {
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem('language');
            return stored || APP_CONFIG.defaultLanguage;
        }
        return APP_CONFIG.defaultLanguage;
    });

    // Get current translations (memoized for performance)
    const translations = useMemo(() => {
        return TRANSLATIONS[language] || TRANSLATIONS[APP_CONFIG.defaultLanguage];
    }, [language]);

    // Translation function
    const t = useCallback((key) => {
        return translations[key] || key;
    }, [translations]);

    // Change language function (stabilized with useCallback)
    const changeLanguage = useCallback((newLang) => {
        if (TRANSLATIONS[newLang]) {
            setLanguage(newLang);
            localStorage.setItem('language', newLang);

            // Update document direction for RTL languages
            if (typeof window !== 'undefined') {
                const direction = TRANSLATIONS[newLang].rtl ? 'rtl' : 'ltr';
                document.documentElement.setAttribute('dir', direction);
            }
        }
    }, []);

    // Auto-detect browser language on mount
    const detectBrowserLanguage = useCallback(() => {
        if (typeof window !== 'undefined') {
            const browserLang = navigator.language.split('-')[0]; // Get 'en' from 'en-US'

            if (TRANSLATIONS[browserLang]) {
                changeLanguage(browserLang);
            }
        }
    }, [changeLanguage]);

    const value = {
        language,
        currentLanguage: language,
        changeLanguage,
        detectBrowserLanguage,
        t,
        isRTL: translations.rtl,
        availableLanguages: Object.keys(TRANSLATIONS).map(code => ({
            code,
            name: TRANSLATIONS[code].name
        }))
    };

    return (
        <LanguageContext.Provider value={value}>
            {children}
        </LanguageContext.Provider>
    );
};

// Custom hook for accessing language context
export const useLanguage = () => {
    const context = useContext(LanguageContext);

    if (!context) {
        throw new Error('useLanguage must be used within a LanguageProvider');
    }

    return context;
};

export default LanguageContext;
