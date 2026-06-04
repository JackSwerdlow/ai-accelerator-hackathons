// Marp CLI engine that renders ```mermaid fenced code blocks.
//
// Marp Core does not understand Mermaid out of the box. This engine rewrites
// every ```mermaid fence into a <pre class="mermaid"> block; the small ES-module
// <script> at the bottom of the deck then loads Mermaid from a CDN and renders
// those blocks client-side in the exported HTML (or in headless Chrome for PDF).
//
// Usage:
//   npx @marp-team/marp-cli --engine ./engine.js --html hackathon-process-deck.md -o deck.html
//
// See README.md for the full commands.

module.exports = ({ marp }) => {
  const md = marp.markdown
  const defaultFence = md.renderer.rules.fence.bind(md.renderer.rules)

  md.renderer.rules.fence = (tokens, idx, options, env, self) => {
    const token = tokens[idx]
    if ((token.info || '').trim() === 'mermaid') {
      // Mermaid reads the diagram source from the element's text content.
      return `<pre class="mermaid">${token.content}</pre>\n`
    }
    return defaultFence(tokens, idx, options, env, self)
  }

  return marp
}
