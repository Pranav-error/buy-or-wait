"""Runs the 15 ChatGPT-generated test cases (chatgpt_scenarios_data.py) against
the real engine, each in a fully ISOLATED Dataset (these fictional user_ids like
user_01..user_15 collide with real users in dataset/financial_profiles.csv --
completely different people -- so each case gets its own tiny in-memory Dataset,
never merged with the real dataset/ or touching output.csv)."""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from loader import Dataset, _d
from main import decide_one
from chatgpt_scenarios_data import CASES


def build_isolated_ds(case):
    profiles = pd.read_csv(io.StringIO(case["profiles"]))
    events = pd.read_csv(io.StringIO(case["events"]))
    request = pd.read_csv(io.StringIO(case["request"]))
    payment_options = pd.read_csv(io.StringIO(case["payment_options"]))
    rates = pd.read_csv(io.StringIO(case["rates"])) if case["rates"] else pd.DataFrame(
        columns=["rate_date", "from_currency", "to_currency", "rate"])

    events["event_date"] = events["event_date"].apply(_d)
    events["settlement_date"] = events["settlement_date"].apply(_d)
    request["request_date"] = request["request_date"].apply(_d)
    request["desired_completion_date"] = request["desired_completion_date"].apply(_d)
    payment_options["first_payment_date"] = payment_options["first_payment_date"].apply(_d)

    empty = pd.DataFrame()
    ds = Dataset(
        profiles=profiles, events=events, rates=rates, requests=request,
        sample_requests=empty, payment_options=payment_options,
        messages=pd.DataFrame(columns=["user_id", "message_id", "related_event_id", "sent_at", "source_type", "message_text"]),
        images=pd.DataFrame(columns=["image_id", "user_id", "request_id", "related_event_id"]),
    )
    for _, r in rates.iterrows():
        ds.rate_lookup[(r["rate_date"], r["from_currency"], r["to_currency"])] = float(r["rate"])
    return ds, request.iloc[0].to_dict()


def main():
    status_match = 0
    method_match = 0
    for case in CASES:
        ds, request_row = build_isolated_ds(case)
        pred = decide_one(ds, request_row, {})
        exp = case["expected"]
        s_ok = pred["affordability_status"] == exp["status"]
        m_ok = pred["recommended_payment_method"] == exp["method"]
        status_match += s_ok
        method_match += m_ok
        print(f"{case['name']:<38} {'OK' if s_ok else 'MISS':<6} {'OK' if m_ok else 'MISS':<6} "
              f"{exp['status']}/{exp['method']} -> {pred['affordability_status']}/{pred['recommended_payment_method']}")
        if not s_ok or not m_ok:
            print(f"    amount_safe_to_pay={pred['amount_safe_to_pay']}  plan={pred['payment_plan']}")
            print(f"    explanation: {pred['decision_explanation']}")
    print()
    print(f"affordability_status match: {status_match}/{len(CASES)}")
    print(f"recommended_payment_method match: {method_match}/{len(CASES)}")


if __name__ == "__main__":
    main()
