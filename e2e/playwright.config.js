// End-to-end tests: starts the API (which serves the built web app) on a fresh SQLite database seeded with a
// shorter synthetic history, then drives the UI in Chromium.
//   cd web && npm run build && cd ../e2e && npm test
import { defineConfig, devices } from '@playwright/test'
import os from 'node:os'
import path from 'node:path'

const PORT = Number(process.env.E2E_PORT || 8077)
const db = path.join(os.tmpdir(), `eris-e2e-${Date.now()}.db`)

export default defineConfig({
  testDir: './tests',
  timeout: 120_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  globalSetup: './global-setup.js',
  use: {
    baseURL: `http://localhost:${PORT}`,
    ...devices['Desktop Chrome'],
    launchOptions: process.env.PW_CHROMIUM_PATH ? { executablePath: process.env.PW_CHROMIUM_PATH } : {},
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: `python -m uvicorn app.main:app --port ${PORT}`,
    cwd: '../api',
    url: `http://localhost:${PORT}/api/health`,
    timeout: 120_000,
    reuseExistingServer: false,
    env: {
      DATABASE_URL: `sqlite:///${db}`,
      SEED_DEMO_DATA: 'true',
      SEED_DAYS: '240',
      LLM_ENABLED: 'false',
      JWT_SECRET_KEY: 'e2e-only-secret-key-0123456789abcdef-0123456789',
    },
  },
})
