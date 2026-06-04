#!/usr/bin/env bash
# Build the slide deck to PDF (and HTML).
#
# Two stages, because Marp cannot render Mermaid and runtime-rendered SVGs clip
# when scaled for print:
#   1. mermaid-cli (mmdc) pre-renders every ```mermaid block to a PNG at natural
#      size, emitting build/deck.md with image references.
#   2. marp-cli converts that to PDF + HTML.
#
# Requires Node.js. A Chromium/Chrome is needed for both tools; if you don't have
# one, install the puppeteer build once:  npx puppeteer browsers install chrome
#
# Usage:  ./build.sh          # writes deck.pdf and deck.html
set -euo pipefail
cd "$(dirname "$0")"

SRC="hackathon-process-deck.md"
OUT_PDF="deck.pdf"
OUT_HTML="deck.html"

# --- locate a browser -------------------------------------------------------
CHROME="${CHROME_PATH:-}"
if [[ -z "$CHROME" ]]; then
  CHROME="$(ls -d "$HOME"/.cache/puppeteer/chrome/*/chrome-linux64/chrome 2>/dev/null | head -1 || true)"
fi
if [[ -z "$CHROME" ]]; then
  CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
fi
if [[ -z "$CHROME" ]]; then
  echo "No Chrome/Chromium found. Run: npx puppeteer browsers install chrome" >&2
  exit 1
fi
echo "Using browser: $CHROME"

export CHROME_PATH="$CHROME"
export PUPPETEER_EXECUTABLE_PATH="$CHROME"
export CHROME_NO_SANDBOX=1   # required for headless Chrome in many CI/sandbox envs

mkdir -p build

echo "[1/2] Pre-rendering Mermaid diagrams to PNG..."
npx --yes @mermaid-js/mermaid-cli@latest \
  -i "$SRC" -o build/deck.md \
  -e png -s 3 -b transparent -t neutral \
  -c mermaid-config.json -p puppeteer-config.json

echo "[2/3] Converting to PDF + HTML with Marp..."
# --allow-local-files lets Marp embed the locally pre-rendered diagram PNGs.
npx --yes @marp-team/marp-cli@latest --html --allow-local-files build/deck.md --pdf -o "$OUT_PDF"
npx --yes @marp-team/marp-cli@latest --html --allow-local-files build/deck.md -o "$OUT_HTML"

echo "[3/3] Printing the one-pager + timeline to PDF (headless Chrome)..."
# Self-contained HTML infographics -> single-page PDFs. @page CSS sets size + zero margin.
for html in one-pager timeline; do
  "$CHROME" --headless --no-sandbox --disable-gpu --no-pdf-header-footer \
    --run-all-compositor-stages-before-draw --virtual-time-budget=3000 \
    --print-to-pdf="$html.pdf" "$html.html" 2>/dev/null
done

echo "Done: $OUT_PDF, $OUT_HTML, one-pager.pdf and timeline.pdf"
