"""Scores the engine against dataset/sample_requests.csv across ALL SIX
criteria problem_statement.md lists under "Evaluation":

    - accuracy of amount_safe_to_pay
    - correctness of affordability_status
    - correctness of recommended_payment_method and payment_plan
    - accuracy of earliest_date_for_full_payment
    - validity of spending_changes_needed
    - usefulness and consistency of decision_explanation

The 25 solved samples are the only ground truth available before submission,
so every one of those six is measured here rather than just the three that are
easy to compare as strings.

Run:  ./.venv/bin/python code/evaluation/main.py
      ./.venv/bin/python code/evaluation/main.py -v     # per-request detail
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pandas as pd

from loader import load
from main import decide_one
import evidence

VALID_STATUS = {"affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"}
VALID_METHOD = {"full_payment", "partial_payment", "installments", "wait", "not_recommended"}


def _norm(v):
    """Ground-truth blanks arrive as NaN or ''; normalise both to ''."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _parse_plan(plan):
    """'YYYY-MM-DD:amount|...' -> [(date, float)]. 'none'/'' -> []."""
    plan = _norm(plan)
    if not plan or plan.lower() == "none":
        return []
    out = []
    for part in plan.split("|"):
        if ":" not in part:
            continue
        d, _, a = part.rpartition(":")
        try:
            out.append((d.strip(), float(a)))
        except ValueError:
            pass
    return out


def _rel_err(pred, truth):
    """Relative error, scale-free so INR and EUR rows weigh the same."""
    if truth == 0:
        return 0.0 if abs(pred) < 1e-6 else 1.0
    return abs(pred - truth) / abs(truth)


def score_amount(pred, truth):
    """amount_safe_to_pay: exact, within 1%, within 5%, plus mean rel. error."""
    err = _rel_err(pred, truth)
    return err, abs(pred - truth) < 0.01, err <= 0.01, err <= 0.05


def score_date(pred, truth):
    """earliest_date_for_full_payment: exact match, and days off when both set."""
    p, t = _norm(pred), _norm(truth)
    if not p and not t:
        return True, 0
    if not p or not t:
        return False, None
    if p == t:
        return True, 0
    try:
        return False, abs((pd.Timestamp(p) - pd.Timestamp(t)).days)
    except Exception:
        return False, None


def validate_spending_changes(value, profile, ds, user_id):
    """spending_changes_needed is scored on VALIDITY, not string equality: at
    most 3 actions, correct syntax, referencing real event_ids belonging to
    this user, in categories the user actually permits changing, and never a
    protected category."""
    v = _norm(value)
    problems = []
    if not v or v.lower() == "none":
        return problems
    actions = v.split("|")
    if len(actions) > 3:
        problems.append(f"{len(actions)} actions (max 3)")

    protect = {c.strip() for c in str(profile["expense_categories_to_protect"]).split("|") if c.strip()}
    can_reduce = {c.strip() for c in str(profile["expense_categories_user_is_willing_to_reduce"]).split("|") if c.strip() and c.strip() != "nan"}
    can_stop = {c.strip() for c in str(profile["expense_categories_user_is_willing_to_stop"]).split("|") if c.strip() and c.strip() != "nan"}
    user_ev = ds.events[ds.events["user_id"] == user_id]

    for a in actions:
        m_stop = re.fullmatch(r"stop:(\S+)", a)
        m_red = re.fullmatch(r"reduce_to:([^:]+):([0-9]+(?:\.[0-9]+)?)", a)
        if not (m_stop or m_red):
            problems.append(f"bad syntax: {a!r}")
            continue
        eid = (m_stop or m_red).group(1)
        row = user_ev[user_ev["event_id"] == eid]
        if row.empty:
            problems.append(f"{eid} not an event of {user_id}")
            continue
        cat = row.iloc[0]["category"]
        if cat in protect:
            problems.append(f"{eid} is protected ({cat})")
        if m_stop and cat not in can_stop:
            problems.append(f"stop:{eid} but {cat} not stoppable by user")
        if m_red and cat not in can_reduce:
            problems.append(f"reduce:{eid} but {cat} not reducible by user")
        if m_red:
            floor = row.iloc[0]["minimum_allowed_amount"]
            if pd.notna(floor) and float(m_red.group(2)) < float(floor) - 1e-6:
                problems.append(f"{eid} reduced below its minimum_allowed_amount")
    return problems


def check_explanation(text, pred, request, home_ccy):
    """decision_explanation: 'useful and consistent'. Machine-checkable proxies
    -- non-empty, reasonable length, mentions the currency, states a concrete
    amount, doesn't contradict its own recommendation, no formatting artifacts."""
    problems = []
    t = _norm(text)
    if not t:
        return ["empty"]
    if len(t) < 25:
        problems.append("too short to be useful")
    if len(t) > 600:
        problems.append("overlong")
    if home_ccy and home_ccy not in t:
        problems.append("no currency named")
    if not re.search(r"\d", t):
        problems.append("no concrete figure")
    if re.search(r"e\+\d|nan|None|\{|\}", t):
        problems.append("formatting artifact")

    method = pred["recommended_payment_method"]
    low = t.lower()
    # The explanation must not recommend the opposite of the decision.
    if method == "not_recommended" and re.search(r"\bpay .{0,18}\bin full\b", low):
        problems.append("says pay in full but method is not_recommended")
    if method == "wait" and "wait" not in low:
        problems.append("method is wait but explanation never says so")
    if method == "installments" and "installment" not in low:
        problems.append("method is installments but explanation never says so")
    if pred["spending_changes_needed"] not in ("", "none") and not re.search(
            r"stop|reduc|cut|cancel|pause|trim", low):
        problems.append("spending change required but not explained")
    return problems


