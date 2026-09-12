"""Per-user event resolution: currency normalization, recurrence detection,
and construction of the forward-looking cash-flow ledger used by forecast.py.

Historical `financial_events.csv` rows are dated at or before the user's
request_date; `current_available_balance` in the profile already reflects all
settled cash up to that point. So historical events are only used to (a)
detect recurring expense patterns to project forward and (b) resolve
evidence (blank amounts, flexibility, protection). Only events dated *after*
request_date, plus projected recurring occurrences, feed the 90-day forecast.
"""

from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass

import pandas as pd

from loader import Dataset

CASH_STATUSES_HISTORICAL = {"settled"}
CASH_STATUSES_FUTURE_COMMITTED = {"scheduled", "pending"}
EXCLUDED_STATUSES = {"cancelled", "failed", "unrealized"}

RECURRING_EVENT_TYPES = {"expense", "subscription", "debt_payment", "income"}
MIN_OCCURRENCES_FOR_RECURRENCE = int(os.environ.get("BOW_MIN_OCC", "3"))
CADENCE_TOLERANCE = float(os.environ.get("BOW_CADENCE_TOL", "0.35"))  # relative std/median tolerance on inter-event gaps

# How many recent occurrences of a recurring category feed the conservative
# amount estimate (max for debits, min for credits). Overridable via env var
# purely so code/evaluation/sweep.py can calibrate it against sample_requests.
RECENCY_WINDOW = int(os.environ.get("BOW_RECENCY_WINDOW", "3"))

# A recent debit above this multiple of its category's historical median is
# treated as a one-off spike (a bulk purchase), not the new normal, and is
# excluded from the conservative recurring estimate. Calibrated by sweep.py.
SPIKE_OUTLIER_FACTOR = float(os.environ.get("BOW_SPIKE_FACTOR", "2.5"))


@dataclass
class RecurringPattern:
    user_id: str
    category: str
    event_type: str
    direction: str
    cadence_days: float
    avg_amount: float
    last_date: dt.date
    flexibility: str
    minimum_allowed_amount: float | None
    sample_event_id: str


@dataclass
class LedgerItem:
    date: dt.date
    amount_home: float  # signed: +credit, -debit
    source: str  # 'explicit' or 'recurring_projection' or 'evidence'
    event_id: str | None
    category: str | None
    flexibility: str | None
    minimum_allowed_amount: float | None
    description: str


def user_events(ds: Dataset, user_id: str) -> pd.DataFrame:
    return ds.events[ds.events["user_id"] == user_id]


def resolve_amount_home(ds: Dataset, row, home_ccy: str, amount_override: float | None = None) -> float:
    amt = row["amount"] if amount_override is None else amount_override
    date = row["settlement_date"] or row["event_date"]
    return ds.to_home(float(amt), row["currency"], home_ccy, date)


