import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // En desarrollo, /api se reenvía al backend (en producción lo hace nginx).
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
})
