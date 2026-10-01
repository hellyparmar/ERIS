/**
 * Enterprise Retail Intelligence System v3.0
 * ANALYTICS ENGINE (Business Logic Class)
 * 
 * Core intelligence layer processing retail data and providing insights.
 * Separates business logic from UI components (V3.0 Protocol: Modularity).
 * 
 * V3.0 Intelligence Features:
 * - Auto-language detection
 * - External factors analysis
 * - Decline analysis with counter-strategies
 */

import {
    generateDemandData,
    generateForecastData,
    generateInventoryData,
    generateAlerts,
    calculateMetrics
} from './mockData';

import { ALERT_THRESHOLDS, EXTERNAL_FACTORS } from './constants';

class AnalyticsEngine {
    constructor() {
        this.demandData = [];
        this.forecastData = [];
        this.inventoryData = [];
        this.alerts = [];
        this.metrics = {};
        this.externalFactors = {};

        this.initialized = false;
    }

    /**
     * Initialize engine with data (call once on app load).
     * 
     * @param {Object} options - Configuration options
     */
    initialize(options = {}) {
        const {
            demandDays = 90,
            forecastDays = 30,
            productCount = 20
        } = options;

        console.log('🔧 Initializing Analytics Engine...');

        // Generate data
        this.demandData = generateDemandData(demandDays);
        this.forecastData = generateForecastData(this.demandData, forecastDays);
        this.inventoryData = generateInventoryData(productCount);
        this.alerts = generateAlerts(this.inventoryData, this.demandData);
        this.metrics = calculateMetrics(this.demandData, this.inventoryData);

        // Simulate external factors
        this.externalFactors = this._simulateExternalFactors();

        this.initialized = true;
        console.log('✅ Analytics Engine initialized');
        console.log(`   Demand records: ${this.demandData.length}`);
        console.log(`   Forecast days: ${this.forecastData.length}`);
        console.log(`   Products: ${this.inventoryData.length}`);
        console.log(`   Active alerts: ${this.alerts.length}`);
    }

    /**
     * Get dashboard metrics.
     * 
     * @returns {Object} KPI metrics
     */
    getMetrics() {
        if (!this.initialized) {
            throw new Error('AnalyticsEngine not initialized. Call initialize() first.');
        }

        return {
            ...this.metrics,
            alertCount: this.alerts.length,
            criticalAlertCount: this.alerts.filter(a => a.severity === 'critical').length
        };
    }

    /**
     * Get sales chart data (historical + forecast).
     * 
     * @param {number} days - Days of historical data to include
     * @returns {Array} Combined historical and forecast data
     */
    getSalesChartData(days = 30) {
        if (!this.initialized) {
            throw new Error('AnalyticsEngine not initialized');
        }

        const historical = this.demandData.slice(-days).map(d => ({
            date: d.date,
            actual: d.sales,
            type: 'historical'
        }));

        const forecast = this.forecastData.slice(0, 15).map(d => ({
            date: d.date,
            predicted: d.predicted,
            lowerBound: d.lowerBound,
            upperBound: d.upperBound,
            type: 'forecast'
        }));

        return [...historical, ...forecast];
    }

    /**
     * Get inventory alerts (sorted by severity).
     * 
     * @param {string} severity - Filter by severity ('all', 'critical', 'warning')
     * @returns {Array} Filtered alerts
     */
    getAlerts(severity = 'all') {
        if (!this.initialized) {
            throw new Error('AnalyticsEngine not initialized');
        }

        if (severity === 'all') {
            return this.alerts;
        }

        return this.alerts.filter(alert => alert.severity === severity);
    }

    /**
     * Get inventory status summary.
     * 
     * @returns {Object} Inventory summary
     */
    getInventorySummary() {
        if (!this.initialized) {
            throw new Error('AnalyticsEngine not initialized');
        }

        const criticalCount = this.inventoryData.filter(
            item => item.daysToStockout < ALERT_THRESHOLDS.STOCKOUT_CRITICAL
        ).length;

        const warningCount = this.inventoryData.filter(
            item => item.daysToStockout >= ALERT_THRESHOLDS.STOCKOUT_CRITICAL &&
                item.daysToStockout < ALERT_THRESHOLDS.STOCKOUT_WARNING
        ).length;

        const healthyCount = this.inventoryData.length - criticalCount - warningCount;

        return {
            total: this.inventoryData.length,
            critical: criticalCount,
            warning: warningCount,
            healthy: healthyCount,
            criticalPercentage: (criticalCount / this.inventoryData.length) * 100,
            items: this.inventoryData.slice(0, 10) // Top 10 priority items
        };
    }

