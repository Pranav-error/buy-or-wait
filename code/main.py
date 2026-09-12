"""Entry point: python3 code/main.py
Reads dataset/*.csv, decides every request, writes output.csv at repo root."""

import csv
import datetime as dt
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loader import load, ROOT
from events import build_ledger, detect_recurring_patterns
from decision import (
    build_candidates,
    pick_flexible_reduction_candidates,
    apply_action_to_ledger,
    action_str,
    _split,
)
from explain import explain
import evidence

# problem_statement.md fixes the safety window at 90 days. Swept over
# 60/90/120/150/180 during calibration (see evaluation/CALIBRATION.md): 90 and
# 120 tie for best sample accuracy, so the spec's own figure is kept.
FORECAST_HORIZON_DAYS = 90


def decide_one(ds, request_row, evidence_overrides):
    user_id = request_row["user_id"]
    profile = ds.profiles[ds.profiles["user_id"] == user_id].iloc[0]
    home_ccy = profile["home_currency"]
    min_balance = float(profile["minimum_balance_to_keep"])
    current_balance = float(profile["current_available_balance"])
    request_date = request_row["request_date"]
    horizon_end = request_date + dt.timedelta(days=FORECAST_HORIZON_DAYS)

    amount_overrides = evidence_overrides.get(user_id, {}).get("amount_overrides", {})
    exclude_ids = evidence_overrides.get(user_id, {}).get("exclude_event_ids", set())
    extra_items = evidence_overrides.get(user_id, {}).get("extra_items", [])
    evidence_note = evidence_overrides.get(user_id, {}).get("note") or None
    recurring_overrides = evidence_overrides.get(user_id, {}).get("recurring_overrides", {})

    ledger = build_ledger(ds, user_id, home_ccy, request_date, horizon_end,
                           amount_overrides, exclude_ids, extra_items, recurring_overrides)
    patterns = detect_recurring_patterns(ds, user_id, home_ccy, request_date, amount_overrides, recurring_overrides)
    opts = ds.payment_options[ds.payment_options["request_id"] == request_row["request_id"]]

    candidates, baseline_amt_safe, baseline_earliest = build_candidates(
        profile, request_row, opts, ledger, current_balance, min_balance, horizon_end,
        None, None,
    )

    best = None
    changes_used = []
    if candidates:
        best = min(candidates, key=lambda c: c.rank_key())
    else:
        actions = pick_flexible_reduction_candidates(profile, patterns, request_date, horizon_end)
        # Prefer fewer spending changes (rule 2); within a given number of
        # changes, compare every valid combo (not just the first one found)
        # and rank per the full 6-rule order. Only fall back to a safe-but-
        # late plan if no combo of any size completes on time.
        best_on_time_by_r = {}
        best_any_by_r = {}
        for r in (1, 2, 3):
            for combo in itertools.combinations(actions, r):
                cats = [a[1].category for a in combo]
                if len(cats) != len(set(cats)):
                    continue
                mod_ledger = ledger
                for a in combo:
                    mod_ledger = apply_action_to_ledger(mod_ledger, a)
                cands2, _, _ = build_candidates(
                    profile, request_row, opts, mod_ledger, current_balance, min_balance, horizon_end,
                    baseline_amt_safe, baseline_earliest, uses_spending_change=True,
                )
                if not cands2:
                    continue
                any_best = min(cands2, key=lambda c: c.rank_key())
                if r not in best_any_by_r or any_best.rank_key() < best_any_by_r[r][0].rank_key():
                    best_any_by_r[r] = (any_best, combo)
                on_time = [c for c in cands2 if c.meets_deadline]
                if on_time:
                    on_time_best = min(on_time, key=lambda c: c.rank_key())
                    if r not in best_on_time_by_r or on_time_best.rank_key() < best_on_time_by_r[r][0].rank_key():
                        best_on_time_by_r[r] = (on_time_best, combo)
            if r in best_on_time_by_r:
                best, changes_used = best_on_time_by_r[r][0], list(best_on_time_by_r[r][1])
                break
        if best is None and best_any_by_r:
            r = min(best_any_by_r)
            best, changes_used = best_any_by_r[r][0], list(best_any_by_r[r][1])

    if best is None:
        return {
            "request_id": request_row["request_id"],
            "amount_safe_to_pay": round(baseline_amt_safe, 2),
            "affordability_status": "not_affordable",
            "recommended_payment_method": "not_recommended",
            "payment_plan": "none",
            "earliest_date_for_full_payment": baseline_earliest.isoformat() if baseline_earliest else "",
            "spending_changes_needed": "none",
            "decision_explanation": explain("not_recommended", "not_affordable", baseline_amt_safe,
                                             home_ccy, min_balance, None, request_row["desired_completion_date"],
                                             [], evidence_note,
                                             requested_amount=float(request_row["requested_amount"]),
                                             accepted_methods=_split(profile["payment_methods_user_will_consider"])),
        }

    spending_str = "none"
    if changes_used:
        spending_str = "|".join(action_str(k, p) for k, p, _ in changes_used)

    return {
        "request_id": request_row["request_id"],
        "amount_safe_to_pay": round(baseline_amt_safe, 2),
        "affordability_status": best.status,
        "recommended_payment_method": best.method,
        "payment_plan": best.plan_str(),
        "earliest_date_for_full_payment": baseline_earliest.isoformat() if baseline_earliest else "",
        "spending_changes_needed": spending_str,
        "decision_explanation": explain(best.method, best.status, baseline_amt_safe, home_ccy, min_balance,
                                         best, request_row["desired_completion_date"], changes_used, evidence_note),
    }


def main():
    ds = load()
    evidence_overrides = evidence.build_overrides(ds)

    rows = []
    for _, r in ds.requests.iterrows():
        try:
            rows.append(decide_one(ds, r, evidence_overrides))
        except Exception as e:
            print(f"ERROR on {r['request_id']}: {e}", file=sys.stderr)
            raise

    out_path = os.path.join(ROOT, "output.csv")
    fieldnames = ["request_id", "amount_safe_to_pay", "affordability_status", "recommended_payment_method",
                  "payment_plan", "earliest_date_for_full_payment", "spending_changes_needed",
                  "decision_explanation"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
