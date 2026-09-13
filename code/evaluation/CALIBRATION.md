# Calibration and validation record

## Scoring against the actual criteria

`problem_statement.md` lists **six** things the hidden ground truth is scored
on. For most of this project's development the evaluation harness measured only
three of them — `affordability_status`, `recommended_payment_method`, and the
`payment_plan` string — which meant three scored criteria were never checked at
all, and `amount_safe_to_pay` (a *numeric* accuracy measure) was never
quantified. `evaluation/main.py` now scores all six:

| # | Criterion | Measured as | Current |
|---|---|---|---:|
| 1 | accuracy of `amount_safe_to_pay` | exact / ≤1% / ≤5% + mean relative error | 4 · 5 · 11 / 25 |
| 2 | correctness of `affordability_status` | exact label | **20 / 25** |
| 3 | correctness of `recommended_payment_method` + `payment_plan` | exact label; exact plan string; plan totals | **22 / 25**, 20 / 25, 25 / 25 |
| 4 | accuracy of `earliest_date_for_full_payment` | exact date, days-off when wrong | **13 / 25** |
| 5 | validity of `spending_changes_needed` | syntax, ≤3 actions, real event ids, permitted + unprotected categories, respects `minimum_allowed_amount` | **25 / 25** |
| 6 | usefulness/consistency of `decision_explanation` | non-empty, names currency + a figure, no artifacts, never contradicts its own recommendation | **25 / 25** |

Turning the last three on immediately exposed three real defects that the
three-criterion harness had been blind to — all fixed below.


Every tunable in this engine was chosen by sweeping it against
`dataset/sample_requests.csv` and recording the result, not by picking a
plausible-looking number. This file is that record.

Reproduce any row with:

```bash
BOW_RECENCY_WINDOW=<n> ./.venv/bin/python code/evaluation/main.py
BOW_SPIKE_FACTOR=<f>   ./.venv/bin/python code/evaluation/main.py
```

---

## Accuracy progression

Each step is a defect found and fixed, with the sample score before and after.
Scores are `affordability_status` / `recommended_payment_method` out of 25.

| # | Change | Before | After |
|---|---|---|---|
| 0 | First working engine (mean-based recurrence, no salary special case) | 212/250 rows `not_affordable` | — |
| 1 | Salary treated as recurring from 2 confirmed points | — | 17 / 19 |
| 2 | Conservative estimate: `max` for debits, `min` for credits (was mean) | 17 / 19 | 18 / 20 |
| 3 | Spending-change search compares all combos per size; status always `affordable_with_plan` | 18 / 20 | 18 / 20 |
| 4 | Evidence cache populated for all 219 users | 18 / 20 | 18 / 20 |
| 5 | `recurring_overrides` — salary changes actually reach the forecast | 18 / 20 | **19 / 21** |
| 6 | Salary anchor skips same-cycle arrears/bonus rows | 19 / 21 | 19 / 21 |
| 7 | Partial-payment remainder gets its own earliest-safe date | 19 / 21 | 19 / 21 |
| 8 | One-off spike excluded from conservative recurring estimate | 19 / 21 | **20 / 22** |
| 9 | Monthly recurrence steps by calendar month, not 30 days | 20 / 22 | 20 / 22 |
| 10 | Pending credits never counted; pending debits reserved | 20 / 22 | 20 / 22 |
| 11 | Refusal explanations state the real, correct reason | 20 / 22 | 20 / 22 |

Steps 9–11 came from switching the harness on for criteria 1, 4 and 6. They
leave the two label metrics untouched but move the three that had never been
measured:

| Criterion | Before | After |
|---|---:|---:|
| `earliest_date_for_full_payment` | 9 / 25 | **13 / 25** |
| `payment_plan` exact string | 17 / 25 | **20 / 25** |
| `decision_explanation` clean | 22 / 25 | **25 / 25** |