    /**
     * Analyze sales decline and suggest counter-strategies.
     * V3.0 Intelligence Feature
     * 
     * @returns {Object} Decline analysis with recommendations
     */
    analyzeSalesDecline() {
        if (!this.initialized) {
            throw new Error('AnalyticsEngine not initialized');
        }

        const recent = this.demandData.slice(-7).reduce((sum, d) => sum + d.sales, 0) / 7;
        const previous = this.demandData.slice(-14, -7).reduce((sum, d) => sum + d.sales, 0) / 7;
        const change = ((recent - previous) / previous) * 100;

        if (change < -10) {
            // Declining sales - provide AI recommendations
            return {
                status: 'declining',
                changePercentage: change.toFixed(1),
                severity: change < -20 ? 'critical' : 'warning',
                recommendations: [
                    {
                        title: 'Run Seasonal Promotion',
                        description: 'Launch targeted promotions based on current weather and seasonal trends',
                        expectedImpact: '+15-20% sales',
                        urgency: 'high'
                    },
                    {
                        title: 'Review Pricing Strategy',
                        description: 'Competitor analysis shows 5% price difference in key categories',
                        expectedImpact: '+10-15% sales',
                        urgency: 'medium'
                    },
                    {
                        title: 'Optimize Inventory Mix',
                        description: 'Stock high-demand items identified by AI forecasting',
                        expectedImpact: '+8-12% sales',
                        urgency: 'medium'
                    }
                ],
                externalFactors: this.externalFactors
            };
        } else if (change > 15) {
            // Growing sales - capitalize
            return {
                status: 'growing',
                changePercentage: change.toFixed(1),
                severity: 'success',
                recommendations: [
                    {
                        title: 'Increase Inventory Levels',
                        description: 'Prevent stockouts during high-demand period',
                        expectedImpact: 'Prevent 5-10% revenue loss',
                        urgency: 'high'
                    },
                    {
                        title: 'Expand Marketing Budget',
                        description: 'Double down on successful campaigns',
                        expectedImpact: '+20-25% sales',
                        urgency: 'medium'
                    }
                ],
                externalFactors: this.externalFactors
            };
        }

        return {
            status: 'stable',
            changePercentage: change.toFixed(1),
            severity: 'info',
            recommendations: [],
            externalFactors: this.externalFactors
        };
    }

    /**
     * Simulate external factors (V3.0 Intelligence Engine requirement).
     * In production, this would fetch from Weather API, Economic APIs, etc.
     * 
     * @returns {Object} External factors
     */
    _simulateExternalFactors() {
        const weatherOptions = Object.values(EXTERNAL_FACTORS.weather);
        const economicOptions = Object.values(EXTERNAL_FACTORS.economic);
        const sentimentOptions = Object.values(EXTERNAL_FACTORS.sentiment);

        return {
            weather: weatherOptions[Math.floor(Math.random() * weatherOptions.length)],
            weatherImpact: Math.random() > 0.5 ? 'positive' : 'neutral',
            economicIndicator: economicOptions[Math.floor(Math.random() * economicOptions.length)],
            inflationRate: (3 + Math.random() * 3).toFixed(1) + '%',
            consumerSentiment: sentimentOptions[Math.floor(Math.random() * sentimentOptions.length)],
            competitorActivity: Math.random() > 0.7 ? 'high' : 'normal'
        };
    }

    /**
     * Get top-selling products.
     * 
     * @param {number} limit - Number of products to return
     * @returns {Array} Top products
     */
    getTopProducts(limit = 5) {
        if (!this.initialized) {
            throw new Error('AnalyticsEngine not initialized');
        }

        // Simulate top products based on inventory turnover
        return this.inventoryData
            .map(item => ({
                ...item,
                revenue: item.dailyConsumption * 100 * 30 // Estimate monthly revenue
            }))
            .sort((a, b) => b.revenue - a.revenue)
            .slice(0, limit);
    }

    /**
     * Get demand forecast summary.
     * 
     * @returns {Object} Forecast summary
     */
    getForecastSummary() {
        if (!this.initialized) {
            throw new Error('AnalyticsEngine not initialized');
        }

        const avgForecast = this.forecastData.reduce((sum, d) => sum + d.predicted, 0) / this.forecastData.length;
        const avgConfidence = this.forecastData.reduce((sum, d) => sum + d.confidence, 0) / this.forecastData.length;

        return {
            nextWeekPrediction: Math.round(this.forecastData.slice(0, 7).reduce((sum, d) => sum + d.predicted, 0)),
            avgDailyForecast: Math.round(avgForecast),
            avgConfidence: Math.round(avgConfidence),
            trend: avgForecast > this.metrics.avgDailySales ? 'increasing' : 'decreasing',
            forecastData: this.forecastData
        };
    }

    /**
     * Refresh analytics (simulate real-time updates).
     * Call this periodically or on user action.
     */
    refresh() {
        console.log('🔄 Refreshing analytics...');
        const options = {
            demandDays: 90,
            forecastDays: 30,
            productCount: this.inventoryData.length
        };
        this.initialize(options);
    }
}

// Export singleton instance
const analytics = new AnalyticsEngine();
export default analytics;
