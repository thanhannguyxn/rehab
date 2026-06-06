import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'

const BACKEND = process.env.VITE_BACKEND_URL || 'http://localhost:8000'
const BACKEND_WS = BACKEND.replace(/^http/, 'ws')

export default defineConfig({
  plugins: [react(), basicSsl()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/main.tsx', 'src/vite-env.d.ts']
    }
  },
  server: {
    port: 3000,
    hmr: {
      clientPort: 443
    },
    proxy: {
      // All /api/* requests go through the proxy → cookies stay on same-scheme origin
      '/api': {
        target: BACKEND,
        changeOrigin: true,
      },
      // Static assets (exercise demo videos, thumbnails)
      '/static': {
        target: BACKEND,
        changeOrigin: true,
      },
      '/uploads': {
        target: BACKEND,
        changeOrigin: true,
      },
      // WebSocket — exercise pose analysis
      '/ws': {
        target: BACKEND_WS,
        ws: true,
        secure: false,
      },
    },
  },
})
