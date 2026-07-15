"""Closes checklist PII1: measures whether personal data plausibly appears
in consultation responses, so the redaction question (PII4) is decided from
a real number rather than a guess. Pure pattern matching - no API calls,
no cost, safe to run on any dataset including the full 20,000-row export.

Deliberately does NOT implement or attempt redaction - that's PII4, a
separate, not-yet-made policy decision.
"""
import argparse
import csv
import json
import re
from pathlib import Path

EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
UK_PHONE_RE = re.compile(r"\b(?:\+44\s?7\d{3}|07\d{3})[\s-]?\d{3}[\s-]?\d{3}\b")
# UK National Insurance number *shape*: two letters, six digits, one letter.
# Deliberately loose (not a strict validator excluding D/F/I/Q/U/V per HMRC
# rules) - this is a screening scan, so a false positive (flagging
# HMRC's own "QQ123456C" documentation example) is far cheaper than a false
# negative (missing a real, oddly-formatted one).
NI_NUMBER_RE = re.compile(r"\b[A-Za-z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-Za-z]\b")

PATTERNS = {
    "email": EMAIL_RE,
    "uk_phone": UK_PHONE_RE,
    "ni_number": NI_NUMBER_RE,
}


def scan_text(text):
    """Return {pattern_name: [matches]} for one string of text."""
    hits = {}
    for name, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            hits[name] = matches
    return hits


def scan_csv_rows(csv_path, text_field="response_text"):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    findings = []
    for row in rows:
        hits = scan_text(row.get(text_field, ""))
        if hits:
            findings.append({"id": row.get("id"), "hits": {k: len(v) for k, v in hits.items()}})
    return len(rows), findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="CSV with a response_text column to scan")
    parser.add_argument("--field", default="response_text")
    args = parser.parse_args()

    total_rows, findings = scan_csv_rows(args.csv_path, args.field)
    pct = (len(findings) / total_rows * 100) if total_rows else 0.0

    report = {
        "csv_path": str(args.csv_path),
        "total_rows": total_rows,
        "rows_with_likely_pii": len(findings),
        "pct_rows_with_likely_pii": round(pct, 1),
        "findings": findings,
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
