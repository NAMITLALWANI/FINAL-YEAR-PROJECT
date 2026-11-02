import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/search':             'http://localhost:8000',
      '/publications':       'http://localhost:8000',
      '/similarity-log':     'http://localhost:8000',
      '/metrics':            'http://localhost:8000',
      '/health':             'http://localhost:8000',
      '/evidence':           'http://localhost:8000',
      '/author-resolutions': 'http://localhost:8000',
    },
  },
})
