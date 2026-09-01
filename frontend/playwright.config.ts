/**
 * Playwright Configuration for Test Suites
 * Includes Phase 2 (Responsive), Phase 4 (Cross-Browser), Phase 5 (Accessibility)
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'test-results/html' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],

  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    // Phase 2: Responsive Design Tests
    {
      name: 'chromium-responsive',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/phase-2-responsive/**',
    },
    {
      name: 'firefox-responsive',
      use: { ...devices['Desktop Firefox'] },
      testMatch: '**/phase-2-responsive/**',
    },
    {
      name: 'webkit-responsive',
      use: { ...devices['Desktop Safari'] },
      testMatch: '**/phase-2-responsive/**',
    },

    // Mobile viewports for responsive
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
      testMatch: '**/phase-2-responsive/**',
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
      testMatch: '**/phase-2-responsive/**',
    },

    // Tablet viewports
    {
      name: 'tablet-chrome',
      use: { ...devices['iPad Pro'] },
      testMatch: '**/phase-2-responsive/**',
    },

    // Phase 4: Cross-Browser Tests
    {
      name: 'chrome-cross-browser',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/phase-4-cross-browser/**',
    },
    {
      name: 'firefox-cross-browser',
      use: { ...devices['Desktop Firefox'] },
      testMatch: '**/phase-4-cross-browser/**',
    },
    {
      name: 'webkit-cross-browser',
      use: { ...devices['Desktop Safari'] },
      testMatch: '**/phase-4-cross-browser/**',
    },
    {
      name: 'edge',
      use: { ...devices['Desktop Edge'] },
      testMatch: '**/phase-4-cross-browser/**',
    },

    // Phase 5: Accessibility Tests
    {
      name: 'accessibility',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/phase-5-accessibility/**',
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
