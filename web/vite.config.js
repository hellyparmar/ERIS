import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development the API runs on :8000 and is proxied, so the app always calls relative /api URLs.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target: process.env.VITE_API_PROXY || 'http://127.0.0.1:8000', changeOrigin: true } },
  },
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        // function form: Vite 8 (Rolldown) no longer accepts the object form
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (/node_modules\/(recharts|d3-|victory-vendor)/.test(id)) return 'charts'
          if (/node_modules\/(react|react-dom|react-router|react-router-dom|scheduler|@tanstack)\//.test(id)) return 'vendor'
          return undefined
        },
      },
    },
  },
})
