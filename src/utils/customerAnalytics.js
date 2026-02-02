/**
 * Enterprise Retail Intelligence System v3.0
 * CUSTOMER ANALYTICS - LTV, Churn, and Cohort Analysis
 */

/**
 * Calculate Customer Lifetime Value (LTV)
 * @param {Object} customer - Customer object
 * @returns {number} Lifetime value
 */
export const calculateLTV = (customer) => {
    // Simple LTV = Total Spent (actual historical value)
    // For more sophisticated: Average Order Value * Purchase Frequency * Customer Lifespan
    const accountAge = Math.floor(
        (new Date() - new Date(customer.registrationDate)) / (1000 * 60 * 60 * 24)
    );

    // Avoid division by zero
    if (accountAge === 0) return customer.totalSpent;

    // Projected annual value based on current rate
    const dailyValue = customer.totalSpent / accountAge;
    const projectedAnnualValue = dailyValue * 365;

    // Assume 3-year customer lifespan for prediction
    const predictedLTV = projectedAnnualValue * 3;

    return Math.floor(predictedLTV);
};

/**
 * Predict churn risk for a customer (0-100)
 * @param {Object} customer - Customer object
 * @returns {number} Churn risk percentage
 */
export const predictChurnRisk = (customer) => {
    const today = new Date();
    const lastPurchase = new Date(customer.lastPurchaseDate);
    const daysSinceLastPurchase = Math.floor((today - lastPurchase) / (1000 * 60 * 60 * 24));

    // Base risk on recency
    let riskScore = 0;

    // Recency factor (0-40 points)
    if (daysSinceLastPurchase > 180) riskScore += 40;
    else if (daysSinceLastPurchase > 120) riskScore += 30;
    else if (daysSinceLastPurchase > 90) riskScore += 20;
    else if (daysSinceLastPurchase > 60) riskScore += 10;

    // Frequency factor (0-30 points) - inverse relationship
    if (customer.totalPurchases < 2) riskScore += 30;
    else if (customer.totalPurchases < 5) riskScore += 20;
    else if (customer.totalPurchases < 10) riskScore += 10;
    else if (customer.totalPurchases < 20) riskScore += 5;

    // Monetary factor (0-20 points) - inverse relationship
    if (customer.totalSpent < 10000) riskScore += 20;
    else if (customer.totalSpent < 25000) riskScore += 15;
    else if (customer.totalSpent < 50000) riskScore += 10;
    else if (customer.totalSpent < 100000) riskScore += 5;

    // Purchase frequency pattern (0-10 points)
    if (customer.purchaseFrequency > 60) riskScore += 10;
    else if (customer.purchaseFrequency > 45) riskScore += 7;
    else if (customer.purchaseFrequency > 30) riskScore += 4;

    return Math.min(riskScore, 100);
};

/**
 * Get churn risk category
 * @param {number} riskScore - Churn risk score (0-100)
 * @returns {Object} Risk category info
 */
export const getChurnRiskCategory = (riskScore) => {
    if (riskScore >= 70) {
        return {
            level: 'High',
            color: 'text-danger',
            bgColor: 'bg-danger/20',
            borderColor: 'border-danger/30',
            action: 'Immediate intervention required'
        };
    } else if (riskScore >= 40) {
        return {
            level: 'Medium',
            color: 'text-warning',
            bgColor: 'bg-warning/20',
            borderColor: 'border-warning/30',
            action: 'Monitor and engage'
        };
    } else {
        return {
            level: 'Low',
            color: 'text-success',
            bgColor: 'bg-success/20',
            borderColor: 'border-success/30',
            action: 'Maintain relationship'
        };
    }
};

/**
 * Group customers by acquisition cohort (month)
 * @param {Array} customers - Array of customer objects
 * @returns {Object} Cohorts by month
 */
export const getCustomerCohorts = (customers) => {
    const cohorts = {};

    customers.forEach(customer => {
        const registrationDate = new Date(customer.registrationDate);
        const cohortKey = `${registrationDate.getFullYear()}-${String(registrationDate.getMonth() + 1).padStart(2, '0')}`;

        if (!cohorts[cohortKey]) {
            cohorts[cohortKey] = {
                month: cohortKey,
                customers: [],
                totalCustomers: 0,
                totalRevenue: 0,
                activeCustomers: 0
            };
        }

        cohorts[cohortKey].customers.push(customer);
        cohorts[cohortKey].totalCustomers++;
        cohorts[cohortKey].totalRevenue += customer.totalSpent;

        // Active if purchased in last 90 days
        const daysSinceLastPurchase = Math.floor(
            (new Date() - new Date(customer.lastPurchaseDate)) / (1000 * 60 * 60 * 24)
        );
        if (daysSinceLastPurchase <= 90) {
            cohorts[cohortKey].activeCustomers++;
        }
    });

    // Calculate retention rate for each cohort
    Object.keys(cohorts).forEach(key => {
        cohorts[key].retentionRate = (
            (cohorts[key].activeCustomers / cohorts[key].totalCustomers) * 100
        ).toFixed(1);
    });

    return cohorts;
};

