// @ts-check
import { defineConfig, devices } from '@playwright/test';
import os from 'node:os';

// Dedicated E2E port so the suite never clashes with a hand-run dev server (5002).
const PORT = Number(process.env.E2E_PORT) || 5050;
// Lab hostname, not localhost — required by the project CLAUDE.md and more robust
// here (localhost resolves to IPv6 ::1, which would miss the IPv4 0.0.0.0 bind).
const HOST = process.env.E2E_HOST || os.hostname();
const BASE_URL = process.env.E2E_BASE_URL || `http://${HOST}:${PORT}`;
// The Vite dev server must bind the SAME port Playwright polls/visits, even when
// BASE_URL is overridden wholesale — derive it from BASE_URL so they can't drift.
const SERVE_PORT = new URL(BASE_URL).port || String(PORT);

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure', // keep a trace on any failure, even with retries: 0 locally
    screenshot: 'only-on-failure',
    // Emulate prefers-reduced-motion so the motion-safe page-enter fade
    // (App.css, guarded by @media prefers-reduced-motion) is disabled. Without
    // this, axe can sample link colours mid-fade (semi-transparent blue) and
    // report false color-contrast failures; the resting state is #1d70b8 on
    // white (5.17:1, passes). This also keeps the whole suite deterministic.
    reducedMotion: 'reduce',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    env: { VITE_PORT: SERVE_PORT },
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
