/**
 * Performance Monitoring Utility
 * Tracks and reports key performance metrics
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }

    init() {
        if (typeof window === 'undefined') return;

        // Monitor page load performance
        window.addEventListener('load', () => {
            this.measurePageLoad();
        });

        // Monitor route changes
        this.observeRouteChanges();

        // Monitor resource loading
        this.observeResources();
    }

    measurePageLoad() {
        if (!window.performance) return;

        const perfData = window.performance.timing;
        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
        const connectTime = perfData.responseEnd - perfData.requestStart;
        const renderTime = perfData.domComplete - perfData.domLoading;
        const domContentLoaded = perfData.domContentLoadedEventEnd - perfData.navigationStart;

        this.metrics.pageLoad = {
            total: pageLoadTime,
            connect: connectTime,
            render: renderTime,
            domContentLoaded,
            timestamp: new Date().toISOString(),
        };

        // Log to console in development
        if (import.meta.env.DEV) {
            console.log('📊 Performance Metrics:', this.metrics.pageLoad);
        }

        // Send to analytics in production
        if (import.meta.env.PROD) {
            this.sendToAnalytics('page_load', this.metrics.pageLoad);
        }
    }

    measureRouteChange(routeName) {
        const startTime = performance.now();

        return () => {
            const endTime = performance.now();
            const duration = endTime - startTime;

            this.metrics[`route_${routeName}`] = {
                duration,
                timestamp: new Date().toISOString(),
            };

            if (import.meta.env.DEV) {
                console.log(`📊 Route Change (${routeName}):`, duration.toFixed(2), 'ms');
            }

            if (import.meta.env.PROD) {
                this.sendToAnalytics('route_change', {
                    route: routeName,
                    duration,
                });
            }
        };
    }

    observeRouteChanges() {
        // Monitor history changes
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;

        history.pushState = function (...args) {
            originalPushState.apply(this, args);
            window.dispatchEvent(new Event('pushstate'));
        };

        history.replaceState = function (...args) {
            originalReplaceState.apply(this, args);
            window.dispatchEvent(new Event('replacestate'));
        };

        window.addEventListener('pushstate', () => {
            this.trackNavigation();
        });

        window.addEventListener('popstate', () => {
            this.trackNavigation();
        });
    }

    trackNavigation() {
        const path = window.location.pathname;
        const startTime = performance.now();

        requestAnimationFrame(() => {
            const endTime = performance.now();
            const duration = endTime - startTime;

            if (import.meta.env.DEV) {
                console.log(`📊 Navigation to ${path}:`, duration.toFixed(2), 'ms');
            }
        });
    }

    observeResources() {
        if (!window.PerformanceObserver) return;

        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.entryType === 'resource') {
                    this.trackResource(entry);
                } else if (entry.entryType === 'paint') {
                    this.trackPaint(entry);
                }
            }
        });

        observer.observe({ entryTypes: ['resource', 'paint', 'navigation'] });
    }

    trackResource(entry) {
        const resourceType = entry.initiatorType;
        const duration = entry.duration;
        const size = entry.transferSize;

        // Track slow resources
        if (duration > 1000) {
            if (import.meta.env.DEV) {
                console.warn(`⚠️ Slow resource (${resourceType}):`, entry.name, duration.toFixed(2), 'ms');
            }

            if (import.meta.env.PROD) {
                this.sendToAnalytics('slow_resource', {
                    type: resourceType,
                    url: entry.name,
                    duration,
                    size,
                });
            }
        }
    }

    trackPaint(entry) {
        if (import.meta.env.DEV) {
            console.log(`🎨 ${entry.name}:`, entry.startTime.toFixed(2), 'ms');
        }

        if (import.meta.env.PROD) {
            this.sendToAnalytics('paint', {
                name: entry.name,
                startTime: entry.startTime,
            });
        }
    }

    // Track custom metrics
    trackCustomMetric(name, value, unit = 'ms') {
        this.metrics[name] = {
            value,
            unit,
            timestamp: new Date().toISOString(),
        };

        if (import.meta.env.DEV) {
            console.log(`📊 ${name}:`, value, unit);
        }

        if (import.meta.env.PROD) {
            this.sendToAnalytics('custom_metric', {
                name,
                value,
                unit,
            });
        }
    }

    // Send to analytics service
    sendToAnalytics(eventName, data) {
        // Send to Vercel Analytics, Google Analytics, or custom endpoint
        if (window.va) {
            window.va('track', eventName, data);
        }

        // Send to custom analytics endpoint
        if (import.meta.env.VITE_ANALYTICS_ENDPOINT) {
            fetch(import.meta.env.VITE_ANALYTICS_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    event: eventName,
                    data,
                    timestamp: new Date().toISOString(),
                }),
            }).catch(() => {
                // Silently fail
            });
        }
    }

    // Get all metrics
    getMetrics() {
        return this.metrics;
    }

    // Get Web Vitals
    getWebVitals() {
        if (!window.performance) return null;

        const navigation = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');

        const fcp = paint.find(entry => entry.name === 'first-contentful-paint');
        const lcp = performance.getEntriesByType('largest-contentful-paint').pop();

        return {
            // First Contentful Paint
            FCP: fcp ? fcp.startTime : null,
            // Largest Contentful Paint
            LCP: lcp ? lcp.startTime : null,
            // Time to Interactive (approximation)
            TTI: navigation ? navigation.domInteractive : null,
            // Total Blocking Time (approximation)
            TBT: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : null,
        };
    }
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

// Export for use in components
export default performanceMonitor;

// Helper hook for React components
export const usePerformanceTracking = (componentName) => {
    React.useEffect(() => {
        const endMeasure = performanceMonitor.measureRouteChange(componentName);
        return endMeasure;
    }, [componentName]);
};
