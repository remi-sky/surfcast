import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // ← add this block:
  preview: {
    host: '0.0.0.0',
    port: Number(process.env.PORT) || 4173,
    allowedHosts: [
      'surfcast-production.up.railway.app',  // your Railway front-end hostname
      // you can add other domains here if needed
    ],
  },
})
