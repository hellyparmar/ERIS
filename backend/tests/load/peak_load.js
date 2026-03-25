import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

/**
 * k6 Load Test: Peak Load (500 concurrent users)
 * 
 * Simulates peak traffic (festival season, sale events)
 * 
 * Performance Targets:
 * - p95 response time < 1000ms
 * - p99 response time < 2000ms
 * - Error rate < 5%
 * - Throughput > 100 req/s
 */

// Custom metrics
const errorRate = new Rate('errors');
const requestDuration = new Trend('request_duration');
const requestCount = new Counter('request_count');

// Test configuration
export const options = {
    stages: [
        { duration: '2m', target: 100 },   // Ramp up to 100
        { duration: '3m', target: 250 },   // Ramp to 250
        { duration: '5m', target: 500 },   // Peak at 500 users
        { duration: '5m', target: 500 },   // Hold peak
        { duration: '3m', target: 250 },   // Ramp down
        { duration: '2m', target: 0 },     // Cool down
    ],

    thresholds: {
        http_req_duration: ['p(95)<1000', 'p(99)<2000'],
        http_req_failed: ['rate<0.05'],  // < 5% errors
        errors: ['rate<0.05'],
        request_duration: ['p(95)<1000'],
    },

    // Resource limits
    maxVUs: 1000,
};

// Configuration
const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// User pool for realistic testing
const users = [
    { email: 'demo@rdios.com', password: 'Demo@123' },
    { email: 'user1@rdios.com', password: 'User@123' },
    { email: 'user2@rdios.com', password: 'User@123' },
    { email: 'user3@rdios.com', password: 'User@123' },
];

/**
 * Weighted scenarios to simulate realistic user behavior
 */
export default function () {
    const scenario = Math.random();

    if (scenario < 0.4) {
        // 40% - Browse products & dashboard
        browseScenario();
    } else if (scenario < 0.7) {
        // 30% - Create invoice
        createInvoiceScenario();
    } else if (scenario < 0.9) {
        // 20% - View analytics
        analyticsScenario();
    } else {
        // 10% - Manage inventory
        inventoryScenario();
    }
}

/**
 * Browse products and dashboard
 */
function browseScenario() {
    const user = users[Math.floor(Math.random() * users.length)];
    const token = login(user.email, user.password);

    if (!token) return;

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    // Get products
    measureRequest('GetProducts', () => {
        return http.get(`${BASE_URL}/api/v1/products`, { headers });
    });

    sleep(1);

    // Get dashboard
    measureRequest('GetDashboard', () => {
        return http.get(`${BASE_URL}/api/v1/analytics/dashboard`, { headers });
    });

    sleep(2);
}

/**
 * Create invoice scenario
 */
function createInvoiceScenario() {
    const user = users[Math.floor(Math.random() * users.length)];
    const token = login(user.email, user.password);

    if (!token) return;

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    // Get customers
    measureRequest('GetCustomers', () => {
        return http.get(`${BASE_URL}/api/v1/customers`, { headers });
    });

    sleep(1);

    // Get products
    measureRequest('GetProducts', () => {
        return http.get(`${BASE_URL}/api/v1/products`, { headers });
    });

    sleep(2);

    // Create invoice
    const invoiceData = {
        customer_id: `customer-${Math.floor(Math.random() * 100)}`,
        items: [
            {
                product_id: `product-${Math.floor(Math.random() * 50)}`,
                quantity: Math.floor(Math.random() * 10) + 1,
                unit_price: Math.floor(Math.random() * 5000) + 500,
                tax_rate: 18,
            }
        ],
        discount_amount: 0,
    };

    measureRequest('CreateInvoice', () => {
        return http.post(
            `${BASE_URL}/api/v1/invoices`,
            JSON.stringify(invoiceData),
            { headers }
        );
    });

    sleep(1);
}

/**
 * View analytics scenario
 */
function analyticsScenario() {
    const user = users[Math.floor(Math.random() * users.length)];
    const token = login(user.email, user.password);

    if (!token) return;

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    // Sales analytics
    measureRequest('GetSalesAnalytics', () => {
        return http.get(`${BASE_URL}/api/v1/analytics/sales`, { headers });
    });

    sleep(1);

    // Inventory analytics
    measureRequest('GetInventoryAnalytics', () => {
        return http.get(`${BASE_URL}/api/v1/analytics/inventory`, { headers });
    });

    sleep(1);

    // Customer RFM
    measureRequest('GetCustomerRFM', () => {
        return http.get(`${BASE_URL}/api/v1/analytics/customers/rfm`, { headers });
    });

    sleep(2);
}

/**
 * Inventory management scenario
 */
function inventoryScenario() {
    const user = users[Math.floor(Math.random() * users.length)];
    const token = login(user.email, user.password);

    if (!token) return;

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    // Get inventory
    measureRequest('GetInventory', () => {
        return http.get(`${BASE_URL}/api/v1/inventory`, { headers });
    });

    sleep(1);

    // Update stock (random product)
    const productId = `product-${Math.floor(Math.random() * 50)}`;
    const updateData = {
        quantity_change: Math.floor(Math.random() * 20) - 10,
        reason: 'stock_adjustment',
    };

    measureRequest('UpdateInventory', () => {
        return http.put(
            `${BASE_URL}/api/v1/inventory/${productId}`,
            JSON.stringify(updateData),
            { headers }
        );
    });

    sleep(2);
}

/**
 * Helper: Login and return token
 */
function login(email, password) {
    const res = measureRequest('Login', () => {
        return http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
            username: email,
            password: password,
        }), {
            headers: { 'Content-Type': 'application/json' },
        });
    });

    const success = check(res, {
        'login successful': (r) => r.status === 200,
    });

    if (!success) {
        errorRate.add(1);
        return null;
    }

    return res.json('access_token');
}

/**
 * Helper: Measure request duration and count
 */
function measureRequest(name, requestFn) {
    requestCount.add(1);

    const res = requestFn();

    requestDuration.add(res.timings.duration, { operation: name });

    const success = check(res, {
        [`${name} success`]: (r) => r.status >= 200 && r.status < 400,
    });

    if (!success) {
        errorRate.add(1);
    }

    return res;
}

/**
 * Setup
 */
export function setup() {
    console.log('Starting PEAK load test (500 users)...');
    console.log(`Target: ${BASE_URL}`);
    console.log('User scenarios: Browse (40%), Invoice (30%), Analytics (20%), Inventory (10%)');

    return { startTime: new Date() };
}

/**
 * Teardown
 */
export function teardown(data) {
    const endTime = new Date();
    const duration = (endTime - data.startTime) / 1000;
    console.log(`Peak load test completed in ${duration}s`);
}
