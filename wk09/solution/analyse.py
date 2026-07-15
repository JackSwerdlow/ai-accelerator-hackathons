# Consultation Insights - batch analyser
# Analyses consultation responses one at a time and saves the results.

import csv
import json
import os

import anthropic

import telemetry

MODEL = "claude-sonnet-5"

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


def make_client():
    return anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", "PASTE-YOUR-KEY-HERE")
    )


def analyse_response(client, row_id, text):
    """Analyse one consultation response. Returns (outcome, analysis, spend_gbp):
      - outcome: "success" | "parse_error" | "api_error"
      - analysis: the parsed dict on success, else None
      - spend_gbp: cost of this call in GBP, 0.0 if the API call itself failed
    Never raises: API and JSON-parse failures are caught, recorded via
    telemetry (metric + log), and returned as a failed outcome so the caller
    can skip this row and continue with the rest of the batch.
    """
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": INSTRUCTIONS + text}],
        )
    except anthropic.AnthropicError as error:
        telemetry.record_row_outcome("api_error")
        telemetry.log_api_error(row_id, error)
        return "api_error", None, 0.0

    raw_text = message.content[0].text
    telemetry.record_response_size(len(raw_text.encode("utf-8")))
    spend_gbp = telemetry.record_spend(
        MODEL, message.usage.input_tokens, message.usage.output_tokens
    )

    try:
        analysis = json.loads(raw_text)
    except json.JSONDecodeError as error:
        telemetry.record_row_outcome("parse_error")
        telemetry.log_parse_error(row_id, raw_text, error)
        return "parse_error", None, spend_gbp

    telemetry.record_row_outcome("success")
    return "success", analysis, spend_gbp


def main():
    telemetry.init_telemetry()

    with open("../data/responses_sample.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Analysing {len(rows)} responses...")
    client = make_client()
    start_time = telemetry.log_batch_started(MODEL, len(rows))

    results = []
    outcomes = {"success": 0, "parse_error": 0, "api_error": 0}
    total_spend_gbp = 0.0

    for i, row in enumerate(rows, start=1):
        outcome, analysis, spend_gbp = analyse_response(
            client, row["id"], row["response_text"]
        )
        outcomes[outcome] += 1
        total_spend_gbp += spend_gbp
        if analysis is not None:
            results.append(
                {
                    "id": row["id"],
                    "respondent_type": row["respondent_type"],
                    "response_text": row["response_text"],
                    **analysis,
                }
            )
        print(f"  [{i}/{len(rows)}] {outcome}")

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    telemetry.log_batch_finished(start_time, outcomes, total_spend_gbp)
    print(
        f"Saved results.json ({outcomes['success']} succeeded, "
        f"{outcomes['parse_error']} parse errors, {outcomes['api_error']} API "
        f"errors, £{total_spend_gbp:.4f} spent)"
    )


if __name__ == "__main__":
    main()
