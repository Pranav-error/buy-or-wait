# Chat transcript — Buy or Wait?

**Participant:** Pranav (solo) · **Tool:** Claude Code (Haiku 4.5 → Sonnet 5 → Opus 5)
**Session:** 2026-09-12 18:26 IST → 2026-09-13 (deadline 18:00 IST same day)
**Repo:** `Pranav-error/buy-or-wait`

Reconstructed from `log.txt`, appended after every turn per `AGENTS.md` §5.2.
One redaction: a friend's API key pasted mid-chat appears as `[REDACTED]`.

The build followed one loop throughout: **hypothesis → implement → measure
against the 25 solved samples → keep only if the number moves → record the
result either way.** That produced 8 accepted fixes and 6 explicitly rejected
ones (all logged in `code/evaluation/CALIBRATION.md`), because a rejected
hypothesis is as much a finding as an accepted one.

---

## Build (18:26 – 21:00)

Cloned the repo, read the spec. Built the deterministic core: FX-aware loading,
recurrence detection, a 90-day balance forecast, candidate-plan ranking, and
templated explanations.

First run: **212 of 250 requests came back `not_affordable`.** The engine
projected recurring expenses forward but not income — `current_available_balance`
is a snapshot, not a pot that already contains future salary. Fixed by treating
two confirmed points (last paycheck + the scheduled "next confirmed salary") as
enough to establish a monthly cadence. **17/25 status, 19/25 method.**

Two more bugs followed: recurring amounts were averaged, which isn't
conservative in either direction (switched to max-for-expenses /
min-for-income); and the spending-change search took the first working
combination instead of comparing all of them. **18/25 → 20/22 by evening.**

Evidence extraction (`evidence.py`) was wired in but blocked — the carried-over
API key returned 401, and the user said to leave it blank for now.

> **Pranav:** find an alternative or see if u can power the evidence.py with
> normal cladude itslef

`evidence.py` already caches one JSON patch per user and skips the API on a
cache hit. So instead of calling any API, five parallel Claude Code agents read
the same context the API prompt would have sent and wrote the cache files
directly — same reasoning, zero cost. All 219 users processed.

Re-running produced an *identical* score to the pre-evidence baseline, which
was suspicious enough to chase: the evidence schema had no field for "this
category's recurring amount changed," so every salary raise or cut sat in
human-readable text, never reaching the forecast. Added a `recurring_overrides`
field end-to-end and classified all 84 salary-related notes by hand.
**19/25 status, 21/25 method.**

---

## Validation beyond the samples (21:00 – 23:00)

> **Pranav:** i want all 100 per on that [the images]

Read all 16 dataset images by hand against their extracted amounts —
**16/16 correct**, including a handwritten receipt cross-validated against its
own itemized sum and one screenshot correctly flagged as cropped rather than
guessed.

Built 15 new requests on **real** users' actual history (not fabricated
finances) to stress-test cases the 25 samples don't cover. This found two real
bugs: a one-off arrears payment was being read as the new ongoing salary
(corrupting a real user's €1,452 into €653.40), and a partial-payment plan's
second date was computed against the full amount instead of the smaller
remainder.

A separately generated 15-case set (via ChatGPT) scored only 7/15 —
investigation showed 13 of those cases supply just one historical data point
per expense category, so the ≥3-occurrence recurrence rule correctly declines
to project anything. Not an engine bug; not used as a baseline.

> **Pranav:** this isnt concreate enough we lacking

Hand-audited 20 real predictions against their actual ledgers. **20/20
correct**, including two that looked wrong at first glance and weren't: one
user with healthy current balance whose nine recurring bills genuinely drain
them below the floor before payday, and one whose balance never dips but who is
correctly refused because their own stated payment preferences rule out every
option offered.

---

## Accuracy and the unique angle (23:00 – 00:45)

Re-opened a dismissed mismatch and found a real bug: a user's grocery spend is
normally ~₹7–11K/week, but one receipt-derived amount was a **₹41,272** bulk
purchase. The "conservative max" estimator was projecting that as the *weekly*
baseline, quadrupling the real drain. Fixed by excluding one-off spikes above
2.5× a category's own median — a fix that scores identically across a 1.5–4.0
threshold range, the signature of a structural fix rather than a tuned number.
**20/25 status, 22/25 method.**

Searched the dataset for adversarial content and found it seeds real
advance-fee fraud, in English and Indonesian:

> *"Congratulations! You've been selected for a cash prize. Pay the release
> charge today to receive the funds immediately."*

Audited every targeted user: **zero phantom income.** The reason is
architectural, not a prompt instruction — message content can only reach the
financial model through a closed, five-key typed schema with no field capable
of expressing an instruction. Wrote 25 tests pinning this.

---

## The most valuable find (00:45)

> **Pranav:** i think u can see the creitera for submiison ... i am still not
> satisfied with the overall project

Re-read the spec's evaluation section: it scores **six** criteria. The harness
had only ever measured three — `amount_safe_to_pay` (a numeric accuracy metric)
had never been quantified at all. Rewriting the scorer to cover all six
immediately exposed three real defects:

1. **Calendar drift** — monthly recurrences stepped by a fixed 30 days, so a payday anchored on the 15th silently drifted to the 14th, then 13th, misplacing `earliest_date_for_full_payment` almost everywhere. Fixed to advance by calendar month.
2. **Pending credits counted as income** — the spec says not to count them until settled; one user's pending refund was inflating their forecast. Fixed, while scheduled (confirmed) salary still counts as the spec requires.
3. **Refusals that didn't say why, and once could've said something false** — some `not_affordable` cases have sufficient cash and are blocked purely by the user's own payment preferences; the explanation now says the real reason.

`earliest_date` moved 9→13/25, `payment_plan` 17→20/25, `explanation` 22→25/25.

> **Pranav:** fix the amount_safe_to_pay and earliest_date now and also test
> our results with there ground truth

The two remaining weak metrics are the same root cause wearing two hats. Six
more hypotheses were implemented and measured — longer forecast horizons,
percentile-based gig-income projection, intraday debit/credit ordering,
recurrence-threshold changes — and **all six made things worse or changed
nothing**, so all were reverted. The residual gap on the closest near-misses
runs in *opposite* directions on different requests, ruling out a single
correctable bias; closing it further would mean fitting to 25 samples at likely
cost to the 250 hidden ones, which this project consistently declined to do.
Note: the hidden grading ground truth was never available — `sample_requests.csv`
is the only ground truth that exists before submission, and it's what every
number above is measured against.

---

## Final scores (vs. the 25 solved samples)

| Criterion | Result |
|---|---:|
| `amount_safe_to_pay` accuracy | 4 exact · 11 within 5% / 25 |
| `affordability_status` | 20 / 25 |
| `recommended_payment_method` | 22 / 25 |
| `payment_plan` (string · totals) | 20 / 25 · 25 / 25 |
| `earliest_date_for_full_payment` | 13 / 25 |
| `spending_changes_needed` validity | 25 / 25 |
| `decision_explanation` usefulness | 25 / 25 |

37 automated tests passing. `output.csv` covers all 250 requests. Zero metered
model calls in the submitted run. `amount_safe_to_pay` and `earliest_date`
remain the honest weak point — measured and documented rather than hidden,
after exhausting every cheap structural explanation for the gap.