**Step 9 — calendar-month recurrence.** Monthly series were projected by
stepping `round(median_gap)` days forward. A salary anchored on the 15th with a
30-day median gap lands on the 14th, then the 13th, then the 12th — drifting
further every cycle. Since `earliest_date_for_full_payment` is usually *exactly*
a payday, that misplaced almost every date by two to five days, and by sliding
paydays around it could also pull an extra income cycle inside the 90-day
window and inflate `amount_safe_to_pay`. Monthly, two-monthly and quarterly
cadences now advance by calendar month (clamping 31 Jan → 28/29 Feb); weekly and
fortnightly cadences genuinely are fixed-interval and keep day arithmetic.

**Step 10 — pending credits.** The spec is explicit: *"Reserve pending debits.
Do not count pending credits, bonuses, commissions, refunds, lottery proceeds,
or investment gains until they settle."* The engine was counting **any**
pending or scheduled row, so an unsettled inbound row such as `user_20`'s
₹8,640 pending shopping refund was being treated as income. Pending credits are
now dropped entirely, while *scheduled* credits — the confirmed upcoming salary
— still count, exactly as the spec distinguishes them. Symmetrically, a pending
**debit** dated at or before the request date used to be skipped for being "in
the past"; but it has not settled, so the balance does not reflect it and the
money is still going to leave. Those are now reserved at the front of the
window.

**Step 11 — refusal explanations.** Every `not_affordable` row emitted one
fixed sentence with no currency, no figure and no reason. Worse, once a figure
was added it revealed an inconsistency: some refusals have *sufficient* cash and
are blocked purely by the user's own accepted payment methods, so blaming
committed expenses would have been factually wrong. Refusals now distinguish the
two cases and state the real one.

Steps 3, 6 and 7 did not move the sample score but each fixed a real defect
found by other means — they are correctness fixes that the 25 samples happen not
to exercise. That is exactly why sample accuracy is not the only gate.

Current: **20/25 status, 22/25 method, 20/25 exact payment-plan string.**

---

## Parameter sweeps

### Recency window — how many recent occurrences feed the conservative estimate

| Window | Status | Method | Plan |
|---:|---:|---:|---:|
| 2 | 18 | 20 | 16 |
| **3 (chosen)** | **20** | **22** | **17** |
| 4 | 20 | 22 | 17 |
| 5 | 20 | 22 | 17 |
| 6 | 18 | 20 | 15 |
| all history | 17 | 19 | 15 |

3, 4 and 5 tie. 3 is kept as the smallest value at the optimum — it reacts
fastest to a genuine change in spending level while still averaging out noise.
Using all history is clearly worse: it drags in stale amounts from months the
user has moved on from.

### Spike outlier factor — when a recent debit is a one-off, not the new normal

A recent debit above `factor × (category's historical median)` is excluded from
the conservative `max`, as long as one normal occurrence remains.

| Factor | Status | Method | Plan |
|---:|---:|---:|---:|
| 1.5 | 20 | 22 | 17 |
| 2.0 | 20 | 22 | 17 |
| **2.5 (chosen)** | **20** | **22** | **17** |
| 3.0 | 20 | 22 | 17 |
| 4.0 | 20 | 22 | 17 |
| ∞ (disabled) | 19 | 21 | 16 |

The score is **completely flat from 1.5 to 4.0** and only drops when the
mechanism is removed. This is the signature of a structural fix rather than a
fitted constant: what matters is that one-off spikes are recognised at all, not
where exactly the line sits. 2.5 is chosen as the midpoint of the flat region.

### Variable (gig) income — tested and rejected

`user_10` is a delivery-platform worker: 21 weekly payouts ranging ₹40,977 to
₹82,667 (coefficient of variation 0.20, where regular payroll users sit at
0.00). The engine anchors future income on the most recent payout, which for a
variable stream means treating one arbitrary week as guaranteed. Projecting
such streams at a low percentile of their own history instead looked more
conservative and better aligned with *"count **confirmed** salary"*, so it was
implemented and measured:

| Percentile | Status | Method | Mean amount err |
|---|---:|---:|---:|
| baseline (most recent payout) | **20** | **22** | 1.852 |
| 0th (minimum) | 17 | 19 | 1.924 |
| 25th | 19 | 21 | 1.812 |
| 50th (median) | 20 | 22 | 1.852 |

