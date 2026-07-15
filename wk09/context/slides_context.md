
How it works
Form a team of 2–4 and choose one of three scenarios
Read your brief — a realistic situation with real stakes, and a codebase to match
Run the prototype first — you cannot operationalise what you haven't seen working
Audit, prioritise, build — the brief signposts directions; the priority call is yours
Present at the end of each day — progress, decisions, and evidence
There is no feature list to complete. There is a system to make trustworthy — and a defence to make of where you spent your two days.

Scenario 2 — Consultation Insights
DSIT. A batch tool that summarises and classifies public consultation responses. The demo impressed the policy team; the next consultation expects 20,000+ responses feeding a published government summary.

What you inherit:

One API call per response, full instructions re-sent each time, priciest model
A crash at row 19,000 loses everything — no resume, no checkpoints, no retries
json.loads on raw model output, and a shared departmental budget paying for it all
Strong themes: resilience, Batch API, cost projection, quality evals, productisation

What success looks like
Production-grade is evidence, not features. By Wednesday afternoon you should be able to show:

Visibility — you can see what the system is doing and what it costs. Numbers, not vibes.
Correctness — tests or evals that prove the important behaviour, and would catch a regression
Resilience — it fails gracefully, recovers, and you can demonstrate the failure
Security — the obvious attack is closed and secrets are handled like secrets
Operability — someone who isn't you could run it, from your README, tomorrow
A small change you can prove beats a big change you hope works. Judged accordingly.

What success is not
Feature-adding — the policy team does not need dark mode
The great rewrite — two days rebuilding it in FastAPI is two days not operationalising it
Infrastructure cosplay — a Kubernetes manifest for a service with no tests is decoration
Silent perfection — work you can't demonstrate or explain didn't happen, as far as the audience knows
The trap in every scenario is the same: doing what's interesting instead of what the brief's stakes demand. Re-read your brief's stakes at lunchtime.



Stretch directions
Self-led, for teams who find their footing early — or want a research angle for the Day 1 presentation:

A standalone cost-monitoring service — own database, own API, a dashboard; something every team in the department could point their apps at
An LLM-eval CI gate — the build fails if answer quality drops below threshold
Batch API economics — what changes when the overnight discount is 50%?
Load testing — simulate the 7am shift change; find the actual breaking point
The W7 pipeline, for real — SHA-pinned actions, scan, build, approval gate on your repo
A disaster recovery drill — kill the database, restore from backup, time it, document it

The presentations
End of Day 1 — 5 minutes. Your priority call: what you found, what you chose, why, and early progress. Or: teach the room a concept you researched to unblock yourselves — caching pricing mechanics, Batch API semantics, ICO day-counting rules.

End of Day 2 — 10 minutes. What you shipped:

The before and after — show the prototype's sin, then show it fixed
The evidence — tests running, evals scoring, the cost number moving
The honest ledger — what you didn't get to, and what Day 3 would hold
Naming what you didn't do — knowingly, with reasons — is a production-grade behaviour. It scores, not costs.

Ground rules
AI-assisted coding is allowed and encouraged — with the W7 verification workflow: you review, you test, you own every line you commit
Your API spend is production spend — develop on a cheaper model, know what your day cost; that number belongs in your presentation
No Docker or Git on your machine is not a blocker — everything runs with plain python; containers and version control are directions, not prerequisites
Keep it running — demo from working software, not screenshots of software that worked earlier

Recap
You inherit a working prototype and two days to make it production-grade — the priority call is yours to make and defend
Three scenarios, one goal: a system someone else could trust, run, and afford
Success is evidence: visibility, correctness, resilience, security, operability
Presentations both days — decisions and proof, not feature tours
The honest ledger is part of the deliverable: what you did, what you didn't, what's next