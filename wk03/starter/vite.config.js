import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import os from 'node:os';

const PORT = Number(process.env.VITE_PORT) || 5002;
const HOSTNAME = process.env.VITE_PUBLIC_HOSTNAME || os.hostname();

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: PORT,
    strictPort: true,
    hmr: { protocol: 'wss', host: HOSTNAME, clientPort: PORT },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.js'],
    css: false,
    // Scope Vitest to src/ so it never tries to run the Playwright e2e specs
    // (whose `test`/`expect` come from @playwright/test, not Vitest).
    include: ['src/**/*.{test,spec}.{js,jsx}'],
  },
});