It made things worse at the 0th and 25th percentile and changed nothing at the
median, so **it was reverted**. The hypothesis was reasonable, the evidence said
no, and shipping it on intuition would have traded a measured 20/22 for an
unmeasured guess across 250 hidden rows. A comment in `events.py` records the
result so nobody re-derives it.

### Forecast horizon

| Days | Status | Method | Plan |
|---:|---:|---:|---:|
| 60 | 19 | 21 | 17 |
| **90 (chosen)** | **20** | **22** | **17** |
| 120 | 20 | 22 | 17 |
| 150 | 19 | 22 | 17 |
| 180 | 19 | 22 | 16 |

90 and 120 tie; 90 is kept because `problem_statement.md` specifies a 90-day
window. The horizon is a hardcoded constant in `main.py`
(`FORECAST_HORIZON_DAYS`), not an env var — the spec fixes it, and the sweep
only existed to confirm the spec's figure is also the empirically best one.

---

## Validation beyond the samples

Sample accuracy measures agreement with 25 reference answers. It does not
measure correctness on the other 225, and it cannot detect a bug that the 25
happen not to touch. Three further layers cover that gap.

### Regression suite — `code/tests/test_engine.py` (8 tests)

Every defect fixed above is pinned by a named test, so a later change cannot
silently reintroduce it. Plus invariants over all 250 requests: one row per
`request_id`, `0 ≤ amount_safe_to_pay ≤ requested_amount`, no scientific
notation in any amount, every installment plan matches a supplied payment
option, and a calibration floor that fails the build if the sample score drops.

### Adversarial suite — `code/tests/test_adversarial_evidence.py` (25 tests)

The dataset seeds deliberately deceptive evidence — advance-fee fraud in two
languages, prize proceeds "still processing", approved-but-unsettled invoices,
bonuses pending review, unrealized investment swings in both directions. These
tests assert no such message produces phantom income, no evidence patch anywhere
introduces an outbound debit, and every patch conforms to the closed five-key
schema. See `ARCHITECTURE.md` §3.

### Hand-built scenarios — `code/tests/run_synthetic_scenarios.py` (15 cases)

15 new requests constructed against **real** users' actual
`financial_events.csv` history, chosen to cover situations the 25 samples
under-represent: a user whose accepted payment methods are installments-only, a
USD salary paid to an INR-home user, wait-for-payday, near-floor balances, and
clear affordable/unaffordable extremes.

This layer found the two bugs in steps 6 and 7. Neither was visible in the
sample score.

A second set of 15 fully synthetic cases (`run_chatgpt_scenarios.py`, generated
externally) scored 7/15 — investigation showed 13 of them supply only **one**
historical occurrence per expense category, so the ≥3-occurrence recurrence rule
correctly declines to project any recurring expense at all. The disagreement is
with the generator's human-intuitive assumption that rent obviously recurs, not
with the engine. Retained as documentation of that boundary; **not** used as an
accuracy baseline.

### Hand audit — `code/tests/audit_real_requests.py` (20 requests)

20 real predictions, stratified across all four statuses and five currencies,
each verified by inspecting the underlying ledger trajectory rather than
trusting the output. **20/20 correct.** Two initially looked wrong and both
turned out to be the engine being right:

- **`request_119`** — ₹130,901 of headroom today, yet `amount_safe_to_pay = 0`. The ledger shows nine recurring categories draining the balance to ₹96,974, below the ₹151,200 floor, before the next salary lands. Exactly the failure a current-balance check would miss.
- **`request_76`** — the balance climbs from ~$2,700 to $27,000 and never dips, yet the result is `not_affordable`. The profile accepts `partial_payment` **only**, and the request sets `allows_partial_payment = False`. No permitted plan exists.

---

## A real fix: fixed vs. adjustable categories use different estimators

