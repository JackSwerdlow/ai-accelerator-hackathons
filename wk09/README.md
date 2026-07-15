# Consultation Insights

Analyses public consultation responses with AI: one-line summary, themes,
and sentiment per response, plus a results viewer.

Built in a rush before the 'Digital Identity in Public Services' consultation
closed. The policy team loved the demo. There is now talk of running every
DSIT consultation through it — the last one got 1,100 responses and the big
identity one is expected to get 20,000+.

**Status:** demo quality. `responses_sample.csv` is a 40-row sample of the
full export (the full file lives on the shared drive).

## Running it

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here     # Windows: set ANTHROPIC_API_KEY=your-key-here
python analyse.py        # analyses every row, writes results.json
python viewer.py         # then open http://localhost:5001
```

## Notes

- Each response is analysed with its own API call. 40 rows takes a couple
  of minutes. Not sure what happens with 20,000 rows. Probably fine.
- If a call fails halfway through, run it again from the start.
- If the model returns something that isn't JSON, the script crashes.
  It's only happened twice.
- Re-running re-analyses everything, including rows it has already done.
- The policy team asked if two people running it at once would cause
  problems. Haven't checked.
