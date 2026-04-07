import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/recharts')) {
            return 'vendor-recharts'
          }
          if (id.includes('node_modules/react-router-dom')) {
            return 'vendor-router'
          }
          if (id.includes('node_modules/lucide-react')) {
            return 'vendor-icons'
          }
          if (id.includes('node_modules/axios')) {
            return 'vendor-axios'
          }
          if (id.includes('node_modules')) {
            return 'vendor-core'
          }
          return undefined
        },
      },
    },
  },
})
