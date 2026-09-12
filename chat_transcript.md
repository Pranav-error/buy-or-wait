# Chat transcript — Buy or Wait?

**Participant:** Pranav (solo)
**Challenge:** HackerRank Orchestrate, September 2026 — *Buy or Wait?*
**Tool used:** Claude Code (Anthropic), models Haiku 4.5 → Sonnet 5 → Opus 5
**Working session:** 2026-09-12 18:26 IST → 2026-09-13 01:12 IST (~6h 45m)
**Repository:** `Pranav-error/buy-or-wait`

This is the development conversation, reconstructed from `log.txt`, which was
appended to after every turn as required by `AGENTS.md` §5.2 (verbatim user
prompt, what was done, why, and the files touched). Nothing has been added
after the fact. One value is redacted: an API key pasted into chat appears as
`[REDACTED]`, as it did in the log.

Timestamps are IST. Section headings are the log's own turn titles.

---

## Summary of how the system was developed

The build followed one loop, deliberately, from start to finish:

> **form a hypothesis → implement it → measure it against the 25 solved samples → keep it only if the number moves → write down the result either way**

That loop produced eight accepted fixes and **five rejected ones**. The
rejections matter as much as the acceptances: each was a plausible idea that
measurement contradicted, and shipping any of them on intuition would have
traded a measured score for a guess across 250 hidden rows. All five are
recorded in `code/evaluation/CALIBRATION.md` so the reasoning is not repeated.

Three moments changed the project's direction:

1. **Realising income had to be projected, not just expenses** (18:48). The first working engine returned 212/250 `not_affordable` because it drained every balance with no offsetting salary.
2. **Discovering the dataset contains real adversarial evidence** (22:52). Advance-fee fraud in two languages, which drove the trust-boundary design.
3. **Discovering the evaluation harness was scoring only 3 of the 6 criteria the brief lists** (00:45). This was the single most valuable find of the session and came from re-reading the problem statement rather than from the code.

---

## 18:26 — Session start

> **Pranav:** well we came for september ediition this time
> https://github.com/interviewstreet/hackerrank-orchestrate-september26.git
> i thnink u will have wht ever u need here

Cloned the repo into a fresh directory, separate from the August "Message
Notification Router" project. Read `AGENTS.md`, `CLAUDE.md` and
`problem_statement.md` in full.

The task: for every purchase request, decide whether the user should pay in
full, part-pay, use installments, wait, or not proceed — reconstructing their
financial position from profiles, event history, fixed dated exchange rates,
seller payment options, and optional messages/images treated as untrusted
evidence. Output is `output.csv` with eight fixed columns. Deadline
2026-09-13 18:00 IST.

Created `.gitignore` (log, `.env`, `__pycache__`, `code.zip`) and the log file.
No code yet.

---

## 18:48 — Deterministic core built; first real modelling lesson

