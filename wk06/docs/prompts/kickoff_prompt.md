# Kick off prompt for week 6 hackathon

## Context

This project is a hackathon exercise to solidify learning around RAG models and multi-agent systems.

**Full lab brief, acceptance criteria, starter scaffold description, and setup instructions are in `context/LAB_README.md`. Read that first — this document records team decisions, patterns, and working rules that extend or override it.**

### Project Summary

Build a CLI multi-agent system that automates FOI request processing: a triage agent classifies requests, a compliance agent checks exemptions against policy documents using RAG, a response drafting agent composes replies, and a supervisor orchestrates the pipeline with a human-in-the-loop approval gate.

## Team Tooling Choices

> **Note:** `context/LAB_README.md` uses OpenAI (`gpt-4o-mini`, `gpt-4o`) and a plain OpenAI client. This team is using Claude models instead, with LangChain as the abstraction layer. All other lab requirements remain the same.

- **LLM API**: Claude models via Anthropic API key (`python-dotenv` for key management)
  - `langchain-anthropic` — LangChain integration for Claude
- **LLM interaction / tool creation / orchestration**: LangChain — agent loops, tool calling, output parsing, retry via `tenacity`
- **Embeddings**: `langchain-huggingface` with `sentence-transformers/all-MiniLM-L6-v2` (local, no API cost)
  - Fallback: set `EMBEDDING_PROVIDER=openai` in `.env` if HuggingFace Hub is blocked on the network
- **Vector store**: ChromaDB via `langchain-chroma`
- **Chunking**: LangChain `RecursiveCharacterTextSplitter` (built-in — no extra dependency)
- **Structured I/O**: Pydantic + LangChain `with_structured_output()`
- **Cost tracking**: LangChain callbacks (`BaseCallbackHandler`) — capture model, prompt tokens, completion tokens, and estimated cost per call without extra dependencies
- **Logging**: Python stdlib `logging` with a JSON formatter — structured, free, zero setup

Suggest alternatives where there are clear benefits, but ask before incorporating new libraries.

## Assessment Rubric

| Criterion | Excellent | Good | Needs Work |
| --- | --- | --- | --- |
| **Automation value** | System processes requests end-to-end with minimal human input; classification and exemption checking produce accurate, evidence-backed results | System automates most steps; some manual intervention needed beyond the designed checkpoints | Agents run but produce generic or unhelpful output; little time saved over manual processing |
| **Reliability** | All error paths handled; system recovers from API failures, malformed input, and empty results without crashing | Most errors handled; one or two edge cases cause unhandled exceptions | System crashes on unexpected input or API errors |
| **Governance** | HITL gate displays rich evidence (retrieved chunks, classification, draft) with timestamped override audit trail; approve/reject/modify decisions logged with operator identity and evidence refs | HITL gate pauses and accepts approve/reject/modify; decision logged with timestamp but evidence display or audit fields are minimal | No human checkpoint, or checkpoint is cosmetic (auto-approves) |
| **Cost awareness** | Per-agent and per-request cost breakdown (model + prompt tokens + completion tokens + estimated cost per call); end-of-run summary | Per-call model + token + cost logging with end-of-run summary total | No cost tracking implemented |

## Implementation Patterns

- Scope agents tightly: define the trigger, tool set, completion condition, and failure mode before coding
- Wrap every tool execution in `try/except` and return structured errors to the model
- Use exponential backoff for API rate limits (2^attempt seconds)
- Implement circuit breakers: disable tools after N consecutive failures
- Set token budgets per conversation and exit early when exceeded
- Tier model usage to reduce costs (typically 40–60%): use `claude-haiku-4-5-20251001` for high-volume, well-defined tasks (triage, routing); use `claude-sonnet-4-6` for complex reasoning (compliance analysis, response drafting). Maintain a central reference of input/output token costs for each model used.
- PydanticAI adds type safety, `ModelRetry`, and built-in usage tracking
- Evaluate agents with defined test cases: track tool selection accuracy and output correctness
- Log all tool calls as structured JSON for audit compliance
- Connect to observability tools (Logfire, OpenTelemetry) for production monitoring

## Open Questions

- Best patterns/tools for testing agents rigorously but cost-effectively?
- How best to implement the HITL check — how to present outputs clearly for user approval?
- If/how to cache outputs for efficient re-use (e.g. handling a near-duplicate FOI)?

## Working Sequence

Follow each step in order. **Do not jump ahead.**

1. Configure the project — ensure `CLAUDE.md` and ways of working are clearly defined
2. Draw up clear specification documents, identifying gaps in requirements or available information
3. Research areas lacking clarity or where there are ranges of viable options
4. Refine specs as necessary based on research outputs
5. Pin down high-level tooling decisions
6. Implement a detailed implementation plan based on final spec and tooling choices
7. Implement code and tests
8. Document the final system
9. Document how the project was executed for presenting to other teams (timelines, infographics, etc.)

### Spec / Plan file conventions

- Implementation-agnostic specification information → `docs/specs/`
- Detailed implementation plans (tooling, libraries, patterns) → `docs/plans/`