Tracing the two closest near-misses by hand (`request_22`, `request_23`)
against their raw per-category history exposed a distinction the estimator was
missing: `flexibility` isn't just an eligibility flag for spending-change
plans — it's a signal about *whether the amount is expected to be constant*.
A `fixed` category (rent, a debt repayment, groceries when the user has no
control over it) genuinely gets projected at its recent maximum; that's what
"conservative" means for essential spending the user cannot adjust. But a
`reducible` or `stoppable` category is, by definition, something the user is
already actively managing — projecting it at a spiking recent peak assumes the
worst month repeats forever, when the more grounded assumption is that it
continues at its *current* level.

Changed the estimator: `fixed` categories keep max-of-recent (debits) /
min-of-recent (credits); `reducible` and `stoppable` categories now project at
their single most recent observation instead. Measured, not assumed:

| Estimator | Status | Method | Amount ≤1% | Amount ≤5% |
|---|---:|---:|---:|---:|
| max/min uniformly (old) | 20 | 22 | 5 | 11 |
| last-observed uniformly | 19 | 21 | 6 | 10 |
| **fixed→max/min, variable→last (shipped)** | **20** | **22** | **6** | 11 |
| variable→max/min, fixed→last | 19 | 19 | 6 | 9 |

Only the shipped combination improves a sub-metric (≤1% band, 5→6) with **zero
regression** on any of the other five. The clearest single win: `request_03`'s
`amount_safe_to_pay` error dropped from 150% to 0.06% (₹2,183,755.81 →
₹872,452.60 against a true value of ₹873,000.00) — a case that was previously
the single worst outlier after the two unexplained 21× cases below, now
essentially exact.

This is shipped as the default (`ESTIMATOR_MODE = "hybrid2"` in `events.py`,
overridable via `BOW_ESTIMATOR` for re-sweeping). It's a real, principled,
measured improvement — but it does not close the gap on the two dominant
outliers below, which remain unexplained after this and every other hypothesis
tried.

## Hypotheses tested and rejected

`amount_safe_to_pay` (4/25 exact) and `earliest_date_for_full_payment` (13/25)
are the two weakest criteria. They are not independent: the spec defines
`earliest_date` as equal to `request_date` whenever the status is
`affordable_now`, so a too-optimistic `amount_safe_to_pay` produces a
too-early date automatically. Both trace to one thing — this engine's
`global_min` differs from the reference forecast's.

Five structural hypotheses were implemented and measured against the samples.
**All five were rejected by the evidence and reverted.** They are recorded here
so the reasoning is not silently repeated:

| Hypothesis | Rationale | Result |
|---|---|---|
| Longer forecast horizon (120–365d) | more chances to dip ⇒ lower `global_min` ⇒ less optimistic | status 20→17, `earliest_date` 13→8 at 365d. **Worse.** |
| Percentile projection for variable gig income | anchoring on the latest payout treats one arbitrary week as guaranteed | 0th pct 17/19, 25th 19/21, 50th unchanged. **Worse or neutral.** |
| Intraday debits before credits | netting a same-day salary against same-day bills assumes the credit clears first | status 20→19, amount ≤5% 11→9. **Worse** — the reference nets same-day too. |
| Lower/higher recurrence threshold (2, 4) | maybe the reference projects categories with fewer occurrences | byte-identical output. **No effect.** |
| Wider/narrower recency window (2, 4, 5, 6, all) | maybe the amount estimate uses a different lookback | 3–5 tie; 2 and 6+ worse. **Already optimal.** |

What remains is a residual difference in the *per-category expense estimate*
itself. On the two closest near-misses the gap is small and in **opposite
directions** — `request_22` is 6.62 above the reference, `request_23` is 681.46
below it — so it is not a uniform bias that a single constant or a global
conservatism factor could correct. Recovering it would mean inferring the
grader's exact per-category estimator from 25 samples that contain many more
unknowns than that (per-category amount rule, in-window occurrence counts,
same-day ordering). Fitting a correction to those 25 rows would almost certainly
degrade the 250 hidden ones, which is the trade this project has consistently
refused to make.

The honest position: these two criteria are the known weak point, they are now
**measured rather than invisible**, and every cheap structural explanation has
been tested and ruled out.
