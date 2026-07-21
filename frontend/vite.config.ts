import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    target: 'esnext'
  },
  esbuild: {
    supported: {
      'destructuring': true
    }
  },
  optimizeDeps: {
    esbuildOptions: {
      supported: {
        'destructuring': true
      }
    }
  }
})


