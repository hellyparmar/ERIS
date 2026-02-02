/**
 * Enterprise Retail Intelligence System v3.0
 * TAX CALCULATIONS - GST and compliance utilities
 */

// Indian GST rates
export const GST_RATES = {
    EXEMPT: 0,
    RATE_5: 5,
    RATE_12: 12,
    RATE_18: 18,
    RATE_28: 28
};

// Product categories and their GST rates
export const CATEGORY_GST_MAPPING = {
    'Food & Beverages': GST_RATES.RATE_5,
    'Groceries': GST_RATES.RATE_5,
    'Electronics': GST_RATES.RATE_18,
    'Clothing': GST_RATES.RATE_12,
    'Footwear': GST_RATES.RATE_5,
    'Household': GST_RATES.RATE_18,
    'Personal Care': GST_RATES.RATE_18,
    'Luxury': GST_RATES.RATE_28
};

/**
 * Calculate GST amount from base price
 */
export const calculateGST = (basePrice, gstRate) => {
    return (basePrice * gstRate) / 100;
};

/**
 * Calculate price including GST
 */
export const calculatePriceWithGST = (basePrice, gstRate) => {
    return basePrice + calculateGST(basePrice, gstRate);
};

/**
 * Extract GST from final price
 */
export const extractGSTFromPrice = (finalPrice, gstRate) => {
    return (finalPrice * gstRate) / (100 + gstRate);
};

/**
 * Calculate base price from final price
 */
export const calculateBasePrice = (finalPrice, gstRate) => {
    return finalPrice - extractGSTFromPrice(finalPrice, gstRate);
};

/**
 * Generate mock tax transactions
 */
export const generateTaxTransactions = (count = 50) => {
    const categories = Object.keys(CATEGORY_GST_MAPPING);
    const transactions = [];

    for (let i = 0; i < count; i++) {
        const category = categories[Math.floor(Math.random() * categories.length)];
        const gstRate = CATEGORY_GST_MAPPING[category];
        const basePrice = Math.floor(Math.random() * 5000) + 100;
        const gstAmount = calculateGST(basePrice, gstRate);
        const finalPrice = basePrice + gstAmount;

        const date = new Date();
        date.setDate(date.getDate() - Math.floor(Math.random() * 90)); // Last 90 days

        transactions.push({
            id: `TXN${String(i + 1).padStart(5, '0')}`,
            date,
            category,
            basePrice,
            gstRate,
            gstAmount,
            finalPrice,
            invoiceNumber: `INV-2024-${String(i + 1).padStart(5, '0')}`,
            customerName: `Customer ${i + 1}`,
            status: Math.random() > 0.1 ? 'Filed' : 'Pending'
        });
    }

    return transactions.sort((a, b) => b.date - a.date);
};

/**
 * Calculate tax summary from transactions
 */
export const calculateTaxSummary = (transactions) => {
    const summary = {
        totalTransactions: transactions.length,
        totalRevenue: 0,
        totalGST: 0,
        byRate: {},
        byCategory: {},
        byMonth: {},
        filedCount: 0,
        pendingCount: 0
    };

    transactions.forEach(txn => {
        summary.totalRevenue += txn.finalPrice;
        summary.totalGST += txn.gstAmount;

        // By rate
        if (!summary.byRate[txn.gstRate]) {
            summary.byRate[txn.gstRate] = { count: 0, gst: 0, revenue: 0 };
        }
        summary.byRate[txn.gstRate].count++;
        summary.byRate[txn.gstRate].gst += txn.gstAmount;
        summary.byRate[txn.gstRate].revenue += txn.finalPrice;

        // By category
        if (!summary.byCategory[txn.category]) {
            summary.byCategory[txn.category] = { count: 0, gst: 0, revenue: 0 };
        }
        summary.byCategory[txn.category].count++;
        summary.byCategory[txn.category].gst += txn.gstAmount;
        summary.byCategory[txn.category].revenue += txn.finalPrice;

        // By month
        const monthKey = `${txn.date.getFullYear()}-${String(txn.date.getMonth() + 1).padStart(2, '0')}`;
        if (!summary.byMonth[monthKey]) {
            summary.byMonth[monthKey] = { count: 0, gst: 0, revenue: 0 };
        }
        summary.byMonth[monthKey].count++;
        summary.byMonth[monthKey].gst += txn.gstAmount;
        summary.byMonth[monthKey].revenue += txn.finalPrice;

        // Status
        if (txn.status === 'Filed') summary.filedCount++;
        else summary.pendingCount++;
    });

    return summary;
};

/**
 * Get compliance status
 */
export const getComplianceStatus = (transactions) => {
    const summary = calculateTaxSummary(transactions);
    const filingRate = (summary.filedCount / summary.totalTransactions) * 100;

    return {
        status: filingRate >= 95 ? 'Compliant' : filingRate >= 80 ? 'Warning' : 'Non-Compliant',
        filingRate: parseFloat(filingRate.toFixed(1)),
        pendingReturns: summary.pendingCount,
        nextDeadline: getNextDeadline()
    };
};

/**
 * Get next GST filing deadline
 */
export const getNextDeadline = () => {
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    // GST filing is typically on 20th of next month
    let deadlineMonth = currentMonth + 1;
    let deadlineYear = currentYear;

    if (deadlineMonth > 11) {
        deadlineMonth = 0;
        deadlineYear++;
    }

    return new Date(deadlineYear, deadlineMonth, 20);
};

/**
 * Format currency for display
 */
export const formatCurrency = (value) => {
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(2)}Cr`;
    if (value >= 100000) return `₹${(value / 100000).toFixed(2)}L`;
    if (value >= 1000) return `₹${(value / 1000).toFixed(2)}k`;
    return `₹${value.toFixed(2)}`;
};
