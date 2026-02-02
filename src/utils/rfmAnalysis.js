/**
 * Enterprise Retail Intelligence System v3.0
 * RFM ANALYSIS - Customer Segmentation Utilities
 */

/**
 * Calculate RFM scores for a customer
 * R (Recency): How recently did the customer purchase?
 * F (Frequency): How often do they purchase?
 * M (Monetary): How much do they spend?
 * 
 * @param {Object} customer - Customer object
 * @param {Date} referenceDate - Reference date for recency calculation (usually today)
 * @returns {Object} RFM scores { r, f, m }
 */
export const calculateRFM = (customer, referenceDate = new Date()) => {
    // Calculate Recency (days since last purchase)
    const lastPurchase = new Date(customer.lastPurchaseDate);
    const daysSinceLastPurchase = Math.floor((referenceDate - lastPurchase) / (1000 * 60 * 60 * 24));

    // Recency Score (1-5, where 5 is most recent)
    let r;
    if (daysSinceLastPurchase <= 30) r = 5;
    else if (daysSinceLastPurchase <= 60) r = 4;
    else if (daysSinceLastPurchase <= 90) r = 3;
    else if (daysSinceLastPurchase <= 180) r = 2;
    else r = 1;

    // Frequency Score (1-5, based on total purchases)
    let f;
    if (customer.totalPurchases >= 20) f = 5;
    else if (customer.totalPurchases >= 10) f = 4;
    else if (customer.totalPurchases >= 5) f = 3;
    else if (customer.totalPurchases >= 2) f = 2;
    else f = 1;

    // Monetary Score (1-5, based on total spent)
    let m;
    if (customer.totalSpent >= 100000) m = 5; // ₹1 Lakh+
    else if (customer.totalSpent >= 50000) m = 4; // ₹50k+
    else if (customer.totalSpent >= 25000) m = 3; // ₹25k+
    else if (customer.totalSpent >= 10000) m = 2; // ₹10k+
    else m = 1;

    return { r, f, m };
};

/**
 * Assign customer segment based on RFM scores
 * @param {Object} rfmScore - RFM scores { r, f, m }
 * @returns {string} Segment name
 */
export const assignRFMSegment = (rfmScore) => {
    const { r, f, m } = rfmScore;

    // Champions: Best customers - bought recently, buy often, spend the most
    if (r >= 4 && f >= 4 && m >= 4) return 'Champions';

    // Loyal Customers: Spend good money, buy regularly
    if (r >= 3 && f >= 4 && m >= 3) return 'Loyal Customers';

    // Potential Loyalists: Recent customers with good frequency
    if (r >= 4 && f >= 2 && m >= 2) return 'Potential Loyalists';

    // Recent Customers: Bought recently but not frequently
    if (r >= 4 && f <= 2 && m <= 3) return 'Recent Customers';

    // Promising: Recent shoppers but haven't spent much
    if (r >= 3 && f <= 2 && m <= 2) return 'Promising';

    // Need Attention: Above average recency, frequency, and monetary
    if (r >= 3 && f >= 3 && m >= 3) return 'Need Attention';

    // About to Sleep: Below average recency, frequency, and monetary
    if (r >= 2 && f >= 2 && m >= 2) return 'About to Sleep';

    // At Risk: Spent big money, purchased often but long time ago
    if (r <= 2 && f >= 4 && m >= 4) return 'At Risk';

    // Can't Lose Them: Made big purchases and often but long time ago
    if (r <= 2 && f >= 4 && m >= 5) return "Can't Lose Them";

    // Hibernating: Last purchase was long ago, low spenders, low frequency
    if (r <= 2 && f <= 2 && m <= 3) return 'Hibernating';

    // Lost: Lowest recency, frequency, and monetary scores
    if (r <= 1 && f <= 2 && m <= 2) return 'Lost';

    // Default fallback
    return 'Need Attention';
};

/**
 * Get segment color for UI display
 * @param {string} segment - Segment name
 * @returns {Object} Color configuration
 */