/**
 * Get top customers by total spent
 * @param {Array} customers - Array of customer objects
 * @param {number} limit - Number of top customers to return
 * @returns {Array} Top customers
 */
export const getTopCustomers = (customers, limit = 20) => {
    return [...customers]
        .sort((a, b) => b.totalSpent - a.totalSpent)
        .slice(0, limit);
};

/**
 * Get customers at risk of churning
 * @param {Array} customers - Array of customer objects
 * @param {number} threshold - Minimum churn risk threshold (default 70)
 * @returns {Array} At-risk customers
 */
export const getAtRiskCustomers = (customers, threshold = 70) => {
    return customers
        .filter(customer => customer.churnRisk >= threshold)
        .sort((a, b) => b.churnRisk - a.churnRisk);
};

/**
 * Calculate customer metrics summary
 * @param {Array} customers - Array of customer objects
 * @returns {Object} Summary metrics
 */
export const getCustomerMetrics = (customers) => {
    const totalCustomers = customers.length;
    const totalRevenue = customers.reduce((sum, c) => sum + c.totalSpent, 0);
    const totalPurchases = customers.reduce((sum, c) => sum + c.totalPurchases, 0);

    // Active customers (purchased in last 90 days)
    const activeCustomers = customers.filter(c => {
        const daysSince = Math.floor(
            (new Date() - new Date(c.lastPurchaseDate)) / (1000 * 60 * 60 * 24)
        );
        return daysSince <= 90;
    }).length;

    // New customers (registered in last 30 days)
    const newCustomers = customers.filter(c => {
        const daysSince = Math.floor(
            (new Date() - new Date(c.registrationDate)) / (1000 * 60 * 60 * 24)
        );
        return daysSince <= 30;
    }).length;

    // Average metrics
    const avgOrderValue = totalRevenue / totalPurchases;
    const avgCustomerValue = totalRevenue / totalCustomers;
    const avgPurchasesPerCustomer = totalPurchases / totalCustomers;

    // Retention rate (active / total)
    const retentionRate = (activeCustomers / totalCustomers) * 100;

    // Churn rate (inverse of retention)
    const churnRate = 100 - retentionRate;

    return {
        totalCustomers,
        activeCustomers,
        newCustomers,
        totalRevenue,
        totalPurchases,
        avgOrderValue: Math.floor(avgOrderValue),
        avgCustomerValue: Math.floor(avgCustomerValue),
        avgPurchasesPerCustomer: avgPurchasesPerCustomer.toFixed(1),
        retentionRate: retentionRate.toFixed(1),
        churnRate: churnRate.toFixed(1)
    };
};

/**
 * Get customer growth trend (monthly)
 * @param {Array} customers - Array of customer objects
 * @returns {Array} Monthly growth data
 */
export const getCustomerGrowthTrend = (customers) => {
    const monthlyData = {};

    customers.forEach(customer => {
        const regDate = new Date(customer.registrationDate);
        const monthKey = `${regDate.getFullYear()}-${String(regDate.getMonth() + 1).padStart(2, '0')}`;

        if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = {
                month: monthKey,
                newCustomers: 0,
                revenue: 0
            };
        }

        monthlyData[monthKey].newCustomers++;
        monthlyData[monthKey].revenue += customer.totalSpent;
    });

    // Convert to array and sort by month
    return Object.values(monthlyData).sort((a, b) => a.month.localeCompare(b.month));
};

/**
 * Get demographic breakdown
 * @param {Array} customers - Array of customer objects
 * @returns {Object} Demographic statistics
 */
export const getDemographicBreakdown = (customers) => {
    const ageGroups = { '18-25': 0, '26-35': 0, '36-45': 0, '46-60': 0 };
    const genders = { Male: 0, Female: 0, Other: 0 };
    const locations = {};
    const categories = {};

    customers.forEach(customer => {
        // Age groups
        const age = customer.demographics.age;
        if (age >= 18 && age <= 25) ageGroups['18-25']++;
        else if (age >= 26 && age <= 35) ageGroups['26-35']++;
        else if (age >= 36 && age <= 45) ageGroups['36-45']++;
        else if (age >= 46 && age <= 60) ageGroups['46-60']++;

        // Gender
        genders[customer.demographics.gender]++;

        // Location
        const loc = customer.demographics.location;
        locations[loc] = (locations[loc] || 0) + 1;

        // Preferred category
        const cat = customer.demographics.preferredCategory;
        categories[cat] = (categories[cat] || 0) + 1;
    });

    return {
        ageGroups,
        genders,
        locations,
        categories
    };
};
