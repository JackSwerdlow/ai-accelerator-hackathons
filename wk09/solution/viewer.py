# Consultation Insights - results viewer
# Run analyse.py first, then this. Crashes if results.json doesn't exist.

import json
from collections import Counter

from flask import Flask, render_template_string

app = Flask(__name__)

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Consultation Insights</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; color: #0b0c0c; }
    h1 { border-bottom: 4px solid #1d70b8; padding-bottom: .3rem; }
    table { border-collapse: collapse; width: 100%; font-size: .9rem; }
    th, td { border: 1px solid #b1b4b6; padding: .5rem; text-align: left; vertical-align: top; }
    th { background: #f3f2f1; }
    .pill { display: inline-block; background: #f3f2f1; border: 1px solid #b1b4b6; padding: 1px 8px; margin: 1px; font-size: .8rem; }
    .supportive { color: #00703c; font-weight: bold; }
    .opposed { color: #d4351c; font-weight: bold; }
    .mixed { color: #f47738; font-weight: bold; }
    .neutral { color: #505a5f; font-weight: bold; }
    .counts { display: flex; gap: 2rem; flex-wrap: wrap; margin: 1.5rem 0; }
    .card { border: 1px solid #b1b4b6; padding: 1rem; min-width: 200px; }
  </style>
</head>
<body>
  <h1>Consultation Insights</h1>
  <p>Digital Identity in Public Services: Call for Views &mdash; {{ results|length }} responses analysed</p>

  <div class="counts">
    <div class="card">
      <h3>Sentiment</h3>
      {% for s, n in sentiments.most_common() %}
        <div><span class="{{ s }}">{{ s }}</span>: {{ n }}</div>
      {% endfor %}
    </div>
    <div class="card">
      <h3>Top themes</h3>
      {% for t, n in themes.most_common(6) %}
        <div>{{ t }}: {{ n }}</div>
      {% endfor %}
    </div>
  </div>

  <table>
    <tr><th>#</th><th>Type</th><th>Summary</th><th>Themes</th><th>Sentiment</th></tr>
    {% for r in results %}
    <tr>
      <td>{{ r.id }}</td>
      <td>{{ r.respondent_type }}</td>
      <td>{{ r.summary }}</td>
      <td>{% for t in r.themes %}<span class="pill">{{ t }}</span>{% endfor %}</td>
      <td class="{{ r.sentiment }}">{{ r.sentiment }}</td>
    </tr>
    {% endfor %}
  </table>
</body>
</html>
"""


@app.route("/")
def index():
    with open("results.json", encoding="utf-8") as f:
        results = json.load(f)

    sentiments = Counter(r["sentiment"] for r in results)
    themes = Counter(t for r in results for t in r["themes"])

    return render_template_string(PAGE, results=results, sentiments=sentiments, themes=themes)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
