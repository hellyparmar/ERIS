import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { Plugin } from 'vite'

// Root node_modules (where package.json and node_modules actually live)
const rootNodeModules = path.resolve(__dirname, '../node_modules')

export default defineConfig({
  plugins: [react()],
  define: {
    'window.glMatrixArrayType': 'Float32Array',
    'glMatrixArrayType': 'Float32Array',
  },
  resolve: {
    // Force a single copy of React across all packages (fixes recharts/ResponsiveContainer hook errors)
    dedupe: ['react', 'react-dom', 'react/jsx-runtime', 'react-dom/client'],
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Explicitly point React to the root node_modules copy
      'react': path.resolve(rootNodeModules, 'react'),
      'react-dom': path.resolve(rootNodeModules, 'react-dom'),
      'react/jsx-runtime': path.resolve(rootNodeModules, 'react/jsx-runtime'),
      'react-dom/client': path.resolve(rootNodeModules, 'react-dom/client'),
    },
    // Also resolve modules from root node_modules
    modules: [rootNodeModules, 'node_modules'],
  },
  server: {
    port: 4173,
    host: '127.0.0.1',
    open: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})
