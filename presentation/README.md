# Hackathon process deck

A slide deck describing the process behind the **Green Home Grant** hackathon build —
reconstructed from `../wk03/starter/AI_LOG.md`, the git history, and `../wk03/docs/PLAN.md`.

Audience: engineers with a moderate understanding of AI-mediated development.

- **Deck:** [`hackathon-process-deck.md`](./hackathon-process-deck.md) — [Marp](https://marp.app/) Markdown.
- Diagrams use [Mermaid](https://mermaid.js.org/) fenced code blocks.

> This deck lives outside `wk03/` and does **not** modify any wk03 code or content.

## Viewing it

### Quickest — read the Markdown directly
GitHub and most Mermaid-aware Markdown viewers (incl. the VS Code built-in preview with a
Mermaid extension) render the `mermaid` blocks inline. You won't get slide pagination, but
all content and diagrams are visible.

### As real slides (HTML / PDF) with rendered diagrams
Marp Core doesn't render Mermaid by itself, so we ship a tiny engine (`engine.js`) that
hands Mermaid blocks to the Mermaid runtime in the exported page.

```bash
cd presentation

# Export to a self-contained HTML deck (diagrams render in the browser):
npx @marp-team/marp-cli@latest --engine ./engine.js --html hackathon-process-deck.md -o deck.html

# Or to PDF (uses headless Chrome; needs network access for the Mermaid CDN):
npx @marp-team/marp-cli@latest --engine ./engine.js --html --pdf hackathon-process-deck.md -o deck.pdf

# Live preview while editing:
npx @marp-team/marp-cli@latest --engine ./engine.js --html -p -w hackathon-process-deck.md
```

The `--html` flag is required so the Mermaid loader `<script>` at the foot of the deck
passes through to the output. The engine and the script are CDN-backed, so an internet
connection is needed when exporting (not when reading the raw Markdown).

If you prefer the VS Code **Marp for VS Code** extension, point its
`markdown.marp.mathTypesetting`/engine setting at `engine.js`, or just export from the CLI above.

## Files

| File | Purpose |
|---|---|
| `hackathon-process-deck.md` | The deck (Marp Markdown + Mermaid) |
| `engine.js` | Marp CLI engine that renders `mermaid` fences |
| `README.md` | This file |
