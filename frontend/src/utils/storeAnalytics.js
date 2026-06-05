/**
 * Enterprise Retail Intelligence System v3.0
 * STORE ANALYTICS - Performance analysis and comparison utilities
 */

/**
 * Calculate overall store network metrics
 */
export const getNetworkMetrics = (stores) => {
    const totalStores = stores.length;
    const activeStores = stores.filter(s => s.operational.status === 'Active').length;
    const totalRevenue = stores.reduce((sum, s) => sum + s.performance.monthlyRevenue, 0);
    const totalFootfall = stores.reduce((sum, s) => sum + s.performance.footfall, 0);
    const avgRevenue = totalRevenue / totalStores;
    const avgGrowth = stores.reduce((sum, s) => sum + s.metrics.salesGrowth, 0) / totalStores;

    return {
        totalStores,
        activeStores,
        totalRevenue,
        avgRevenue: Math.floor(avgRevenue),
        totalFootfall,
        avgFootfall: Math.floor(totalFootfall / totalStores),
        avgGrowth: parseFloat(avgGrowth.toFixed(1)),
        avgSatisfaction: parseFloat((stores.reduce((sum, s) => sum + s.metrics.customerSatisfaction, 0) / totalStores).toFixed(1))
    };
};

/**
 * Get store performance trends (monthly data)
 */
export const getStorePerformanceTrends = (stores) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    return months.map((month, idx) => {
        // Simulate monthly variation
        const seasonalFactor = 0.8 + Math.sin(idx / 12 * Math.PI * 2) * 0.2;
        const totalRevenue = stores.reduce((sum, s) => {
            return sum + (s.performance.monthlyRevenue * seasonalFactor * (0.9 + Math.random() * 0.2));
        }, 0);

        return {
            month,
            revenue: Math.floor(totalRevenue),
            stores: stores.length,
            avgPerStore: Math.floor(totalRevenue / stores.length)
        };
    });
};

/**
 * Compare store performance against network average
 */
export const compareStorePerformance = (store, stores) => {
    const metrics = getNetworkMetrics(stores);

    return {
        revenueVsAvg: parseFloat(((store.performance.monthlyRevenue / metrics.avgRevenue - 1) * 100).toFixed(1)),
        footfallVsAvg: parseFloat(((store.performance.footfall / metrics.avgFootfall - 1) * 100).toFixed(1)),
        growthVsAvg: parseFloat((store.metrics.salesGrowth - metrics.avgGrowth).toFixed(1)),
        satisfactionVsAvg: parseFloat((store.metrics.customerSatisfaction - metrics.avgSatisfaction).toFixed(1))
    };
};

/**
 * Get store rankings
 */
export const getStoreRankings = (stores) => {
    const sortedByRevenue = [...stores].sort((a, b) => b.performance.monthlyRevenue - a.performance.monthlyRevenue);
    const sortedByGrowth = [...stores].sort((a, b) => b.metrics.salesGrowth - a.metrics.salesGrowth);
    const sortedBySatisfaction = [...stores].sort((a, b) => b.metrics.customerSatisfaction - a.metrics.customerSatisfaction);

    return stores.map(store => ({
        storeId: store.id,
        storeName: store.name,
        revenueRank: sortedByRevenue.findIndex(s => s.id === store.id) + 1,
        growthRank: sortedByGrowth.findIndex(s => s.id === store.id) + 1,
        satisfactionRank: sortedBySatisfaction.findIndex(s => s.id === store.id) + 1
    }));
};

/**
 * Identify underperforming stores
 */
export const getUnderperformingStores = (stores, threshold = -5) => {
    return stores.filter(s => s.metrics.salesGrowth < threshold)
        .sort((a, b) => a.metrics.salesGrowth - b.metrics.salesGrowth);
};

/**
 * Get stores needing attention
 */
