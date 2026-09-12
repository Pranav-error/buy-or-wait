"""Loads dataset/*.csv into indexed, typed in-memory structures."""

from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass, field

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET = os.path.join(ROOT, "dataset")


def _d(s):
    if pd.isna(s) or s == "":
        return None
    return dt.date.fromisoformat(str(s)[:10])


@dataclass
class Dataset:
    profiles: pd.DataFrame
    events: pd.DataFrame
    rates: pd.DataFrame
    requests: pd.DataFrame
    sample_requests: pd.DataFrame
    payment_options: pd.DataFrame
    messages: pd.DataFrame
    images: pd.DataFrame

    rate_lookup: dict = field(default_factory=dict)

    def fx_rate(self, date: dt.date, from_ccy: str, to_ccy: str) -> float:
        if from_ccy == to_ccy:
            return 1.0
        key = (date.isoformat(), from_ccy, to_ccy)
        if key in self.rate_lookup:
            return self.rate_lookup[key]
        inv_key = (date.isoformat(), to_ccy, from_ccy)
        if inv_key in self.rate_lookup:
            return 1.0 / self.rate_lookup[inv_key]
        raise KeyError(f"no exchange rate for {from_ccy}->{to_ccy} on {date}")

    def to_home(self, amount: float, from_ccy: str, to_ccy: str, date: dt.date) -> float:
        return amount * self.fx_rate(date, from_ccy, to_ccy)


def load() -> Dataset:
    profiles = pd.read_csv(os.path.join(DATASET, "financial_profiles.csv"))
    events = pd.read_csv(os.path.join(DATASET, "financial_events.csv"))
    rates = pd.read_csv(os.path.join(DATASET, "exchange_rates.csv"))
    requests = pd.read_csv(os.path.join(DATASET, "requests.csv"))
    sample_requests = pd.read_csv(os.path.join(DATASET, "sample_requests.csv"))
    payment_options = pd.read_csv(os.path.join(DATASET, "request_payment_options.csv"))
    messages = pd.read_csv(os.path.join(DATASET, "messages.csv"))
    images = pd.read_csv(os.path.join(DATASET, "images.csv"))

    events["event_date"] = events["event_date"].apply(_d)
    events["settlement_date"] = events["settlement_date"].apply(_d)
    requests["request_date"] = requests["request_date"].apply(_d)
    requests["desired_completion_date"] = requests["desired_completion_date"].apply(_d)
    payment_options["first_payment_date"] = payment_options["first_payment_date"].apply(_d)
    sample_requests["request_date"] = sample_requests["request_date"].apply(_d)
    sample_requests["desired_completion_date"] = sample_requests["desired_completion_date"].apply(_d)

    ds = Dataset(
        profiles=profiles,
        events=events,
        rates=rates,
        requests=requests,
        sample_requests=sample_requests,
        payment_options=payment_options,
        messages=messages,
        images=images,
    )
    for _, r in rates.iterrows():
        ds.rate_lookup[(r["rate_date"], r["from_currency"], r["to_currency"])] = float(r["rate"])
    return ds
