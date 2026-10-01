/**
 * Enterprise Retail Intelligence System v3.0
 * MOCK DATA GENERATOR
 * 
 * Realistic synthetic data generation for dashboard demonstration.
 * Simulates retail patterns: seasonality, trends, demand spikes, stockouts.
 * 
 * V3.0 Intelligence: Data reflects real-world retail scenarios.
 */

/**
 * Generate realistic demand data with seasonal patterns.
 * 
 * Simulates:
 * - Weekly seasonality (weekends higher)
 * - Monthly trends (growth/decline)
 * - Random noise (market volatility)
 * - Occasional demand spikes (promotions, events)
 * 
 * @param {number} days - Number of days to generate
 * @returns {Array} Array of daily sales records
 */
export const generateDemandData = (days = 90) => {
  const data = [];
  const today = new Date();
  const baselineDaily = 50000; // ₹50,000 baseline daily sales
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    const dayOfWeek = date.getDay();
    const dayOfYear = Math.floor((date - new Date(date.getFullYear(), 0, 0)) / 86400000);
    
    // Seasonal patterns
    const weekendBoost = (dayOfWeek === 0 || dayOfWeek === 6) ? 1.3 : 1.0;
    const monthlyTrend = 1 + (Math.sin(dayOfYear / 30) * 0.15); // ±15% monthly variation
    const seasonalPattern = 1 + (Math.sin(2 * Math.PI * dayOfYear / 365) * 0.2); // ±20% yearly
    
    // Random events (5% chance of demand spike)
    const hasEvent = Math.random() < 0.05;
    const eventMultiplier = hasEvent ? 1.5 + Math.random() * 0.5 : 1.0;
    
    // Market noise
    const noise = 1 + (Math.random() - 0.5) * 0.1; // ±5% daily variance
    
    // Calculate final sales
    const sales = Math.round(
      baselineDaily * 
      weekendBoost * 
      monthlyTrend * 
      seasonalPattern * 
      eventMultiplier * 
      noise
    );
    
    data.push({
      date: date.toISOString().split('T')[0],
      sales,
      orders: Math.round(sales / 250), // Avg order value ₹250
      customers: Math.round(sales / 500), // Avg customer value ₹500
      hasEvent
    });
  }
  
  return data;
};

/**
 * Generate AI-powered forecast data.
 * 
 * Simulates ML model predictions with confidence intervals.
 * 
 * @param {Array} historicalData - Past sales data
 * @param {number} forecastDays - Days to forecast
 * @returns {Array} Forecast with confidence bounds
 */
export const generateForecastData = (historicalData, forecastDays = 30) => {
  if (!historicalData || historicalData.length === 0) {
    return [];
  }
  
  const forecast = [];
  const recentAvg = historicalData.slice(-7).reduce((sum, d) => sum + d.sales, 0) / 7;
  const trend = (historicalData[historicalData.length - 1].sales - historicalData[0].sales) / historicalData.length;
  
  const lastDate = new Date(historicalData[historicalData.length - 1].date);
  
  for (let i = 1; i <= forecastDays; i++) {
    const forecastDate = new Date(lastDate);
    forecastDate.setDate(forecastDate.getDate() + i);
    
    const dayOfWeek = forecastDate.getDay();
    const weekendBoost = (dayOfWeek === 0 || dayOfWeek === 6) ? 1.3 : 1.0;
    
    // Predicted sales (trend + seasonality)
    const predicted = Math.round((recentAvg + (trend * i)) * weekendBoost);
    
    // Confidence intervals (widen over time)
    const uncertaintyFactor = 1 + (i / forecastDays) * 0.3; // 30% max uncertainty
    const lowerBound = Math.round(predicted * (1 - 0.1 * uncertaintyFactor));
    const upperBound = Math.round(predicted * (1 + 0.1 * uncertaintyFactor));
    
    forecast.push({
      date: forecastDate.toISOString().split('T')[0],
      predicted,
      lowerBound,
      upperBound,
      confidence: Math.round((1 - (i / forecastDays) * 0.3) * 100) // 70-100% confidence
    });
  }
  
  return forecast;
};

/**
 * Generate inventory data with stockout risks.
 * 
 * @param {number} productCount - Number of products
 * @returns {Array} Inventory records
 */
export const generateInventoryData = (productCount = 20) => {
  const categories = ['Groceries', 'Electronics', 'Clothing', 'Home & Kitchen', 'Beauty'];
  const inventory = [];
  
  for (let i = 1; i <= productCount; i++) {
    const category = categories[Math.floor(Math.random() * categories.length)];
    const currentStock = Math.floor(Math.random() * 500);
    const dailyConsumption = 10 + Math.floor(Math.random() * 40);
    const daysToStockout = Math.floor(currentStock / dailyConsumption);
    
    // Determine status based on V3.0 thresholds
    let status = 'healthy';
    let severity = 'success';
    
    if (daysToStockout < 7) {
      status = 'critical';
      severity = 'critical';
    } else if (daysToStockout < 14) {
      status = 'warning';
      severity = 'warning';
    }
    
    inventory.push({
      id: `PROD_${i.toString().padStart(3, '0')}`,
      name: `Product ${i}`,
      category,
      currentStock,
      reorderPoint: dailyConsumption * 14, // 2-week safety stock
      dailyConsumption,
      daysToStockout,
      status,
      severity,
      lastRestocked: new Date(Date.now() - Math.random() * 30 * 86400000).toISOString().split('T')[0]
    });
  }
  
  return inventory.sort((a, b) => a.daysToStockout - b.daysToStockout);
};

