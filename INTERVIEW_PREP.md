# Submission interview prep — Buy or Wait?

For the post-submission AI interview. Every number and claim here was verified
live against the codebase before writing it down — check `code/evaluation/CALIBRATION.md`
and `code/ARCHITECTURE.md` if a follow-up question needs more depth than what's
here. **Don't recite this word-for-word** — the interviewer can ask follow-ups,
and the goal is to actually know this, not perform having read it once.

---

## 30-second pitch, if asked to describe the solution

"It's a two-stage engine. Stage 2 is a fully deterministic cash-flow simulator
— it builds a day-by-day 90-day balance forecast from the user's event history
and checks which payment plans keep the balance above their floor throughout.
Stage 1 is the only place a model is involved: it turns messages and images
into a small typed patch, never raw text, so an instruction embedded in a
message — and the dataset actually contains advance-fee fraud — has nowhere to
land. I found and fixed 12 real bugs by testing against real user data rather
than trusting the sample score, and I can walk through any of them."

---

## "Walk me through the architecture"

Pipeline: `loader.py` (CSV parsing, exact-date FX lookup) → `events.py`
(recurrence detection, builds the forward ledger) → `forecast.py` (balance
path, safe-amount, earliest-safe-date via suffix-minimum) → `decision.py`
(generates every plan the user's constraints allow, ranks them) →
`explain.py` (templated explanation, zero cost). `evidence.py` sits
off to the side and only touches messages/images.

**Key thing to say if asked "why deterministic":** the brief scores exact
numeric/date accuracy (`amount_safe_to_pay`, `earliest_date_for_full_payment`)
and structural validity (`spending_changes_needed`). An LLM asked to do
arithmetic on a 90-day cash-flow simulation is going to be less
reliable than direct computation, and it can't be identically reproduced or
audited — the deterministic core makes the whole engine debuggable, which is
exactly how the bugs below were found.

---

## "Where does the model actually get used, and why is that safe?"

Only in `evidence.py`, one call per user with message/image evidence, and it
returns a JSON patch with exactly 5 keys: `amount_overrides`,
`exclude_event_ids`, `extra_items`, `recurring_overrides`, `note`. No key means
"take an action" or "make a payment." The deterministic engine never sees raw
message text — only this patch.

**Why this matters, concretely:** the dataset contains real advance-fee fraud.
`message_67` (English) and `message_142` (Indonesian) say, roughly, "you've won
a cash prize, pay a release charge to receive it." If you paste that into a
prompt next to the financial data and ask for a decision, the model can either
book the phantom prize as income or act on "pay the release charge." Here,
neither is possible — there's no field in the schema that can express either
one. I audited all 13 users targeted by prize/lottery narratives: **zero
phantom income**, and wrote 25 tests (`test_adversarial_evidence.py`) that pin
this — no evidence patch anywhere may add income from a prize narrative, and
none may add an outbound debit at all.

**If asked "how did you populate the evidence cache without an API key":**
`evidence.py` caches one patch per user to disk and skips the API entirely on
a cache hit. Instead of paying for 219 live calls, I had 5 parallel Claude Code
agents read the same context the API prompt would have received and write the
cache files directly, following the identical system prompt rules. Same
model family, same reasoning, zero metered cost. This is disclosed in
`code/evaluation/usage_report.md`.

---

## "What bugs did you actually find, and how?"

12 real defects were found and fixed over the session (full list with
before/after sample scores in `CALIBRATION.md`'s progression table). Be ready
to describe at least 3-4 in detail — this is the strongest evidence of genuine
engagement with the problem, not a templated solution:

1. **No income projection at all (earliest bug).** First full run: 212/250 requests came back `not_affordable`. The engine projected expenses forward but not the matching salary, so every balance just drained to zero. Fixed by treating 2 confirmed points (last paycheck + the scheduled "next confirmed salary") as enough to establish a monthly pattern.
2. **Mean instead of max/min.** Recurring amounts were averaged. The brief says forecast conservatively — an average isn't conservative in either direction. Switched to max-of-recent for expenses, min-of-recent for income.
3. **Spending-change search took the first match, not the best one.** It accepted the first combination of spending cuts that worked instead of comparing every combination of that size and picking the best-ranked, and it discarded safe-but-late plans entirely instead of falling back to them.
4. **Status misclassified when a plan needed a spending change.** A `wait` plan that only became safe because a spending change freed up cash was tagged `affordable_later` (its natural status), but the brief defines `affordable_with_plan` as completion via a schedule, installments, *or* spending changes — so any plan built on one now reports that status.
5. **Evidence schema had no field for "this category's recurring amount changed."** Every salary raise or cut extracted from a message sat in human-readable `note` text and never reached the forecast, so applying 219 users' worth of evidence made *zero* difference to the score. Added a `recurring_overrides` field end-to-end.
6. **Salary corrupted by a same-cycle bonus.** A one-off arrears payment landing days after regular payroll was picked as the new ongoing salary — turned a real user's €1,452/month into €653.40. Confirmed this pattern affected 4 real evaluation users, not just the one I found it on.
7. **Partial-payment remainder used the wrong safe-date.** The second installment's date was computed against the *full* requested amount instead of the smaller remainder, so valid plans were discarded whenever the full amount never became safe but the remainder would.
8. **One-off spike treated as the new baseline.** A user's groceries run ~₹7-11K/week, but one receipt-derived amount was ₹41,272 (a bulk purchase). Taking the max of recent occurrences projected that as the *weekly* spend, draining the forecast ~4x and wrongly rejecting an affordable request. Fixed by excluding values above 2.5x a category's historical median — a threshold that's flat across 1.5-4.0, so it's a structural fix, not a number tuned to one sample.
9. **Calendar drift.** Monthly recurrence stepped by a fixed 30 days, so a payday anchored on the 15th silently drifted to the 14th, then the 13th, misplacing `earliest_date_for_full_payment` almost everywhere. Fixed to advance by calendar month.
10. **Pending credits counted as income.** The brief explicitly says not to count them until settled. One user's pending refund was inflating their forecast — dropped entirely, while scheduled (confirmed) salary still counts, exactly as the brief distinguishes the two.
11. **Refusals gave no reason, and once could have given a false one.** Every `not_affordable` row emitted one generic sentence; adding a real figure revealed some refusals have sufficient cash and are blocked purely by the user's own payment preferences, so blaming cash flow would have been wrong. Refusals now state the actual reason.
12. **Fixed vs. adjustable categories need different estimators.** `flexibility="fixed"` categories (rent, non-negotiable spending) keep the conservative max/min treatment; `reducible`/`stoppable` categories — which the user is already actively managing — now project at their most recent value instead of an inflated peak. One case's error dropped from 150% to 0.06%.

**If asked "how did you find these" — the honest answer:** several ways.
Bugs 1-2 came from calibrating against the 25 samples directly. Bugs 6-7 came
from hand-building 15 test scenarios on real users' actual event history,
targeting cases the samples under-cover. Bugs 9-11 came from realizing the
scoring harness only measured 3 of the 6 criteria the brief lists, and turning
the other 3 on. Bug 12 came from tracing the two closest near-misses by hand
down to their raw per-category history. Several of these (3, 4, 6, 7) didn't
move the sample score at all — they were found by other means and are real
fixes the 25 samples simply don't exercise.

---

## "What's the weakest part of your solution, and why?"

Be honest here — the interviewer can check the repo, and an evasive answer on
a documented limitation reads worse than a direct one.

`amount_safe_to_pay` (4/25 exact, 11/25 within 5%) and
`earliest_date_for_full_payment` (13/25) are the two weak criteria. They're not
independent — the brief defines `earliest_date` as equal to `request_date`
when status is `affordable_now`, so an off `amount_safe_to_pay` produces an off
date automatically.

**What I tried and why it didn't fully close the gap:** I tested roughly ten
hypotheses — longer forecast horizons, percentile-based projection for
variable/gig income, intraday debit-before-credit ordering, different
recurrence thresholds, and the fixed/adjustable estimator split above. Most
were measured and rejected because they made things worse; one (the
fixed/adjustable split) was a real, measured improvement I shipped. Two
outliers remain unexplained — off by roughly 20x — where the residual runs in
*opposite directions* on different requests, which rules out a single
correctable bias. Closing it further would mean reverse-engineering the exact
reference estimator from 25 samples, and I was not willing to fit a correction
to 25 rows at likely cost to the 225 hidden ones.

**If pushed "so what would you do with more time":** get more solved samples
to distinguish signal from noise on those two outliers, or find a second
independent way to reconstruct the reference forecast (e.g. if partial
grading feedback becomes available) rather than guessing structurally again.

---

## "How did you validate this beyond the sample score?"

Four independent layers, because sample accuracy alone can be — and initially
was — misleading:

- **The evaluation harness itself was incomplete for most of development.** The brief scores 6 criteria; the harness measured 3. Turning the other 3 on (`amount_safe_to_pay`, `earliest_date`, `decision_explanation`) immediately exposed 3 more real bugs, including the calendar-drift one above. This is probably the single most important thing to mention if asked "what would you do differently" — I should have read the scoring section that carefully on day one.
- **37 automated tests** (later grown further), each pinning one specific defect so it can't silently regress.
- **15 hand-built scenarios on real users' data** — found bugs the sample score never moved on.
- **20 hand-audited real predictions**, verified by tracing the ledger by hand, not by comparing to a hidden label (there isn't one). 20/20 correct, including two that looked wrong at first and weren't.

---

## "Is this over-engineered / under-engineered for the problem?"

Answer honestly based on what you believe, but the defensible position: the
core decision logic (`decision.py`, ranking, candidate generation) is close to
a direct transcription of the brief's own rules — it's not overbuilt. The
complexity is concentrated in `events.py`'s recurrence detection, which earned
its size through real bugs (the spike filter, the calendar-drift fix, the
fixed/adjustable split) — each addition is backed by a measured improvement,
not speculative generality. The adversarial-evidence testing (25 tests) is the
one piece that goes beyond what's strictly required, and that was a deliberate
choice because the brief's own untrusted-evidence rule seemed worth taking
literally rather than as a formality.

---

## Numbers to have ready

| | |
|---|---|
| Sample accuracy | 20/25 status, 22/25 method, 20/25 exact plan, 25/25 plan totals |
| `amount_safe_to_pay` | 4/25 exact, 6/25 within 1%, 11/25 within 5% |
| `earliest_date_for_full_payment` | 13/25 |
| `spending_changes_needed` validity | 25/25 |
| `decision_explanation` usefulness | 25/25 |
| Automated tests | 38 passing |
| Real bugs found and fixed | 12 |
| Structural hypotheses tested and rejected | ~10 |
| Images hand-verified | 16/16 correct |
| Real predictions hand-audited | 20/20 correct |
| Users targeted by fraud/prize narratives | 13, zero produced phantom income |
| Metered API calls in the submitted run | 0 |

---

## Questions to expect that aren't in this file

If something comes up that isn't covered here, the honest move is to open the
actual file and answer from it rather than guess — `code/ARCHITECTURE.md` has
the full reasoning with diagrams, `code/evaluation/CALIBRATION.md` has every
sweep and every rejected hypothesis with numbers, and `code/README.md` ties
both together. Do not invent a number or a design rationale that isn't
actually in the repo — if the interviewer checks, an invented answer is far
worse than "let me check that."
