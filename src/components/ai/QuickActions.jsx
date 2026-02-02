import React from 'react';
import { motion } from 'framer-motion';
import {
    TrendingUp, Package, AlertTriangle, BarChart3,
    Users, DollarSign, ShoppingCart, Calendar,
    Target, TrendingDown, FileText, Zap
} from 'lucide-react';

/**
 * QuickActions Component
 * Pre-defined common queries for quick access - Enhanced with more actions
 */
const QuickActions = ({ onActionClick, currentLanguage }) => {
    // Quick action templates in multiple languages - Expanded
    const actions = {
        en: [
            { icon: TrendingUp, text: "Today's sales summary", query: "Show me today's sales summary" },
            { icon: Package, text: "Low stock products", query: "What products are low in stock?" },
            { icon: AlertTriangle, text: "Critical alerts", query: "Show me critical inventory alerts" },
            { icon: BarChart3, text: "Sales forecast", query: "Generate a 7-day sales forecast" },
            { icon: Users, text: "Top customers", query: "Who are my top 10 customers this month?" },
            { icon: DollarSign, text: "Revenue analysis", query: "Analyze my revenue trends for the last 30 days" },
            { icon: ShoppingCart, text: "Best selling items", query: "What are my best selling products?" },
            { icon: Calendar, text: "Weekly report", query: "Generate a weekly sales report" },
            { icon: Target, text: "Sales targets", query: "Am I meeting my sales targets?" },
            { icon: TrendingDown, text: "Slow movers", query: "Which products are moving slowly?" },
            { icon: FileText, text: "Inventory report", query: "Generate an inventory status report" },
            { icon: Zap, text: "Quick insights", query: "Give me quick business insights" }
        ],
        hi: [
            { icon: TrendingUp, text: "आज की बिक्री सारांश", query: "मुझे आज की बिक्री का सारांश दिखाएं" },
            { icon: Package, text: "कम स्टॉक उत्पाद", query: "कौन से उत्पाद कम स्टॉक में हैं?" },
            { icon: AlertTriangle, text: "महत्वपूर्ण अलर्ट", query: "मुझे महत्वपूर्ण इन्वेंटरी अलर्ट दिखाएं" },
            { icon: BarChart3, text: "बिक्री पूर्वानुमान", query: "7-दिन का बिक्री पूर्वानुमान बनाएं" },
            { icon: Users, text: "शीर्ष ग्राहक", query: "इस महीने मेरे शीर्ष 10 ग्राहक कौन हैं?" },
            { icon: DollarSign, text: "राजस्व विश्लेषण", query: "पिछले 30 दिनों के लिए मेरे राजस्व रुझानों का विश्लेषण करें" },
            { icon: ShoppingCart, text: "सबसे अधिक बिकने वाले आइटम", query: "मेरे सबसे अधिक बिकने वाले उत्पाद क्या हैं?" },
            { icon: Calendar, text: "साप्ताहिक रिपोर्ट", query: "एक साप्ताहिक बिक्री रिपोर्ट बनाएं" }
        ],
        gu: [
            { icon: TrendingUp, text: "આજનો વેચાણ સારાંશ", query: "મને આજનો વેચાણ સારાંશ બતાવો" },
            { icon: Package, text: "ઓછા સ્ટોક ઉત્પાદનો", query: "કયા ઉત્પાદનો ઓછા સ્ટોકમાં છે?" },
            { icon: AlertTriangle, text: "મહત્વપૂર્ણ ચેતવણીઓ", query: "મને મહત્વપૂર્ણ ઇન્વેન્ટરી ચેતવણીઓ બતાવો" },
            { icon: BarChart3, text: "વેચાણ આગાહી", query: "7-દિવસની વેચાણ આગાહી બનાવો" },
            { icon: Users, text: "ટોચના ગ્રાહકો", query: "આ મહિને મારા ટોચના 10 ગ્રાહકો કોણ છે?" },
            { icon: DollarSign, text: "આવક વિશ્લેષણ", query: "છેલ્લા 30 દિવસ માટે મારા આવક વલણોનું વિશ્લેષણ કરો" },
            { icon: ShoppingCart, text: "સૌથી વધુ વેચાતી વસ્તુઓ", query: "મારા સૌથી વધુ વેચાતા ઉત્પાદનો શું છે?" },
            { icon: Calendar, text: "સાપ્તાહિક રિપોર્ટ", query: "સાપ્તાહિક વેચાણ રિપોર્ટ બનાવો" }
        ],
        mr: [
            { icon: TrendingUp, text: "आजचा विक्री सारांश", query: "मला आजचा विक्री सारांश दाखवा" },
            { icon: Package, text: "कमी स्टॉक उत्पादने", query: "कोणती उत्पादने कमी स्टॉकमध्ये आहेत?" },
            { icon: AlertTriangle, text: "महत्त्वाचे इशारे", query: "मला महत्त्वाचे इन्व्हेंटरी इशारे दाखवा" },
            { icon: BarChart3, text: "विक्री अंदाज", query: "7-दिवसांचा विक्री अंदाज तयार करा" },
            { icon: Users, text: "शीर्ष ग्राहक", query: "या महिन्यात माझे शीर्ष 10 ग्राहक कोण आहेत?" },
            { icon: DollarSign, text: "महसूल विश्लेषण", query: "गेल्या 30 दिवसांसाठी माझ्या महसूल ट्रेंडचे विश्लेषण करा" },
            { icon: ShoppingCart, text: "सर्वाधिक विकली जाणारी वस्तू", query: "माझी सर्वाधिक विकली जाणारी उत्पादने कोणती आहेत?" },
            { icon: Calendar, text: "साप्ताहिक अहवाल", query: "साप्ताहिक विक्री अहवाल तयार करा" }
        ],
        ta: [
            { icon: TrendingUp, text: "இன்றைய விற்பனை சுருக்கம்", query: "இன்றைய விற்பனை சுருக்கத்தைக் காட்டு" },
            { icon: Package, text: "குறைந்த சரக்கு தயாரிப்புகள்", query: "எந்த தயாரிப்புகள் குறைந்த சரக்கில் உள்ளன?" },
            { icon: AlertTriangle, text: "முக்கிய எச்சரிக்கைகள்", query: "முக்கிய சரக்கு எச்சரிக்கைகளைக் காட்டு" },
            { icon: BarChart3, text: "விற்பனை முன்னறிவிப்பு", query: "7-நாள் விற்பனை முன்னறிவிப்பை உருவாக்கு" },
            { icon: Users, text: "சிறந்த வாடிக்கையாளர்கள்", query: "இந்த மாதம் எனது சிறந்த 10 வாடிக்கையாளர்கள் யார்?" },
            { icon: DollarSign, text: "வருவாய் பகுப்பாய்வு", query: "கடந்த 30 நாட்களுக்கான எனது வருவாய் போக்குகளை பகுப்பாய்வு செய்" },
            { icon: ShoppingCart, text: "அதிகம் விற்பனையாகும் பொருட்கள்", query: "எனது அதிகம் விற்பனையாகும் தயாரிப்புகள் என்ன?" },
            { icon: Calendar, text: "வாராந்திர அறிக்கை", query: "வாராந்திர விற்பனை அறிக்கையை உருவாக்கு" }
        ],
        te: [
            { icon: TrendingUp, text: "నేటి అమ్మకాల సారాంశం", query: "నాకు నేటి అమ్మకాల సారాంశం చూపించు" },
            { icon: Package, text: "తక్కువ స్టాక్ ఉత్పత్తులు", query: "ఏ ఉత్పత్తులు తక్కువ స్టాక్‌లో ఉన్నాయి?" },
            { icon: AlertTriangle, text: "కీలక హెచ్చరికలు", query: "నాకు కీలక ఇన్వెంటరీ హెచ్చరికలు చూపించు" },
            { icon: BarChart3, text: "అమ్మకాల అంచనా", query: "7-రోజుల అమ్మకాల అంచనా రూపొందించు" },
            { icon: Users, text: "అగ్ర వినియోగదారులు", query: "ఈ నెలలో నా అగ్ర 10 వినియోగదారులు ఎవరు?" },
            { icon: DollarSign, text: "ఆదాయ విశ్లేషణ", query: "గత 30 రోజుల కోసం నా ఆదాయ ధోరణులను విశ్లేషించు" },
            { icon: ShoppingCart, text: "అత్యధికంగా అమ్ముడయ్యే వస్తువులు", query: "నా అత్యధికంగా అమ్ముడయ్యే ఉత్పత్తులు ఏమిటి?" },
            { icon: Calendar, text: "వారపు నివేదిక", query: "వారపు అమ్మకాల నివేదికను రూపొందించు" }
        ],
        ur: [
            { icon: TrendingUp, text: "آج کی فروخت کا خلاصہ", query: "مجھے آج کی فروخت کا خلاصہ دکھائیں" },
            { icon: Package, text: "کم اسٹاک مصنوعات", query: "کون سی مصنوعات کم اسٹاک میں ہیں؟" },
            { icon: AlertTriangle, text: "اہم الرٹس", query: "مجھے اہم انوینٹری الرٹس دکھائیں" },
            { icon: BarChart3, text: "فروخت کی پیش گوئی", query: "7 دن کی فروخت کی پیش گوئی بنائیں" },
            { icon: Users, text: "اعلیٰ صارفین", query: "اس ماہ میرے اعلیٰ 10 صارفین کون ہیں؟" },
            { icon: DollarSign, text: "آمدنی کا تجزیہ", query: "پچھلے 30 دنوں کے لیے میری آمدنی کے رجحانات کا تجزیہ کریں" },
            { icon: ShoppingCart, text: "سب سے زیادہ فروخت ہونے والی اشیاء", query: "میری سب سے زیادہ فروخت ہونے والی مصنوعات کیا ہیں?" },
            { icon: Calendar, text: "ہفتہ وار رپورٹ", query: "ہفتہ وار فروخت کی رپورٹ بنائیں" }
        ]
    };

    const currentActions = actions[currentLanguage] || actions.en;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[600px] overflow-y-auto pr-2">
            {currentActions.map((action, index) => (
                <motion.button
                    key={index}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => onActionClick(action.query)}
                    className="flex items-center gap-3 p-3 bg-white/5 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg hover:shadow-md dark:hover:shadow-blue-500/20 dark:hover:border-blue-500/50 transition-all text-left group"
                >
                    <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex-shrink-0">
                        <action.icon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {action.text}
                    </span>
                </motion.button>
            ))}
        </div>
    );
};

export default QuickActions;