/**
 * Generate actionable alerts based on V3.0 Intelligence Engine rules.
 * 
 * @param {Array} inventoryData - Current inventory
 * @param {Array} demandData - Recent sales data
 * @returns {Array} Alert objects
 */
export const generateAlerts = (inventoryData, demandData) => {
  const alerts = [];
  
  // Stockout alerts
  const criticalItems = inventoryData.filter(item => item.daysToStockout < 7);
  const warningItems = inventoryData.filter(item => item.daysToStockout >= 7 && item.daysToStockout < 14);
  
  criticalItems.forEach(item => {
    alerts.push({
      id: `alert_${item.id}_stockout`,
      type: 'stockout',
      severity: 'critical',
      productId: item.id,
      productName: item.name,
      message: `Critical: ${item.name} will run out in ${item.daysToStockout} days`,
      recommendation: `Order ${item.reorderPoint * 2} units immediately`,
      daysToStockout: item.daysToStockout,
      timestamp: new Date().toISOString()
    });
  });
  
  warningItems.forEach(item => {
    alerts.push({
      id: `alert_${item.id}_low`,
      type: 'low_stock',
      severity: 'warning',
      productId: item.id,
      productName: item.name,
      message: `Warning: ${item.name} stock running low (${item.daysToStockout} days remaining)`,
      recommendation: `Plan reorder of ${item.reorderPoint} units`,
      daysToStockout: item.daysToStockout,
      timestamp: new Date().toISOString()
    });
  });
  
  // Demand spike alerts
  if (demandData && demandData.length > 0) {
    const recentSales = demandData.slice(-7).reduce((sum, d) => sum + d.sales, 0) / 7;
    const previousSales = demandData.slice(-14, -7).reduce((sum, d) => sum + d.sales, 0) / 7;
    const growthRate = ((recentSales - previousSales) / previousSales) * 100;
    
    if (growthRate > 30) {
      alerts.push({
        id: 'alert_demand_spike',
        type: 'demand_spike',
        severity: 'info',
        message: `Demand spike detected: ${growthRate.toFixed(1)}% increase over last week`,
        recommendation: 'Review inventory levels and prepare for increased orders',
        growthRate,
        timestamp: new Date().toISOString()
      });
    }
  }
  
  return alerts.sort((a, b) => {
    const severityOrder = { critical: 0, warning: 1, info: 2 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  });
};

/**
 * Calculate key performance metrics.
 * 
 * @param {Array} demandData - Sales data
 * @param {Array} inventoryData - Inventory data
 * @returns {Object} KPI metrics
 */
export const calculateMetrics = (demandData, inventoryData) => {
  if (!demandData || demandData.length === 0) {
    return {
      totalRevenue: 0,
      avgDailySales: 0,
      totalOrders: 0,
      totalCustomers: 0,
      inventoryValue: 0,
      stockoutRisk: 0,
      growthRate: 0
    };
  }
  
  // Revenue metrics
  const totalRevenue = demandData.reduce((sum, d) => sum + d.sales, 0);
  const avgDailySales = totalRevenue / demandData.length;
  const totalOrders = demandData.reduce((sum, d) => sum + d.orders, 0);
  const totalCustomers = demandData.reduce((sum, d) => sum + d.customers, 0);
  
  // Growth rate (last 7 days vs previous 7 days)
  const recentRevenue = demandData.slice(-7).reduce((sum, d) => sum + d.sales, 0);
  const previousRevenue = demandData.slice(-14, -7).reduce((sum, d) => sum + d.sales, 0);
  const growthRate = previousRevenue > 0 ? ((recentRevenue - previousRevenue) / previousRevenue) * 100 : 0;
  
  // Inventory metrics
  const inventoryValue = inventoryData ? inventoryData.reduce((sum, item) => sum + (item.currentStock * 100), 0) : 0; // Assume ₹100 per unit
  const criticalItems = inventoryData ? inventoryData.filter(item => item.daysToStockout < 7).length : 0;
  const stockoutRisk = inventoryData ? (criticalItems / inventoryData.length) * 100 : 0;
  
  return {
    totalRevenue,
    avgDailySales: Math.round(avgDailySales),
    totalOrders,
    totalCustomers,
    inventoryValue,
    stockoutRisk: Math.round(stockoutRisk),
    growthRate: parseFloat(growthRate.toFixed(1))
  };
};