def detect_recurring_patterns(ds: Dataset, user_id: str, home_ccy: str, as_of: dt.date,
                               amount_overrides: dict[str, float],
                               recurring_overrides: dict[str, float] | None = None) -> list[RecurringPattern]:
    recurring_overrides = recurring_overrides or {}
    ev = user_events(ds, user_id)
    ev = ev[ev["event_type"].isin(RECURRING_EVENT_TYPES)]
    ev = ev[ev["status"] == "settled"]
    ev = ev[ev["event_date"] <= as_of]
    patterns: list[RecurringPattern] = []
    for (category, direction), grp in ev.groupby(["category", "direction"]):
        if category == "salary":
            continue  # handled separately below: too few settled rows for the generic path
        grp = grp.sort_values("event_date")
        if len(grp) < MIN_OCCURRENCES_FOR_RECURRENCE:
            continue
        dates = list(grp["event_date"])
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        if not gaps:
            continue
        gaps_series = pd.Series(gaps)
        median_gap = gaps_series.median()
        if median_gap <= 0:
            continue
        spread = (gaps_series - median_gap).abs().median()
        if spread / median_gap > CADENCE_TOLERANCE:
            continue  # too irregular to call recurring
        # Robust baseline: the typical scale of this category across its whole
        # history, used below to recognise one-off spikes.
        all_amounts = [
            resolve_amount_home(ds, r, home_ccy, amount_overrides.get(r["event_id"]))
            for _, r in grp.iterrows()
        ]
        median_amount = pd.Series(all_amounts).median()

        recent = grp.tail(RECENCY_WINDOW)
        amounts_home = []
        for _, r in recent.iterrows():
            override = amount_overrides.get(r["event_id"])
            amounts_home.append(resolve_amount_home(ds, r, home_ccy, override))
        # Conservative forecasting: assume the worse case for essential
        # variable spending (the highest recent expense), not an average.
        #
        # But "conservative" means the worst *typical* cycle, not "assume every
        # future cycle repeats an exceptional one-off". A single bulk purchase
        # (e.g. a stock-up grocery run, often the very row whose blank amount
        # was resolved from a receipt image) can sit many multiples above the
        # category's normal level; projecting it forward every cycle drains the
        # forecast by a large factor and wrongly rejects affordable requests.
        # So for debits, ignore recent occurrences that are extreme outliers
        # against the category's own historical median -- provided at least one
        # normal occurrence remains to anchor the estimate.
        if direction == "debit" and median_amount and median_amount > 0:
            typical = [a for a in amounts_home if a <= median_amount * SPIKE_OUTLIER_FACTOR]
            if typical:
                amounts_home = typical
        avg_amount = max(amounts_home) if direction == "debit" else min(amounts_home)
        last_row = grp.iloc[-1]
        last_date = last_row["event_date"]

        # Anchor to an already-explicit future occurrence (e.g. the one
        # "next confirmed salary" row) if present, so recurring projection
        # resumes after it instead of duplicating it.
        future = user_events(ds, user_id)
        future = future[
            (future["category"] == category)
            & (future["direction"] == direction)
            & (future["status"].isin(CASH_STATUSES_FUTURE_COMMITTED))
            & (future["event_date"] > as_of)
        ]
        if not future.empty:
            future_row = future.sort_values("event_date").iloc[-1]
            last_date = max(last_date, future_row["event_date"])
            if category == "salary":
                # Base future salary cycles on the confirmed upcoming amount,
                # not an average that includes a prorated first paycheck.
                override = amount_overrides.get(future_row["event_id"])
                avg_amount = resolve_amount_home(ds, future_row, home_ccy, override)

        if category in recurring_overrides:
            # Evidence (a message/image) confirmed a new go-forward amount for
            # this recurring category (e.g. a raise, a temporary reduction
            # still in effect, or a household income change) that isn't yet
            # reflected in any dated event row.
            avg_amount = recurring_overrides[category]

        patterns.append(
            RecurringPattern(
                user_id=user_id,
                category=category,
                event_type=last_row["event_type"],
                direction=direction,
                cadence_days=median_gap,
                avg_amount=avg_amount,
                last_date=last_date,
                flexibility=last_row["flexibility"],
                minimum_allowed_amount=(
                    float(last_row["minimum_allowed_amount"])
                    if pd.notna(last_row["minimum_allowed_amount"])
                    else None
                ),
                sample_event_id=last_row["event_id"],
            )
        )

    # Salary: usually only one settled historical row plus one explicit
    # "next confirmed salary" scheduled row exists, so it fails the generic
    # >=3-occurrence check. Two confirmed points already establish a monthly
    # cadence, so treat it as recurring and project future cycles from the
    # confirmed (not prorated) amount.
    all_salary = user_events(ds, user_id)
    all_salary = all_salary[
        (all_salary["category"] == "salary")
        & (~all_salary["status"].isin(EXCLUDED_STATUSES))
        & ((all_salary["event_date"] <= as_of) | (all_salary["status"].isin(CASH_STATUSES_FUTURE_COMMITTED)))
    ].sort_values("event_date")
    if len(all_salary) >= 2:
        dates = list(all_salary["event_date"])
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        median_gap = pd.Series(gaps).median()
        # A same-category row spaced much closer to its predecessor than the
        # established cadence (e.g. a one-off arrears/bonus/commission
        # payment shortly after the regular payroll credit) is not the next
        # regular cycle -- walk back to the most recent row that IS properly
        # spaced, so it anchors the projected amount/cadence instead.
        last_idx = len(all_salary) - 1
        if median_gap > 0:
            while last_idx > 0 and (dates[last_idx] - dates[last_idx - 1]).days < 0.5 * median_gap:
                last_idx -= 1
        last_row = all_salary.iloc[last_idx]
        if median_gap > 0:
            override = amount_overrides.get(last_row["event_id"])
            avg_amount = resolve_amount_home(ds, last_row, home_ccy, override)
            # NOTE: projecting variable gig/platform income at a low percentile
            # of its own history (rather than at the most recent payout) was
            # tried and measured -- see evaluation/CALIBRATION.md. It made
            # sample accuracy worse at the 0th and 25th percentile and made no
            # difference at the median, so it is deliberately not done.
            if "salary" in recurring_overrides:
                avg_amount = recurring_overrides["salary"]
            patterns.append(
                RecurringPattern(
                    user_id=user_id,
                    category="salary",
                    event_type="income",
                    direction="credit",
                    cadence_days=median_gap,
                    avg_amount=avg_amount,
                    last_date=last_row["event_date"],
                    flexibility=last_row["flexibility"],
                    minimum_allowed_amount=None,
                    sample_event_id=last_row["event_id"],
                )
            )
    return patterns


def _add_months(d: dt.date, k: int) -> dt.date:
    """d plus k calendar months, keeping the day-of-month where possible and
    clamping to the last valid day otherwise (31 Jan + 1 month -> 28/29 Feb)."""
    month_index = d.month - 1 + k
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    if month == 12:
        next_month_start = dt.date(year + 1, 1, 1)
    else:
        next_month_start = dt.date(year, month + 1, 1)
    days_in_month = (next_month_start - dt.timedelta(days=1)).day
    return dt.date(year, month, min(d.day, days_in_month))


