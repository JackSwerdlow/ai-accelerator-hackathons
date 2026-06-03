import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',                       // (1) bind all interfaces — reachable through the proxy
    port: 5000,                            // (2) listen on 5000
    strictPort: true,                      // fail loudly instead of silently picking another port
    allowedHosts: ['.labs.decoded.com'],   // (3) accept Host: app-lab9102.labs.decoded.com (any *.labs.decoded.com)
    hmr: {
      protocol: 'wss',                     // (4)(6) proxy terminates TLS → HMR client connects over wss…
      host: 'app-lab9102.labs.decoded.com',
      clientPort: 443,                     // …to the public host on 443, not ws://localhost:5000
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.js'],
    css: false,
  },
});
