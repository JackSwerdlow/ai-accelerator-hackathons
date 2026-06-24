# Intelligent Automation System -- Project Lab

## Objectives

Build a multi-agent system that automates FOI request processing: classify requests, check exemptions against policy documents using RAG, draft responses, and enforce human approval before finalising.

> **Environment check.** After completing step 1 below, run `make smoke` in your working directory before the hackathon begins. If it fails, see the Environment Contract at `learner/units/w00-programme/appendices/environment-contract.md` (§5 Offline / vendored-wheel escape, §7 Support). For HuggingFace-blocked networks, set `EMBEDDING_PROVIDER=openai` in `.env` and re-run. Contact your instructor if the issue persists.

## Prerequisites

### Skills (from preceding content weeks)

- Building AI agents with tool use and function calling (W05 D1 AM)
- Implementing error handling and fallback strategies in agents (W05 D1 PM)
- Managing and monitoring costs for agent systems (W05 D1 PM)
- Building a knowledge base with embeddings and ChromaDB (W05 D2 AM)
- Orchestrating multiple agents with defined roles (W05 D2 PM)
- Implementing agent communication via shared state (W05 D2 PM)

### Tools and Access

- Python 3.12+
- `openai` Python package
- `chromadb` Python package
- `python-dotenv` Python package
- An OpenAI API key with access to `gpt-4o-mini` and `gpt-4o`
- A terminal and text editor

## Starter Scaffold

The `starter/` directory contains:

| File/Directory | Purpose |
|---|---|
| `main.py` | CLI entry point. Parses arguments, runs the processing loop. Works out of the box but calls placeholder agent functions. |
| `agents.py` | Agent function stubs with docstrings. You implement: `triage_agent()`, `compliance_agent()`, `response_agent()`, `supervisor()`. |
| `indexer.py` | Document indexing. `chunk_text()` is provided. You implement: `index_policies()`, `search_policies()`. |
| `cost_tracker.py` | Cost tracking class. `log_call()` and `summary()` are partially implemented. You complete the cost calculation. |
| `documents/foi_requests/` | Three sample FOI request files to process. |
| `documents/policies/` | Two policy documents on FOI exemptions that the compliance agent retrieves from. |
| `requirements.txt` | Python dependencies. |
| `.env.example` | Copy to `.env` and add your `OPENAI_API_KEY`. |
| `README.md` | Setup instructions for the starter. |

## Acceptance Criteria

- [ ] System processes all three sample FOI requests without crashing
- [ ] Triage agent classifies each request by topic and complexity (high/medium/low)
- [ ] Compliance agent retrieves relevant policy excerpts from ChromaDB and cites them in its exemption analysis
- [ ] Response agent drafts a reply that references the triage classification and compliance findings
- [ ] Human-in-the-loop checkpoint pauses execution, displays the draft response with evidence, and accepts operator input (approve/reject/modify)
- [ ] If an API call fails, the system logs the error and continues with a fallback response rather than raising an unhandled exception
- [ ] Each LLM call is logged with model name, prompt tokens, completion tokens, and estimated cost
- [ ] A cost summary prints at the end of the run showing total tokens and cost by agent
- [ ] Each processed request produces a JSON result file with classification, exemptions, draft response, human decision, and cost
- [ ] An `AI_LOG.md` file documents 3+ AI-assisted development instances (open the seeded `AI_LOG.md` in your working directory and complete four fields per entry)

## Day 1 Target

By end of Day 1, these should be working:

- [ ] Policy documents indexed into ChromaDB (run `python main.py index` without errors)
- [ ] Triage agent classifies a request and returns structured output
- [ ] Compliance agent retrieves policy chunks and produces an exemption analysis
- [ ] Agents are wired together: running `python main.py process documents/foi_requests/` calls triage, then compliance, then response for each request
- [ ] Basic error handling: a network timeout or malformed LLM response does not crash the system

## ChromaDB Quick Start

ChromaDB is the vector database you use for RAG retrieval. The starter scaffold includes `chromadb` in `requirements.txt`. Follow these steps to get it running before you start implementing agents.

### 1. Install dependencies in a virtual environment

The courseware mount is read-only, so copy the starter scaffold into your own working directory first (working directory per Environment Contract §2d):

```bash
mkdir -p ~/Documents/my-work/w06-hackathon && cd ~/Documents/my-work/w06-hackathon
cp -r ~/Documents/readonly-courseware/swe-v1-ukds-c1/courseware/labs/w06-hackathon-intelligent-automation/hackathon/starter/. .
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

All subsequent commands run from `~/Documents/my-work/w06-hackathon`.

### 2. Verify ChromaDB loads

```bash
python -c "import chromadb; client = chromadb.Client(); print('ChromaDB OK')"
```

You should see `ChromaDB OK`. If you see an import error, check the troubleshooting section below.

### 3. Index the policy documents

Once you implement `index_policies()` in `indexer.py`:

```bash
python main.py index
```

This reads the `.txt` files in `documents/policies/`, splits them into chunks, and stores the chunks in a ChromaDB in-memory collection. The command should print the number of chunks indexed (expect 15--30 depending on your chunk size).

### 4. Test retrieval

Once you implement `search_policies()` in `indexer.py`:

```python
from indexer import search_policies
results = search_policies("section 40 personal information")
for r in results:
    print(r["source"], ":", r["text"][:80])