Built the whole deterministic engine: `loader.py` (CSV loading, FX conversion
via a single exact-settlement-date rate row), `events.py` (recurrence detection
and forward ledger), `forecast.py` (90-day balance path, safety check,
earliest-safe-date by suffix-minimum), `decision.py` (candidate plans and the
spec's ranking), `explain.py` (templated explanations, zero LLM cost), and
`main.py`.

First full run: **212 of 250 requests came back `not_affordable`.**

Root cause, and the session's first real lesson: the engine projected recurring
*expenses* forward but not recurring *income*. `current_available_balance` is a
snapshot at `request_date`, not a pot that already contains future salary — so
projecting only outflows drains every user to zero. Salary also needed a special
case: most users have one settled payroll row plus one scheduled "next confirmed
salary" row, which fails a ≥3-occurrence recurrence rule, yet two confirmed
points genuinely do establish a monthly cadence.

After the fix: **17/25 status, 19/25 method** with no evidence applied. Nearly
every remaining mismatch belonged to a user with an attached message or image —
confirmed by cross-referencing `messages.csv` and `images.csv` against the
mismatched request ids. That was the expected next stage.

Also fixed a formatting defect: Python's `:g` format spec silently rendered
large amounts in scientific notation (`1.5656e+07`), which is not valid in the
`payment_plan` grammar.

Built `evidence.py` — one cached call per user with message/image evidence,
returning a strict JSON patch, with an explicit untrusted-evidence instruction.
Wired in but inert: the API key carried over from August returned 401.

> **[Asked about the invalid key]** → **Pranav:** i will give it later keep it blank for now

---

## 19:02 — Two genuine bugs, and a look at sibling projects

> **Pranav:** keep working on the deterministic engine, calibrate more samples
> and also check my razopay project if u can use some idea from there and also
> check for last edition of august

Separated the remaining mismatches into "has message/image evidence" (expected,
awaiting the key) and "no evidence" (real bugs). Two real bugs in the second
group:

- A user with a bimodal salary category — stable base pay interleaved with a smaller irregular commission — whose average was being corrupted.
- The core one: recurring expenses used `mean(last 3)`, but the brief says *"forecast essential variable spending conservatively"*, and a mean is not conservative in either direction. Changed to `max` of recent occurrences for expenses and `min` for income.

**17→18/25 status, 19→20/25 method.**

Reviewed the two sibling projects as asked. From the Razorpay evidence-verifier:
adopted its regression-test discipline (pin every fixed defect as a named test)
and its "state the limitation before a judge does" principle — which is why
`request_05` is documented openly rather than quietly accepted. From the August
edition: confirmed the deterministic-core-plus-LLM-for-evidence split matches
the shape that worked there.

Added `code/tests/test_engine.py`: 7 tests, including a calibration floor that
fails the build if accuracy regresses.

---

## 19:23 — Ranking bug, status bug, submission docs

> **Pranav:** [screenshot] check for the api key they told they have give the access

The screenshot was HackerRank's own "Pair" browser IDE advertising $30 of
credits. Confirmed with the user that this is credit inside *their* hosted tool,
not a portable key usable in this repo. Still blocked.

Two more real bugs found and fixed:

- The spending-change search accepted the *first* combination of a given size that worked, instead of comparing all combinations of that size and picking the best-ranked. It also discarded safe-but-late candidates entirely rather than falling back to them.
- A `wait` plan that only became safe *because* spending changes freed cash was tagged `affordable_later` — but the brief defines `affordable_with_plan` as completion through a schedule, installments, **or** permitted spending changes. Any plan built on a spending change now reports that status. Rows using spending changes went from 8 to 19.

Wrote `code/evaluation/main.py` (sample scorer) and
`generate_usage_report.py`, plus `code/README.md` documenting the architecture,
every decision and its reason, and the `request_05` limitation stated plainly.

---

## 21:32 — Credits investigated; a zero-cost path to the evidence stage

> **Pranav:** [two screenshots of pair.sh showing GPT-5.6 Luna / GLM 5.3 / Grok 4.6 and $30 credit]
> so this the ide credits they gave see if u can use it any way possible it has
> these models see if u can divide work or smtg it has 30 dollors and also
> continue building this project i want perfect efficiecy

> **Pranav:** find an alternative or see if u can power the evidence.py with
> normal cladude itslef or else i can use gemini or groq api keys which arent
> good enough as paid version so see if u can only perform the action

Confirmed `pair.sh` model access is scoped to that hosted IDE — no portable key.

Found a better path that needed no key at all. `evidence.py` already caches one
JSON patch per user to disk and skips the API entirely on a cache hit. So the
same context the API would have received was dumped per user, and five parallel
Claude Code sub-agents — acting as the extraction model themselves, following
the exact rules already written in `evidence.py`'s system prompt — wrote the
cache files directly. Zero cost, same reasoning quality.

Mid-turn the user pasted a friend's API key (`[REDACTED]`, capped at $3). It was
stored in `.env` (gitignored, never echoed) but **deliberately not spent**: the
agent path achieves the same result for free, so the friend's credit was left
untouched.

---

## 21:47 — All 219 users covered; a schema gap found by a suspicious result

All five batches finished: 219/219 users. Fixed one cross-batch inconsistency —
one batch had counted four "approved, settlement expected" invoices as confirmed
cash while two others had correctly left equivalent cases alone.

Re-ran the pipeline and got a result **identical** to the pre-evidence baseline.
That was suspicious enough to investigate rather than accept, and it exposed a
real schema gap: the evidence format had `amount_overrides` for a single event
and `extra_items` for one-off facts, but nothing that could say *"this whole
recurring category's go-forward amount changed."* So every salary raise,
temporary reduction and household-income change the agents had extracted was
sitting in human-readable `note` text, never reaching the forecast.

Added `recurring_overrides` end-to-end, then read all 84 salary-related notes and
classified each: permanent raise (18 users), household restructuring (6),
temporary dip still in effect (6), reverts-to-normal after a recorded dip (5),
employment ended entirely (4, override to 0). The remaining ~45 were
confirmations of already-recorded data or explicitly unsettled facts, correctly
left alone.

**18→19/25 status, 20→21/25 method.**

Also rewrote the usage report's zero-call branch to disclose the actual
methodology — agent extraction, not a metered API call — rather than implying
evidence simply wasn't applied.

---

## 22:16 — Image verification, and two bugs found by hand-built scenarios

> **Pranav:** wait for batch 4 then rerun the pipeline and also they have images
> right check if the ocr is working properly or not and also get outside data
> which and test the pipeline on it make that score as the base

> **Pranav:** i meant other data sets in real world not just the data they gave
> and the ocr model is not good enough Verified 8 of the 16 images directly i
> want all 100 per on that

Read all 16 images directly and checked every extracted amount against the
document. **16/16 correct** — including a handwritten pharmacy receipt whose
total is barely legible (the extraction had cross-validated it against the
itemised line sum) and one delivery screenshot genuinely cropped before the
final total, which had been flagged rather than guessed. Corrected the user's
premise: there is no separate OCR model; amounts were read directly by vision.

For "outside data": no public dataset matches this schema, so two things were
built. A ready-to-paste prompt for the user to try against ChatGPT, and —
independently — 15 hand-designed requests built on **real** users' actual event
history, covering cases the 25 samples under-represent (installments-only
payment preferences, a USD salary paid to an INR-home user, wait-for-payday,
near-floor balances).

That harness found **two real bugs**:

- **Salary anchor.** A one-off arrears payment landing days after regular payroll was being taken as the new ongoing salary, turning one user's €1,452 into €653.40. Confirmed to affect four real evaluation users.
- **Partial-payment date.** The second installment's date was computed against the *full* requested amount instead of the smaller remainder, discarding valid plans whenever the full amount never became safe but the remainder would.

---

## 22:29 — Scoring the external test set; hand-auditing real predictions

> **Pranav:** [15 ChatGPT-generated test cases with expected answers] see if this is usefull

Scored 7/15 — then investigated rather than reporting the number. Thirteen of
the fifteen supply only **one** historical occurrence per expense category, so
the ≥3-occurrence rule correctly declines to project any recurring expense.
The disagreement is with the generator's human-intuitive assumption that rent
obviously recurs, not with the engine. Kept as documentation of that boundary;
explicitly **not** used as a baseline.

> **Pranav:** this isnt concreate enough we lacking
> **[Asked what was lacking]** → *overall confidence in the engine's correctness*

Built a ledger-dump audit tool and hand-verified 20 real predictions, stratified
across all four statuses and five currencies. **20/20 correct.** Two looked
wrong and both turned out to be the engine being right:

- `request_119` — ₹130,901 of headroom today, yet zero safe. Nine recurring commitments drain the balance to ₹96,975, below the ₹151,200 floor, before the next salary. Exactly what a current-balance check would miss.
- `request_76` — balance climbs to $27,000 and never dips, yet `not_affordable`. The profile accepts `partial_payment` only, and the request forbids it.

---

## 22:52 — Accuracy, adversarial robustness, and documentation

> **Pranav:** yes increase the accuracy and precission and all so create
> architure diagram and proper undertsnading docs for the poject and we need
> something unique as all of us have the same problem statment

Re-opened three mismatches previously written off, and found a real bug behind
one. `user_17` buys groceries weekly at ~₹7,000–11,400; one row — the blank
amount resolved from a receipt image — is **₹41,272**, a bulk stock-up. The
conservative `max()` adopted it as the *weekly* baseline, over-draining the
forecast ~4× and rejecting an affordable request. Fixed by excluding values far
above a category's own historical median. **19→20/25 status, 21→22/25 method.**

The fix is flat across thresholds 1.5–4.0 and only changes when switched off
entirely — the signature of a structural fix rather than a fitted constant.

For "something unique": searched the dataset for adversarial content and found
the brief means its untrusted-evidence rule literally. `message_67` (English)
and `message_142` (Indonesian) are textbook advance-fee fraud — *"Congratulations!
You've been selected for a cash prize. Pay the release charge today…"* — alongside
eleven subtler prize and receivable traps.

Audited all 13 targeted users: **zero phantom income**. The property that makes
this robust is architectural — the evidence schema is closed and typed, with no
field capable of expressing an instruction, and the deterministic engine never
sees raw message text. Wrote 25 tests pinning it.

Wrote `ARCHITECTURE.md` (diagrams, rationale, limitations) and
`CALIBRATION.md` (every sweep, full accuracy progression).

---

## 00:45 — The most valuable find: scoring only half the rubric

> **Pranav:** i think u can see the creitera for submiison if u cant pull from
> the august edition and adjust everything accordingly as we need to be
> verycarful and i am still not satisfied with the overall project

Went back to `problem_statement.md` §Evaluation. It lists **six** scored items.
The evaluation harness measured **three**. So three scored criteria had never
been checked at all, and `amount_safe_to_pay` — a *numeric* accuracy measure —
had never been quantified. The project looked strong on the metrics being
watched while being unmeasured on half the rubric. That was the real substance
behind the user's dissatisfaction.

Rewrote the scorer to cover all six. Turning the missing three on immediately
exposed **three real defects**:

1. **Calendar drift.** Monthly recurrences stepped forward by `round(median_gap)` days, so a salary anchored on the 15th lands on the 14th, then the 13th — drifting every cycle. The pattern was unmistakable once measured: predicted `2025-09-13` vs true `2025-09-15`, `2019-11-13` vs `2019-11-15`. Since `earliest_date` is almost always exactly a payday, this corrupted it directly. **earliest_date 9→13/25, payment_plan 17→20/25.**
2. **Pending credits counted as income.** The brief says plainly *"Do not count pending credits… until they settle."* Any pending row was being counted, so one user's ₹8,640 pending refund inflated their forecast. Now pending credits are dropped while *scheduled* credits (confirmed salary) still count. The mirror bug too: pending **debits** dated before the request were skipped as "past", but they haven't settled and the money still leaves.
3. **Uninformative — and in one case false — refusals.** Every `not_affordable` row emitted one generic sentence. Adding a figure then revealed that some refusals have *sufficient* cash and are blocked purely by the user's accepted payment methods, so blaming committed expenses would have been factually wrong. **explanation 22→25/25.**

Also tested and **rejected** a gig-income hypothesis: `user_10` is a
delivery-platform worker (21 weekly payouts, CV 0.20 vs 0.00 for salaried
users), and anchoring on the latest payout arguably treats one arbitrary week as
guaranteed. Percentile projection scored *worse* at the 0th and 25th percentile
and identical at the median, so it was reverted and the result recorded.

---

## 01:12 — Four more hypotheses, all rejected on measurement

> **Pranav:** fix the amount_safe_to_pay and earliest_date now and also test the
> our results with there ground truth

Established first that the two weak criteria are **not independent**: the brief
defines `earliest_date` as equal to `request_date` whenever the status is
`affordable_now`, so a too-optimistic `amount_safe_to_pay` mechanically produces
a too-early date. Both reduce to one thing — this engine's `global_min` differs
from the reference forecast's. A sharp diagnostic confirmed it: all four "exact"
amount hits are cases where the answer is simply the `requested_amount` cap.

Also clarified that the hidden ground truth is not available; `sample_requests.csv`
is the only ground truth testable before submission.

Implemented and measured four more hypotheses. **All rejected:**

| Hypothesis | Result |
|---|---|
| Longer horizon (120–365d) | status 20→17, date 13→8. Worse |
| Intraday debits before credits | status 20→19, amount ≤5% 11→9. Worse — the reference nets same-day too |
| Recurrence threshold 2 / 4 | byte-identical. No effect |
| Recency window re-sweep | 3–5 tie. Already optimal |

Diagnosed why no single correction closes the gap: on the two *closest*
near-misses the residual runs in **opposite directions** (`request_22` is 6.62
above the reference, `request_23` is 681.46 below), so it is not a uniform bias.
What remains is the grader's per-category expense estimator, which 25 samples
containing many more unknowns cannot determine. Fitting a correction to those 25
rows would very likely degrade the 250 hidden ones — the trade this project
refused to make throughout.

Documented openly in `CALIBRATION.md` under "Hypotheses tested and rejected".

---

## 01:00 — Repository

> **Pranav:** push evrything also / no make a seprate repo for this and push how
> we did for the last edition

Checked the remote before pushing and found `origin` pointed at the
**organiser's** repo. Did not push there: it would either fail on permissions or
publish a solo-challenge solution publicly. Mirrored the August convention
instead — own repo under the participant's account, named for the challenge —
but created it **private**, since unlike August this challenge was still live.
Kept the organiser's repo as `upstream`. Verified no `.env`, no log, and no key
string in any tracked file before pushing.

---

## Final state

| Scored criterion | Result |
|---|---:|
| `amount_safe_to_pay` accuracy | 4 exact · 11 within 5% / 25 |
| `affordability_status` | **20 / 25** |
| `recommended_payment_method` | **22 / 25** |
| `payment_plan` (exact string · totals) | 20 / 25 · **25 / 25** |
| `earliest_date_for_full_payment` | 13 / 25 |
| `spending_changes_needed` validity | **25 / 25** |
| `decision_explanation` usefulness | **25 / 25** |

37 automated tests passing. `output.csv` covers all 250 requests.
Zero metered model calls for the submitted run.

**Known weaknesses, stated plainly:** `amount_safe_to_pay` and `earliest_date`
are the weak criteria. Every cheap structural explanation for the residual has
been tested and ruled out; what remains would require inferring the grader's
exact per-category estimator from 25 samples. They are now measured rather than
invisible, which is the difference that mattered in the last hours of the build.