export const getStoresNeedingAttention = (stores) => {
    const metrics = getNetworkMetrics(stores);

    return stores.filter(store => {
        const hasLowRevenue = store.performance.monthlyRevenue < metrics.avgRevenue * 0.7;
        const hasNegativeGrowth = store.metrics.salesGrowth < 0;
        const hasLowSatisfaction = store.metrics.customerSatisfaction < 4.0;
        const hasLowConversion = store.performance.conversionRate < 20;

        return hasLowRevenue || hasNegativeGrowth || hasLowSatisfaction || hasLowConversion;
    }).map(store => ({
        ...store,
        issues: [
            store.performance.monthlyRevenue < metrics.avgRevenue * 0.7 && 'Low Revenue',
            store.metrics.salesGrowth < 0 && 'Negative Growth',
            store.metrics.customerSatisfaction < 4.0 && 'Low Satisfaction',
            store.performance.conversionRate < 20 && 'Low Conversion'
        ].filter(Boolean)
    }));
};

/**
 * Calculate inventory distribution across stores
 */
export const getInventoryDistribution = (stores) => {
    const totalInventory = stores.reduce((sum, s) => sum + s.performance.inventoryValue, 0);

    return stores.map(store => ({
        storeId: store.id,
        storeName: store.name,
        inventoryValue: store.performance.inventoryValue,
        percentageOfTotal: parseFloat((store.performance.inventoryValue / totalInventory * 100).toFixed(1)),
        turnoverRate: store.metrics.inventoryTurnover,
        daysOfStock: Math.floor(365 / store.metrics.inventoryTurnover)
    })).sort((a, b) => b.inventoryValue - a.inventoryValue);
};

/**
 * Get geographic clusters
 */
export const getGeographicClusters = (stores) => {
    const clusters = {};

    stores.forEach(store => {
        const state = store.location.state;
        if (!clusters[state]) {
            clusters[state] = {
                state,
                region: store.location.region,
                stores: [],
                totalRevenue: 0,
                avgRevenue: 0
            };
        }

        clusters[state].stores.push(store);
        clusters[state].totalRevenue += store.performance.monthlyRevenue;
    });

    return Object.values(clusters).map(cluster => ({
        ...cluster,
        storeCount: cluster.stores.length,
        avgRevenue: Math.floor(cluster.totalRevenue / cluster.stores.length)
    })).sort((a, b) => b.totalRevenue - a.totalRevenue);
};

/**
 * Calculate distance between two coordinates (Haversine formula)
 */
export const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
};

/**
 * Find nearest stores to a given location
 */
export const findNearestStores = (targetStore, allStores, limit = 5) => {
    const { lat, lng } = targetStore.location.coordinates;

    return allStores
        .filter(s => s.id !== targetStore.id)
        .map(store => ({
            ...store,
            distance: calculateDistance(
                lat, lng,
                store.location.coordinates.lat,
                store.location.coordinates.lng
            )
        }))
        .sort((a, b) => a.distance - b.distance)
        .slice(0, limit);
};

/**
 * Get transfer recommendations based on inventory and performance
 */
export const getTransferRecommendations = (stores) => {
    const avgTurnover = stores.reduce((sum, s) => sum + s.metrics.inventoryTurnover, 0) / stores.length;

    const overstocked = stores.filter(s => s.metrics.inventoryTurnover < avgTurnover * 0.7);
    const understocked = stores.filter(s => s.metrics.inventoryTurnover > avgTurnover * 1.3);

    const recommendations = [];

    overstocked.forEach(source => {
        understocked.forEach(destination => {
            const distance = calculateDistance(
                source.location.coordinates.lat,
                source.location.coordinates.lng,
                destination.location.coordinates.lat,
                destination.location.coordinates.lng
            );

            if (distance < 500) { // Within 500km
                recommendations.push({
                    from: source.name,
                    fromId: source.id,
                    to: destination.name,
                    toId: destination.id,
                    distance: Math.floor(distance),
                    priority: distance < 200 ? 'High' : distance < 350 ? 'Medium' : 'Low',
                    estimatedValue: Math.floor(source.performance.inventoryValue * 0.1)
                });
            }
        });
    });

    return recommendations.sort((a, b) => a.distance - b.distance).slice(0, 10);
};
