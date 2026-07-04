"""Build the self-contained HTML dashboard from processed data + analytics output.

All data is baked into a single file as JSON; Plotly loads from CDN; the diversification tab
rolls up live in the browser. Output: outputs/dashboard.html (double-click to open).

Run:  python -m portfolio_lab.dashboard.build
"""
from __future__ import annotations
import csv
import json
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.regimes import REGIMES
from portfolio_lab.dashboard.template import HTML, JS


def _rd(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def _collect_data() -> dict:
    perf = _rd(C.PERFORMANCE_SUMMARY)
    for r in perf:
        for k in ("cw_CAGR", "cw_ann_vol", "cw_sharpe_rf0", "cw_max_drawdown", "full_CAGR"):
            r[k] = float(r[k])
    fvr = _rd(C.FACTOR_VS_REFERENCE)
    for r in fvr:
        for k in ("ref_CAGR", "factor_CAGR", "excess_CAGR", "monthly_hit_rate"):
            r[k] = float(r[k])
    regperf = _rd(C.REGIME_PERFORMANCE)
    for r in regperf:
        for k in ("total_return", "annualized", "ann_vol"):
            r[k] = float(r[k])
        r["excess_vs_ref"] = None if r["excess_vs_ref"] in ("", "nan") else float(r["excess_vs_ref"])
    regime_meta = [{k: rg[k] for k in ("id", "name", "start", "end", "macro", "factors", "regions", "shift")}
                   for rg in REGIMES]

    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0)
    levels = {"dates": list(lv.index),
              "series": {c: [None if pd.isna(x) else round(x, 3) for x in lv[c]] for c in lv.columns}}

    def load_corr(path):
        df = pd.read_csv(path, index_col=0)
        return {"labels": list(df.columns), "z": [[round(v, 3) for v in row] for row in df.values]}
    corr = {"full": load_corr(C.CORRELATION_FULL)}
    for rg in REGIMES:
        p = C.CORR_REGIME_DIR / f"{rg['id']}.csv"
        if p.exists():
            corr[rg["id"]] = load_corr(p)
    roll = _rd(C.ROLLING_CORRELATION)
    rcol = [c for c in roll[0].keys() if c != "date"][0]
    rolling = {"dates": [r["date"] for r in roll], "vals": [float(r[rcol]) for r in roll]}

    def by_index(rows, key):
        d = {}
        for r in rows:
            d.setdefault(r["index_name"], {})[r[key]] = float(r["weight_pct"])
        return d
    sec_by = by_index(_rd(C.SECTOR_WEIGHTS), "sector")
    ctry_by = by_index(_rd(C.COUNTRY_WEIGHTS), "country")
    stk_by = by_index(_rd(C.TOP_CONSTITUENTS), "constituent")
    usa_idx = [r["index_name"] for r in _rd(C.INDEX_META) if r["region"] == "USA"]

    return dict(perf=perf, fvr=fvr, regperf=regperf, regime_meta=regime_meta, levels=levels,
                corr=corr, rolling=rolling, sec_by=sec_by, ctry_by=ctry_by, stk_by=stk_by,
                usa_idx=usa_idx, indices=sorted(sec_by.keys()),
                thresh=C.CONCENTRATION_THRESHOLDS, country_fix=C.COUNTRY_FIX)


def build():
    C.ensure_dirs()
    data = _collect_data()
    html = HTML.replace("__DATA__", json.dumps(data)).replace("__JS__", JS)
    C.DASHBOARD_HTML.write_text(html)
    print(f"[dashboard] wrote {C.DASHBOARD_HTML} ({len(html)//1024} KB)")


if __name__ == "__main__":
    build()
