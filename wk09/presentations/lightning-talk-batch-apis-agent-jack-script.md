# Speaker script — "Batch APIs: Cheaper, Not Faster" (~2 min)

Slide: `lightning-talk-batch-apis-agent-jack.html`

---

Quick one. Today I learned there's a whole category of "batch" APIs across
LLM providers — Anthropic, OpenAI, Google — that I'd been thinking about
wrong.

When I heard "batch processing," I pictured firing off a bunch of requests
at once and getting them all back fast — parallelism. That's not what a
Batch API is.

A real Batch API trades speed for cost. You submit your whole job, it goes
into a queue, and you get results back... whenever. Anthropic's own SLA is
up to 24 hours. There's no minimum — it could finish in a couple of minutes
or it could sit there for hours. In exchange, you get roughly 50% off the
token price.

*[point at slide]* We actually tested all three ways of driving the same
API on the same real workload today. One request at a time took just under
two minutes. Firing them all concurrently — genuine parallelism, still
paying full price — took about eleven seconds. The real Batch API took
twenty-six minutes, for less than half the cost.

The thing I want you to take away: "batch" and "concurrent" are two
completely different tools, and mixing them up is an easy mistake — I made
it myself this morning. If you actually need a fast answer, batch is the
wrong call regardless of the discount. It's built for the big job nobody's
sitting there waiting on.

And this isn't an Anthropic quirk — OpenAI's Batch API and Google's Gemini
Batch Mode both use the exact same structure: 50% off, roughly a 24-hour
target, and in practice almost always faster than that. It's a genuine
industry pattern for how providers price non-urgent inference.

So — next time someone says "let's batch it" to make something faster,
ask them which kind of batch they mean.

---

**Timing:** ~280 words, ~2 minutes at a natural conversational pace.

**Sources for the "not just Anthropic" claim** (checked 2026-07-15):
- [OpenAI Batch API docs](https://developers.openai.com/api/docs/guides/batch) — 50% discount, 24h processing window
- [Google Gemini Batch API docs](https://ai.google.dev/gemini-api/docs/batch-api) — 50% discount, 24h target SLO
