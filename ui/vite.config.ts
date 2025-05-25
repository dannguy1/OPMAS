import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Allow external access
    port: 3000,
    strictPort: true, // Don't try other ports if 3000 is taken
    cors: true,       // Enable CORS
    hmr: {
      host: 'localhost', // Use localhost for HMR
      port: 3000,
      clientPort: 3000,
    }
  }
})
