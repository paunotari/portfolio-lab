"""Ken French GLOBAL factors -> ff_global_factors_monthly.csv (v2.0).

The menu spans ACWI, World, the USA, Europe, Japan, EM and AC Asia ex Japan, so its strategies
are priced against global factors, not the US set in ``ingest/ff_factors.py``. Ken French's
"Developed" files are the global set (23 developed markets); the emerging-markets files price
what Developed leaves out. Both start July 1990 (momentum November 1990), in USD, monthly.

Columns written (fractions, month-end PERIOD stamps on calendar month-ends):
  dev_mkt_rf, dev_smb, dev_hml, dev_rmw, dev_cma, dev_wml, rf,
  em_mkt_rf, em_smb, em_hml, em_rmw, em_cma, em_wml

``rf`` is Ken French's one-month T-bill (the same series in every file; taken from Developed).

Alignment warning, and the reason ``align`` exists: the MSCI levels are stamped on BUSINESS
month-ends (2009-01-30) and Ken French on CALENDAR month-ends (2009-01-31). An exact-date join
silently keeps only the months where the two coincide — 148 of the 210 OOS months, which is
exactly the "risk-free covers only 148 months" note in MILESTONES M40. Join on the month
period, always.

Network-dependent: WARN and keep the previous file on failure, like ``ingest/ff_factors.py``.

Run:  python -m portfolio_lab.v2.factors
"""
from __future__ import annotations

import io

import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.ingest.ff_factors import _ROW, _fetch_csv_lines

_RENAME = {"Mkt-RF": "mkt_rf", "SMB": "smb", "HML": "hml", "RMW": "rmw", "CMA": "cma",
           "WML": "wml", "RF": "rf"}


def _parse_monthly(lines: list[str]) -> pd.DataFrame:
    """Same block extraction as ``ingest.ff_factors._parse_monthly``, but missing values are
    masked with ``where`` instead of ``replace([...], pd.NA)``, which raises inside pandas 3.0
    on the emerging-markets file (IndexError in ``replace_list``)."""
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
    df = df.apply(pd.to_numeric, errors="coerce").astype(float)
    return df.where(~df.isin([-99.99, -999.0])) / 100.0


def fetch() -> pd.DataFrame:
    frames = {}
    for key, stem in C.FF_GLOBAL_FILES.items():
        df = _parse_monthly(_fetch_csv_lines(C.FF_GLOBAL_BASE.format(stem)))
        df.columns = [_RENAME.get(c.strip(), c.strip().lower()) for c in df.columns]
        frames[key] = df
    dev = pd.concat([frames["dev5"], frames["dev_mom"]], axis=1, sort=True)
    em = pd.concat([frames["em5"].drop(columns="rf"), frames["em_mom"]], axis=1, sort=True)
    out = pd.concat([dev.add_prefix("dev_").rename(columns={"dev_rf": "rf"}),
                     em.add_prefix("em_")], axis=1, sort=True)
    out.index.name = "date"
    return out.astype(float)


def fetch_aqr() -> pd.DataFrame:
    """AQR global Betting-Against-Beta and Quality-Minus-Junk factors (monthly, USD, the
    'Global' column of each workbook's first sheet; header on row 19). Free research data;
    AQR's terms of use apply."""
    import tempfile
    import urllib.request
    import ssl
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
    cols = {}
    for key, (stem, sheet) in C.AQR_FILES.items():
        req = urllib.request.Request(C.AQR_BASE.format(stem), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=120) as r, \
                tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp:
            tmp.write(r.read())
            tmp.flush()
            d = pd.read_excel(tmp.name, sheet_name=sheet, header=18)
        d["DATE"] = pd.to_datetime(d["DATE"])
        cols[key] = d.set_index("DATE")["Global"].astype(float)
    out = pd.DataFrame(cols)
    out.index = out.index.to_period("M").to_timestamp("M")
    out.index.name = "date"
    return out


def run() -> pd.DataFrame | None:
    C.ensure_dirs()
    try:
        df = fetch()
    except Exception as e:                                   # network/parse: warn, not fail
        print(f"[v2.factors] WARN fetch failed ({e}) — "
              + ("keeping existing file" if C.FF_GLOBAL_MONTHLY.exists() else "no file written"))
        return None
    try:                                                     # AQR BAB / QMJ (optional)
        df = df.join(fetch_aqr(), how="left")
    except Exception as e:
        print(f"[v2.factors] WARN AQR fetch failed ({e}) — BAB/QMJ models will be skipped")
    df.to_csv(C.FF_GLOBAL_MONTHLY)
    print(f"[v2.factors] wrote {C.FF_GLOBAL_MONTHLY} ({len(df)} months, "
          f"{df.index[0].date()} -> {df.index[-1].date()}, cols: {', '.join(df.columns)})")
    return df


def load() -> pd.DataFrame:
    if not C.FF_GLOBAL_MONTHLY.exists():
        run()
    return pd.read_csv(C.FF_GLOBAL_MONTHLY, index_col=0, parse_dates=True)


def align(frame: pd.DataFrame | pd.Series, factors: pd.DataFrame = None) -> pd.DataFrame:
    """Factor rows for the months of `frame`, matched on the month PERIOD and re-stamped
    with `frame`'s own index (see the module docstring for why an exact-date join is wrong)."""
    f = load() if factors is None else factors
    f = f.copy()
    f.index = f.index.to_period("M")
    out = f.reindex(frame.index.to_period("M"))
    out.index = frame.index
    return out


if __name__ == "__main__":
    run()
