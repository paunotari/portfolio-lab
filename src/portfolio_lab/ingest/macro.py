"""Ingest historical macro indicators from FRED, aligned monthly to the returns series.

Two access routes, chosen automatically:
  * official JSON API  — used when the FRED_API_KEY env var is set (higher limits, metadata)
  * keyless CSV endpoint (fredgraph.csv) — default fallback, works with no key

Each series is resampled to month-end and optionally transformed (e.g. CPI level -> YoY inflation).
Outputs:
  data/processed/macro_monthly.csv  date (month-end) x indicator columns (transformed)
  data/processed/macro_meta.csv     id, name, transform, units, source, start, end, n

Run:  python -m portfolio_lab.ingest.macro
Env:  FRED_API_KEY (optional)
"""
from __future__ import annotations
import os
import io
import ssl
import urllib.request
import json
import pandas as pd

from portfolio_lab import config as C

# macOS Python often lacks the system CA store; use certifi so HTTPS to FRED verifies.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # pragma: no cover
    _SSL_CTX = ssl.create_default_context()

# id, output name, transform, human units. transform in {level, yoy}
#   level = use the value as-is (rates, spreads, indices, binary flags)
#   yoy   = 12-month % change of a price/level index (inflation, real-activity growth)
SERIES = [
    ("CPIAUCSL",     "cpi_yoy",          "yoy",   "CPI inflation YoY %"),
    ("PCEPILFE",     "core_pce_yoy",     "yoy",   "Core PCE inflation YoY %"),
    ("FEDFUNDS",     "fed_funds",        "level", "Fed funds rate %"),
    ("DGS10",        "ust_10y",          "level", "10Y Treasury yield %"),
    ("T10Y2Y",       "yc_10y_2y",        "level", "10Y-2Y term spread %"),
    ("INDPRO",       "indpro_yoy",       "yoy",   "Industrial production YoY %"),
    ("UNRATE",       "unemployment",     "level", "Unemployment rate %"),
    ("BAMLH0A0HYM2", "hy_credit_spread", "level", "US HY OAS credit spread %"),
    ("VIXCLS",       "vix",              "level", "VIX index"),
    ("DTWEXBGS",     "usd_broad",        "level", "Broad USD index (2006+)"),
    ("DCOILWTICO",   "wti_oil",          "level", "WTI crude oil $/bbl"),
    ("PPIACO",       "ppi_commodities_yoy", "yoy", "PPI all commodities YoY %"),
    # added for the 4-quadrant macro-state classifier (analytics/macro_state.py):
    ("T10YIE",       "breakeven_10y",    "level", "10Y breakeven inflation expectation % (1997+)"),
    ("T5YIE",        "breakeven_5y",     "level", "5Y breakeven inflation expectation % (2003+)"),
    ("USREC",        "us_recession",     "level", "NBER US recession indicator (0/1)"),
]

FRED_API = "https://api.stlouisfed.org/fred/series/observations"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def _fetch_raw(series_id: str) -> pd.Series:
    """Return a date-indexed float Series of raw observations for one FRED id."""
    key = os.environ.get("FRED_API_KEY")
    if key:
        url = f"{FRED_API}?series_id={series_id}&api_key={key}&file_type=json"
        with urllib.request.urlopen(url, timeout=30, context=_SSL_CTX) as r:
            obs = json.load(r)["observations"]
        idx = pd.to_datetime([o["date"] for o in obs])
        vals = pd.to_numeric([o["value"] for o in obs], errors="coerce")
        return pd.Series(vals, index=idx, name=series_id).dropna()
    # keyless CSV fallback (cosd forces full history where the endpoint would default to recent)
    url = f"{FRED_CSV}?id={series_id}&cosd=1900-01-01"
    with urllib.request.urlopen(url, timeout=30, context=_SSL_CTX) as r:
        df = pd.read_csv(io.BytesIO(r.read()))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().set_index("date")["value"].rename(series_id)


def _to_month_end(s: pd.Series) -> pd.Series:
    """Resample any frequency to month-end using the last observation in each month."""
    return s.resample("ME").last()


def _transform(s: pd.Series, how: str) -> pd.Series:
    if how == "yoy":
        return (s / s.shift(12) - 1.0) * 100.0
    return s  # level


def run() -> pd.DataFrame:
    C.ensure_dirs()
    key_mode = "api" if os.environ.get("FRED_API_KEY") else "csv(keyless)"
    cols, meta = {}, []
    for sid, name, how, units in SERIES:
        try:
            raw = _to_month_end(_fetch_raw(sid))
        except Exception as e:  # noqa: BLE001 - network/parse failure: report and skip this series
            print(f"[macro] WARN {sid} ({name}) failed: {e}")
            continue
        series = _transform(raw, how).dropna()
        cols[name] = series
        meta.append(dict(id=sid, name=name, transform=how, units=units, source="FRED",
                         start=str(series.index.min().date()), end=str(series.index.max().date()),
                         n=len(series)))
    macro = pd.DataFrame(cols).sort_index()
    macro.index.name = "date"
    macro.to_csv(C.MACRO_MONTHLY)
    pd.DataFrame(meta).to_csv(C.MACRO_META, index=False)
    if macro.empty:
        print("[macro] ERROR: no series fetched (check network / FRED availability)")
    else:
        print(f"[macro] via {key_mode}: {macro.shape[1]} indicators, "
              f"{macro.index.min().date()}..{macro.index.max().date()} -> {C.MACRO_MONTHLY.name}")
    return macro


if __name__ == "__main__":
    run()
