# Buy or Wait? — solution

A financial affordability engine for HackerRank Orchestrate (September 2026).
For every request in `dataset/requests.csv` it decides whether to pay in full,
pay partially, use installments, wait, or not proceed — honouring the 90-day
minimum-balance safety rule and each user's own payment preferences.

**Documentation map**
- **[Visual architecture walkthrough](https://claude.ai/code/artifact/7fd6600e-b0e1-44eb-b21a-fe2832e635de)** — the illustrated version, built around a real projected-balance trajectory from the evaluation set. The quickest way to understand the design.
- **[`ARCHITECTURE.md`](ARCHITECTURE.md)** — how it works and why, with diagrams. Start here for the written version.
- **[`evaluation/CALIBRATION.md`](evaluation/CALIBRATION.md)** — every parameter sweep, the accuracy progression, and the full validation record.
- **[`evaluation/usage_report.md`](evaluation/usage_report.md)** — model usage and cost for the submitted run.

---

## The idea in one example

`request_119` asks to spend ₹203,500. The user holds ₹282,101 and keeps a floor
of ₹151,200 — so a subtraction says there is ₹130,901 of room, and stops there.

The engine instead projects the next ninety days and finds nine recurring
commitments draining the account to **₹96,975 by 13 June — ₹54,225 below the
floor** — before salary lands the next day. The purchase was never the problem;
spending today would only have deepened a hole that was already coming.

That is the whole thesis. The system is not a classifier that predicts a label,
it is a cash-flow simulator: build the day-by-day balance trajectory, find which
payment plans keep every point above the floor, and let the label fall out of
which plans survive.

---

## Setup and run

```bash
python3 -m venv .venv
./.venv/bin/pip install pandas anthropic pillow python-dotenv pytest
./.venv/bin/python code/main.py
```

Writes `output.csv` at the repo root — one row per `request_id`, 8 columns, in
the order the spec requires.

No API key is needed. `evidence.py` reads its per-user cache from
`code/.cache/evidence/`, which ships populated for all 219 users with
message/image evidence; with the cache present it never calls any API. Set
`ANTHROPIC_API_KEY` in `.env` and clear that directory to regenerate it live.

```bash
./.venv/bin/python code/evaluation/main.py                   # score vs sample_requests.csv
./.venv/bin/python -m pytest code/tests -q                   # 33 tests
./.venv/bin/python code/tests/run_synthetic_scenarios.py     # 15 hand-built scenarios
./.venv/bin/python code/tests/audit_real_requests.py         # ledger dump for hand-auditing
./.venv/bin/python code/evaluation/generate_usage_report.py  # regenerate usage report
```

---

## Layout

```
code/
├── loader.py       # CSV loading, typed dates, exact-settlement-date FX lookup
├── events.py       # recurrence detection → forward cash-flow ledger
├── forecast.py     # 90-day balance path, safe-amount, earliest-safe-date, schedule safety
├── decision.py     # candidate plan generation + the spec's 6-rule ranking
├── explain.py      # deterministic templated decision_explanation (zero LLM cost)
├── evidence.py     # Stage 1: message/image → closed typed JSON patch (cached per user)
├── main.py         # orchestration; writes output.csv
├── tests/          # regression, adversarial, synthetic-scenario and audit suites
└── evaluation/     # sample scorer, calibration record, usage report
```

---

## What makes this solution different

**The untrusted-evidence boundary is architectural, not a prompt instruction.**
The dataset contains real attacks. `message_67` (English) and `message_142`
(Indonesian) are textbook advance-fee fraud:

> *"Congratulations! You've been selected for a cash prize. Pay the release
> charge today to receive the funds immediately. Pay the processing charge now
> to avoid losing the claim."*

A pipeline that feeds message text to a model and trusts the answer has two ways
to fail here: book the never-arriving prize as income and green-light an
unaffordable purchase, or read *"pay the release charge"* as an instruction and
act on it.

This engine removes the possibility structurally rather than defending against
it with prompt wording. Message content reaches the financial model through
exactly one channel — a closed five-key typed schema with **no field capable of
expressing an instruction** — and the deterministic engine never sees raw text
at all. An embedded instruction has nowhere to land; the widest reachable
influence is moving a number on an event that already exists in the ledger.

25 tests in `tests/test_adversarial_evidence.py` pin it: zero phantom income
across all 13 users targeted by prize narratives, both outright frauds reduced
to completely empty patches, approved-but-unsettled invoices never counted as
cash, and no evidence patch anywhere permitted to introduce an outbound debit.
See [`ARCHITECTURE.md` §3](ARCHITECTURE.md).

**Conservative is defined precisely, not vaguely.** "Forecast conservatively"
is easy to over-apply. Taking the max of recent expenses is conservative; taking
the max including a one-off bulk purchase is just wrong — it projected a ₹41,272
grocery stock-up as `user_17`'s *weekly* spend and rejected a request they could
comfortably afford. The estimator now separates worst-*typical*-cycle from
worst-cycle-ever, and the fix is stable across a 1.5–4.0 threshold range rather
than tuned to one value.

**Validated four independent ways, because sample accuracy can be gamed.**
25 official samples, 33 automated tests, 15 scenarios hand-built on real users'
histories, and 20 real predictions hand-audited against their ledgers (20/20
correct). The scenarios and the audit are what actually found bugs — the sample
score was blind to all three defects fixed late in development.

**Every number was swept, and the flat optima are the point.** Recency window,
spike threshold and forecast horizon were each calibrated and recorded in
[`CALIBRATION.md`](evaluation/CALIBRATION.md). A parameter that only works at
one exact value is fitted to the samples; a parameter that is flat across a wide
range is fitted to the problem.

---

## Key modelling decisions

- **Income is projected forward, not just expenses.** `current_available_balance` is a snapshot at `request_date`; it does not contain future cash. Projecting expenses without the matching recurring salary produces an ever-draining balance for everyone — the first working version returned 212/250 `not_affordable` for exactly this reason. Salary needs only 2 confirmed points (last settled paycheck + the explicit "next confirmed salary" row) since 3 rarely exist.
- **Recurring amounts are conservative and directional:** `max` of recent occurrences for expenses, `min` for income — never the mean, which is not conservative.
- **One-off spikes are excluded** from that estimate (above 2.5× the category's historical median), so a bulk purchase does not become the permanent baseline.
- **The salary anchor skips same-cycle arrears/bonus rows**, which would otherwise be mistaken for the new ongoing salary. This affected four real evaluation users.
- **`amount_safe_to_pay` and `earliest_date_for_full_payment` are always computed on the baseline forecast**, independent of the recommended method or any spending change — the spec states these measure financial capacity independently of payment preferences.
- **`spending_changes_needed` targets the historical `event_id` representing the recurring pattern**, since no future scheduled/pending row in the dataset is ever flagged reducible or stoppable (verified: 0 of 141). The recurrence itself is what gets stopped or reduced.
- **Spending changes are a last resort**, tried only when no unmodified plan is safe, smallest number first, comparing every combination at each size. Any plan built on one reports `affordable_with_plan`.

---

## Evidence stage

`evidence.py` turns each user's messages and images into a small typed patch —
`amount_overrides` (blank amounts resolved from receipt/payslip images),
`exclude_event_ids` (cancelled, reversed or internal-transfer rows),
`extra_items` (a one-off cash fact with no matching event), `recurring_overrides`
(a new go-forward amount for a recurring category, e.g. a raise or a household
income change), and a display-only `note`. Results cache to
`code/.cache/evidence/<user_id>.json`; a cache hit skips the API entirely.

For this submission the cache was populated **without any metered API call** —
Claude Code, the assistant used throughout development, read the same
messages and images the prompt would have sent and applied the same rules.
`evaluation/usage_report.md` discloses this in full. The live API path is
unchanged and still works with a key and an empty cache.

Image extraction was verified exhaustively: **all 16 images checked by hand
against the extracted amount, 16/16 correct** — including a handwritten pharmacy
receipt where the total is barely legible and was cross-validated against the
itemised line sum, and one delivery screenshot genuinely cropped before the
final total, which was flagged rather than guessed.

---

## Accuracy and validation

**20/25 `affordability_status`, 22/25 `recommended_payment_method`** on the
solved samples, up from 17/19 when the engine first ran end-to-end.

`evaluation/main.py` scores **all six** criteria `problem_statement.md` lists,
not just the three that are easy string comparisons:

| # | Scored criterion | Result |
|---|---|---:|
| 1 | `amount_safe_to_pay` accuracy | 4 exact · 11 within 5% / 25 |
| 2 | `affordability_status` | **20 / 25** |
| 3 | `recommended_payment_method` · `payment_plan` | **22 / 25** · 20 / 25 (totals correct 25/25) |
| 4 | `earliest_date_for_full_payment` | **13 / 25** |
| 5 | `spending_changes_needed` validity | **25 / 25** |
| 6 | `decision_explanation` usefulness | **25 / 25** |

| Layer | Covers | Result |
|---|---|---|
| Regression suite | Every fixed defect + invariants across all 250 | 12 / 12 |
| Adversarial suite | Fraud, receivables, schema containment | 25 / 25 |
| Hand-built scenarios | 15 requests on real users' histories | found 2 real bugs |
| Hand audit | 20 real predictions traced to their ledgers | **20 / 20 correct** |
| Image extraction | All 16 dataset images verified by hand | **16 / 16 correct** |

The scenarios and the hand audit are what actually found bugs — the sample score
was blind to three of the defects fixed late in development. Two audited cases
looked wrong at first and both turned out to be the engine being right:
`request_119` (the trajectory above), and a user whose balance climbs to $27,000
yet still returns `not_affordable` because they accept partial payment only and
the request forbids it.

Full accuracy progression across all eight fixes, and every parameter sweep, in
[`CALIBRATION.md`](evaluation/CALIBRATION.md).

### Known limitations

Stated openly rather than buried:

- **`request_05`** — expected `not_affordable`, computed `affordable_now`, with a ~20× gap in `amount_safe_to_pay` that nothing in the dataset explains (no message, no image, no unusual pattern, no FX).
- **`request_06` / `11` / `19` / `21`** — the reference answers forecast 2–5% more pessimistically than this engine, enough to flip them from "already safe" to "needs a spending change" (or to a partial payment). Swept the recency window, horizon and spike factor; none explain the gap, and it is too small and irregular to reverse-engineer into a rule without overfitting. Left alone deliberately — forcing an unnecessary spending change would violate the spec's own "avoid spending changes" preference on the hidden set.
- **`request_08`** — expects `affordable_later`; the engine finds no safe date within the window.
