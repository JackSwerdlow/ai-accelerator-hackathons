# Consultation Insights - batch analyser
# Analyses consultation responses one at a time and saves the results.
# Takes a while to run but you can watch the progress bar. Grab a coffee.

import csv
import json
import os

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


def analyse_response(text):
    response = llm.invoke(INSTRUCTIONS + text)
    return json.loads(response.content)  # the model always returns valid JSON (right?)


def main():
    with open("data/responses_sample.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Analysing {len(rows)} responses...")
    results = []

    for i, row in enumerate(rows, start=1):
        analysis = analyse_response(row["response_text"])
        results.append({
            "id": row["id"],
            "respondent_type": row["respondent_type"],
            "response_text": row["response_text"],
            **analysis,
        })
        print(f"  [{i}/{len(rows)}] done")

    # Write everything out at the end in one go.
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Saved results.json")


if __name__ == "__main__":
    main()
