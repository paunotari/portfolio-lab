"""Ken French INTERNATIONAL portfolios -> ff_intl_monthly.csv — the virgin universe.

Purpose (paper track item 2, MILESTONES M16): a confirmatory dataset the estimator NEVER
touched during development. For each developed region (Europe, Japan, Asia-Pacific ex Japan),
three MSCI-shaped sleeves so the frozen optimizer machinery applies verbatim:

  "FF <Region> | Reference"      = regional market total return (Mkt-RF + RF, regional
                                   3-factor file)
  "FF <Region> | Enhanced Value" = mean of the two high-B/M portfolios (SMALL HiBM, BIG HiBM)
                                   from the regional 6 size x book-to-market sort — a
                                   long-only value tilt, the FF analog of an Enhanced Value
                                   index
  "FF <Region> | Momentum"       = mean of the two winner portfolios (SMALL HiPRIOR,
                                   BIG HiPRIOR) from the regional 6 size x momentum sort

All USD, value-weighted, monthly, 1990-07+ (Ken French's developed-international start).
The factor labels are deliberately the registry's ("Enhanced Value"/"Momentum") so
`long_history.msci_factor_prior`'s frozen mapping (hml / mom, beta on modern overlap,
era-agreement gate) binds without any code change — that is the point of the test.

Same network discipline as ingest/ff_factors.py: WARN and keep the previous file on failure.
NOT a pipeline stage — fetched once by portfolio/ff_intl_test.py (or manually).

Run:  python -m portfolio_lab.ingest.ff_international
"""
from __future__ import annotations

import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.ingest.ff_factors import _fetch_csv_lines, _parse_monthly


def _hi_mean(df: pd.DataFrame) -> pd.Series:
    """Mean of the two 'Hi' columns of a 6-portfolio sort (SMALL Hi*, BIG Hi*)."""
    hi = [c for c in df.columns if "hi" in c.strip().lower()]
    if len(hi) != 2:
        raise ValueError(f"expected 2 'Hi' columns, got {hi} in {list(df.columns)}")
    return df[hi].mean(axis=1)


def run() -> pd.DataFrame | None:
    C.ensure_dirs()
    cols = {}
    for region, prefix in C.FF_INTL_REGIONS.items():
        try:
            fac = _parse_monthly(_fetch_csv_lines(C.FF_INTL_BASE.format(f"{prefix}_3_Factors")))
            fac.columns = [c.strip().lower().replace("-", "_") for c in fac.columns]
            bm = _parse_monthly(_fetch_csv_lines(
                C.FF_INTL_BASE.format(f"{prefix}_6_Portfolios_ME_BE-ME")))
            mom = _parse_monthly(_fetch_csv_lines(
                C.FF_INTL_BASE.format(f"{prefix}_6_Portfolios_ME_Prior_12_2")))
            cols[f"{region} | Reference"] = fac["mkt_rf"] + fac["rf"]
            cols[f"{region} | Enhanced Value"] = _hi_mean(bm)
            cols[f"{region} | Momentum"] = _hi_mean(mom)
        except Exception as e:                                  # network/parse: warn, not fail
            print(f"[ff_intl] WARN {region} fetch failed ({e}) — skipping region")
    if not cols:
        print("[ff_intl] nothing fetched; keeping existing file" if
              C.FF_INTL_MONTHLY.exists() else "[ff_intl] nothing fetched, no file written")
        return None
    df = pd.DataFrame(cols).dropna()
    df.index.name = "date"
    df.to_csv(C.FF_INTL_MONTHLY)
    print(f"[ff_intl] wrote {C.FF_INTL_MONTHLY.name}: {df.shape[1]} sleeves, "
          f"{len(df)} months, {df.index[0].date()} -> {df.index[-1].date()}")
    return df


if __name__ == "__main__":
    run()
