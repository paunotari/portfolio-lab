"""Fama-French research factors from Ken French's data library -> ff_factors_monthly.csv.

Monthly Mkt-RF / SMB / HML / RF (1926-07+) and Mom (1927-01+), the longest freely available
factor-return record there is. Purpose (info/TODO.md data roadmap P2): a LONG-HISTORY PROXY for
the regime layer — with ~66 years of classifiable macro history instead of ~28, the per-quadrant
factor patterns can be checked against the real 1970s stagflation instead of only its 2021-22
echo. These are research series, NOT investable sleeves: deliberately kept out of the index
registry, never fed to the optimizer as assets (analytics/long_history.py is the only consumer).

Source: Ken French's data library (Dartmouth) — free, publicly redistributed, not FRED (so the
caveat-#11 ToS line doesn't apply). Files are zipped CSVs with a text preamble, a monthly block
(YYYYMM rows, values in percent, -99.99 = missing), then an annual block we discard.

Network-dependent like ingest/macro.py: failures WARN and keep the previous CSV rather than
failing the pipeline.

Run:  python -m portfolio_lab.ingest.ff_factors
"""
from __future__ import annotations
import io
import re
import ssl
import urllib.request
import zipfile

import certifi
import pandas as pd

from portfolio_lab import config as C

_ROW = re.compile(r"^\s*(\d{6})\s*,")


def _fetch_csv_lines(url: str) -> list[str]:
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx, timeout=60) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
        return z.read(z.namelist()[0]).decode("latin-1").splitlines()


def _parse_monthly(lines: list[str]) -> pd.DataFrame:
    """Extract the monthly block: starts at the first YYYYMM row, ends at the first row that
    isn't one (the annual section). Percent -> fraction; -99.99 -> NaN."""
    header, rows, started = None, [], False
    for i, line in enumerate(lines):
        if _ROW.match(line):
            if not started:
                header = [h.strip() for h in lines[i - 1].split(",")][1:]
                started = True
            rows.append(line)
        elif started:
            break
    if not rows:
        raise ValueError("no monthly YYYYMM rows found")
    df = pd.read_csv(io.StringIO("\n".join(rows)), header=None, index_col=0)
    df.columns = header
    df.index = pd.PeriodIndex(df.index.astype(str), freq="M").to_timestamp("M")
    df = df.apply(pd.to_numeric, errors="coerce").replace(-99.99, pd.NA)
    return df / 100.0


def run():
    C.ensure_dirs()
    frames = []
    for name, url in C.FF_SOURCES.items():
        try:
            frames.append(_parse_monthly(_fetch_csv_lines(url)))
        except Exception as e:                                     # network/parse: warn, not fail
            print(f"[ff_factors] WARN {name} fetch failed ({e}) — skipping")
    if not frames:
        print("[ff_factors] nothing fetched; keeping existing file" if
              C.FF_FACTORS_MONTHLY.exists() else "[ff_factors] nothing fetched, no file written")
        return
    df = pd.concat(frames, axis=1)
    df.columns = [c.strip().lower().replace("-", "_") for c in df.columns]
    df.index.name = "date"
    df.to_csv(C.FF_FACTORS_MONTHLY)
    print(f"[ff_factors] wrote {C.FF_FACTORS_MONTHLY} "
          f"({len(df)} months, {df.index[0].date()} -> {df.index[-1].date()}, "
          f"cols: {', '.join(df.columns)})")


if __name__ == "__main__":
    run()