export const getSegmentColor = (segment) => {
    const colors = {
        'Champions': {
            bg: 'from-yellow-400 to-orange-500',
            text: 'text-yellow-600 dark:text-yellow-400',
            border: 'border-yellow-500/30',
            glow: 'shadow-glow-warning'
        },
        'Loyal Customers': {
            bg: 'from-blue-400 to-blue-600',
            text: 'text-blue-600 dark:text-blue-400',
            border: 'border-blue-500/30',
            glow: 'shadow-glow-primary'
        },
        'Potential Loyalists': {
            bg: 'from-green-400 to-green-600',
            text: 'text-green-600 dark:text-green-400',
            border: 'border-green-500/30',
            glow: 'shadow-glow-success'
        },
        'Recent Customers': {
            bg: 'from-cyan-400 to-cyan-600',
            text: 'text-cyan-600 dark:text-cyan-400',
            border: 'border-cyan-500/30',
            glow: 'shadow-glow-primary'
        },
        'Promising': {
            bg: 'from-teal-400 to-teal-600',
            text: 'text-teal-600 dark:text-teal-400',
            border: 'border-teal-500/30',
            glow: 'shadow-glow-success'
        },
        'Need Attention': {
            bg: 'from-purple-400 to-purple-600',
            text: 'text-purple-600 dark:text-purple-400',
            border: 'border-purple-500/30',
            glow: 'shadow-glow-primary'
        },
        'About to Sleep': {
            bg: 'from-orange-400 to-orange-600',
            text: 'text-orange-600 dark:text-orange-400',
            border: 'border-orange-500/30',
            glow: 'shadow-glow-warning'
        },
        'At Risk': {
            bg: 'from-red-400 to-red-600',
            text: 'text-red-600 dark:text-red-400',
            border: 'border-red-500/30',
            glow: 'shadow-glow-danger'
        },
        "Can't Lose Them": {
            bg: 'from-pink-500 to-red-600',
            text: 'text-pink-600 dark:text-pink-400',
            border: 'border-pink-500/30',
            glow: 'shadow-glow-danger'
        },
        'Hibernating': {
            bg: 'from-gray-400 to-gray-600',
            text: 'text-gray-600 dark:text-gray-400',
            border: 'border-gray-500/30',
            glow: ''
        },
        'Lost': {
            bg: 'from-slate-400 to-slate-600',
            text: 'text-slate-600 dark:text-slate-400',
            border: 'border-slate-500/30',
            glow: ''
        }
    };

    return colors[segment] || colors['Need Attention'];
};

/**
 * Get recommended action for segment
 * @param {string} segment - Segment name
 * @returns {string} Recommended action
 */
export const getSegmentAction = (segment) => {
    const actions = {
        'Champions': 'Reward them! Offer exclusive deals and early access.',
        'Loyal Customers': 'Upsell higher value products. Ask for reviews.',
        'Potential Loyalists': 'Offer membership or loyalty program.',
        'Recent Customers': 'Provide onboarding support and product recommendations.',
        'Promising': 'Create brand awareness. Offer free shipping.',
        'Need Attention': 'Make limited time offers. Recommend based on history.',
        'About to Sleep': 'Share valuable resources. Recommend popular products.',
        'At Risk': 'Send personalized emails. Offer renewals or helpful products.',
        "Can't Lose Them": 'Win them back via surveys, renewals, and helpful products.',
        'Hibernating': 'Offer other relevant products and special discounts.',
        'Lost': 'Revive interest with reach out campaign. Ignore otherwise.'
    };

    return actions[segment] || 'Monitor customer activity.';
};

/**
 * Get RFM distribution across all customers
 * @param {Array} customers - Array of customer objects
 * @returns {Object} Distribution by segment
 */
export const getRFMDistribution = (customers) => {
    const distribution = {};

    customers.forEach(customer => {
        const segment = customer.segment || 'Unknown';
        if (!distribution[segment]) {
            distribution[segment] = {
                count: 0,
                totalValue: 0,
                avgValue: 0,
                percentage: 0
            };
        }
        distribution[segment].count++;
        distribution[segment].totalValue += customer.totalSpent;
    });

    // Calculate averages and percentages
    const totalCustomers = customers.length;
    Object.keys(distribution).forEach(segment => {
        distribution[segment].avgValue = Math.floor(distribution[segment].totalValue / distribution[segment].count);
        distribution[segment].percentage = ((distribution[segment].count / totalCustomers) * 100).toFixed(1);
    });

    return distribution;
};

/**
 * Process customers with RFM analysis
 * @param {Array} customers - Array of customer objects
 * @returns {Array} Customers with RFM scores and segments
 */
export const processCustomersWithRFM = (customers) => {
    return customers.map(customer => {
        const rfmScore = calculateRFM(customer);
        const segment = assignRFMSegment(rfmScore);

        return {
            ...customer,
            rfmScore,
            segment
        };
    });
};
