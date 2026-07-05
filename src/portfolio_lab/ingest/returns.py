"""Ingest monthly index-level series from the MSCI '...FULL...Monthly.xlsx' exports.

Each workbook has a header row (col A = 'Date', col B = index name) followed by month-end
levels rebased to 100. We emit two tidy files:

  returns_monthly_long.csv : date, index_id, index_name, region, factor_type, level, ret
  levels_wide.csv          : date index x one column per series ("<region> | <factor_type>")

Run:  python -m portfolio_lab.ingest.returns
"""
from __future__ import annotations
import re
import openpyxl
import pandas as pd

from portfolio_lab import config as C

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _read_workbook(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    data = list(ws.iter_rows(values_only=True))
    hdr = next(i for i, r in enumerate(data) if r and r[0] == "Date")
    idx_name = data[hdr][1]
    out = []
    for r in data[hdr + 1:]:
        if not r or r[0] is None or r[1] is None:
            continue
        d = str(r[0])[:10]
        if _DATE_RE.match(d):
            out.append((d, float(r[1])))
    return idx_name, out


def run() -> pd.DataFrame:
    C.ensure_dirs()
    rows = []
    for region in C.REGIONS:
        for f in sorted((C.RAW_DIR / region).glob("*FULL*.xlsx")):
            index_id = f.name.split(" - ")[0].strip()
            idx_name, series = _read_workbook(f)
            ft = C.factor_type(idx_name)
            for d, lvl in series:
                rows.append([d, index_id, idx_name, region, ft, lvl])

    df = pd.DataFrame(rows, columns=["date", "index_id", "index_name",
                                     "region", "factor_type", "level"])
    df = df.sort_values(["region", "factor_type", "date"]).reset_index(drop=True)
    df["ret"] = df.groupby(["region", "factor_type"])["level"].pct_change()
    df.to_csv(C.RETURNS_LONG, index=False)

    df["col"] = df["region"] + " | " + df["factor_type"]
    wide = df.pivot_table(index="date", columns="col", values="level")
    wide.to_csv(C.LEVELS_WIDE)

    print(f"[returns] {len(df)} rows, {wide.shape[1]} series, "
          f"{wide.index.min()}..{wide.index.max()} -> {C.RETURNS_LONG.name}, {C.LEVELS_WIDE.name}")
    return df


if __name__ == "__main__":
    run()
