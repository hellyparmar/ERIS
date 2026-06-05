/**
 * Enterprise Retail Intelligence System v3.0
 * CONSTANTS MODULE
 * 
 * CRITICAL: This module contains ALL configuration constants to avoid
 * dynamic Tailwind class generation (which breaks JIT compilation).
 * 
 * V3.0 Protocol: NO dynamic string interpolation for CSS classes.
 */

// ============================================================================
// COLOR MAPPING (V3.0 Critical Fix)
// ============================================================================
/**
 * COLOR_MAP Object - Maps severity levels to Tailwind classes
 * USAGE: Use with clsx() for conditional styling
 * NEVER use: `bg-${color}-500` ❌
 * ALWAYS use: COLOR_MAP[severity].bg ✅
 */
export const COLOR_MAP = {
    critical: {
        bg: 'bg-red-600',
        bgLight: 'bg-red-500/10',
        border: 'border-red-500',
        text: 'text-red-500',
        darkText: 'dark:text-red-400',
        gradient: 'from-red-600 to-red-700',
        hover: 'hover:bg-red-700',
        badge: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
    },
    warning: {
        bg: 'bg-yellow-600',
        bgLight: 'bg-yellow-500/10',
        border: 'border-yellow-500',
        text: 'text-yellow-500',
        darkText: 'dark:text-yellow-400',
        gradient: 'from-yellow-600 to-yellow-700',
        hover: 'hover:bg-yellow-700',
        badge: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
    },
    success: {
        bg: 'bg-green-600',
        bgLight: 'bg-green-500/10',
        border: 'border-green-500',
        text: 'text-green-500',
        darkText: 'dark:text-green-400',
        gradient: 'from-green-600 to-green-700',
        hover: 'hover:bg-green-700',
        badge: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    },
    info: {
        bg: 'bg-blue-600',
        bgLight: 'bg-blue-500/10',
        border: 'border-blue-500',
        text: 'text-blue-500',
        darkText: 'dark:text-blue-400',
        gradient: 'from-blue-600 to-blue-700',
        hover: 'hover:bg-blue-700',
        badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
    },
    neutral: {
        bg: 'bg-gray-600',
        bgLight: 'bg-gray-500/10',
        border: 'border-gray-500',
        text: 'text-gray-500',
        darkText: 'dark:text-gray-400',
        gradient: 'from-gray-600 to-gray-700',
        hover: 'hover:bg-gray-700',
        badge: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
    }
};

// ============================================================================
// ALERT THRESHOLDS (V3.0 Functional Spec)
// ============================================================================
export const ALERT_THRESHOLDS = {
    STOCKOUT_CRITICAL: 7,      // Days: < 7 = CRITICAL
    STOCKOUT_WARNING: 14,       // Days: 7-14 = WARNING
    DEMAND_SPIKE_CRITICAL: 30,  // Percent: > 30% = CRITICAL
    DEMAND_SPIKE_WARNING: 15    // Percent: 15-30% = WARNING
};

// ============================================================================
// ROLE-BASED ACCESS CONTROL
// ============================================================================
export const USER_ROLES = {
    EXECUTIVE: 'executive',
    MANAGER: 'manager',
    ANALYST: 'analyst'
};

export const ROLE_CONFIG = {
    [USER_ROLES.EXECUTIVE]: {
        label: 'Executive',
        dashboardView: 'strategic',
        features: ['insights', 'trends', 'forecasts'],
        icon: 'Building2'
    },
    [USER_ROLES.MANAGER]: {
        label: 'Manager',
        dashboardView: 'operational',
        features: ['alerts', 'inventory', 'sales', 'actions'],
        icon: 'Users'
    },
    [USER_ROLES.ANALYST]: {
        label: 'Analyst',
        dashboardView: 'technical',
        features: ['reports', 'analytics', 'data', 'exports'],
        icon: 'BarChart3'
    }
};

