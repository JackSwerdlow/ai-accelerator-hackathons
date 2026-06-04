import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Decoded lab reverse-proxy environment.
// The app is only ever reached at https://<app>.labs.decoded.com/ — the proxy
// terminates TLS on 443 and forwards to this dev server over the VM network.
// Default to the proxy-published port 5000; override with VITE_PORT if needed.
const PORT = Number(process.env.VITE_PORT) || 5000;

export default defineConfig({
  plugins: [react()],
  server: {
    // (1) Bind every interface so the proxy can reach us over the network —
    //     a 127.0.0.1-only bind is unreachable and shows "Nothing on port N".
    host: '0.0.0.0',
    // (2) A port the proxy publishes (5000 -> app-lab….labs.decoded.com).
    port: PORT,
    strictPort: true,
    // (3) Accept the external Host header. Vite >=5.4 blocks unknown hosts with
    //     a "Blocked request" page; pin this VM's two published hostnames
    //     (app- = the running app, code- = the IDE). For a different lab VM,
    //     swap lab9102, or use '.labs.decoded.com' to allow any subdomain.
    allowedHosts: ['app-lab9102.labs.decoded.com', 'code-lab9102.labs.decoded.com'],
    // (6) HMR runs through the same HTTPS proxy. The browser must open the
    //     websocket at wss://<public-host>:443 — protocol wss + clientPort 443.
    //     Leaving `host` unset makes the client reuse window.location.hostname,
    //     so it resolves to the public proxy host on whatever lab VM this is.
    hmr: { protocol: 'wss', clientPort: 443 },
  },
  // Same proxy rules for `vite preview` (smoke-testing a production build).
  preview: {
    host: '0.0.0.0',
    port: PORT,
    strictPort: true,
    allowedHosts: ['app-lab9102.labs.decoded.com', 'code-lab9102.labs.decoded.com'],
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