def _nth_occurrence(anchor: dt.date, cadence_days: float, k: int) -> dt.date:
    """The k-th projected occurrence after `anchor`.

    Salaries, rent, subscriptions and most bills recur on a *calendar* schedule
    -- "the 15th of every month" -- not every N days. Stepping by a fixed
    round(cadence) drifts: a monthly series anchored on the 15th with a 30-day
    median gap lands on the 14th, then the 13th, then the 12th. Over a 90-day
    window that misplaces every payday by up to several days, which corrupts
    `earliest_date_for_full_payment` directly and can slide an extra income
    cycle inside the horizon, inflating `amount_safe_to_pay`.

    So a monthly-ish cadence advances by calendar month; sub-monthly cadences
    (weekly, fortnightly) genuinely are fixed-interval and keep day arithmetic.
    """
    if 26 <= cadence_days <= 32:
        return _add_months(anchor, k)
    if 58 <= cadence_days <= 63:
        return _add_months(anchor, 2 * k)
    if 88 <= cadence_days <= 95:
        return _add_months(anchor, 3 * k)
    return anchor + dt.timedelta(days=round(cadence_days) * k)


def project_recurring(pattern: RecurringPattern, start: dt.date, end: dt.date) -> list[LedgerItem]:
    items = []
    sign = 1 if pattern.direction == "credit" else -1
    n = 0
    k = 1
    next_date = _nth_occurrence(pattern.last_date, pattern.cadence_days, k)
    while next_date <= end and n < 400:
        if next_date > start:
            items.append(
                LedgerItem(
                    date=next_date,
                    amount_home=sign * pattern.avg_amount,
                    source="recurring_projection",
                    event_id=None,
                    category=pattern.category,
                    flexibility=pattern.flexibility,
                    minimum_allowed_amount=pattern.minimum_allowed_amount,
                    description=f"projected {pattern.category} ({pattern.event_type})",
                )
            )
        k += 1
        n += 1
        next_date = _nth_occurrence(pattern.last_date, pattern.cadence_days, k)
    return items


def explicit_future_items(ds: Dataset, user_id: str, home_ccy: str, start: dt.date, end: dt.date,
                           amount_overrides: dict[str, float],
                           exclude_event_ids: set[str]) -> list[LedgerItem]:
    ev = user_events(ds, user_id)
    ev = ev[~ev["status"].isin(EXCLUDED_STATUSES)]
    ev = ev[ev["status"].isin(CASH_STATUSES_FUTURE_COMMITTED)]
    items = []
    for _, r in ev.iterrows():
        if r["event_id"] in exclude_event_ids:
            continue
        # "Reserve pending debits. Do not count pending credits, bonuses,
        # commissions, refunds, lottery proceeds, or investment gains until
        # they settle." A *pending* inbound row is money that has not arrived
        # and may never arrive, so it never enters the forecast. A *scheduled*
        # credit is different -- that is the confirmed upcoming salary, which
        # the spec says to count on its settlement date.
        if r["direction"] == "credit" and r["status"] == "pending":
            continue
        date = r["settlement_date"] or r["event_date"]
        if date is None or date > end:
            continue
        if date <= start:
            # A pending debit dated at or before the request has not settled,
            # so `current_available_balance` does not reflect it -- but the
            # money is already committed and will leave. Reserve it at the
            # front of the window rather than dropping it.
            if r["status"] != "pending":
                continue
            date = start + dt.timedelta(days=1)
        override = amount_overrides.get(r["event_id"])
        amt = resolve_amount_home(ds, r, home_ccy, override)
        sign = 1 if r["direction"] == "credit" else -1
        items.append(
            LedgerItem(
                date=date,
                amount_home=sign * amt,
                source="explicit",
                event_id=r["event_id"],
                category=r["category"],
                flexibility=r["flexibility"],
                minimum_allowed_amount=(
                    float(r["minimum_allowed_amount"]) if pd.notna(r["minimum_allowed_amount"]) else None
                ),
                description=r["description"],
            )
        )
    return items


def build_ledger(ds: Dataset, user_id: str, home_ccy: str, as_of: dt.date, horizon_end: dt.date,
                  amount_overrides: dict[str, float] | None = None,
                  exclude_event_ids: set[str] | None = None,
                  extra_items: list[LedgerItem] | None = None,
                  recurring_overrides: dict[str, float] | None = None) -> list[LedgerItem]:
    amount_overrides = amount_overrides or {}
    exclude_event_ids = exclude_event_ids or set()
    items = explicit_future_items(ds, user_id, home_ccy, as_of, horizon_end, amount_overrides, exclude_event_ids)
    patterns = detect_recurring_patterns(ds, user_id, home_ccy, as_of, amount_overrides, recurring_overrides)
    covered_categories = set()
    for it in items:
        if it.category:
            covered_categories.add((it.category, it.amount_home > 0))
    for p in patterns:
        items.extend(project_recurring(p, as_of, horizon_end))
    if extra_items:
        items.extend(extra_items)
    items.sort(key=lambda x: x.date)
    return items
