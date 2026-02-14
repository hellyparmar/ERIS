# Task 2.2: Environment Configuration - Frontend
**Owner:** Frontend Lead  
**Duration:** 3 hours  
**Deadline:** Feb 18, 6:00 PM IST  
**Priority:** 🟡 HIGH (Needed before Task 3.1)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #2.1 Backend Environment Config

---

## Description

Implement environment-based configuration for frontend. Remove hardcoded API URLs and configure Vite to load environment variables. Support multiple environments (dev, staging, prod).

## Acceptance Criteria

- [ ] `.env.example` created for frontend
- [ ] `vite.config.ts` updated to load env variables
- [ ] `src/config.ts` created for app configuration
- [ ] API client uses `VITE_API_BASE_URL` from environment
- [ ] All hardcoded URLs removed from components
- [ ] Build works for dev, staging, and production
- [ ] Environment variables documented
- [ ] Developers can switch environments easily

## Environment Variables

### API Configuration
```bash
# API server endpoint
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=30000

# Feature flags
VITE_ENABLE_INVOICING=true
VITE_ENABLE_FORECASTING=true
VITE_ENABLE_WEATHER=true
```

### Application Settings
```bash
# App metadata
VITE_APP_NAME=Enterprise Retail Intelligence
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=development

# Analytics (optional)
VITE_ANALYTICS_ENABLED=false
VITE_ANALYTICS_ID=
```

### Build Settings
```bash
# Vite specific
VITE_PORT=5173
VITE_HOST=0.0.0.0
```

## Implementation

### Step 1: Create `.env.example` for Frontend
```bash
# .env.example
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=30000
VITE_APP_NAME=Enterprise Retail Intelligence
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=development
VITE_ENABLE_INVOICING=true
VITE_ENABLE_FORECASTING=true
VITE_ENABLE_WEATHER=true
```

### Step 2: Create `src/config.ts`
```typescript
// src/config.ts
export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || 'Enterprise Retail Intelligence',
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
    env: import.meta.env.VITE_APP_ENV || 'development',
  },
  features: {
    invoicing: import.meta.env.VITE_ENABLE_INVOICING === 'true',
    forecasting: import.meta.env.VITE_ENABLE_FORECASTING === 'true',
    weather: import.meta.env.VITE_ENABLE_WEATHER === 'true',
  },
};

// Validation
export function validateConfig() {
  if (!config.api.baseUrl) {
    throw new Error('Missing VITE_API_BASE_URL environment variable');
  }
  if (config.api.timeout < 1000) {
    throw new Error('VITE_API_TIMEOUT must be at least 1000ms');
  }
}
```

### Step 3: Update `vite.config.ts`
```typescript
// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [react()],
    server: {
      port: parseInt(env.VITE_PORT || '5173'),
      host: env.VITE_HOST || '0.0.0.0',
    },
    define: {
      __APP_ENV__: JSON.stringify(env.APP_ENV),
    },
  }
})
```

### Step 4: Update API Client
```typescript
// src/api/client.ts
import axios from 'axios'
import { config } from '../config'

export const apiClient = axios.create({
  baseURL: config.api.baseUrl,
  timeout: config.api.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Example API call
export async function fetchInventory(page: number = 1, limit: number = 50) {
  const response = await apiClient.get('/inventory/list', {
    params: { page, limit }
  })
  return response.data
}
```

### Step 5: Update Components
**Before (Hardcoded):**
```typescript
const response = await fetch('http://localhost:8000/api/v1/inventory/list')
```

**After (Using config):**
```typescript
import { apiClient } from '../api/client'
const response = await apiClient.get('/inventory/list')
```

## Environment-Specific Files

**Development** (`.env.development`)
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_ENV=development
```

**Staging** (`.env.staging`)
```bash
VITE_API_BASE_URL=https://api-staging.example.com/api/v1
VITE_APP_ENV=staging
```

**Production** (`.env.production`)
```bash
VITE_API_BASE_URL=https://api.example.com/api/v1
VITE_APP_ENV=production
```

## Build Commands

```bash
# Development
npm run dev

# Build for staging
npm run build:staging

# Build for production
npm run build

# All three defined in package.json
```

## File Changes

| File | Change | Type |
|------|--------|------|
| `.env.example` | NEW | Config template |
| `.env.development` | NEW | Dev settings |
| `.env.staging` | NEW | Staging settings |
| `.env.production` | NEW | Prod settings |
| `src/config.ts` | NEW | Config loader |
| `vite.config.ts` | UPDATE | Env support |
| `src/api/client.ts` | UPDATE | Use config |
| `package.json` | UPDATE | Build scripts |

## Verification Checklist

```bash
# 1. Verify no hardcoded URLs
grep -r "localhost:8000" src/
grep -r "api.example.com" src/
grep -r "http://" src/ | grep -v "https://" | grep -v ".env"

# 2. Verify config is loaded
cat src/config.ts | grep "VITE_"

# 3. Test build with different environments
npm run build:development
npm run build:staging
npm run build:production

# 4. Verify config values in build
grep -i "api" dist/index.html
```

## Related Issues
- #2.1 Backend Environment Config
- #3.1 Pagination Implementation

## Definition of Done
✅ `.env.example` created with all variables  
✅ `vite.config.ts` loads environment variables  
✅ `src/config.ts` provides configuration to app  
✅ All hardcoded URLs removed from source  
✅ Builds work for dev/staging/prod environments  
✅ API client uses environment-based URL  
✅ Team can build for any environment
