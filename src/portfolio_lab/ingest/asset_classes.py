"""Non-equity asset-class PROXY returns (bonds / gold / cash) -> asset_class_monthly.csv.

Data roadmap P1's free slice (info/TODO.md): the sleeves that structurally win where equities
lose — bonds in deflationary busts, gold in stagflation, cash as the floor — so the maximin mode
can be a real all-weather instead of reshuffling equities. All three are free:

- "Asset | US Treasury 10y": total return CONSTRUCTED from the 10y constant-maturity yield
  already in macro_monthly.csv (FRED ust_10y, 1953+) with the standard carry + duration +
  convexity approximation for a par bond (Swinkels 2019, *Data* 4(3):91 — the published method
  for exactly this):    r_t = y_{t-1}/12 - D(y_t)*dy + 0.5*C(y_t)*dy^2
  with par-bond closed forms D = (1/y)(1-(1+y)^-M), C = (2/y^2)(1-(1+y)^-M) - 2M/(y(1+y)^(M+1)),
  M = 10. Deterministic arithmetic on a published yield — allowed side of caveat #11.
- "Asset | Gold": monthly price return from the datasets/gold-prices LBMA mirror (1833+,
  currently maintained). Pre-1971 the price was pegged (Bretton Woods) — returns exist but are
  near-zero by construction; any long-history use should start ~1971, documented where used.
- "Asset | Cash (T-bill)": the Fama-French RF series (ff_factors_monthly.csv) as-is.

These are PROXIES, not investable index sleeves: no factsheets, no look-through, no registry row
(deliberate — the registry is the investable menu). The optimizer consumes them only when
explicitly asked (include_asset_classes=True); the product default stays equity-only per the
house thesis. Column naming follows the "REGION | NAME" convention with region "Asset" so every
split(" | ") downstream keeps working.

Network: only gold needs it (WARN + keep previous file on failure, like ingest/macro.py); bond
and cash come from already-processed local files.

Run:  python -m portfolio_lab.ingest.asset_classes
"""
from __future__ import annotations
import io
import ssl
import urllib.request

import certifi
import numpy as np
import pandas as pd

from portfolio_lab import config as C

MATURITY = 10  # years, par-bond approximation


def _bond_total_return() -> pd.Series | None:
    if not C.MACRO_MONTHLY.exists():
        return None
    macro = pd.read_csv(C.MACRO_MONTHLY, index_col=0, parse_dates=True).sort_index()
    if "ust_10y" not in macro.columns:
        return None
    y = (macro["ust_10y"] / 100.0).dropna()
    y_prev = y.shift(1)
    dy = y - y_prev
    dur = (1.0 / y) * (1.0 - (1.0 + y) ** -MATURITY)
    conv = (2.0 / y ** 2) * (1.0 - (1.0 + y) ** -MATURITY) \
        - (2.0 * MATURITY) / (y * (1.0 + y) ** (MATURITY + 1))
    r = y_prev / 12.0 - dur * dy + 0.5 * conv * dy ** 2
    return r.dropna().rename("Asset | US Treasury 10y")


def _gold_return() -> pd.Series | None:
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(C.GOLD_PRICES_URL, context=ctx, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
        px = pd.read_csv(io.StringIO(raw))
        px.index = pd.PeriodIndex(px["Date"], freq="M").to_timestamp("M")
        return px["Price"].pct_change().dropna().rename("Asset | Gold")
    except Exception as e:
        print(f"[asset_classes] WARN gold fetch failed ({e}) — skipping")
        return None


def _cash_return() -> pd.Series | None:
    if not C.FF_FACTORS_MONTHLY.exists():
        return None
    ff = pd.read_csv(C.FF_FACTORS_MONTHLY, index_col=0, parse_dates=True)
    return ff["rf"].dropna().rename("Asset | Cash (T-bill)")


def run():
    C.ensure_dirs()
    parts = [s for s in (_bond_total_return(), _gold_return(), _cash_return()) if s is not None]
    if not parts:
        print("[asset_classes] no sources available — nothing written")
        return
    df = pd.concat(parts, axis=1, sort=False).sort_index()
    df.index.name = "date"
    df.to_csv(C.ASSET_CLASS_MONTHLY)
    spans = ", ".join(f"{c.split(' | ')[1]} {df[c].dropna().index[0].year}+" for c in df.columns)
    print(f"[asset_classes] wrote {C.ASSET_CLASS_MONTHLY} ({len(df.columns)} sleeves: {spans})")


if __name__ == "__main__":
    run()