def main():
    verbose = "-v" in sys.argv
    ds = load()
    overrides = evidence.build_overrides(ds)
    samples = ds.sample_requests
    n = len(samples)

    status_ok = method_ok = plan_ok = 0
    amt_exact = amt_1pct = amt_5pct = 0
    amt_errs = []
    date_ok = 0
    date_offs = []
    sc_valid = 0
    sc_problems = []
    exp_clean = 0
    exp_problems = []
    plan_sums_ok = 0
    rows = []

    for _, r in samples.iterrows():
        pred = decide_one(ds, r, overrides)
        profile = ds.profiles[ds.profiles["user_id"] == r["user_id"]].iloc[0]
        home_ccy = profile["home_currency"]

        ok_s = pred["affordability_status"] == r["affordability_status"]
        ok_m = pred["recommended_payment_method"] == r["recommended_payment_method"]
        ok_p = _norm(pred["payment_plan"]) == _norm(r["payment_plan"])
        status_ok += ok_s
        method_ok += ok_m
        plan_ok += ok_p

        err, e0, e1, e5 = score_amount(float(pred["amount_safe_to_pay"]), float(r["amount_safe_to_pay"]))
        amt_errs.append(err)
        amt_exact += e0
        amt_1pct += e1
        amt_5pct += e5

        d_ok, d_off = score_date(pred["earliest_date_for_full_payment"], r["earliest_date_for_full_payment"])
        date_ok += d_ok
        if d_off:
            date_offs.append(d_off)

        scp = validate_spending_changes(pred["spending_changes_needed"], profile, ds, r["user_id"])
        sc_valid += not scp
        if scp:
            sc_problems.append((r["request_id"], scp))

        exp = check_explanation(pred["decision_explanation"], pred, r, home_ccy)
        exp_clean += not exp
        if exp:
            exp_problems.append((r["request_id"], exp))

        # payment_plan internal consistency: payments must total requested_amount
        pay = _parse_plan(pred["payment_plan"])
        if pred["recommended_payment_method"] in ("full_payment", "partial_payment"):
            plan_sums_ok += abs(sum(a for _, a in pay) - float(r["requested_amount"])) < 0.02
        else:
            plan_sums_ok += 1

        rows.append((r["request_id"], ok_s, ok_m, ok_p, err, d_ok, not scp, not exp))

    if verbose:
        print(f"{'request':>12} {'stat':>5} {'meth':>5} {'plan':>5} {'amt_err':>9} {'date':>5} {'sc':>4} {'expl':>5}")
        for rid, s, m, p, e, d, sc, ex in rows:
            print(f"{rid:>12} {'ok' if s else 'MISS':>5} {'ok' if m else 'MISS':>5} "
                  f"{'ok' if p else 'miss':>5} {e:>9.4f} {'ok' if d else 'MISS':>5} "
                  f"{'ok' if sc else 'BAD':>4} {'ok' if ex else 'BAD':>5}")
        print()

    mean_err = sum(amt_errs) / len(amt_errs)
    median_err = sorted(amt_errs)[len(amt_errs) // 2]

    print("=" * 62)
    print(f"  Scored against {n} solved samples -- all six criteria")
    print("=" * 62)
    print(f"1. amount_safe_to_pay      exact {amt_exact}/{n}   <=1% {amt_1pct}/{n}   <=5% {amt_5pct}/{n}")
    print(f"                           mean rel err {mean_err:.4f}   median {median_err:.4f}")
    print(f"2. affordability_status    {status_ok}/{n}")
    print(f"3. recommended_method      {method_ok}/{n}      payment_plan exact {plan_ok}/{n}")
    print(f"                           plan totals correct {plan_sums_ok}/{n}")
    print(f"4. earliest_date           {date_ok}/{n}" + (f"   (mean {sum(date_offs)/len(date_offs):.0f}d off when wrong)" if date_offs else ""))
    print(f"5. spending_changes valid  {sc_valid}/{n}")
    print(f"6. explanation clean       {exp_clean}/{n}")
    print("=" * 62)

    if sc_problems:
        print("\nspending_changes_needed problems:")
        for rid, ps in sc_problems:
            print(f"  {rid}: {'; '.join(ps)}")
    if exp_problems:
        print("\ndecision_explanation problems:")
        for rid, ps in exp_problems:
            print(f"  {rid}: {'; '.join(ps)}")


if __name__ == "__main__":
    main()
