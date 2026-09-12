"""One-off script: injects a structured "recurring_overrides" field into the
already-written evidence cache files, derived by reading each user's existing
"note" text (which the batch extraction agents wrote in fairly consistent
prose) and converting genuine go-forward salary changes into a number the
engine can actually act on. Notes that only confirm already-recorded data,
describe a date shift, or an unsettled/pending fact are deliberately left
alone (no override).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "code", ".cache", "evidence")

# user_id -> {"salary": new_home_currency_amount_per_cycle}
# 0 means "no further recurring salary" (employment ended).
OVERRIDES = {
    # Permanent raises / base-salary-only corrections (commission excluded)
    "user_02": 42750000, "user_104": 35860, "user_108": 33440, "user_11": 38760000,
    "user_117": 1188, "user_135": 828, "user_162": 29070000, "user_164": 44270000,
    "user_176": 847, "user_189": 627, "user_216": 2424, "user_248": 1548,
    "user_36": 2988, "user_45": 17290000, "user_54": 42460, "user_76": 3072,
    "user_80": 158000, "user_92": 49280,
    # Household income restructuring (remaining confirmed total)
    "user_154": 1628, "user_230": 2827, "user_238": 912, "user_42": 148000,
    "user_50": 126000, "user_58": 25840000,
    # Temporary dip still in effect for upcoming cycle(s) — conservative:
    # project the reduced amount near-term rather than the pre-dip normal.
    "user_06": 1037.52, "user_08": 1422.85, "user_103": 164880, "user_130": 2177.28,
    "user_193": 1750.32, "user_85": 8618400,
    # Reverts to normal after a one-off dip already recorded in events
    "user_132": 1193.40, "user_150": 893.75, "user_168": 137150, "user_177": 1731.60,
    "user_249": 702,
    # Employment ended entirely — no further recurring salary
    "user_75": 0, "user_111": 0, "user_165": 0, "user_246": 0,
}


def main():
    applied = 0
    for user_id, amount in OVERRIDES.items():
        path = os.path.join(CACHE_DIR, f"{user_id}.json")
        if not os.path.exists(path):
            print(f"WARN: no cache file for {user_id}")
            continue
        with open(path) as f:
            data = json.load(f)
        data["recurring_overrides"] = {"salary": float(amount)}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        applied += 1
    print(f"Applied recurring_overrides to {applied}/{len(OVERRIDES)} users")


if __name__ == "__main__":
    main()
