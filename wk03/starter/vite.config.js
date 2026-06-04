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
    // The /help intent matcher loads its model from the same-origin /models/
    // path (Transformers.js localModelPath). Browsers behind the lab reverse
    // proxy can't reach huggingface.co directly, but the dev server can — so
    // proxy /models/<org>/<repo>/<file> to the model's resolve URL on the Hub
    // and follow the redirect to the weights CDN. Without this, /models/ hits
    // the SPA history-fallback (index.html) and the matcher degrades to a
    // basic keyword search.
    proxy: {
      '/models': {
        target: 'https://huggingface.co',
        changeOrigin: true,
        followRedirects: true,
        rewrite: (path) =>
          path.replace(/^\/models\/([^/]+\/[^/]+)\/(.+)$/, '/$1/resolve/main/$2'),
      },
    },
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
