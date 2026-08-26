import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Reconstructed from what production actually serves. The live site has
  // always shipped four vendor chunks alongside the lazy per-page ones -
  // react, router, charts and motion - but no committed config produced
  // them, so a build from this repo collapsed them into the entry bundle.
  // Recharts and framer-motion are the heavy two: split out, they are
  // fetched only by the pages that use them.
  build: {
    rollupOptions: {
      output: {
        // Matched on path, not bare specifier: the app imports
        // 'react-dom/client', which a { react: ['react-dom'] } key does not
        // match, and React silently lands in whichever chunk pulls it first.
        // Router is tested before React so react-router-* is not swallowed
        // by the react/ prefix.
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('node_modules/react-router')) return 'router'
          if (
            id.includes('node_modules/react-dom') ||
            id.includes('node_modules/react/') ||
            id.includes('node_modules/scheduler')
          ) return 'react'
          if (id.includes('node_modules/recharts')) return 'charts'
          if (id.includes('node_modules/framer-motion')) return 'motion'
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
