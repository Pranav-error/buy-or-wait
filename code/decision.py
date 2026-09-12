"""Core decision logic: builds and ranks eligible safe payment plans for one
request, following problem_statement.md 'Choosing Between Safe Plans'.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from events import build_ledger, detect_recurring_patterns, LedgerItem
from forecast import build_forecast, amount_safe_today, earliest_safe_date_for_full_payment, schedule_is_safe

EPS = 1e-6


def _fmt_amount(a: float) -> str:
    r = round(a, 2)
    if abs(r - round(r)) < 1e-9:
        return str(int(round(r)))
    return f"{r:.2f}"


def _split(s) -> set:
    if s is None or (isinstance(s, float)):
        return set()
    s = str(s).strip()
    if not s or s.lower() == "nan":
        return set()
    return set(x.strip() for x in s.split("|") if x.strip())


@dataclass
class Candidate:
    method: str
    status: str
    payments: list  # list of (date, amount)
    earliest_date_field: object  # what earliest_date_for_full_payment should read (baseline, unmodified by this candidate)
    payment_option_id: str = ""
    meets_deadline: bool = True
    uses_spending_change: bool = False

    @property
    def total_paid(self):
        return sum(a for _, a in self.payments)

    @property
    def start_date(self):
        return self.payments[0][0] if self.payments else None

    @property
    def n_payments(self):
        return len(self.payments)

    def plan_str(self):
        if not self.payments:
            return "none"
        return "|".join(f"{d.isoformat()}:{_fmt_amount(a)}" for d, a in self.payments)

    def rank_key(self):
        opt_num = 0
        if self.payment_option_id:
            try:
                opt_num = int(self.payment_option_id.split("_")[-1])
            except Exception:
                opt_num = 0
        return (
            0 if self.meets_deadline else 1,
            0 if not self.uses_spending_change else 1,
            round(self.total_paid, 2),
            self.start_date or dt.date.max,
            self.n_payments,
            opt_num,
        )


def build_candidates(profile, request, payment_options_rows, ledger, current_balance, min_balance,
                      horizon_end, baseline_amt_safe, baseline_earliest, uses_spending_change=False):
    accepted = _split(profile["payment_methods_user_will_consider"])
    request_date = request["request_date"]
    desired = request["desired_completion_date"]
    requested_amount = float(request["requested_amount"])
    allows_partial = str(request["allows_partial_payment"]).strip().lower() == "true"

    candidates = []
    fc = build_forecast(current_balance, ledger, request_date, horizon_end)
    amt_safe = amount_safe_today(fc, min_balance, requested_amount)
    earliest = earliest_safe_date_for_full_payment(fc, min_balance, requested_amount)

    # A plan reached only because spending changes freed up cash is, by
    # definition, "completed... using permitted spending changes" -- always
    # affordable_with_plan, regardless of which payment method it uses.
    def status_for(natural_status):
        return "affordable_with_plan" if uses_spending_change else natural_status

    if "full_payment" in accepted and amt_safe >= requested_amount - EPS:
        candidates.append(Candidate(
            method="full_payment", status=status_for("affordable_now"),
            payments=[(request_date, requested_amount)],
            earliest_date_field=baseline_earliest, meets_deadline=True,
            uses_spending_change=uses_spending_change,
        ))

    if "full_payment" in accepted and earliest is not None and earliest > request_date:
        candidates.append(Candidate(
            method="wait", status=status_for("affordable_later"),
            payments=[(earliest, requested_amount)],
            earliest_date_field=baseline_earliest,
            meets_deadline=(earliest <= desired) if desired else True,
            uses_spending_change=uses_spending_change,
        ))

    if (allows_partial and "partial_payment" in accepted and 0 < amt_safe < requested_amount - EPS):
        # The remainder is a smaller amount than the full requested_amount,
        # so its own earliest-safe date (computed on the forecast *after*
        # the first payment is already deducted) can be defined -- and
        # earlier -- even when earliest_safe_date_for_full_payment(...,
        # requested_amount) above found no safe date for the ORIGINAL full
        # amount within the horizon.
        remainder = requested_amount - amt_safe
        fc_after_first_payment = build_forecast(current_balance - amt_safe, ledger, request_date, horizon_end)
        remainder_earliest = earliest_safe_date_for_full_payment(fc_after_first_payment, min_balance, remainder)
        if remainder_earliest is not None and remainder_earliest <= desired:
            candidates.append(Candidate(
                method="partial_payment", status=status_for("affordable_with_plan"),
                payments=[(request_date, amt_safe), (remainder_earliest, remainder)],
                earliest_date_field=baseline_earliest, meets_deadline=True,
                uses_spending_change=uses_spending_change,
            ))

    if "installments" in accepted:
        max_months = profile["max_installment_months"]
        max_months = float(max_months) if str(max_months).strip() not in ("", "nan", "None") else None
        for _, opt in payment_options_rows.iterrows():
            if opt["payment_method"] != "installments":
                continue
            n = int(opt["number_of_payments"])
            freq = float(opt["payment_frequency_days"])
            first = opt["first_payment_date"]
            amt = float(opt["payment_amount"])
            schedule = [(first + dt.timedelta(days=round(freq * k)), amt) for k in range(n)]
            last_date = schedule[-1][0]
            duration_months = ((n - 1) * freq) / 30.44 if n > 1 else 0
            if max_months is not None and duration_months > max_months + 1e-6:
                continue
            ext_end = max(horizon_end, last_date)
            safe = schedule_is_safe(ledger, current_balance, request_date, ext_end, min_balance, schedule)
            if not safe:
                continue
            candidates.append(Candidate(
                method="installments", status="affordable_with_plan",
                payments=schedule, payment_option_id=opt["payment_option_id"],
                earliest_date_field=baseline_earliest,
                meets_deadline=(last_date <= desired) if desired else True,
                uses_spending_change=uses_spending_change,
            ))

    return candidates, amt_safe, earliest


def pick_flexible_reduction_candidates(profile, patterns, horizon_start, horizon_end):
    protect = _split(profile["expense_categories_to_protect"])
    willing_reduce = _split(profile["expense_categories_user_is_willing_to_reduce"])
    willing_stop = _split(profile["expense_categories_user_is_willing_to_stop"])
    actions = []
    for p in patterns:
        if p.direction != "debit" or p.category in protect:
            continue
        if p.category in willing_stop and p.flexibility in ("stoppable", "reducible_or_stoppable"):
            actions.append(("stop", p, p.avg_amount))
        if p.category in willing_reduce and p.flexibility in ("reducible", "reducible_or_stoppable"):
            floor = p.minimum_allowed_amount if p.minimum_allowed_amount is not None else 0.0
            freed = max(0.0, p.avg_amount - floor)
            if freed > 0:
                actions.append(("reduce", p, freed))
    actions.sort(key=lambda a: -a[2])
    return actions


def apply_action_to_ledger(ledger, action):
    kind, pattern, _ = action
    new_ledger = []
    for it in ledger:
        if it.category == pattern.category and it.source == "recurring_projection":
            if kind == "stop":
                continue
            if kind == "reduce":
                floor = pattern.minimum_allowed_amount if pattern.minimum_allowed_amount is not None else 0.0
                sign = 1 if it.amount_home > 0 else -1
                it = LedgerItem(date=it.date, amount_home=-floor, source=it.source, event_id=it.event_id,
                                 category=it.category, flexibility=it.flexibility,
                                 minimum_allowed_amount=it.minimum_allowed_amount, description=it.description)
        new_ledger.append(it)
    return new_ledger


def action_str(kind, pattern):
    if kind == "stop":
        return f"stop:{pattern.sample_event_id}"
    floor = pattern.minimum_allowed_amount if pattern.minimum_allowed_amount is not None else 0.0
    return f"reduce_to:{pattern.sample_event_id}:{_fmt_amount(floor)}"
