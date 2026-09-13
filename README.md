# Buy or Wait?

A financial affordability engine for **HackerRank Orchestrate (September 2026)**.
For every request in `dataset/requests.csv` it decides whether to pay in full,
pay partially, use installments, wait, or not proceed — honouring a 90-day
minimum-balance safety rule and each user's own payment preferences.

**This is a completed solo submission, not the starter template.** All source
lives in [`code/`](code/); the original hackathon brief is preserved unchanged
at [`problem_statement.md`](problem_statement.md).

**Start here → [`code/README.md`](code/README.md)** — full architecture with
embedded diagrams, a step-by-step trace of one request through the whole
pipeline, and current results.

---

## The idea in one example

`request_119` asks to spend ₹203,500. The user holds ₹282,101 and keeps a
floor of ₹151,200 — a subtraction says there's ₹130,901 of room and stops
there. The engine instead projects the next 90 days and finds nine recurring
commitments draining the account to **₹96,975 — ₹54,225 below the floor** —
before salary lands the next day. The purchase was never the problem; paying
today would have deepened a hole that was already coming.

The system isn't a classifier predicting a label — it's a cash-flow simulator
that builds the day-by-day balance trajectory and lets the label fall out of
which payment plans survive it.

## What makes it different

The dataset seeds real advance-fee fraud in two languages (*"Congratulations!
You've been selected for a cash prize. Pay the release charge today..."*).
Message/image content reaches the financial engine through a closed, 5-key
typed schema with **no field capable of expressing an instruction** — the
deterministic engine never sees raw text. 25 tests confirm zero phantom income
across every targeted user. Full details in [`code/README.md`](code/README.md).

## Results

| | |
|---|---|
| `affordability_status` / `recommended_payment_method` | 20/25 · 22/25 (vs. the 25 solved samples) |
| `spending_changes_needed` / `decision_explanation` validity | 25/25 · 25/25 |
| Automated tests | 38 passing |
| Real bugs found & fixed | 12 |
| Real predictions hand-audited against their ledgers | 20/20 correct |
| Dataset images verified by hand | 16/16 correct |
| Metered API calls in the submitted run | 0 |

Full accuracy progression, every parameter sweep, and every hypothesis tested
and rejected: [`code/evaluation/CALIBRATION.md`](code/evaluation/CALIBRATION.md).

## Setup and run

```bash
python3 -m venv .venv
./.venv/bin/pip install pandas anthropic pillow python-dotenv pytest
./.venv/bin/python code/main.py
```

Writes `output.csv` at the repo root. No API key needed — `code/.cache/evidence/`
ships pre-populated for all 219 users with message/image evidence.

```bash
./.venv/bin/python code/evaluation/main.py   # score vs sample_requests.csv, all 6 criteria
./.venv/bin/python -m pytest code/tests -q   # 38 tests
```

---

## Documentation map

- **[`code/README.md`](code/README.md)** — architecture, diagrams, full request walkthrough, results
- **[`code/ARCHITECTURE.md`](code/ARCHITECTURE.md)** — the same design in prose, plus known limitations
- **[`code/evaluation/CALIBRATION.md`](code/evaluation/CALIBRATION.md)** — every sweep and every rejected hypothesis
- **[`code/evaluation/usage_report.md`](code/evaluation/usage_report.md)** — model usage and cost
- **[`chat_transcript.md`](chat_transcript.md)** — development transcript
- **[`problem_statement.md`](problem_statement.md)** — the original, unmodified hackathon brief
