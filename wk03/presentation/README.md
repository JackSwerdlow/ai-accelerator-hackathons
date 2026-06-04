# Hackathon process deck

A slide deck describing the process behind the **Green Home Grant** hackathon build —
reconstructed from `../starter/AI_LOG.md`, the git history, and `../docs/PLAN.md`.

Audience: engineers with a moderate understanding of AI-mediated development.

- **Deck:** [`hackathon-process-deck.md`](./hackathon-process-deck.md) — [Marp](https://marp.app/) Markdown (22 slides). Diagrams use [Mermaid](https://mermaid.js.org/) fenced code blocks.
- **One-pager:** [`one-pager.html`](./one-pager.html) — a self-contained A4 infographic distilling the whole story onto a single page.
- **Timeline:** [`timeline.html`](./timeline.html) — a **16:9 presentation slide** mapping every README objective + stretch goal to when it landed, across the plan → develop → improve phases (Day 1 10:30–16:30 → overnight pause → Day 2 from 10:00), with a rising cumulative-tests curve. Exports a crisp `timeline.png` for screen-sharing plus a 16:9 `timeline.pdf`.

> This deck is a process retrospective; it documents the wk03 build rather than
> changing any application code.

## Viewing it

### Quickest — read the Markdown directly
GitHub and most Mermaid-aware Markdown viewers (incl. the VS Code built-in preview with a
Mermaid extension) render the `mermaid` blocks inline. You won't get slide pagination, but
all content and diagrams are visible.

### As real slides (PDF + HTML)

```bash
cd wk03/presentation
./build.sh        # writes deck.pdf, deck.html and one-pager.pdf
```

`build.sh` runs three stages (all need a Chromium/Chrome):

1. **`mermaid-cli` (mmdc)** pre-renders every ` ```mermaid ` block to a PNG at its natural
   size, writing `build/deck.md` with image references. We pre-render rather than render
   Mermaid at slide time because Marp can't render Mermaid itself, and runtime-rendered SVGs
   get their labels **clipped when Chrome scales them down for print**. Rasterising each
   diagram at full size first sidesteps that entirely.
2. **`marp-cli`** converts `build/deck.md` to `deck.pdf` and `deck.html`
   (`--allow-local-files`, so the local diagram PNGs embed).
3. **headless Chrome** prints the self-contained infographics `one-pager.html` and
   `timeline.html` to single-page PDFs (`--print-to-pdf`; no pre-render step needed), and
   screenshots the 16:9 `timeline.html` to a 2× `timeline.png` for screen-sharing/embedding.

If you don't have a browser installed, grab the puppeteer one once:

```bash
npx puppeteer browsers install chrome
```

The script auto-detects that browser (or any `google-chrome`/`chromium` on `PATH`, or a
`CHROME_PATH` you set) and runs it headless with `--no-sandbox`.

> Editing diagrams: change the `mermaid` fences in `hackathon-process-deck.md` (the single
> source) and re-run `./build.sh`. Diagram sizing on slides is controlled by the `img`
> rule in the deck's frontmatter `style` block.

## Files

| File | Purpose |
|---|---|
| `hackathon-process-deck.md` | The deck — Marp Markdown with `mermaid` diagrams (the source) |
| `one-pager.html` | Self-contained A4 infographic (the whole story on one page) |
| `timeline.html` | Self-contained 16:9 presentation slide (objectives + stretch goals over time) |
| `build.sh` | Three-stage build (mmdc → marp → Chrome) producing `deck.pdf`, `deck.html`, `one-pager.pdf`, `timeline.pdf`, `timeline.png` |
| `mermaid-config.json` | Mermaid theme/layout used by the pre-render step |
| `puppeteer-config.json` | Headless-Chrome args (`--no-sandbox`) for both tools |
| `README.md` | This file |

Generated outputs (`deck.pdf`, `deck.html`, `build/`) are git-ignored — rebuild with `./build.sh`.
