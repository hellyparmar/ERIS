/**
 * Enterprise Retail Intelligence System v3.0
 * MULTI-STORE DATA - Mock store locations and performance data
 */

// Indian cities with coordinates for geographic visualization
const INDIAN_CITIES = [
    { city: 'Mumbai', state: 'Maharashtra', lat: 19.0760, lng: 72.8777, region: 'West' },
    { city: 'Delhi', state: 'Delhi', lat: 28.7041, lng: 77.1025, region: 'North' },
    { city: 'Bangalore', state: 'Karnataka', lat: 12.9716, lng: 77.5946, region: 'South' },
    { city: 'Hyderabad', state: 'Telangana', lat: 17.3850, lng: 78.4867, region: 'South' },
    { city: 'Chennai', state: 'Tamil Nadu', lat: 13.0827, lng: 80.2707, region: 'South' },
    { city: 'Kolkata', state: 'West Bengal', lat: 22.5726, lng: 88.3639, region: 'East' },
    { city: 'Pune', state: 'Maharashtra', lat: 18.5204, lng: 73.8567, region: 'West' },
    { city: 'Ahmedabad', state: 'Gujarat', lat: 23.0225, lng: 72.5714, region: 'West' },
    { city: 'Jaipur', state: 'Rajasthan', lat: 26.9124, lng: 75.7873, region: 'North' },
    { city: 'Lucknow', state: 'Uttar Pradesh', lat: 26.8467, lng: 80.9462, region: 'North' },
    { city: 'Chandigarh', state: 'Chandigarh', lat: 30.7333, lng: 76.7794, region: 'North' },
    { city: 'Kochi', state: 'Kerala', lat: 9.9312, lng: 76.2673, region: 'South' },
    { city: 'Indore', state: 'Madhya Pradesh', lat: 22.7196, lng: 75.8577, region: 'Central' },
    { city: 'Bhopal', state: 'Madhya Pradesh', lat: 23.2599, lng: 77.4126, region: 'Central' },
    { city: 'Nagpur', state: 'Maharashtra', lat: 21.1458, lng: 79.0882, region: 'Central' }
];

const STORE_TYPES = ['Flagship', 'Standard', 'Express', 'Outlet'];
const STORE_SIZES = ['Large', 'Medium', 'Small'];

// Generate realistic store data
const generateStoreData = () => {
    const stores = [];
    const usedCities = new Set();

    INDIAN_CITIES.forEach((location, idx) => {
        // Create 1-2 stores per major city
        const storesInCity = idx < 8 ? 2 : 1;

        for (let i = 0; i < storesInCity; i++) {
            const storeId = `ST${String(stores.length + 1).padStart(3, '0')}`;
            const storeType = STORE_TYPES[Math.floor(Math.random() * STORE_TYPES.length)];
            const storeSize = STORE_SIZES[Math.floor(Math.random() * STORE_SIZES.length)];

            // Performance varies by store type and size
            const baseRevenue = storeType === 'Flagship' ? 800000 :
                storeType === 'Standard' ? 500000 :
                    storeType === 'Express' ? 300000 : 200000;

            const sizeMultiplier = storeSize === 'Large' ? 1.3 :
                storeSize === 'Medium' ? 1.0 : 0.7;

            const monthlyRevenue = Math.floor(baseRevenue * sizeMultiplier * (0.8 + Math.random() * 0.4));
            const footfall = Math.floor(monthlyRevenue / 500); // Avg transaction ₹500
            const conversionRate = 0.15 + Math.random() * 0.25; // 15-40%
            const avgTransactionValue = Math.floor(300 + Math.random() * 700);

            stores.push({
                id: storeId,
                name: `${location.city} ${i > 0 ? location.state.split(' ')[0] : storeType}`,
                type: storeType,
                size: storeSize,
                location: {
                    city: location.city,
                    state: location.state,
                    region: location.region,
                    coordinates: {
                        lat: location.lat + (Math.random() - 0.5) * 0.1, // Slight variation
                        lng: location.lng + (Math.random() - 0.5) * 0.1
                    },
                    address: `${Math.floor(Math.random() * 500) + 1}, ${location.city} Main Road`
                },
                performance: {
                    monthlyRevenue,
                    yearlyRevenue: monthlyRevenue * 12,
                    footfall,
                    conversionRate: parseFloat((conversionRate * 100).toFixed(1)),
                    avgTransactionValue,
                    inventoryValue: Math.floor(monthlyRevenue * 0.4),
                    staffCount: storeSize === 'Large' ? 25 : storeSize === 'Medium' ? 15 : 8
                },
                metrics: {
                    salesGrowth: parseFloat((-10 + Math.random() * 30).toFixed(1)), // -10% to +20%
                    customerSatisfaction: parseFloat((3.5 + Math.random() * 1.5).toFixed(1)), // 3.5-5.0
                    inventoryTurnover: parseFloat((4 + Math.random() * 8).toFixed(1)), // 4-12x per year
                    profitMargin: parseFloat((8 + Math.random() * 12).toFixed(1)) // 8-20%
                },
                operational: {
                    openingDate: new Date(2020 + Math.floor(Math.random() * 4), Math.floor(Math.random() * 12), 1),
                    manager: `Manager ${stores.length + 1}`,
                    operatingHours: '09:00 - 22:00',
                    status: Math.random() > 0.05 ? 'Active' : 'Maintenance'
                }
            });
        }
    });

    return stores;
};

const mockStores = generateStoreData();

export default mockStores;

// Export helper functions
export const getStoresByRegion = (stores) => {
    return stores.reduce((acc, store) => {
        const region = store.location.region;
        if (!acc[region]) acc[region] = [];
        acc[region].push(store);
        return acc;
    }, {});
};

export const getTopPerformingStores = (stores, limit = 5) => {
    return [...stores]
        .sort((a, b) => b.performance.monthlyRevenue - a.performance.monthlyRevenue)
        .slice(0, limit);
};

export const getBottomPerformingStores = (stores, limit = 5) => {
    return [...stores]
        .sort((a, b) => a.performance.monthlyRevenue - b.performance.monthlyRevenue)
        .slice(0, limit);
};

export const getStoresByType = (stores) => {
    return stores.reduce((acc, store) => {
        const type = store.type;
        if (!acc[type]) acc[type] = [];
        acc[type].push(store);
        return acc;
    }, {});
};

export const calculateRegionalPerformance = (stores) => {
    const byRegion = getStoresByRegion(stores);

    return Object.entries(byRegion).map(([region, regionStores]) => {
        const totalRevenue = regionStores.reduce((sum, s) => sum + s.performance.monthlyRevenue, 0);
        const avgRevenue = totalRevenue / regionStores.length;
        const totalFootfall = regionStores.reduce((sum, s) => sum + s.performance.footfall, 0);

        return {
            region,
            storeCount: regionStores.length,
            totalRevenue,
            avgRevenue: Math.floor(avgRevenue),
            totalFootfall,
            avgGrowth: parseFloat((regionStores.reduce((sum, s) => sum + s.metrics.salesGrowth, 0) / regionStores.length).toFixed(1))
        };
    }).sort((a, b) => b.totalRevenue - a.totalRevenue);
};
