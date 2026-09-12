"""Deterministic, template-based decision_explanation text.

Grounded in the actual computed numbers so the explanation stays consistent
across identical situations, at zero LLM cost.
"""

from __future__ import annotations


def fmt(amount, currency):
    r = round(amount, 2)
    if abs(r - round(r)) < 1e-9:
        return f"{currency} {int(round(r)):,}"
    return f"{currency} {r:,.2f}"


def explain(method, status, amount_safe, currency, min_balance, plan, desired, changes, evidence_notes,
            requested_amount=None, accepted_methods=None):
    parts = []
    if method == "full_payment":
        parts.append(f"Pay {fmt(plan.total_paid, currency)} in full on {plan.start_date}.")
        parts.append(f"This keeps at least {fmt(min_balance, currency)} available through the 90-day forecast.")
    elif method == "partial_payment":
        first, second = plan.payments
        parts.append(
            f"Pay {fmt(first[1], currency)} today ({first[0]}) and the remaining {fmt(second[1], currency)} "
            f"on {second[0]}."
        )
        parts.append(f"This keeps at least {fmt(min_balance, currency)} available throughout.")
    elif method == "installments":
        parts.append(
            f"Use {plan.n_payments} installments of {fmt(plan.payments[0][1], currency)} starting "
            f"{plan.start_date}, totaling {fmt(plan.total_paid, currency)}."
        )
        parts.append(f"This keeps the balance at or above {fmt(min_balance, currency)} at every step.")
    elif method == "wait":
        parts.append(
            f"Wait and pay the full {fmt(plan.total_paid, currency)} on {plan.start_date}, "
            f"once the balance can safely absorb it."
        )
    else:
        # A bare refusal is not a useful answer. Say how much *is* safe, name
        # the reserve the request would breach, and point at what would change
        # the outcome -- grounded entirely in the computed figures.
        cash_covers_it = (
            requested_amount is not None and amount_safe is not None
            and amount_safe >= requested_amount - 1e-6
        )
        if cash_covers_it:
            # The money is there; what blocks it is the user's own stated
            # payment preferences, so say that instead of blaming cash flow.
            allowed = ", ".join(sorted(accepted_methods)) if accepted_methods else "the accepted methods"
            parts.append(
                f"Not recommended: {fmt(requested_amount, currency)} would itself stay above the "
                f"{fmt(min_balance, currency)} you want to keep, but none of the payment options "
                f"offered for this request fit the methods you accept ({allowed})."
            )
        elif amount_safe and amount_safe > 0:
            parts.append(
                f"Not recommended right now: only {fmt(amount_safe, currency)} can be paid without "
                f"dropping below the {fmt(min_balance, currency)} you want to keep."
            )
            parts.append(
                "Committed expenses over the next 90 days use up the remaining headroom, so no full, "
                "partial or installment plan stays safe"
                + (f" by {desired}." if desired else " within the forecast.")
            )
        else:
            parts.append(
                f"Not recommended right now: no part of this can be paid without dropping below the "
                f"{fmt(min_balance, currency)} you want to keep."
            )
            parts.append(
                "Committed expenses over the next 90 days consume the available headroom"
                + (f" before {desired}." if desired else " within the forecast.")
            )

    if changes:
        change_desc = "; ".join(
            f"stopping {c[1].category}" if c[0] == "stop" else f"reducing {c[1].category} to its minimum"
            for c in changes
        )
        parts.append(f"This requires {change_desc} to free up enough cash.")

    if evidence_notes:
        parts.append(evidence_notes)

    return " ".join(parts)
