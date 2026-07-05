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
        for k in ("CAGR", "ann_vol", "sharpe_rf0", "max_drawdown"):
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
    index_meta_rows = _rd(C.INDEX_META)
    usa_idx = [r["index_name"] for r in index_meta_rows if r["region"] == "USA"]
    # index_name -> "<region> | <factor_type>" — the column key in levels_wide.csv / DATA.levels,
    # so the dashboard's live diversification widget can blend each sleeve's own return series.
    idx_series_key = {r["index_name"]: f"{r['region']} | {r['factor_type']}" for r in index_meta_rows}

    # macro series + meta + index<->macro correlation matrices (optional: skipped when absent)
    macro = macro_meta = macro_corr = None
    if C.MACRO_MONTHLY.exists() and C.MACRO_CORR_CONTEMP_CHG.exists():
        mm = pd.read_csv(C.MACRO_MONTHLY, index_col=0)
        macro = {"dates": list(mm.index),
                 "series": {c: [None if pd.isna(x) else round(float(x), 3) for x in mm[c]]
                            for c in mm.columns}}
        macro_meta = _rd(C.MACRO_META)

        def load_wide(path):
            df = pd.read_csv(path, index_col=0)
            return {"series": list(df.index), "indicators": list(df.columns),
                    "z": [[None if pd.isna(v) else round(float(v), 3) for v in row]
                          for row in df.values]}
        macro_corr = {"level": load_wide(C.MACRO_CORR_CONTEMP_LEVEL),
                      "chg": load_wide(C.MACRO_CORR_CONTEMP_CHG)}

    # 4-quadrant macro-state + scenario simulation (optional: skipped when absent)
    macro_state = scenario = None
    if C.MACRO_STATE_MONTHLY.exists() and C.MACRO_STATE_PERFORMANCE.exists():
        ms = pd.read_csv(C.MACRO_STATE_MONTHLY, index_col=0, parse_dates=True)
        last = ms.iloc[-1]
        months_in = int((ms.state[::-1] == last.state).cumprod().sum())
        perf_state = _rd(C.MACRO_STATE_PERFORMANCE)
        for r in perf_state:
            for k in ("mean_monthly_return", "annualized_return", "ann_vol"):
                r[k] = float(r[k])
            r["n_months"] = int(r["n_months"])
        attr = _rd(C.MACRO_STATE_FACTOR_ATTRIBUTION) if C.MACRO_STATE_FACTOR_ATTRIBUTION.exists() else []
        for r in attr:
            for k in ("avg_monthly_excess", "hit_rate"):
                r[k] = float(r[k])
        freq = (ms.state.value_counts(normalize=True) * 100).round(1).to_dict()
        macro_state = {
            "dates": [str(d.date()) for d in ms.index],
            "states": list(ms.state),
            "freq": freq,
            "current": {
                "as_of": str(ms.index[-1].date()), "state": last.state,
                "months_in_state": months_in,
                "growth_dir": "accelerating" if last.growth_up else "decelerating",
                "growth_value": round(float(last.growth_value), 2),
                "inflation_dir": "accelerating" if last.inflation_up else "decelerating",
                "inflation_value": round(float(last.inflation_value), 2),
            },
            "performance": perf_state, "attribution": attr,
        }
    if C.SCENARIO_SUMMARY.exists():
        rows = _rd(C.SCENARIO_SUMMARY)
        for r in rows:
            for k in ("cagr_p5", "cagr_p25", "cagr_p50", "cagr_p75", "cagr_p95",
                      "maxdd_p5", "maxdd_p50", "maxdd_p95", "prob_cumulative_loss"):
                r[k] = float(r[k])
        scenario = {"rows": rows, "years": C.SCENARIO_YEARS, "trials": C.SCENARIO_TRIALS}

    return dict(perf=perf, fvr=fvr, regperf=regperf, regime_meta=regime_meta, levels=levels,
                corr=corr, rolling=rolling, sec_by=sec_by, ctry_by=ctry_by, stk_by=stk_by,
                usa_idx=usa_idx, indices=sorted(sec_by.keys()), idx_series_key=idx_series_key,
                thresh=C.CONCENTRATION_THRESHOLDS, country_fix=C.COUNTRY_FIX,
                weight_tolerance_pct=C.PORTFOLIO_WEIGHT_TOLERANCE_PCT,
                macro=macro, macro_meta=macro_meta, macro_corr=macro_corr,
                macro_state=macro_state, scenario=scenario)


def run():
    C.ensure_dirs()
    data = _collect_data()
    html = HTML.replace("__DATA__", json.dumps(data)).replace("__JS__", JS)
    C.DASHBOARD_HTML.write_text(html)
    print(f"[dashboard] wrote {C.DASHBOARD_HTML} ({len(html)//1024} KB)")


if __name__ == "__main__":
    run()
