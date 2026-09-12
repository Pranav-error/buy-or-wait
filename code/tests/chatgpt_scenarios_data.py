"""Raw CSV text blocks for the 15 ChatGPT-generated test cases the user supplied,
transcribed verbatim. Parsed into isolated per-case Dataset objects by
run_chatgpt_scenarios.py -- NOT merged into the real dataset/ (these user_ids,
e.g. user_01..user_15, collide with real users in dataset/financial_profiles.csv
who are different people)."""

CASES = [
    dict(
        name="case1_comfortable_inr_purchase",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_01,INR,185000.0,50000.0,savings|education,rent|groceries|utilities|education,dining|shopping,food_delivery|streaming,full_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_01,user_01,income,Monthly payroll salary,salary,credit,92000.0,INR,2026-05-30,2026-05-30,settled,,,
event_02,user_01,income,Monthly payroll salary,salary,credit,92000.0,INR,2026-06-30,2026-06-30,settled,,,
event_03,user_01,income,Monthly payroll salary,salary,credit,92000.0,INR,2026-07-31,2026-07-31,settled,,,
event_04,user_01,income,Monthly payroll salary,salary,credit,92000.0,INR,2026-08-31,2026-08-31,settled,,,
event_05,user_01,income,Monthly payroll salary,salary,credit,92000.0,INR,2026-09-30,2026-09-30,scheduled,,,
event_06,user_01,expense,Apartment rent,rent,debit,24000.0,INR,2026-06-01,2026-06-01,settled,,fixed,
event_07,user_01,expense,Apartment rent,rent,debit,24000.0,INR,2026-07-01,2026-07-01,settled,,fixed,
event_08,user_01,expense,Apartment rent,rent,debit,24000.0,INR,2026-08-01,2026-08-01,settled,,fixed,
event_09,user_01,expense,Groceries,groceries,debit,10500.0,INR,2026-08-05,2026-08-05,settled,,reducible,9000.0
event_10,user_01,expense,Groceries,groceries,debit,9800.0,INR,2026-07-05,2026-07-05,settled,,reducible,9000.0
event_11,user_01,expense,Electricity and internet,utilities,debit,4200.0,INR,2026-08-10,2026-08-10,settled,,fixed,
event_12,user_01,subscription,Netflix and music subscriptions,streaming,debit,1200.0,INR,2026-08-15,2026-08-15,settled,,stoppable,
event_13,user_01,expense,Restaurant spending,dining,debit,4500.0,INR,2026-08-20,2026-08-20,settled,,reducible,2000.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_01,user_01,2026-09-12,purchase,28000.0,2026-09-12,False,"I want to buy a new phone for 28000 today. Can I afford it?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_01,request_01,full_payment,28000.0,1,2026-09-12,,0.0,28000.0""",
        rates=None,
        expected=dict(status="affordable_now", method="full_payment"),
    ),
    dict(
        name="case2_tight_with_spending_cut",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_02,INR,72000.0,30000.0,debt_repayment|savings,rent|groceries|debt_repayment,dining|shopping,delivery_membership|streaming,full_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_14,user_02,income,Payroll salary,salary,credit,68000.0,INR,2026-05-31,2026-05-31,settled,,,
event_15,user_02,income,Payroll salary,salary,credit,68000.0,INR,2026-06-30,2026-06-30,settled,,,
event_16,user_02,income,Payroll salary,salary,credit,68000.0,INR,2026-07-31,2026-07-31,settled,,,
event_17,user_02,income,Payroll salary,salary,credit,68000.0,INR,2026-08-31,2026-08-31,settled,,,
event_18,user_02,income,Payroll salary,salary,credit,68000.0,INR,2026-09-30,2026-09-30,scheduled,,,
event_19,user_02,expense,Monthly rent,rent,debit,21000.0,INR,2026-06-02,2026-06-02,settled,,fixed,
event_20,user_02,expense,Monthly rent,rent,debit,21000.0,INR,2026-07-02,2026-07-02,settled,,fixed,
event_21,user_02,expense,Monthly rent,rent,debit,21000.0,INR,2026-08-02,2026-08-02,settled,,fixed,
event_22,user_02,expense,Groceries,groceries,debit,8500.0,INR,2026-06-06,2026-06-06,settled,,reducible,7500.0
event_23,user_02,expense,Groceries,groceries,debit,9100.0,INR,2026-08-06,2026-08-06,settled,,reducible,7500.0
event_24,user_02,debt_payment,Education loan repayment,debt_repayment,debit,9000.0,INR,2026-08-07,2026-08-07,settled,,fixed,
event_25,user_02,expense,Restaurant meals,dining,debit,5200.0,INR,2026-08-18,2026-08-18,settled,,reducible,1500.0
event_26,user_02,subscription,Food delivery membership,delivery_membership,debit,599.0,INR,2026-08-20,2026-08-20,settled,,stoppable,""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_02,user_02,2026-09-12,purchase,32000.0,2026-09-12,False,"I need a 32000 laptop for work. Can I buy it now?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_02,request_02,full_payment,32000.0,1,2026-09-12,,0.0,32000.0""",
        rates=None,
        expected=dict(status="affordable_with_plan", method="full_payment"),
    ),
    dict(
        name="case3_not_affordable",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_03,USD,4100.0,2500.0,debt_repayment|emergency_savings,rent|utilities|debt_repayment|groceries,dining|entertainment,streaming|food_delivery,full_payment|installments,3""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_27,user_03,income,Employer payroll,salary,credit,4800.0,USD,2026-05-29,2026-05-29,settled,,,
event_28,user_03,income,Employer payroll,salary,credit,4800.0,USD,2026-06-30,2026-06-30,settled,,,
event_29,user_03,income,Employer payroll,salary,credit,4800.0,USD,2026-07-31,2026-07-31,settled,,,
event_30,user_03,income,Employer payroll,salary,credit,4800.0,USD,2026-08-31,2026-08-31,settled,,,
event_31,user_03,income,Employer payroll,salary,credit,4800.0,USD,2026-09-30,2026-09-30,scheduled,,,
event_32,user_03,expense,Apartment rent,rent,debit,1800.0,USD,2026-08-01,2026-08-01,settled,,fixed,
event_33,user_03,expense,Groceries,groceries,debit,620.0,USD,2026-08-05,2026-08-05,settled,,reducible,560.0
event_34,user_03,expense,Utilities,utilities,debit,310.0,USD,2026-08-10,2026-08-10,settled,,fixed,
event_35,user_03,debt_payment,Credit card repayment,debt_repayment,debit,550.0,USD,2026-08-15,2026-08-15,settled,,fixed,
event_36,user_03,expense,Dining,dining,debit,300.0,USD,2026-08-20,2026-08-20,settled,,reducible,100.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_03,user_03,2026-09-12,purchase,2200.0,2026-09-12,False,"I found a 2200 dollar camera I want to buy today. Can I afford it?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_03,request_03,full_payment,2200.0,1,2026-09-12,,0.0,2200.0
payment_option_04,request_03,installments,760.0,3,2026-09-12,30,80.0,2280.0""",
        rates=None,
        expected=dict(status="not_affordable", method="not_recommended"),
    ),
    dict(
        name="case4_wait_for_payday",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_04,EUR,1450.0,1000.0,savings|rent,rent|groceries|utilities,dining|entertainment,streaming,full_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_37,user_04,income,Monthly salary,salary,credit,3100.0,EUR,2026-05-29,2026-05-29,settled,,,
event_38,user_04,income,Monthly salary,salary,credit,3100.0,EUR,2026-06-30,2026-06-30,settled,,,
event_39,user_04,income,Monthly salary,salary,credit,3100.0,EUR,2026-07-31,2026-07-31,settled,,,
event_40,user_04,income,Monthly salary,salary,credit,3100.0,EUR,2026-08-31,2026-08-31,settled,,,
event_41,user_04,income,Monthly salary,salary,credit,3100.0,EUR,2026-09-30,2026-09-30,scheduled,,,
event_42,user_04,expense,Apartment rent,rent,debit,1100.0,EUR,2026-08-01,2026-08-01,settled,,fixed,
event_43,user_04,expense,Groceries,groceries,debit,420.0,EUR,2026-08-04,2026-08-04,settled,,reducible,380.0
event_44,user_04,expense,Electricity and internet,utilities,debit,180.0,EUR,2026-08-08,2026-08-08,settled,,fixed,
event_45,user_04,expense,Dining,dining,debit,220.0,EUR,2026-08-18,2026-08-18,settled,,reducible,80.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_04,user_04,2026-09-12,purchase,380.0,2026-09-15,False,"I want to spend 380 euro on a pair of headphones. Should I buy them now or wait for payday?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_05,request_04,full_payment,380.0,1,2026-09-12,,0.0,380.0""",
        rates=None,
        expected=dict(status="affordable_later", method="wait"),
    ),
    dict(
        name="case5_fx_usd_for_inr_user",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_05,INR,240000.0,80000.0,savings|education,rent|groceries|education,dining|shopping,streaming|delivery_membership,full_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_46,user_05,income,Software engineer payroll,salary,credit,125000.0,INR,2026-05-31,2026-05-31,settled,,,
event_47,user_05,income,Software engineer payroll,salary,credit,125000.0,INR,2026-06-30,2026-06-30,settled,,,
event_48,user_05,income,Software engineer payroll,salary,credit,125000.0,INR,2026-07-31,2026-07-31,settled,,,
event_49,user_05,income,Software engineer payroll,salary,credit,125000.0,INR,2026-08-31,2026-08-31,settled,,,
event_50,user_05,income,Software engineer payroll,salary,credit,125000.0,INR,2026-09-30,2026-09-30,scheduled,,,
event_51,user_05,expense,Apartment rent,rent,debit,32000.0,INR,2026-08-01,2026-08-01,settled,,fixed,
event_52,user_05,expense,Groceries,groceries,debit,12000.0,INR,2026-08-05,2026-08-05,settled,,reducible,10500.0
event_53,user_05,expense,University course fee,education,debit,15000.0,INR,2026-08-12,2026-08-12,settled,,fixed,
event_54,user_05,expense,Dining,dining,debit,6000.0,INR,2026-08-20,2026-08-20,settled,,reducible,2500.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_05,user_05,2026-09-12,purchase,11776.0,2026-09-12,False,"A US website is charging me 100 dollars for a developer tool. Can I afford it in rupees?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_06,request_05,full_payment,11776.0,1,2026-09-12,,0.0,11776.0""",
        rates="""rate_date,from_currency,to_currency,rate
2026-09-12,USD,INR,117.76""",
        expected=dict(status="affordable_now", method="full_payment"),
    ),
    dict(
        name="case6_recent_raise",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_06,ZAR,96000.0,30000.0,savings|home_deposit,rent|groceries|utilities,dining|entertainment,streaming|delivery,full_payment|installments,4""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_55,user_06,income,Salary before promotion,salary,credit,38000.0,ZAR,2026-05-30,2026-05-30,settled,,,
event_56,user_06,income,Salary before promotion,salary,credit,38000.0,ZAR,2026-06-30,2026-06-30,settled,,,
event_57,user_06,income,Salary after promotion,salary,credit,47000.0,ZAR,2026-07-31,2026-07-31,settled,,,
event_58,user_06,income,Salary after promotion,salary,credit,47000.0,ZAR,2026-08-31,2026-08-31,settled,,,
event_59,user_06,income,Salary after promotion,salary,credit,47000.0,ZAR,2026-09-30,2026-09-30,scheduled,,,
event_60,user_06,expense,Apartment rent,rent,debit,13500.0,ZAR,2026-08-01,2026-08-01,settled,,fixed,
event_61,user_06,expense,Groceries,groceries,debit,7200.0,ZAR,2026-08-05,2026-08-05,settled,,reducible,6500.0
event_62,user_06,expense,Utilities,utilities,debit,3800.0,ZAR,2026-08-10,2026-08-10,settled,,fixed,
event_63,user_06,expense,Dining,dining,debit,3500.0,ZAR,2026-08-20,2026-08-20,settled,,reducible,1500.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_06,user_06,2026-09-12,purchase,24000.0,2026-09-12,False,"I just got promoted and want to buy a 24000 rand monitor. Is it reasonable now?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_07,request_06,full_payment,24000.0,1,2026-09-12,,0.0,24000.0
payment_option_08,request_06,installments,6250.0,4,2026-09-12,30,1000.0,25000.0""",
        rates=None,
        expected=dict(status="affordable_now", method="full_payment"),
    ),
    dict(
        name="case7_recent_pay_cut",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_07,USD,6800.0,3000.0,emergency_savings|debt_repayment,rent|groceries|debt_repayment,entertainment|dining,streaming|delivery,full_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_64,user_07,income,Salary before pay cut,salary,credit,6500.0,USD,2026-05-29,2026-05-29,settled,,,
event_65,user_07,income,Salary before pay cut,salary,credit,6500.0,USD,2026-06-30,2026-06-30,settled,,,
event_66,user_07,income,Salary before pay cut,salary,credit,6500.0,USD,2026-07-31,2026-07-31,settled,,,
event_67,user_07,income,Reduced monthly salary,salary,credit,5100.0,USD,2026-08-31,2026-08-31,settled,,,
event_68,user_07,income,Reduced monthly salary,salary,credit,5100.0,USD,2026-09-30,2026-09-30,scheduled,,,
event_69,user_07,expense,Apartment rent,rent,debit,1900.0,USD,2026-08-01,2026-08-01,settled,,fixed,
event_70,user_07,expense,Groceries,groceries,debit,650.0,USD,2026-08-05,2026-08-05,settled,,reducible,580.0
event_71,user_07,debt_payment,Personal loan,debt_repayment,debit,750.0,USD,2026-08-15,2026-08-15,settled,,fixed,
event_72,user_07,expense,Dining,dining,debit,420.0,USD,2026-08-20,2026-08-20,settled,,reducible,150.0
event_73,user_07,subscription,Video streaming,streaming,debit,65.0,USD,2026-08-22,2026-08-22,settled,,stoppable,""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_07,user_07,2026-09-12,purchase,1800.0,2026-09-12,False,"My salary was recently cut. Can I still buy this 1800 dollar tablet?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_09,request_07,full_payment,1800.0,1,2026-09-12,,0.0,1800.0""",
        rates=None,
        expected=dict(status="not_affordable", method="not_recommended"),
    ),
    dict(
        name="case8_gig_commission_income",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_08,INR,145000.0,60000.0,emergency_savings|tax_reserve,rent|groceries|tax_reserve,dining|shopping,streaming|delivery,full_payment|installments,3""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_74,user_08,income,Freelance software project,salary,credit,78000.0,INR,2026-05-28,2026-05-28,settled,,,
event_75,user_08,income,Freelance software project,salary,credit,92000.0,INR,2026-06-29,2026-06-29,settled,,,
event_76,user_08,income,Commission payment,salary,credit,45000.0,INR,2026-07-30,2026-07-30,settled,,,
event_77,user_08,income,Freelance project,salary,credit,110000.0,INR,2026-08-29,2026-08-29,settled,,,
event_78,user_08,income,Expected client payment,salary,credit,85000.0,INR,2026-09-25,2026-09-25,scheduled,,,
event_79,user_08,expense,Apartment rent,rent,debit,26000.0,INR,2026-08-01,2026-08-01,settled,,fixed,
event_80,user_08,expense,Groceries,groceries,debit,10500.0,INR,2026-08-05,2026-08-05,settled,,reducible,9000.0
event_81,user_08,expense,Tax reserve transfer,tax_reserve,debit,18000.0,INR,2026-08-10,2026-08-10,settled,,fixed,
event_82,user_08,expense,Dining,dining,debit,5000.0,INR,2026-08-20,2026-08-20,settled,,reducible,2000.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_08,user_08,2026-09-12,purchase,42000.0,2026-09-12,False,"My freelance income varies, but I currently have 145000 saved. Can I spend 42000 on a new monitor?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_10,request_08,full_payment,42000.0,1,2026-09-12,,0.0,42000.0
payment_option_11,request_08,installments,14500.0,3,2026-09-12,30,1500.0,45000.0""",
        rates=None,
        expected=dict(status="affordable_now", method="full_payment"),
    ),
    dict(
        name="case9_near_minimum_floor",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_09,ZAR,43500.0,40000.0,emergency_savings,rent|groceries|utilities,dining|shopping,streaming|delivery,full_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_83,user_09,income,Monthly salary,salary,credit,31000.0,ZAR,2026-05-29,2026-05-29,settled,,,
event_84,user_09,income,Monthly salary,salary,credit,31000.0,ZAR,2026-06-30,2026-06-30,settled,,,
event_85,user_09,income,Monthly salary,salary,credit,31000.0,ZAR,2026-07-31,2026-07-31,settled,,,
event_86,user_09,income,Monthly salary,salary,credit,31000.0,ZAR,2026-08-31,2026-08-31,settled,,,
event_87,user_09,income,Monthly salary,salary,credit,31000.0,ZAR,2026-09-30,2026-09-30,scheduled,,,
event_88,user_09,expense,Apartment rent,rent,debit,12000.0,ZAR,2026-08-01,2026-08-01,settled,,fixed,
event_89,user_09,expense,Groceries,groceries,debit,6200.0,ZAR,2026-08-05,2026-08-05,settled,,reducible,5500.0
event_90,user_09,expense,Utilities,utilities,debit,3000.0,ZAR,2026-08-10,2026-08-10,settled,,fixed,
event_91,user_09,expense,Dining,dining,debit,2500.0,ZAR,2026-08-20,2026-08-20,settled,,reducible,1000.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_09,user_09,2026-09-12,purchase,5000.0,2026-09-12,False,"I have 43500 rand in my account and want to buy something for 5000. Is that safe?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_12,request_09,full_payment,5000.0,1,2026-09-12,,0.0,5000.0""",
        rates=None,
        expected=dict(status="not_affordable", method="not_recommended"),
    ),
    dict(
        name="case10_refuses_installments",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_10,EUR,9200.0,3500.0,debt_repayment|savings,rent|groceries|debt_repayment,dining|travel,streaming|delivery,full_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_92,user_10,income,Monthly salary,salary,credit,3600.0,EUR,2026-05-29,2026-05-29,settled,,,
event_93,user_10,income,Monthly salary,salary,credit,3600.0,EUR,2026-06-30,2026-06-30,settled,,,
event_94,user_10,income,Monthly salary,salary,credit,3600.0,EUR,2026-07-31,2026-07-31,settled,,,
event_95,user_10,income,Monthly salary,salary,credit,3600.0,EUR,2026-08-31,2026-08-31,settled,,,
event_96,user_10,income,Monthly salary,salary,credit,3600.0,EUR,2026-09-30,2026-09-30,scheduled,,,
event_97,user_10,expense,Apartment rent,rent,debit,1250.0,EUR,2026-08-01,2026-08-01,settled,,fixed,
event_98,user_10,expense,Groceries,groceries,debit,430.0,EUR,2026-08-05,2026-08-05,settled,,reducible,380.0
event_99,user_10,debt_payment,Car loan,debt_repayment,debit,600.0,EUR,2026-08-15,2026-08-15,settled,,fixed,
event_100,user_10,expense,Dining,dining,debit,250.0,EUR,2026-08-20,2026-08-20,settled,,reducible,100.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_10,user_10,2026-09-12,purchase,4200.0,2026-09-12,False,"The store offers installments, but I never use them. Can I pay 4200 euro in full?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_13,request_10,full_payment,4200.0,1,2026-09-12,,0.0,4200.0
payment_option_14,request_10,installments,1100.0,4,2026-09-12,30,200.0,4400.0""",
        rates=None,
        expected=dict(status="affordable_now", method="full_payment"),
    ),
    dict(
        name="case11_seller_offers_both",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_11,INR,88000.0,40000.0,savings|rent,rent|groceries|utilities,dining|shopping,streaming,full_payment|installments,4""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_101,user_11,income,Monthly payroll,salary,credit,72000.0,INR,2026-05-31,2026-05-31,settled,,,
event_102,user_11,income,Monthly payroll,salary,credit,72000.0,INR,2026-06-30,2026-06-30,settled,,,
event_103,user_11,income,Monthly payroll,salary,credit,72000.0,INR,2026-07-31,2026-07-31,settled,,,
event_104,user_11,income,Monthly payroll,salary,credit,72000.0,INR,2026-08-31,2026-08-31,settled,,,
event_105,user_11,income,Monthly payroll,salary,credit,72000.0,INR,2026-09-30,2026-09-30,scheduled,,,
event_106,user_11,expense,Apartment rent,rent,debit,22000.0,INR,2026-08-01,2026-08-01,settled,,fixed,
event_107,user_11,expense,Groceries,groceries,debit,9000.0,INR,2026-08-05,2026-08-05,settled,,reducible,8000.0
event_108,user_11,expense,Utilities,utilities,debit,4500.0,INR,2026-08-10,2026-08-10,settled,,fixed,
event_109,user_11,expense,Dining,dining,debit,4200.0,INR,2026-08-20,2026-08-20,settled,,reducible,1800.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_11,user_11,2026-09-12,purchase,30000.0,2026-09-12,False,"The seller lets me either pay 30000 now or split it into four payments. Which should I choose?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_15,request_11,full_payment,30000.0,1,2026-09-12,,0.0,30000.0
payment_option_16,request_11,installments,7750.0,4,2026-09-12,30,1000.0,31000.0""",
        rates=None,
        expected=dict(status="affordable_now", method="full_payment"),
    ),
    dict(
        name="case12_medical_constrained",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_12,IDR,18500000.0,10000000.0,medical|emergency_savings,rent|groceries|medical,dining|shopping,streaming|delivery,full_payment|installments,6""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_110,user_12,income,Monthly salary,salary,credit,11500000.0,IDR,2026-05-30,2026-05-30,settled,,,
event_111,user_12,income,Monthly salary,salary,credit,11500000.0,IDR,2026-06-30,2026-06-30,settled,,,
event_112,user_12,income,Monthly salary,salary,credit,11500000.0,IDR,2026-07-31,2026-07-31,settled,,,
event_113,user_12,income,Monthly salary,salary,credit,11500000.0,IDR,2026-08-31,2026-08-31,settled,,,
event_114,user_12,income,Monthly salary,salary,credit,11500000.0,IDR,2026-09-30,2026-09-30,scheduled,,,
event_115,user_12,expense,Apartment rent,rent,debit,4200000.0,IDR,2026-08-01,2026-08-01,settled,,fixed,
event_116,user_12,expense,Groceries,groceries,debit,2500000.0,IDR,2026-08-05,2026-08-05,settled,,reducible,2200000.0
event_117,user_12,expense,Prescribed medicine,medical,debit,1100000.0,IDR,2026-08-12,2026-08-12,settled,,fixed,
event_118,user_12,expense,Dining,dining,debit,900000.0,IDR,2026-08-20,2026-08-20,settled,,reducible,300000.0
event_119,user_12,expense,Upcoming medical bill,medical,debit,2500000.0,IDR,2026-09-20,2026-09-20,scheduled,,fixed,""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_12,user_12,2026-09-12,medical,7000000.0,2026-09-12,False,"I have a medical treatment costing IDR 7 million. Can I pay for it now?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_17,request_12,full_payment,7000000.0,1,2026-09-12,,0.0,7000000.0
payment_option_18,request_12,installments,1250000.0,6,2026-09-12,30,500000.0,8000000.0""",
        rates=None,
        expected=dict(status="not_affordable", method="not_recommended"),
    ),
    dict(
        name="case13_fx_eur_for_zar_user",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_13,ZAR,185000.0,70000.0,education|savings,rent|groceries|education,dining|travel,streaming|delivery,full_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_120,user_13,income,Monthly salary,salary,credit,52000.0,ZAR,2026-05-29,2026-05-29,settled,,,
event_121,user_13,income,Monthly salary,salary,credit,52000.0,ZAR,2026-06-30,2026-06-30,settled,,,
event_122,user_13,income,Monthly salary,salary,credit,52000.0,ZAR,2026-07-31,2026-07-31,settled,,,
event_123,user_13,income,Monthly salary,salary,credit,52000.0,ZAR,2026-08-31,2026-08-31,settled,,,
event_124,user_13,income,Monthly salary,salary,credit,52000.0,ZAR,2026-09-30,2026-09-30,scheduled,,,
event_125,user_13,expense,Apartment rent,rent,debit,16000.0,ZAR,2026-08-01,2026-08-01,settled,,fixed,
event_126,user_13,expense,Groceries,groceries,debit,8500.0,ZAR,2026-08-05,2026-08-05,settled,,reducible,7500.0
event_127,user_13,expense,Professional education course,education,debit,6000.0,ZAR,2026-08-12,2026-08-12,settled,,fixed,
event_128,user_13,expense,Dining,dining,debit,4500.0,ZAR,2026-08-20,2026-08-20,settled,,reducible,2000.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_13,user_13,2026-09-12,purchase,1973.65,2026-09-12,False,"A European website charges 100 euro for a course. What would that cost me and can I afford it?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_19,request_13,full_payment,1973.65,1,2026-09-12,,0.0,1973.65""",
        rates="""rate_date,from_currency,to_currency,rate
2026-09-12,EUR,ZAR,19.7365""",
        expected=dict(status="affordable_now", method="full_payment"),
    ),
    dict(
        name="case14_partial_payment_safe",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_14,INR,95000.0,50000.0,emergency_savings|rent,rent|groceries|utilities,dining|shopping,streaming|delivery,full_payment|partial_payment,""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_129,user_14,income,Monthly salary,salary,credit,60000.0,INR,2026-05-31,2026-05-31,settled,,,
event_130,user_14,income,Monthly salary,salary,credit,60000.0,INR,2026-06-30,2026-06-30,settled,,,
event_131,user_14,income,Monthly salary,salary,credit,60000.0,INR,2026-07-31,2026-07-31,settled,,,
event_132,user_14,income,Monthly salary,salary,credit,60000.0,INR,2026-08-31,2026-08-31,settled,,,
event_133,user_14,income,Monthly salary,salary,credit,60000.0,INR,2026-09-30,2026-09-30,scheduled,,,
event_134,user_14,expense,Apartment rent,rent,debit,18000.0,INR,2026-08-01,2026-08-01,settled,,fixed,
event_135,user_14,expense,Groceries,groceries,debit,8000.0,INR,2026-08-05,2026-08-05,settled,,reducible,7000.0
event_136,user_14,expense,Utilities,utilities,debit,4000.0,INR,2026-08-10,2026-08-10,settled,,fixed,
event_137,user_14,expense,Dining,dining,debit,4500.0,INR,2026-08-20,2026-08-20,settled,,reducible,1500.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_14,user_14,2026-09-12,family_transfer,70000.0,2026-09-12,True,"I need to send 70000 to my family, but I do not want to go below my 50000 emergency buffer. How much can I safely send now?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_20,request_14,full_payment,70000.0,1,2026-09-12,,0.0,70000.0
payment_option_21,request_14,partial_payment,40000.0,1,2026-09-12,,0.0,40000.0""",
        rates=None,
        expected=dict(status="affordable_with_plan", method="partial_payment"),
    ),
    dict(
        name="case15_fx_usd_idr_with_upcoming_bill",
        profiles="""user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
user_15,IDR,32000000.0,15000000.0,savings|housing,rent|groceries|utilities,dining|shopping,streaming|delivery,full_payment|installments,3""",
        events="""event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
event_138,user_15,income,Monthly payroll,salary,credit,14500000.0,IDR,2026-05-30,2026-05-30,settled,,,
event_139,user_15,income,Monthly payroll,salary,credit,14500000.0,IDR,2026-06-30,2026-06-30,settled,,,
event_140,user_15,income,Monthly payroll,salary,credit,14500000.0,IDR,2026-07-31,2026-07-31,settled,,,
event_141,user_15,income,Monthly payroll,salary,credit,14500000.0,IDR,2026-08-31,2026-08-31,settled,,,
event_142,user_15,income,Monthly payroll,salary,credit,14500000.0,IDR,2026-09-30,2026-09-30,scheduled,,,
event_143,user_15,expense,Apartment rent,rent,debit,5500000.0,IDR,2026-08-01,2026-08-01,settled,,fixed,
event_144,user_15,expense,Groceries,groceries,debit,2800000.0,IDR,2026-08-05,2026-08-05,settled,,reducible,2400000.0
event_145,user_15,expense,Electricity and internet,utilities,debit,1500000.0,IDR,2026-08-10,2026-08-10,settled,,fixed,
event_146,user_15,expense,Annual insurance payment,insurance,debit,6000000.0,IDR,2026-09-25,2026-09-25,scheduled,,fixed,
event_147,user_15,expense,Dining,dining,debit,1200000.0,IDR,2026-08-20,2026-08-20,settled,,reducible,400000.0""",
        request="""request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
request_15,user_15,2026-09-12,purchase,11776000.0,2026-09-12,False,"A US store is charging 1000 dollars for a laptop. Can I afford the purchase in rupiah?" """,
        payment_options="""payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
payment_option_22,request_15,full_payment,11776000.0,1,2026-09-12,,0.0,11776000.0
payment_option_23,request_15,installments,4100000.0,3,2026-09-12,30,530000.0,12830000.0""",
        rates="""rate_date,from_currency,to_currency,rate
2026-09-12,USD,IDR,17611.0""",
        expected=dict(status="not_affordable", method="not_recommended"),
    ),
]
