import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/react'
import './index.css'
import App from './App.jsx'
import { ThemeProvider } from './hooks/useTheme'
import { LanguageProvider } from './hooks/useLanguage'
import { queryClient } from './lib/queryClient'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LanguageProvider>
          <App />
          <Analytics />
          <SpeedInsights />
        </LanguageProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
)
