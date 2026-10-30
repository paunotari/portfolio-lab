"""Month alignment — the one correct way to join series stamped on different month-ends.

MSCI levels are stamped on the LAST BUSINESS DAY of each month (2009-01-30); Ken French, FRED
and the macro-state labels on the LAST CALENDAR DAY (2009-01-31). They coincide only in months
that do not end on a weekend, so an exact-date join silently keeps about 70% of the months and
raises no error. That single mistake produced the false "risk-free covers 148 of 210 months"
(M40/M42) and dropped 95 of 330 months from the whole regime layer (M56). Join on the month.
"""
from __future__ import annotations

import pandas as pd


def to_month_end(obj):
    """Copy of `obj` with its index re-stamped on calendar month-ends."""
    out = obj.copy()
    out.index = pd.DatetimeIndex(out.index).to_period("M").to_timestamp("M")
    return out


def align_months(obj, index: pd.DatetimeIndex):
    """Rows of `obj` for the months of `index`, matched by month and stamped with `index`."""
    out = obj.copy()
    out.index = pd.DatetimeIndex(out.index).to_period("M")
    out = out[~out.index.duplicated(keep="last")].reindex(pd.DatetimeIndex(index).to_period("M"))
    out.index = index
    return out