// ============================================================================
// MULTILINGUAL TRANSLATIONS (V3.0 Intelligence Engine)
// ============================================================================
export const TRANSLATIONS = {
    en: {
        code: 'en',
        name: 'English',
        rtl: false,
        dashboard: {
            title: 'Dashboard',
            subtitle: 'Enterprise Retail Intelligence System v3.0',
            totalRevenue: 'Total Revenue',
            totalOrders: 'Total Orders',
            inventoryValue: 'Inventory Value',
            stockoutRisk: 'Stockout Risk',
            salesTrend: 'Sales Trend & 15-Day Forecast',
            inventoryAlerts: 'Inventory Alerts',
            vsLastPeriod: 'vs last period',
            total: 'total'
        },
        sidebar: {
            dashboard: 'Dashboard',
            analytics: 'Analytics',
            inventory: 'Inventory',
            forecasts: 'Forecasts',
            alerts: 'Alerts',
            team: 'Team',
            enterprise: 'Enterprise'
        }
    },
    hi: {
        code: 'hi',
        name: 'हिन्दी',
        rtl: false,
        dashboard: {
            title: 'डैशबोर्ड',
            subtitle: 'एंटरप्राइज रिटेल इंटेलिजेंस सिस्टम v3.0',
            totalRevenue: 'कुल राजस्व',
            totalOrders: 'कुल ऑर्डर',
            inventoryValue: 'इन्वेंटरी मूल्य',
            stockoutRisk: 'स्टॉक समाप्ति जोखिम',
            salesTrend: 'बिक्री प्रवृत्ति और 15-दिन पूर्वानुमान',
            inventoryAlerts: 'इन्वेंटरी अलर्ट',
            vsLastPeriod: 'पिछली अवधि की तुलना में',
            total: 'कुल'
        },
        sidebar: {
            dashboard: 'डैशबोर्ड',
            analytics: 'विश्लेषण',
            inventory: 'इन्वेंटरी',
            forecasts: 'पूर्वानुमान',
            alerts: 'अलर्ट',
            team: 'टीम',
            enterprise: 'एंटरप्राइज'
        }
    },
    gu: {
        code: 'gu',
        name: 'ગુજરાતી',
        rtl: false,
        dashboard: {
            title: 'ડૅશબોર્ડ',
            subtitle: 'એન્ટરપ્રાઇઝ રિટેલ ઇન્ટેલિજન્સ સિસ્ટમ v3.0',
            totalRevenue: 'કુલ આવક',
            totalOrders: 'કુલ ઓર્ડર',
            inventoryValue: 'ઇન્વેન્ટરી મૂલ્ય',
            stockoutRisk: 'સ્ટોક સમાપ્ત થવાનું જોખમ',
            salesTrend: 'વેચાણ વલણ અને 15-દિવસની આગાહી',
            inventoryAlerts: 'ઇન્વેન્ટરી ચેતવણીઓ',
            vsLastPeriod: 'છેલ્લા સમયગાળા સાથે',
            total: 'કુલ'
        },
        sidebar: {
            dashboard: 'ડૅશબોર્ડ',
            analytics: 'વિશ્લેષણ',
            inventory: 'ઇન્વેન્ટરી',
            forecasts: 'આગાહીઓ',
            alerts: 'ચેતવણીઓ',
            team: 'ટીમ',
            enterprise: 'એન્ટરપ્રાઇઝ'
        }
    },
    mr: {
        code: 'mr',
        name: 'मराठी',
        rtl: false,
        dashboard: {
            title: 'डॅशबोर्ड',
            subtitle: 'एंटरप्राइझ रिटेल इंटेलिजन्स सिस्टम v3.0',
            totalRevenue: 'एकूण महसूल',
            totalOrders: 'एकूण ऑर्डर',
            inventoryValue: 'इन्व्हेंटरी मूल्य',
            stockoutRisk: 'स्टॉक संपण्याचा धोका',
            salesTrend: 'विक्री प्रवृत्ती आणि 15-दिवसांचा अंदाज',
            inventoryAlerts: 'इन्व्हेंटरी इशारे',
            vsLastPeriod: 'मागील कालावधीच्या तुलनेत',
            total: 'एकूण'
        },
        sidebar: {
            dashboard: 'डॅशबोर्ड',
            analytics: 'विश्लेषण',
            inventory: 'इन्व्हेंटरी',
            forecasts: 'अंदाज',
            alerts: 'इशारे',
            team: 'टीम',
            enterprise: 'एंटरप्राइझ'
        }
    },
    ta: {
        code: 'ta',
        name: 'தமிழ்',
        rtl: false,
        dashboard: {
            title: 'டாஷ்போர்டு',
            subtitle: 'எண்டர்பிரைஸ் ரீடெய்ல் இன்டெலிஜென்ஸ் அமைப்பு v3.0',
            totalRevenue: 'மொத்த வருவாய்',
            totalOrders: 'மொத்த ஆர்டர்கள்',
            inventoryValue: 'சரக்கு மதிப்பு',
            stockoutRisk: 'இருப்பு முடியும் அபாயம்',
            salesTrend: 'விற்பனை போக்கு & 15-நாள் முன்னறிவிப்பு',
            inventoryAlerts: 'சரக்கு எச்சரிக்கைகள்',
            vsLastPeriod: 'கடந்த காலத்துடன் ஒப்பிடுகையில்',
            total: 'மொத்தம்'
        },
        sidebar: {
            dashboard: 'டாஷ்போர்டு',
            analytics: 'பகுப்பாய்வு',
            inventory: 'சரக்கு',
            forecasts: 'முன்னறிவிப்புகள்',
            alerts: 'எச்சரிக்கைகள்',
            team: 'குழு',
            enterprise: 'நிறுவனம்'
        }
    },
    te: {
        code: 'te',
        name: 'తెలుగు',
        rtl: false,
        dashboard: {
            title: 'డ్యాష్‌బోర్డ్',
            subtitle: 'ఎంటర్‌ప్రైజ్ రిటైల్ ఇంటెలిజెన్స్ సిస్టం v3.0',
            totalRevenue: 'మొత్తం ఆదాయం',
            totalOrders: 'మొత్తం ఆర్డర్లు',
            inventoryValue: 'ఇన్వెంటరీ విలువ',
            stockoutRisk: 'స్టాక్ అయిపోయే ప్రమాదం',
            salesTrend: 'అమ్మకాల ధోరణి & 15-రోజుల అంచనా',
            inventoryAlerts: 'ఇన్వెంటరీ హెచ్చరికలు',
            vsLastPeriod: 'గత కాలంతో పోల్చితే',
            total: 'మొత్తం'
        },
        sidebar: {
            dashboard: 'డ్యాష్‌బోర్డ్',
            analytics: 'విశ్లేషణ',
            inventory: 'ఇన్వెంటరీ',
            forecasts: 'అంచనాలు',
            alerts: 'హెచ్చరికలు',
            team: 'టీమ్',
            enterprise: 'ఎంటర్‌ప్రైజ్'
        }
    },
    ur: {
        code: 'ur',
        name: 'اردو',
        rtl: true,
        dashboard: {
            title: 'ڈیش بورڈ',
            subtitle: 'انٹرپرائز ریٹیل انٹیلیجنس سسٹم v3.0',
            totalRevenue: 'کل آمدنی',
            totalOrders: 'کل آرڈرز',
            inventoryValue: 'انوینٹری کی قیمت',
            stockoutRisk: 'اسٹاک ختم ہونے کا خطرہ',
            salesTrend: 'فروخت کا رجحان اور 15 دن کی پیش گوئی',
            inventoryAlerts: 'انوینٹری الرٹس',
            vsLastPeriod: 'پچھلے دور کی نسبت',
            total: 'کل'
        },
        sidebar: {
            dashboard: 'ڈیش بورڈ',
            analytics: 'تجزیات',
            inventory: 'انوینٹری',
            forecasts: 'پیش گوئیاں',
            alerts: 'الرٹس',
            team: 'ٹیم',
            enterprise: 'انٹرپرائز'
        }
    }
};

