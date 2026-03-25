import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

/**
 * k6 Load Test: Normal Load (100 concurrent users)
 * 
 * Simulates typical daily usage pattern
 * 
 * Performance Targets:
 * - p95 response time < 500ms
 * - p99 response time < 1000ms
 * - Error rate < 1%
 */

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const invoiceCreationDuration = new Trend('invoice_creation_duration');
const productFetchDuration = new Trend('product_fetch_duration');

// Test configuration
export const options = {
    stages: [
        { duration: '2m', target: 50 },   // Ramp up to 50 users
        { duration: '5m', target: 100 },  // Hold at 100 users
        { duration: '2m', target: 0 },    // Ramp down
    ],

    thresholds: {
        http_req_duration: ['p(95)<500', 'p(99)<1000'],  // Response time thresholds
        http_req_failed: ['rate<0.01'],                   // Error rate < 1%
        errors: ['rate<0.01'],
        login_duration: ['p(95)<300'],
        invoice_creation_duration: ['p(95)<800'],
    },
};

// Configuration
const BASE_URL = __ENV.API_URL || 'http://localhost:8000';
const DEMO_EMAIL = 'demo@rdios.com';
const DEMO_PASSWORD = 'Demo@123';

/**
 * Main test scenario
 */
export default function () {
    // 1. Login
    const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
        username: DEMO_EMAIL,
        password: DEMO_PASSWORD,
    }), {
        headers: { 'Content-Type': 'application/json' },
        tags: { name: 'Login' },
    });

    const loginSuccess = check(loginRes, {
        'login status 200': (r) => r.status === 200,
        'login has token': (r) => r.json('access_token') !== undefined,
    });

    errorRate.add(!loginSuccess);
    loginDuration.add(loginRes.timings.duration);

    if (!loginSuccess) {
        console.error('Login failed');
        return;
    }

    const authToken = loginRes.json('access_token');
    const headers = {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
    };

    sleep(1);

    // 2. Get products
    const productsRes = http.get(`${BASE_URL}/api/v1/products`, {
        headers,
        tags: { name: 'GetProducts' },
    });

    const productsSuccess = check(productsRes, {
        'products status 200': (r) => r.status === 200,
        'has products': (r) => r.json('length') > 0,
    });

    errorRate.add(!productsSuccess);
    productFetchDuration.add(productsRes.timings.duration);

    sleep(1);

    // 3. Get customers
    const customersRes = http.get(`${BASE_URL}/api/v1/customers`, {
        headers,
        tags: { name: 'GetCustomers' },
    });

    check(customersRes, {
        'customers status 200': (r) => r.status === 200,
    });

    sleep(1);

    // 4. Create invoice
    const invoiceData = {
        customer_id: 'demo-customer-uuid',
        items: [
            {
                product_id: 'demo-product-uuid',
                quantity: 5,
                unit_price: 1000,
                tax_rate: 18,
            }
        ],
        discount_amount: 0,
    };

    const invoiceRes = http.post(
        `${BASE_URL}/api/v1/invoices`,
        JSON.stringify(invoiceData),
        {
            headers,
            tags: { name: 'CreateInvoice' },
        }
    );

    const invoiceSuccess = check(invoiceRes, {
        'invoice status 201': (r) => r.status === 201,
        'invoice has id': (r) => r.json('id') !== undefined,
    });

    errorRate.add(!invoiceSuccess);
    invoiceCreationDuration.add(invoiceRes.timings.duration);

    sleep(2);

    // 5. Get dashboard analytics
    const dashboardRes = http.get(`${BASE_URL}/api/v1/analytics/dashboard`, {
        headers,
        tags: { name: 'GetDashboard' },
    });

    check(dashboardRes, {
        'dashboard status 200': (r) => r.status === 200,
    });

    sleep(2);
}

/**
 * Setup function - runs once before tests
 */
export function setup() {
    console.log('Starting load test...');
    console.log(`Target: ${BASE_URL}`);
    return {
        startTime: new Date(),
    };
}

/**
 * Teardown function - runs once after tests
 */
export function teardown(data) {
    const endTime = new Date();
    const duration = (endTime - data.startTime) / 1000;
    console.log(`Test completed in ${duration}s`);
}
