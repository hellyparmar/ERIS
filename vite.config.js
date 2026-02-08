import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import { imagetools } from 'vite-imagetools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Image optimization
    imagetools({
      defaultDirectives: () => {
        // Optimize all images by default
        return new URLSearchParams({
          format: 'webp;jpg', // Generate WebP with JPEG fallback
          quality: '80', // 80% quality
        })
      },
    }),
    // Bundle analyzer (only in build mode)
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true,
      filename: 'dist/stats.html',
    }),
  ],

  build: {
    // Enable source maps for production debugging
    sourcemap: false,

    // Optimize chunk size
    chunkSizeWarningLimit: 1000,

    // Manual chunk splitting for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'chart-vendor': ['recharts'],
          'ui-vendor': ['lucide-react', 'framer-motion'],
          'query-vendor': ['@tanstack/react-query', 'axios'],
        },
      },
    },

    // Minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.logs in production
        drop_debugger: true,
      },
    },
  },

  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'axios',
      'recharts',
      'lucide-react',
      'framer-motion',
    ],
  },

  // Server configuration
  server: {
    port: 5173,
    strictPort: true,
    host: true,
    watch: {
      ignored: ['**/.venv/**', '**/node_modules/**', '**/.git/**'],
    },
  },

  // Preview configuration
  preview: {
    port: 4173,
    strictPort: true,
  },
})
