"""Hand-audit tool: for a list of real request_ids from dataset/requests.csv,
dumps the engine's decision alongside the underlying ledger facts (current
balance, min_balance, lowest projected balance in the 90-day horizon and on
what date, evidence applied) so each one can be independently verified by
inspection rather than trusted blindly. Read-only -- does not modify output.csv.
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loader import load
from events import build_ledger
from main import decide_one
import evidence

REQUEST_IDS = [
    'request_48', 'request_243', 'request_223', 'request_261', 'request_221',
    'request_160', 'request_84', 'request_218', 'request_148', 'request_88',
    'request_70', 'request_208', 'request_57', 'request_259', 'request_156',
    'request_263', 'request_76', 'request_129', 'request_63', 'request_119',
]


def main():
    ds = load()
    overrides = evidence.build_overrides(ds)
    for rid in REQUEST_IDS:
        r = ds.requests[ds.requests["request_id"] == rid].iloc[0]
        user_id = r["user_id"]
        profile = ds.profiles[ds.profiles["user_id"] == user_id].iloc[0]
        home_ccy = profile["home_currency"]
        bal = float(profile["current_available_balance"])
        minb = float(profile["minimum_balance_to_keep"])
        req_date = r["request_date"]
        horizon_end = req_date + dt.timedelta(days=90)

        amount_overrides = overrides.get(user_id, {}).get("amount_overrides", {})
        exclude_ids = overrides.get(user_id, {}).get("exclude_event_ids", set())
        extra_items = overrides.get(user_id, {}).get("extra_items", [])
        recurring_overrides = overrides.get(user_id, {}).get("recurring_overrides", {})
        has_evidence = bool(amount_overrides or exclude_ids or extra_items or recurring_overrides
                             or overrides.get(user_id, {}).get("note"))

        ledger = build_ledger(ds, user_id, home_ccy, req_date, horizon_end,
                               amount_overrides, exclude_ids, extra_items, recurring_overrides)
        running = bal
        low = bal
        low_date = req_date
        for item in ledger:
            running += item.amount_home
            if running < low:
                low = running
                low_date = item.date

        pred = decide_one(ds, r, overrides)

        print(f"=== {rid} | user={user_id} ccy={home_ccy} type={r['request_type']} "
              f"req_amt={r['requested_amount']} req_date={req_date} desired={r['desired_completion_date']} "
              f"allows_partial={r['allows_partial_payment']} evidence={has_evidence} ===")
        print(f"  balance={bal} min_balance={minb} headroom_now={round(bal-minb,2)} "
              f"lowest_over_90d={round(low,2)} on {low_date}")
        print(f"  -> status={pred['affordability_status']} method={pred['recommended_payment_method']} "
              f"amount_safe_to_pay={pred['amount_safe_to_pay']}")
        print(f"     plan={pred['payment_plan']}")
        print(f"     spending_changes={pred['spending_changes_needed']}")
        print(f"     explanation: {pred['decision_explanation']}")
        print()


if __name__ == "__main__":
    main()
