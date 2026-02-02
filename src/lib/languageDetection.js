/**
 * Language Detection and Transliteration Utilities
 * Supports 7 languages: English, Hindi, Gujarati, Marathi, Tamil, Telugu, Urdu
 */

// Script detection patterns
const SCRIPT_PATTERNS = {
    devanagari: /[\u0900-\u097F]/,  // Hindi, Marathi
    gujarati: /[\u0A80-\u0AFF]/,
    tamil: /[\u0B80-\u0BFF]/,
    telugu: /[\u0C00-\u0C7F]/,
    arabic: /[\u0600-\u06FF]/,      // Urdu
    latin: /[A-Za-z]/
};

// Language code to script mapping
const LANGUAGE_SCRIPTS = {
    en: 'latin',
    hi: 'devanagari',
    gu: 'gujarati',
    mr: 'devanagari',
    ta: 'tamil',
    te: 'telugu',
    ur: 'arabic'
};

/**
 * Detect the script type of input text
 * @param {string} text - Input text
 * @returns {string} - Detected script type
 */
export const detectScript = (text) => {
    if (!text || text.trim().length === 0) return 'latin';

    // Count characters for each script
    const scriptCounts = {};
    for (const char of text) {
        for (const [script, pattern] of Object.entries(SCRIPT_PATTERNS)) {
            if (pattern.test(char)) {
                scriptCounts[script] = (scriptCounts[script] || 0) + 1;
            }
        }
    }

    // Return script with highest count
    const dominantScript = Object.entries(scriptCounts)
        .sort((a, b) => b[1] - a[1])[0];

    return dominantScript ? dominantScript[0] : 'latin';
};

/**
 * Detect language from text input
 * @param {string} text - Input text
 * @returns {string} - Detected language code
 */
export const detectLanguage = (text) => {
    if (!text || text.trim().length === 0) return 'en';

    const script = detectScript(text);

    // Map script to language
    const scriptToLanguage = {
        latin: 'en',
        devanagari: 'hi',  // Default to Hindi for Devanagari
        gujarati: 'gu',
        tamil: 'ta',
        telugu: 'te',
        arabic: 'ur'
    };

    return scriptToLanguage[script] || 'en';
};

/**
 * Check if text is in Roman script (transliteration)
 * @param {string} text - Input text
 * @param {string} expectedLanguage - Expected language code
 * @returns {boolean}
 */
export const isRomanScript = (text, expectedLanguage) => {
    if (expectedLanguage === 'en') return true;

    const script = detectScript(text);
    const expectedScript = LANGUAGE_SCRIPTS[expectedLanguage];

    return script === 'latin' && expectedScript !== 'latin';
};

/**
 * Get language name from code
 * @param {string} code - Language code
 * @returns {string} - Language name
 */
export const getLanguageName = (code) => {
    const names = {
        en: 'English',
        hi: 'हिन्दी (Hindi)',
        gu: 'ગુજરાતી (Gujarati)',
        mr: 'मराठी (Marathi)',
        ta: 'தமிழ் (Tamil)',
        te: 'తెలుగు (Telugu)',
        ur: 'اردو (Urdu)'
    };
    return names[code] || 'English';
};

/**
 * Format message for AI based on detected language and script
 * @param {string} text - User input
 * @param {string} detectedLang - Detected language code
 * @returns {object} - Formatted message with metadata
 */
export const formatMessageForAI = (text, detectedLang) => {
    const isRoman = isRomanScript(text, detectedLang);

    return {
        text,
        language: detectedLang,
        script: isRoman ? 'roman' : 'native',
        timestamp: new Date().toISOString()
    };
};

/**
 * Get system prompt for AI based on language
 * @param {string} languageCode - Language code
 * @returns {string} - System prompt
 */
export const getSystemPrompt = (languageCode) => {
    const prompts = {
        en: "You are a helpful AI assistant for an Enterprise Retail Intelligence System. Help users with sales data, inventory management, forecasting, and business insights. Be concise and professional.",
        hi: "आप एक एंटरप्राइज रिटेल इंटेलिजेंस सिस्टम के लिए एक सहायक AI असिस्टेंट हैं। उपयोगकर्ताओं को बिक्री डेटा, इन्वेंटरी प्रबंधन, पूर्वानुमान और व्यावसायिक अंतर्दृष्टि में मदद करें। संक्षिप्त और पेशेवर रहें।",
        gu: "તમે એન્ટરપ્રાઇઝ રિટેલ ઇન્ટેલિજન્સ સિસ્ટમ માટે સહાયક AI સહાયક છો. વપરાશકર્તાઓને વેચાણ ડેટા, ઇન્વેન્ટરી મેનેજમેન્ટ, આગાહી અને વ્યવસાય સમજ સાથે મદદ કરો. સંક્ષિપ્ત અને વ્યાવસાયિક રહો.",
        mr: "तुम्ही एंटरप्राइझ रिटेल इंटेलिजन्स सिस्टमसाठी एक उपयुक्त AI सहाय्यक आहात. वापरकर्त्यांना विक्री डेटा, इन्व्हेंटरी व्यवस्थापन, अंदाज आणि व्यवसाय अंतर्दृष्टी मध्ये मदत करा. संक्षिप्त आणि व्यावसायिक रहा.",
        ta: "நீங்கள் எண்டர்பிரைஸ் ரீடெய்ல் இன்டெலிஜென்ஸ் அமைப்புக்கான உதவிகரமான AI உதவியாளர். பயனர்களுக்கு விற்பனை தரவு, சரக்கு மேலாண்மை, முன்னறிவிப்பு மற்றும் வணிக நுண்ணறிவு ஆகியவற்றில் உதவுங்கள். சுருக்கமாகவும் தொழில்முறையாகவும் இருங்கள்.",
        te: "మీరు ఎంటర్‌ప్రైజ్ రిటైల్ ఇంటెలిజెన్స్ సిస్టమ్ కోసం సహాయక AI అసిస్టెంట్. వినియోగదారులకు అమ్మకాల డేటా, ఇన్వెంటరీ నిర్వహణ, అంచనా మరియు వ్యాపార అంతర్దృష్టులతో సహాయం చేయండి. సంక్షిప్తంగా మరియు వృత్తిపరంగా ఉండండి.",
        ur: "آپ ایک انٹرپرائز ریٹیل انٹیلیجنس سسٹم کے لیے مددگار AI اسسٹنٹ ہیں۔ صارفین کو سیلز ڈیٹا، انوینٹری مینجمنٹ، پیش گوئی اور کاروباری بصیرت میں مدد کریں۔ مختصر اور پیشہ ورانہ رہیں۔"
    };

    return prompts[languageCode] || prompts.en;
};
