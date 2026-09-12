"""Regression tests. Each one pins a specific defect found while calibrating
against dataset/sample_requests.csv, so a future change can't silently
reintroduce it. Run with:  ../.venv/bin/python -m pytest code/tests -q
"""

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loader import load
from events import detect_recurring_patterns, build_ledger
from forecast import build_forecast, amount_safe_today, earliest_safe_date_for_full_payment
from decision import _fmt_amount
from main import decide_one
import evidence

DS = load()
OVERRIDES = evidence.build_overrides(DS)


def test_salary_recurs_from_only_two_confirmed_points():
    """Defect: salary needs >=3 settled rows under the generic recurrence
    rule, but most users only have one settled row plus the one explicit
    'next confirmed salary' scheduled row. Without treating that as
    recurring, essential expenses drain every balance with no offsetting
    income and the engine falsely calls everything not_affordable."""
    patterns = detect_recurring_patterns(DS, "user_01", "ZAR", dt.date(2024, 3, 3), {})
    salary = [p for p in patterns if p.category == "salary"]
    assert salary, "expected a recurring salary pattern from 2 confirmed points"
    assert salary[0].avg_amount == 23320.0, "must use the confirmed amount, not an average with the prorated first paycheck"


def test_expense_projection_is_conservative_not_average():
    """Defect: averaging recent expense amounts is not the 'forecast
    essential variable spending conservatively' the spec asks for; it must
    skew toward the recent maximum for expenses (and minimum for income)."""
    patterns = detect_recurring_patterns(DS, "user_21", "USD", dt.date(2026, 4, 3), {})
    dining = [p for p in patterns if p.category == "dining"][0]
    # recent 3 dining amounts were 97.67, 98.39, 69.31 -> conservative = max = 98.39
    assert dining.avg_amount == 98.39


def test_no_scientific_notation_in_amounts():
    """Defect: Python's `:g` format spec silently switched large payment
    amounts to scientific notation (e.g. '1.5656e+07'), which is not a
    valid amount in the payment_plan/spending_changes_needed grammar."""
    assert "e+" not in _fmt_amount(15656000.0)
    assert _fmt_amount(15656000.0) == "15656000"
    assert _fmt_amount(268.735) == "268.73" or _fmt_amount(268.735) == "268.74"


def test_amount_safe_to_pay_bounds_hold_across_all_requests():
    for _, r in DS.requests.iterrows():
        pred = decide_one(DS, r, OVERRIDES)
        amt = pred["amount_safe_to_pay"]
        assert -1e-6 <= amt <= float(r["requested_amount"]) + 1e-6, r["request_id"]


def test_spending_change_always_implies_affordable_with_plan():
    """Defect: a 'wait' plan that only became safe because spending changes
    freed up cash was tagged affordable_later (the natural status for plain
    wait), but the spec defines affordable_with_plan as completion via "a
    partial-payment schedule, installments, or permitted spending changes" --
    any method reached through spending changes must report that status."""
    found_one = False
    for _, r in DS.requests.iterrows():
        pred = decide_one(DS, r, OVERRIDES)
        if pred["spending_changes_needed"] != "none":
            found_one = True
            assert pred["affordability_status"] == "affordable_with_plan", r["request_id"]
    assert found_one, "expected at least one request to require spending changes"


def test_one_output_row_per_request_no_crash():
    ids = set()
    for _, r in DS.requests.iterrows():
        pred = decide_one(DS, r, OVERRIDES)
        ids.add(pred["request_id"])
    assert ids == set(DS.requests["request_id"])


def test_installment_plan_always_matches_a_supplied_option():
    opts = DS.payment_options
    for _, r in DS.requests.iterrows():
        pred = decide_one(DS, r, OVERRIDES)
        if pred["recommended_payment_method"] != "installments":
            continue
        row_opts = opts[(opts["request_id"] == r["request_id"]) & (opts["payment_method"] == "installments")]
        found = False
        for _, o in row_opts.iterrows():
            n = int(o["number_of_payments"])
            freq = float(o["payment_frequency_days"])
            first = o["first_payment_date"]
            amt = float(o["payment_amount"])
            schedule = "|".join(
                f"{(first + dt.timedelta(days=round(freq * k))).isoformat()}:{_fmt_amount(amt)}" for k in range(n)
            )
            if schedule == pred["payment_plan"]:
                found = True
                break
        assert found, f"{r['request_id']}: installments plan does not match any supplied option"


