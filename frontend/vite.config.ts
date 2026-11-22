import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  // Root-absolute base: the app's routes are root-relative, so its assets
  // must be too. A relative base (`./`) makes the entry document request
  // `./assets/...`, which on a nested route such as `/repairs/1` resolves
  // under the route (`/repairs/assets/...`) and leaves the page blank on
  // direct navigation or refresh.
  base: '/',
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
