# Consultation Insights - batch analyser
# Analyses consultation responses one at a time and saves the results.
# Takes a while to run but you can watch the progress bar. Grab a coffee.

import csv
import json
import os
from pathlib import Path

from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-sonnet-5",
    max_tokens=500,
    api_key=os.environ.get("ANTHROPIC_API_KEY", "PASTE-YOUR-KEY-HERE"),
)

# Full instructions sent with every single response - keeps each call
# self-contained so there's no state to worry about.
INSTRUCTIONS = """You are analysing responses to the UK government consultation
'Digital Identity in Public Services: Call for Views' run by the Department for
Science, Innovation and Technology.

The consultation asked the public and organisations for views on introducing
a certified, reusable digital identity for accessing public services, including
questions on privacy, inclusion, security, business impact, and governance.

For the consultation response below, produce a JSON object with exactly these
fields:
- "summary": a one-sentence neutral summary of the response
- "themes": a list of 1-3 themes from this fixed list ONLY:
  ["privacy", "digital exclusion", "security", "business efficiency",
   "accessibility", "governance", "fraud reduction", "cost", "trust",
   "implementation"]
- "sentiment": one of "supportive", "opposed", "mixed", "neutral"

Respond with ONLY the JSON object, no other text.

RESPONSE TO ANALYSE:
"""

# Paths are relative to this script so it works from any working directory.
_HERE = Path(__file__).parent
_RESULTS = _HERE / "results.json"


def analyse_response(text):
    response = llm.invoke(INSTRUCTIONS + text)
    try:
        return json.loads(response.content)  # the model always returns valid JSON (right?)
    except json.JSONDecodeError:
        # Return a neutral fallback so one bad response doesn't crash the run.
        return {"summary": "Could not parse model response", "themes": [], "sentiment": "neutral"}


def main():
    with open("data/responses_sample.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Load any previously saved results so we can resume after a crash
    # without losing the work already done.
    if _RESULTS.exists():
        with open(_RESULTS, encoding="utf-8") as f:
            results = json.load(f)
        print(f"Resuming — {len(results)} results already saved, skipping those rows")
    else:
        results = []

    processed_ids = {r["id"] for r in results}

    print(f"Analysing {len(rows)} responses...")

    for i, row in enumerate(rows, start=1):
        if row["id"] in processed_ids:
            print(f"  [{i}/{len(rows)}] skipped (already done)")
            continue

        analysis = analyse_response(row["response_text"])
        results.append({
            "id": row["id"],
            "respondent_type": row["respondent_type"],
            "response_text": row["response_text"],
            **analysis,
        })
        print(f"  [{i}/{len(rows)}] done")

        # Write after every result so a crash loses nothing.
        with open(_RESULTS, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    print(f"Saved {_RESULTS}")


if __name__ == "__main__":
    main()
