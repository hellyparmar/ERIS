import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for R-DIOS E2E Testing
 * 
 * Test Coverage:
 * - Authentication flows
 * - Multi-tenant operations
 * - Invoice creation (online/offline)
 * - Payment processing
 * - Integrations (Tally, Zoho)
 * - Offline functionality
 */

export default defineConfig({
    testDir: './tests/e2e',

    // Maximum time one test can run
    timeout: 60 * 1000,

    // Test execution settings
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : 4,

    // Reporter configuration
    reporter: [
        ['html', { outputFolder: 'test-results/html' }],
        ['json', { outputFile: 'test-results/results.json' }],
        ['junit', { outputFile: 'test-results/junit.xml' }],
        ['list']
    ],

    // Shared settings for all tests
    use: {
        // Base URL for tests
        baseURL: process.env.BASE_URL || 'http://localhost:3000',

        // API endpoint
        apiURL: process.env.API_URL || 'http://localhost:8000',

        // Collect trace when retrying failed test
        trace: 'on-first-retry',

        // Screenshot on failure
        screenshot: 'only-on-failure',

        // Video on failure
        video: 'retain-on-failure',

        // Browser context options
        viewport: { width: 1280, height: 720 },

        // Network conditions
        offline: false,

        // Additional context options
        ignoreHTTPSErrors: true,

        // Slow down actions (for debugging)
        // launchOptions: {
        //   slowMo: 50
        // }
    },

    // Test projects for different browsers
    projects: [
        {
            name: 'chromium',
            use: {
                ...devices['Desktop Chrome'],
                // Chrome-specific options
                channel: 'chrome'
            },
        },

        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
        },

        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
        },

        // Mobile viewports
        {
            name: 'mobile-chrome',
            use: { ...devices['Pixel 5'] },
        },

        {
            name: 'mobile-safari',
            use: { ...devices['iPhone 12'] },
        },

        // Offline testing
        {
            name: 'offline-chromium',
            use: {
                ...devices['Desktop Chrome'],
                offline: true,
            },
        },
    ],

    // Web server configuration
    webServer: [
        {
            command: 'npm run start',
            url: 'http://localhost:3000',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
            cwd: '../',
        },
        {
            command: 'cd ../api && uvicorn api.main:app --reload',
            url: 'http://localhost:8000/health',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
        }
    ],

    // Global setup/teardown
    globalSetup: './tests/e2e/global-setup.ts',
    globalTeardown: './tests/e2e/global-teardown.ts',
});
