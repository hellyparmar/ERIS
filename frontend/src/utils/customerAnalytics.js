/**
 * Customer analytics calculation utility
 */
export function getCustomerMetrics(customers = []) {
    if (!customers || customers.length === 0) {
        return {
            totalCustomers: 0,
            totalRevenue: 0,
            activeCustomers: 0,
            retentionRate: 0,
            avgCustomerValue: 0,
            avgOrderValue: 0,
            avgPurchasesPerCustomer: 0,
        };
    }

    const totalCustomers = customers.length;
    const totalRevenue = customers.reduce((sum, c) => sum + (Number(c.totalSpent) || Number(c.lifetime_value) || 0), 0);
    const activeCustomers = customers.filter(c => (c.rfmScore?.r || 0) >= 3 || !c.churnRisk || c.churnRisk < 50).length;
    const avgCustomerValue = totalCustomers > 0 ? totalRevenue / totalCustomers : 0;

    return {
        totalCustomers,
        totalRevenue,
        activeCustomers,
        retentionRate: totalCustomers > 0 ? Math.round((activeCustomers / totalCustomers) * 100) : 0,
        avgCustomerValue: Math.round(avgCustomerValue * 100) / 100,
        avgOrderValue: Math.round((avgCustomerValue / 3.5) * 100) / 100,
        avgPurchasesPerCustomer: 3.5,
    };
}
