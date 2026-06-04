# End-to-end tests (Playwright)

Browser-driven E2E suite covering the full Green Home Grant user journey.

## Run

```bash
npm install                       # if not already done
npx playwright install chromium   # one-time, if the browser is not cached
npm run test:e2e                  # runs the suite (Playwright starts the dev server itself)
npm run test:e2e:report           # open the last HTML report
```

Playwright starts `npm run dev` on port **5050** and points the browser at
`http://<hostname>:5050` (the lab hostname, per the project CLAUDE.md — not
`localhost`). Overrides: `E2E_HOST` and `E2E_PORT` compose the default URL;
`E2E_BASE_URL` overrides host **and** port wholesale (the dev server binds to
whatever port that URL specifies, so they can't drift).

## Layout

- `playwright.config.js` (project root) — chromium project, `webServer`, `baseURL`.
- `e2e/helpers.js` — reusable step helpers + answer-set label constants.
- `e2e/*.spec.js` — one file per concern:
  - `smoke` — app loads and hydrates
  - `journeys` — all six eligibility outcomes end-to-end
  - `navigation` — start, path-aware step indicator, Back, tenant branching
  - `check-answers` — path-aware summary + Change round-trip + Submit
  - `validation` — GOV.UK empty-field error pattern
  - `guards` — deep-link redirects
  - `save-and-return` — localStorage persistence across reload + resume banner
  - `pdf-download` — real PDF download event
  - `accessibility` — skip link, focus management, keyboard-only, 320px reflow,
    a11y-statement nav, and `@axe-core/playwright` WCAG 2.2 AA scans

`npm test` / `npm run test:run` remain the Vitest unit/integration entry points;
they do not run these e2e specs (Vitest `include` is scoped to `src/**`).