```

Each result should contain a policy excerpt relevant to the query.

### Offline / proxy install

If pip cannot reach PyPI, use the vendored wheels (from `~/Documents/my-work/w06-hackathon`):

```bash
make install-offline
```

This installs all dependencies from `vendor/wheels/` without network access. If the vendor directory is missing, ask the facilitator for the archive.

### HuggingFace-blocked troubleshooting

If `sentence-transformers` cannot download the embedding model (403, timeout, or `HfHubHTTPError`), the HuggingFace Hub is blocked on your network. Set the fallback:

1. Edit `.env` in `~/Documents/my-work/w06-hackathon` and set `EMBEDDING_PROVIDER=openai`
2. Ensure `OPENAI_API_KEY` is set to a valid key
3. Re-run `make smoke` in `~/Documents/my-work/w06-hackathon`

With `EMBEDDING_PROVIDER=openai`, ChromaDB uses the OpenAI embeddings API instead of the local model. This requires network access to `api.openai.com`.

Do not set `HF_HUB_DISABLE_SSL_VERIFY=1` or bypass TLS verification. If both HuggingFace and OpenAI are blocked, contact your instructor.

### ChromaDB Troubleshooting

**`pip install chromadb` fails with a build error on `hnswlib`**

ChromaDB depends on `hnswlib`, which needs a C++ compiler. On Ubuntu/Debian: `sudo apt-get install build-essential`. On macOS: `xcode-select --install`. On Windows: install Visual Studio Build Tools with the "C++ build tools" workload. After installing the compiler, run `pip install chromadb` again.

**`ImportError: cannot import name 'Client'` or similar**

Verify you are running inside the virtual environment (`which python` should point to `.venv/bin/python`). If you installed `chromadb` globally, it may conflict with the venv. Delete the venv, recreate it, and reinstall: `rm -rf .venv && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

**`chromadb.Client()` works but `index_policies()` reports 0 chunks**

Check that your policy files are in `documents/policies/` and have `.txt` extensions. Print the output of `chunk_text()` to verify chunking produces non-empty results. A common mistake: passing the wrong directory path to `Path()`.

**`search_policies()` returns empty results after indexing**

ChromaDB uses an in-memory client by default. If you run `python main.py index` and then `python main.py process` as separate commands, the index is lost between runs. Fix: call `index_policies()` at the start of the processing pipeline in `main.py` (or in the `supervisor()` function) so the collection exists in the same process.

**Slow indexing or queries (>30 seconds)**

The default embedding function uses a small local model. On machines without a GPU, indexing 30+ chunks may take 10--20 seconds. This is normal for the hackathon. If it exceeds 60 seconds, reduce `chunk_size` in `chunk_text()` to produce fewer chunks, or reduce the policy document length.

## Teardown

1. Deactivate your virtual environment: `deactivate`
2. Remove the `.env` file containing your API key: `rm .env`
3. Delete any generated result files if you do not want to keep them

## Hints

<details>
<summary>Architecture suggestion</summary>

Structure your pipeline as a sequential flow managed by a `supervisor()` function:

```
supervisor(request) ->
  1. triage_agent(request_text) -> classification
  2. compliance_agent(request_text, classification) -> exemption_analysis
  3. response_agent(request_text, classification, exemption_analysis) -> draft_response
  4. human_checkpoint(draft_response, evidence) -> decision
  5. write_result(all_data) -> JSON file
```

Each agent function takes typed inputs and returns a dataclass or dictionary. The supervisor handles the sequencing, error wrapping, and cost accumulation.

</details>

<details>
<summary>If your compliance agent returns generic answers</summary>

The most common cause: the policy documents are not indexed, or the retrieval query does not match how the policies are worded. Check:

1. Run `python main.py index` and verify it reports a non-zero chunk count.
2. In `compliance_agent()`, pass the request text (not a summary) as the ChromaDB query.
3. Include the retrieved chunks in the LLM prompt as context, before asking for the exemption analysis.
4. Print the retrieved chunks to verify they contain relevant policy text.

</details>

<details>
<summary>If cost tracking shows zero tokens</summary>

The OpenAI response object includes usage data at `response.usage.prompt_tokens` and `response.usage.completion_tokens`. Make sure you pass the response object to `cost_tracker.log_call()` after every `client.chat.completions.create()` call, not before.

</details>
