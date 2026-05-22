import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import path from 'path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '~components': path.resolve(__dirname, './src/components'),
      '~features': path.resolve(__dirname, './src/features'),
      '~lib': path.resolve(__dirname, './src/lib'),
      '~types': path.resolve(__dirname, './src/types'),
    },
  },
  build: {
    outDir: path.resolve(__dirname, '../backend/static'),
    emptyOutDir: true,
    assetsDir: 'assets'
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
