import http from 'k6/http';
import { check, sleep } from 'k6';

/**
 * k6 Stress Test: Find System Breaking Point
 * 
 * Gradually increases load until system fails
 * Helps identify maximum capacity
 */

export const options = {
    stages: [
        { duration: '2m', target: 100 },    // Normal load
        { duration: '3m', target: 500 },    // Peak load
        { duration: '5m', target: 1000 },   // Stress
        { duration: '5m', target: 2000 },   // Heavy stress
        { duration: '5m', target: 3000 },   // Breaking point?
        { duration: '2m', target: 0 },      // Recovery
    ],

    thresholds: {
        // We expect to fail under stress - that's the point
        http_req_duration: ['p(99)<5000'],  // 99% under 5s
    },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function () {
    // Simple health check
    const res = http.get(`${BASE_URL}/health`);

    check(res, {
        'health check ok': (r) => r.status === 200,
    });

    sleep(1);
}

export function setup() {
    console.log('Starting STRESS test...');
    console.log('Goal: Find system breaking point');
    console.log(`Target: ${BASE_URL}`);
}

export function teardown() {
    console.log('Stress test completed. Review metrics to find capacity limits.');
}
