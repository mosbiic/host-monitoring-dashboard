import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 13000,
    allowedHosts: ['monitoring.mosbiic.com'],
    proxy: {
      '/api': {
        target: 'http://localhost:18081',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:18081',
        ws: true
      }
    },
    // Fixed port configuration
    strictPort: true
  }
})
