// Frontend Configuration Module (TypeScript)
// Loads configuration from environment variables at build/runtime

export interface Config {
  api: {
    baseUrl: string;
    timeout: number;
  };
  app: {
    name: string;
    version: string;
    env: 'development' | 'staging' | 'production';
  };
  features: {
    invoicing: boolean;
    forecasting: boolean;
    weather: boolean;
  };
}

// Load configuration from import.meta.env (Vite)
export const config: Config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || 'Enterprise Retail Intelligence',
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
    env: (import.meta.env.VITE_APP_ENV || 'development') as 'development' | 'staging' | 'production',
  },
  features: {
    invoicing: import.meta.env.VITE_ENABLE_INVOICING === 'true',
    forecasting: import.meta.env.VITE_ENABLE_FORECASTING === 'true',
    weather: import.meta.env.VITE_ENABLE_WEATHER === 'true',
  },
};

/**
 * Validate configuration at runtime
 * Throws error if critical values are missing
 */
export function validateConfig(): void {
  if (!config.api.baseUrl) {
    throw new Error('Missing VITE_API_BASE_URL environment variable');
  }

  if (config.api.timeout < 1000) {
    throw new Error('VITE_API_TIMEOUT must be at least 1000ms');
  }

  if (!config.api.baseUrl.match(/^https?:\/\//)) {
    throw new Error('VITE_API_BASE_URL must be a valid HTTP(S) URL');
  }

  console.log('✅ Configuration validated');
  console.log(`  API Base URL: ${config.api.baseUrl}`);
  console.log(`  Environment: ${config.app.env}`);
  console.log(`  API Timeout: ${config.api.timeout}ms`);
}

// Run validation when config loads (in main.tsx)
// validateConfig();

// Example environment files:
// .env.development:
// VITE_API_BASE_URL=http://localhost:8000/api/v1
// VITE_API_TIMEOUT=30000
// VITE_APP_ENV=development
// VITE_ENABLE_INVOICING=true

// .env.production:
// VITE_API_BASE_URL=https://api.example.com/api/v1
// VITE_API_TIMEOUT=30000
// VITE_APP_ENV=production
// VITE_ENABLE_INVOICING=true
