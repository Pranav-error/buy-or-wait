"""Standalone, hand-verified test scenarios using REAL users' existing profiles and
financial_events.csv history (not fabricated finances) -- 15 new purchase requests
that don't exist in dataset/requests.csv or dataset/sample_requests.csv, designed to
stress-test categories the 25 provided samples don't fully cover: payment-method-
preference restrictions (e.g. a user who only considers "installments", never
full_payment), FX-converted salary, waiting-for-payday, and clearly-affordable /
clearly-unaffordable extremes.

Each scenario's expected_status/expected_method was reasoned by hand from that
user's actual balance, minimum_balance_to_keep, and recent income/expense pattern
(see the docstring per case). This does NOT touch dataset/requests.csv, output.csv,
or any organizer-only file -- it's a standalone harness run via
`python3 code/tests/run_synthetic_scenarios.py`.
"""
import datetime as dt

SCENARIOS = [
    dict(
        name="user_30_clearly_affordable",
        user_id="user_30", request_date=dt.date(2026, 4, 5), request_type="purchase",
        requested_amount=1500.0, desired_completion_date=dt.date(2026, 4, 20),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=1500.0,
                               number_of_payments=1, first_payment_date=dt.date(2026, 4, 5),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=1500.0)],
        expected_status="affordable_now", expected_method="full_payment",
        reasoning="bal=3752.72, min=900 -> headroom 2852.72, well above $1500 with only "
                  "~$45-65 in near-term fixed groceries/rent ahead.",
    ),
    dict(
        name="user_36_needs_next_payday",
        user_id="user_36", request_date=dt.date(2026, 7, 3), request_type="purchase",
        requested_amount=1800.0, desired_completion_date=dt.date(2026, 8, 20),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=1800.0,
                               number_of_payments=1, first_payment_date=dt.date(2026, 7, 3),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=1800.0)],
        expected_status="affordable_later", expected_method="wait",
        reasoning="bal=3846.6, min=2400 -> headroom only 1446.6 < 1800. Next $2330.64 salary "
                  "lands 2026-07-15/08-15, easily covering it well before the 08-20 deadline "
                  "without needing to touch protected housing/healthcare/utilities.",
    ),
    dict(
        name="user_53_installments_only_profile",
        user_id="user_53", request_date=dt.date(2025, 11, 10), request_type="education",
        requested_amount=2400.0, desired_completion_date=dt.date(2026, 5, 10),
        allows_partial_payment=False,
        payment_options=[
            dict(payment_method="full_payment", payment_amount=2400.0, number_of_payments=1,
                 first_payment_date=dt.date(2025, 11, 10), payment_frequency_days=None,
                 financing_fee=0.0, total_payable_amount=2400.0),
            dict(payment_method="installments", payment_amount=420.0, number_of_payments=6,
                 first_payment_date=dt.date(2025, 11, 10), payment_frequency_days=30,
                 financing_fee=120.0, total_payable_amount=2520.0),
        ],
        expected_status="affordable_with_plan", expected_method="installments",
        reasoning="payment_methods_user_will_consider='installments' ONLY (no full_payment) "
                  "-- even though bal=3523.42/min=2100 (headroom 1423.42) could almost cover "
                  "full payment, the user's stated preference rules it out; max_installment_months=12 "
                  "comfortably fits the 6-month option offered.",
    ),
    dict(
        name="user_56_clearly_not_affordable",
        user_id="user_56", request_date=dt.date(2025, 1, 20), request_type="purchase",
        requested_amount=50000.0, desired_completion_date=dt.date(2025, 4, 20),
        allows_partial_payment=True,
        payment_options=[
            dict(payment_method="full_payment", payment_amount=50000.0, number_of_payments=1,
                 first_payment_date=dt.date(2025, 1, 20), payment_frequency_days=None,
                 financing_fee=0.0, total_payable_amount=50000.0),
            dict(payment_method="installments", payment_amount=4545.0, number_of_payments=11,
                 first_payment_date=dt.date(2025, 1, 20), payment_frequency_days=30,
                 financing_fee=1000.0, total_payable_amount=51000.0),
        ],
        expected_status="not_affordable", expected_method="not_recommended",
        reasoning="bal=3432.36, salary only ~$2388/month -- $50,000 is roughly 20x monthly "
                  "income and dwarfs even a full 90-day accumulation; not affordable by any method.",
    ),
    dict(
        name="user_28_comfortable_margin",
        user_id="user_28", request_date=dt.date(2024, 6, 10), request_type="purchase",
        requested_amount=600.0, desired_completion_date=dt.date(2024, 6, 25),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=600.0,
                               number_of_payments=1, first_payment_date=dt.date(2024, 6, 10),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=600.0)],
        expected_status="affordable_now", expected_method="full_payment",
        reasoning="bal=1789.4, min=1100 -> headroom 689.4 > 600, near-term rent/groceries/"
                  "transport are modest relative to that margin.",
    ),
    dict(
        name="user_38_far_beyond_reach",
        user_id="user_38", request_date=dt.date(2025, 8, 5), request_type="purchase",
        requested_amount=5000.0, desired_completion_date=dt.date(2025, 11, 5),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=5000.0,
                               number_of_payments=1, first_payment_date=dt.date(2025, 8, 5),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=5000.0)],
        expected_status="not_affordable", expected_method="not_recommended",
        reasoning="bal=779.4, salary only EUR737/month -> even 3 months' accumulated income "
                  "(~2211) plus current balance falls far short of EUR 5000 within the 90-day "
                  "forecast window (desired date is also only 92 days out).",
    ),
    dict(
        name="user_40_installments_bridges_gap",
        user_id="user_40", request_date=dt.date(2024, 6, 10), request_type="purchase",
        requested_amount=1200.0, desired_completion_date=dt.date(2024, 11, 1),
        allows_partial_payment=False,
        payment_options=[
            dict(payment_method="full_payment", payment_amount=1200.0, number_of_payments=1,
                 first_payment_date=dt.date(2024, 6, 10), payment_frequency_days=None,
                 financing_fee=0.0, total_payable_amount=1200.0),
            dict(payment_method="installments", payment_amount=248.0, number_of_payments=5,
                 first_payment_date=dt.date(2024, 6, 10), payment_frequency_days=30,
                 financing_fee=40.0, total_payable_amount=1240.0),
        ],
        expected_status="affordable_with_plan", expected_method="installments",
        reasoning="bal=2394, min=1500 -> headroom only 894 < 1200 needed immediately; "
                  "max_installment_months=5 exactly matches the offered 5-month plan and "
                  "payment_methods_user_will_consider includes installments.",
    ),
    dict(
        name="user_69_partial_payment_bridges_payday",
        user_id="user_69", request_date=dt.date(2025, 12, 28), request_type="purchase",
        requested_amount=1600.0, desired_completion_date=dt.date(2026, 1, 25),
        allows_partial_payment=True,
        payment_options=[dict(payment_method="full_payment", payment_amount=1600.0,
                               number_of_payments=1, first_payment_date=dt.date(2025, 12, 28),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=1600.0)],
        expected_status="affordable_with_plan", expected_method="partial_payment",
        reasoning="bal=1639.5, min=700 -> headroom 939.5 covers most of it now; next EUR1177 "
                  "salary on 2026-01-15 covers the EUR660.5 remainder well before the "
                  "2026-01-25 deadline. allows_partial_payment=True on the request.",
    ),
    dict(
        name="user_33_comfortable_now",
        user_id="user_33", request_date=dt.date(2026, 1, 10), request_type="purchase",
        requested_amount=60000.0, desired_completion_date=dt.date(2026, 1, 25),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=60000.0,
                               number_of_payments=1, first_payment_date=dt.date(2026, 1, 10),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=60000.0)],
        expected_status="affordable_now", expected_method="full_payment",
        reasoning="bal=167280, min=102100 -> headroom 65180 > 60000, comfortably clears "
                  "near-term rent/utilities/transport already reflected in that margin.",
    ),
    dict(
        name="user_34_large_but_affordable",
        user_id="user_34", request_date=dt.date(2024, 12, 5), request_type="purchase",
        requested_amount=300000.0, desired_completion_date=dt.date(2024, 12, 20),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=300000.0,
                               number_of_payments=1, first_payment_date=dt.date(2024, 12, 5),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=300000.0)],
        expected_status="affordable_now", expected_method="full_payment",
        reasoning="bal=559752.5, min=138500 -> headroom 421252.5, more than enough margin "
                  "over 300000 even accounting for rent (~51200) and other fixed monthly costs.",
    ),
    dict(
        name="user_35_wait_for_next_salary",
        user_id="user_35", request_date=dt.date(2025, 10, 20), request_type="purchase",
        requested_amount=180000.0, desired_completion_date=dt.date(2025, 12, 5),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=180000.0,
                               number_of_payments=1, first_payment_date=dt.date(2025, 10, 20),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=180000.0)],
        expected_status="affordable_later", expected_method="wait",
        reasoning="bal=231530, min=106400 -> headroom only 125130 < 180000. Next INR162000 "
                  "salary (2025-11-15) pushes available cash comfortably past 180000 well "
                  "before the 2025-12-05 deadline, with no spending change needed.",
    ),
    dict(
        name="user_39_fx_conversion_after_payday",
        user_id="user_39", request_date=dt.date(2026, 4, 5), request_type="purchase",
        requested_amount=350000.0, desired_completion_date=dt.date(2026, 4, 25),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=350000.0,
                               number_of_payments=1, first_payment_date=dt.date(2026, 4, 5),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=350000.0)],
        expected_status="affordable_later", expected_method="wait",
        reasoning="Salary is paid in USD (3048/month) but home_currency=INR; exchange_rates.csv "
                  "has USD->INR=83.33 on 2026-04-15 (the scheduled settlement date), so the "
                  "next paycheck is worth 3048*83.33=254,013.84 INR. bal=416505, min=213400 -> "
                  "headroom 203105 < 350000 now, but 416505+254013.84-213400-~46000(near-term "
                  "committed spend) is comfortably above 350000 once the 04-15 salary settles, "
                  "well before the 04-25 deadline. This specifically tests that the engine "
                  "converts the USD salary at the correct settlement-date rate, not a wrong "
                  "or stale one.",
    ),
    dict(
        name="user_26_huge_margin",
        user_id="user_26", request_date=dt.date(2025, 7, 20), request_type="purchase",
        requested_amount=50000000.0, desired_completion_date=dt.date(2025, 8, 5),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=50000000.0,
                               number_of_payments=1, first_payment_date=dt.date(2025, 7, 20),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=50000000.0)],
        expected_status="affordable_now", expected_method="full_payment",
        reasoning="bal=100845250, min=24768300 -> headroom 76076950, comfortably above "
                  "50000000 IDR even after near-term groceries/shopping/transport/dining.",
    ),
    dict(
        name="user_31_installments_beyond_headroom",
        user_id="user_31", request_date=dt.date(2024, 8, 18), request_type="purchase",
        requested_amount=25000000.0, desired_completion_date=dt.date(2025, 2, 18),
        allows_partial_payment=False,
        payment_options=[
            dict(payment_method="full_payment", payment_amount=25000000.0, number_of_payments=1,
                 first_payment_date=dt.date(2024, 8, 18), payment_frequency_days=None,
                 financing_fee=0.0, total_payable_amount=25000000.0),
            dict(payment_method="installments", payment_amount=4383333.0, number_of_payments=6,
                 first_payment_date=dt.date(2024, 8, 18), payment_frequency_days=30,
                 financing_fee=300000.0, total_payable_amount=26300000.0),
        ],
        expected_status="affordable_with_plan", expected_method="installments",
        reasoning="bal=30429260, min=16588900 -> headroom 13840360 < 25000000 needed "
                  "immediately. max_installment_months=6 exactly matches the offered plan, "
                  "and payment_methods_user_will_consider includes installments.",
    ),
    dict(
        name="user_27_gig_income_affordable",
        user_id="user_27", request_date=dt.date(2026, 7, 10), request_type="purchase",
        requested_amount=60000.0, desired_completion_date=dt.date(2026, 7, 25),
        allows_partial_payment=False,
        payment_options=[dict(payment_method="full_payment", payment_amount=60000.0,
                               number_of_payments=1, first_payment_date=dt.date(2026, 7, 10),
                               payment_frequency_days=None, financing_fee=0.0, total_payable_amount=60000.0)],
        expected_status="affordable_now", expected_method="full_payment",
        reasoning="bal=93141.8, min=20500 -> headroom 72641.8 > 60000, even accounting for "
                  "rent (8360) and other near-term fixed costs already reflected in the margin.",
    ),
]
