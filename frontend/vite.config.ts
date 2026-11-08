import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  // Relative base so the static bundle can be served from / or any subpath.
  base: './',
  plugins: [react()],
  server: {
    // Dev proxy: keep the app same-origin against the local Flask backend
    // (`make run` binds 127.0.0.1:5000). No CORS configuration needed.
    proxy: {
      '/api': 'http://127.0.0.1:5000',
      '/healthz': 'http://127.0.0.1:5000',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
