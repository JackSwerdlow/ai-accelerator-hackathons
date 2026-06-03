import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import os from 'node:os';

// AiSEng lab-VM reverse-proxy convention: public URLs are
// https://<hostname>:<port> on ports 5000-5005 and 8100-8105.
// Default to 5002; override via VITE_PORT and VITE_PUBLIC_HOSTNAME.
const PORT = Number(process.env.VITE_PORT) || 5002;
const HOSTNAME = process.env.VITE_PUBLIC_HOSTNAME || os.hostname();

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: PORT,
    strictPort: true,
    hmr: {
      protocol: 'wss',
      host: HOSTNAME,
      clientPort: 443,
    },
  },
});
