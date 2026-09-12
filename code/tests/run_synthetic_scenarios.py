"""Runs the hand-verified scenarios in synthetic_scenarios.py against the real
engine (using real users' actual dataset/financial_events.csv history) without
touching dataset/requests.csv or output.csv. Reports status/method match rate as
an expanded baseline on top of the 25-sample calibration.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from loader import load
from main import decide_one
from synthetic_scenarios import SCENARIOS


def main():
    ds = load()
    status_match = 0
    method_match = 0
    rows = []
    for sc in SCENARIOS:
        request_row = {
            "request_id": f"synthetic_{sc['name']}",
            "user_id": sc["user_id"],
            "request_date": sc["request_date"],
            "request_type": sc["request_type"],
            "requested_amount": sc["requested_amount"],
            "desired_completion_date": sc["desired_completion_date"],
            "allows_partial_payment": sc["allows_partial_payment"],
            "request_text": "",
        }
        opt_rows = []
        for i, opt in enumerate(sc["payment_options"]):
            opt_rows.append({
                "payment_option_id": f"synthetic_opt_{sc['name']}_{i}",
                "request_id": request_row["request_id"],
                **opt,
            })
        opts_df = pd.DataFrame(opt_rows)

        # Monkey-patch: decide_one reads ds.payment_options filtered by request_id
        # internally, so temporarily point it at a combined frame for this one call.
        original_opts = ds.payment_options
        ds.payment_options = pd.concat([original_opts, opts_df], ignore_index=True)
        try:
            pred = decide_one(ds, request_row, {})
        finally:
            ds.payment_options = original_opts

        s_ok = pred["affordability_status"] == sc["expected_status"]
        m_ok = pred["recommended_payment_method"] == sc["expected_method"]
        status_match += s_ok
        method_match += m_ok
        rows.append((sc["name"], s_ok, m_ok, sc["expected_status"], pred["affordability_status"],
                     sc["expected_method"], pred["recommended_payment_method"], pred["decision_explanation"]))

    print(f"{'name':<38} {'status':<8} {'method':<8} expected -> got")
    for name, s_ok, m_ok, exp_s, got_s, exp_m, got_m, expl in rows:
        print(f"{name:<38} {'OK' if s_ok else 'MISS':<8} {'OK' if m_ok else 'MISS':<8} "
              f"{exp_s}/{exp_m} -> {got_s}/{got_m}")
        if not s_ok or not m_ok:
            print(f"    explanation: {expl}")
    print()
    print(f"affordability_status match: {status_match}/{len(SCENARIOS)}")
    print(f"recommended_payment_method match: {method_match}/{len(SCENARIOS)}")


if __name__ == "__main__":
    main()