def test_sample_calibration_does_not_regress():
    """Guard rail: with the evidence cache populated (message/image evidence
    extracted by Claude Code agents into code/.cache/evidence/, including
    recurring_overrides for salary changes/reductions/household-income
    changes), the engine matches 20/25 affordability_status and 22/25
    recommended_payment_method on the solved sample_requests.csv. A future
    change should not drop below that without a deliberate, understood
    reason. evaluation/main.py scores all six criteria; this is the floor for
    the two that are pure label matches."""
    status_match = 0
    method_match = 0
    for _, r in DS.sample_requests.iterrows():
        pred = decide_one(DS, r, OVERRIDES)
        status_match += pred["affordability_status"] == r["affordability_status"]
        method_match += pred["recommended_payment_method"] == r["recommended_payment_method"]
    assert status_match >= 20, f"status_match regressed to {status_match}/25"
    assert method_match >= 22, f"method_match regressed to {method_match}/25"


def test_monthly_recurrence_uses_calendar_months_not_30_day_steps():
    """A monthly series anchored on the 15th must keep landing on the 15th.
    Stepping by round(median_gap) days drifts it to the 14th, then the 13th,
    which misplaces every payday and corrupts earliest_date_for_full_payment."""
    from events import project_recurring, RecurringPattern
    p = RecurringPattern(user_id="u", category="salary", event_type="income",
                         direction="credit", cadence_days=30.0, avg_amount=1000.0,
                         last_date=dt.date(2025, 1, 15), flexibility=None,
                         minimum_allowed_amount=None, sample_event_id="e1")
    dates = [i.date for i in project_recurring(p, dt.date(2025, 1, 16), dt.date(2025, 6, 30))]
    assert dates == [dt.date(2025, m, 15) for m in (2, 3, 4, 5, 6)], dates


def test_month_end_anchor_clamps_instead_of_overflowing():
    """31 Jan + 1 month has no 31 Feb; it must clamp to the last valid day."""
    from events import _add_months
    assert _add_months(dt.date(2025, 1, 31), 1) == dt.date(2025, 2, 28)
    assert _add_months(dt.date(2024, 1, 31), 1) == dt.date(2024, 2, 29)  # leap year
    assert _add_months(dt.date(2025, 12, 15), 1) == dt.date(2026, 1, 15)


def test_pending_credits_are_never_counted_but_pending_debits_are_reserved():
    """problem_statement.md: 'Reserve pending debits. Do not count pending
    credits ... until they settle.' user_20 has one of each around its
    request date."""
    from events import explicit_future_items
    start, end = dt.date(2026, 2, 7), dt.date(2026, 5, 8)
    items = explicit_future_items(DS, "user_20", "INR", start, end,
                                  OVERRIDES.get("user_20", {}).get("amount_overrides", {}), set())
    ids = {i.event_id for i in items}
    assert "event_1785" not in ids, "pending credit was counted as income"
    assert "event_1787" in ids, "pending debit was not reserved"
    assert all(i.amount_home < 0 for i in items if i.event_id in ("event_1786", "event_1787"))


def test_refusal_explanation_states_a_real_and_correct_reason():
    """'usefulness and consistency of decision_explanation' is a scored
    criterion. A refusal must name the currency, a figure, and the actual
    blocking reason -- never claim cash flow is the problem when the money is
    there and it is the user's payment preferences that block it."""
    r = DS.sample_requests[DS.sample_requests["request_id"] == "request_10"].iloc[0]
    text = decide_one(DS, r, OVERRIDES)["decision_explanation"]
    assert "INR" in text and any(c.isdigit() for c in text)
    assert "methods you accept" in text, text
    assert "Committed expenses" not in text, "blamed cash flow when cash was sufficient"
