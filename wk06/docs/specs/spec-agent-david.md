# Week 6 Hackathon — FOI Request Automation

## Problem

Government departments get a lot of FOI requests. Each one needs an officer to read it, check policy, decide what can be released, draft a response, and get it reviewed — all within 20 working days. Most requests are routine but still take significant time to process manually.

## What it does

An agent pipeline handles the grunt work before a human reviews it:

1. **Triage** — classifies the request by topic and complexity
2. **Compliance check** — searches policy documents for relevant exemptions and makes a disclosure recommendation
3. **Draft response** — writes a response letter with the correct exemption citations

An officer then reviews the draft and approves, rejects, or edits it. Nothing goes out without a human decision.

## Users

- **FOI officers** — review a pre-populated draft instead of starting from scratch
- **Team leads** — track volume and cost across requests

## Success looks like

- Routine requests processed in under 5 minutes vs the current 30–45
- Correct exemptions identified without officer input
- Every draft cites the right section numbers
- Human approval is mandatory, not optional
- API costs are logged per request

## Scope

In: processing text requests from a local folder, RAG over internal policy docs, human-in-the-loop approval

Out: sending emails, case management integration, classified material, multi-department use
