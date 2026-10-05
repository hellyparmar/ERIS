import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AppProvider, ToastProvider } from './lib/app'
import '@fontsource-variable/inter'
import './styles.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 60_000,
      // a 503 with an answer means "busy, try again shortly" (e.g. every forecast slot is taken): keep trying for ~20 s
      retry: (count, err) => (err?.status === 503 && err?.data ? count < 4 : count < 1),
      retryDelay: (count, err) => (err?.status === 503 && err?.data ? 5000 : Math.min(1000 * 2 ** count, 8000)),
    },
  },
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ToastProvider>
          <AppProvider>
            <App />
          </AppProvider>
        </ToastProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
