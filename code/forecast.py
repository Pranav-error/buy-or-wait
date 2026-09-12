"""90-day balance forecasting: baseline path, safe-amount-today, and
earliest-safe-date for a given target amount, plus schedule safety checks.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from events import LedgerItem

EPS = 1e-6


@dataclass
class Forecast:
    dates: list  # sorted unique dates with an event, ascending
    cum_balance: list  # balance right after processing all events on that date
    start_balance: float
    start_date: dt.date
    end_date: dt.date

    def global_min(self) -> float:
        if not self.cum_balance:
            return self.start_balance
        return min([self.start_balance] + self.cum_balance)


def build_forecast(start_balance: float, ledger_items: list[LedgerItem], start_date: dt.date,
                    end_date: dt.date) -> Forecast:
    by_date: dict[dt.date, float] = {}
    for it in ledger_items:
        if start_date < it.date <= end_date:
            by_date[it.date] = by_date.get(it.date, 0.0) + it.amount_home
    dates = sorted(by_date.keys())
    cum = []
    running = start_balance
    for d in dates:
        # Same-day events are netted. Applying that day's debits before its
        # credits (the more conservative reading) was tested and scored worse
        # -- see evaluation/CALIBRATION.md.
        running += by_date[d]
        cum.append(running)
    return Forecast(dates=dates, cum_balance=cum, start_balance=start_balance,
                     start_date=start_date, end_date=end_date)


def amount_safe_today(fc: Forecast, min_balance: float, requested_amount: float) -> float:
    uncapped = fc.global_min() - min_balance
    return max(0.0, min(requested_amount, uncapped))


def earliest_safe_date_for_full_payment(fc: Forecast, min_balance: float, requested_amount: float):
    """Earliest T in [start_date, end_date] such that min balance over
    [T, end_date] minus requested_amount stays >= min_balance. Returns None
    if never safe within the forecast horizon."""
    threshold = min_balance + requested_amount
    # Check start_date first (covers the whole window == global_min).
    if fc.global_min() >= threshold - EPS:
        return fc.start_date
    n = len(fc.dates)
    # suffix min of cum_balance from position i to end
    suffix = [0.0] * (n + 1)
    suffix[n] = float("inf")
    for i in range(n - 1, -1, -1):
        suffix[i] = min(fc.cum_balance[i], suffix[i + 1])
    for i, d in enumerate(fc.dates):
        window_min = suffix[i]
        if window_min >= threshold - EPS:
            return d
    return None


def schedule_is_safe(fc_ledger_items: list[LedgerItem], start_balance: float, start_date: dt.date,
                      end_date: dt.date, min_balance: float, schedule: list[tuple]) -> bool:
    """schedule: list of (date, debit_amount). Combines with baseline ledger
    and checks the balance never drops below min_balance at any event date
    within [start_date, end_date]."""
    combined = list(fc_ledger_items)
    for d, amt in schedule:
        combined.append(LedgerItem(date=d, amount_home=-amt, source="candidate_payment",
                                    event_id=None, category=None, flexibility=None,
                                    minimum_allowed_amount=None, description="candidate payment"))
    fc = build_forecast(start_balance, combined, start_date, end_date)
    return fc.global_min() >= min_balance - EPS
