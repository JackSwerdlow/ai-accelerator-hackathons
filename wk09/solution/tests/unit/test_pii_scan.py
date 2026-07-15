"""Regression coverage for evals/pii_scan.py, written test-after (the
script itself was validated manually against tests/fixtures/responses_pii.csv
and the real 40-row sample before this test was added) - locks in the
behaviour going forward rather than proving it for the first time.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from evals.pii_scan import scan_text  # noqa: E402


def test_detects_email_and_uk_mobile_number():
    hits = scan_text("Reach me at jane.smith.test@example.com or 07700 900123.")
    assert "email" in hits
    assert "uk_phone" in hits


def test_detects_ni_shaped_string_even_hmrcs_own_example():
    hits = scan_text("My National Insurance number is QQ123456C.")
    assert "ni_number" in hits


def test_ordinary_text_has_no_hits():
    hits = scan_text("I support this proposal as it will make things easier.")
    assert hits == {}