// ============================================================================
// EXTERNAL FACTORS (V3.0 Intelligence Engine)
// ============================================================================
export const EXTERNAL_FACTORS = {
    weather: {
        SUNNY: 'sunny',
        RAINY: 'rainy',
        MONSOON: 'monsoon',
        WINTER: 'winter'
    },
    economic: {
        INFLATION_LOW: 'low',      // < 3%
        INFLATION_MEDIUM: 'medium', // 3-6%
        INFLATION_HIGH: 'high'      // > 6%
    },
    sentiment: {
        POSITIVE: 'positive',
        NEUTRAL: 'neutral',
        NEGATIVE: 'negative'
    }
};

// ============================================================================
// CHART CONFIGURATION
// ============================================================================
export const CHART_COLORS = {
    primary: '#3b82f6',      // Blue
    secondary: '#8b5cf6',    // Purple
    success: '#10b981',      // Green
    warning: '#f59e0b',      // Amber
    danger: '#ef4444',       // Red
    info: '#06b6d4',         // Cyan
    grid: '#374151',         // Gray-700 (dark mode)
    gridLight: '#e5e7eb'     // Gray-200 (light mode)
};

// ============================================================================
// APPLICATION METADATA
// ============================================================================
export const APP_CONFIG = {
    name: 'Enterprise Retail Intelligence System',
    version: '3.0.0',
    author: 'R-DIOS Team',
    defaultLanguage: 'en',
    defaultRole: USER_ROLES.MANAGER,
    defaultTheme: 'dark'
};
