"""Look-through diversification / concentration analysis.

Given a portfolio (index sleeves + weights), roll the underlying sector, country and single-stock
exposures up to the portfolio level and flag concentration (Herfindahl + threshold breaches), and
compute the blended portfolio's own CAGR/vol/Sharpe/max-drawdown.

    from portfolio_lab.portfolio.diversification import analyze_portfolio
    analyze_portfolio({"MSCI USA Momentum Index": 0.4, "MSCI Emerging Markets Index": 0.6})

Weights are fractions of the portfolio and MUST sum to 1.0 (100%) within
config.PORTFOLIO_WEIGHT_TOLERANCE_PCT — a portfolio cannot hold more or less than itself, so this
raises ValueError rather than silently rescaling an input like {"A": 1.5, "B": 1.9} (340%).

Notes:
- Sector & country roll-ups are EXACT (source weights sum to ~100% per index).
- USA indices carry no country chart (single country) -> injected as 100% United States.
- Single-stock roll-up uses each index's TOP-10 only, so stock exposure is a LOWER BOUND.
- Portfolio performance is a constant-mix blend (monthly rebalance to target weights) of the
  selected sleeves' own return series, computed over their overlapping history (not necessarily
  the full 21-series common window) — see analytics/engine.py's _perf_stats for the stat formulas.

Run:  python -m portfolio_lab.portfolio.diversification   (uses data/processed/portfolio.csv or example)
"""
from __future__ import annotations
import csv
from collections import defaultdict

import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.engine import _perf_stats

EXAMPLE = {"MSCI USA Momentum Index": 0.40,
           "MSCI AC Asia ex Japan Momentum Index": 0.30,
           "MSCI Emerging Markets Index": 0.30}


def _load(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def _by_index(rows, key):
    d = defaultdict(dict)
    for r in rows:
        d[r["index_name"]][r[key]] = float(r["weight_pct"])
    return d


def _load_tables():
    sec = _by_index(_load(C.SECTOR_WEIGHTS), "sector")
    ctry = _by_index(_load(C.COUNTRY_WEIGHTS), "country")
    stk = _by_index(_load(C.TOP_CONSTITUENTS), "constituent")
    meta = _load(C.INDEX_META)
    usa = {r["index_name"] for r in meta if r["region"] == "USA"}
    series_key = {r["index_name"]: f"{r['region']} | {r['factor_type']}" for r in meta}
    return sec, ctry, stk, usa, series_key


def _hhi(weights_pct):
    f = [w / 100.0 for w in weights_pct.values()]
    h = sum(x * x for x in f)
    return h, (1.0 / h if h else float("nan"))


def _validate_weights(weights: dict, known: list[str]) -> dict:
    bad = [k for k in weights if k not in known]
    if bad:
        raise ValueError(f"unknown index name(s): {bad}\nknown:\n  " + "\n  ".join(known))
    neg = {k: v for k, v in weights.items() if v < 0}
    if neg:
        raise ValueError(f"portfolio weights must be non-negative, got: {neg}")
    tot_pct = sum(weights.values()) * 100
    tol = C.PORTFOLIO_WEIGHT_TOLERANCE_PCT
    if abs(tot_pct - 100.0) > tol:
        raise ValueError(
            f"portfolio weights must sum to 100% (got {tot_pct:.1f}%). A portfolio can't hold "
            f"more or less than itself — pass weights that already sum to 1.0 (e.g. "
            f"0.4 + 0.3 + 0.3), rather than relying on auto-normalization."
        )
    return {k: v for k, v in weights.items() if v > 0}


def portfolio_performance(w: dict, series_key: dict) -> dict | None:
    """Blended (constant-mix) CAGR/vol/Sharpe/maxDD for the given weights, over the sleeves'
    overlapping history. Returns None if fewer than 2 overlapping months exist."""
    cols = {idx: series_key[idx] for idx in w if idx in series_key}
    if len(cols) < len(w):
        return None  # a selected sleeve has no known return series
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    sub = lv[list(cols.values())].dropna()
    if len(sub) < 2:
        return None
    rets = sub.pct_change().dropna()
    blended = sum(rets[cols[idx]] * w[idx] for idx in cols)
    level = 100.0 * (1 + blended).cumprod()
    level = pd.concat([pd.Series([100.0], index=[sub.index[0]]), level])
    return _perf_stats(level)


def analyze_portfolio(weights: dict, name: str = "portfolio", write: bool = True) -> dict:
    sec_by, ctry_by, stk_by, usa_idx, series_key = _load_tables()
    w = _validate_weights(weights, sorted(sec_by))

    sec, ctry, stk = defaultdict(float), defaultdict(float), defaultdict(float)
    for idx, sw in w.items():
        for s, p in sec_by[idx].items():
            sec[s] += sw * p
        cw = ctry_by.get(idx) or ({"United States": 100.0} if idx in usa_idx else {})
        for c, p in cw.items():
            ctry[C.COUNTRY_FIX.get(c, c)] += sw * p
        for st, p in stk_by[idx].items():
            stk[st] += sw * p

    order = lambda d: dict(sorted(d.items(), key=lambda x: -x[1]))
    sec, ctry, stk = order(sec), order(ctry), order(stk)
    T = C.CONCENTRATION_THRESHOLDS
    flags = {"sector": [k for k, v in sec.items() if v > T["sector"]],
             "country": [k for k, v in ctry.items() if v > T["country"]],
             "stock": [k for k, v in stk.items() if v > T["stock"]]}
    hhi = {"sector": _hhi(sec), "country": _hhi(ctry), "stock": _hhi(stk)}
    performance = portfolio_performance(w, series_key)

    result = dict(weights=w, sector=sec, country=ctry, stock=stk, hhi=hhi, flags=flags,
                 performance=performance)
    if write:
        _write(name, result)
    return result


def _write(name, res):
    C.ensure_dirs()
    for tag in ("sector", "country", "stock"):
        with open(C.DIVERSIFICATION_DIR / f"{name}_{tag}.csv", "w", newline="") as f:
            wr = csv.writer(f); wr.writerow([tag, "weight_pct"])
            wr.writerows([[k, round(v, 3)] for k, v in res[tag].items()])
    (C.DIVERSIFICATION_DIR / f"{name}.md").write_text(render(name, res))


def render(name, res) -> str:
    T = C.CONCENTRATION_THRESHOLDS
    L = [f"# Look-through diversification — {name}\n", "## Sleeves"]
    L += [f"- {v*100:5.1f}%  {k}" for k, v in sorted(res["weights"].items(), key=lambda x: -x[1])]

    perf = res.get("performance")
    L.append("\n## Portfolio performance (constant-mix blend)")
    if perf is None:
        L.append("Insufficient overlapping history among the selected sleeves (<2 months).")
    else:
        L.append(f"Window: {perf['start']} → {perf['end']} ({perf['months']} months)")
        L.append(f"CAGR {perf['CAGR']*100:.1f}% | Ann vol {perf['ann_vol']*100:.1f}% | "
                 f"Sharpe(rf0) {perf['sharpe_rf0']:.2f} | Max drawdown {perf['max_drawdown']*100:.1f}%")

    for title, data, kind in [("Sector", res["sector"], "sector"),
                              ("Country", res["country"], "country"),
                              ("Single-stock (top-10 look-through — lower bound)", res["stock"], "stock")]:
        h, eff = res["hhi"][kind]
        vals = list(data.values())
        L.append(f"\n## {title} exposure")
        L.append(f"HHI {h:.3f} | effective # {eff:.1f} | top-1 {vals[0]:.1f}% | top-3 {sum(vals[:3]):.1f}%")
        for k, v in data.items():
            if v >= 0.5 or v > T[kind]:
                L.append(f"  {v:6.1f}%  {k}{'  ⚠️ OVER' if v > T[kind] else ''}")
    L.append("\n## Verdict")
    fl = [f"{k}: {', '.join(v)}" for k, v in res["flags"].items() if v]
    L.append("Concentration warnings — " + " ; ".join(fl) if fl
             else "No exposure exceeds the configured thresholds.")
    L.append(f"(thresholds: sector>{T['sector']:.0f}%, country>{T['country']:.0f}%, stock>{T['stock']:.0f}%)")
    return "\n".join(L)


def _load_portfolio_csv(path):
    return {r["index_name"]: float(r["weight"]) for r in _load(path)}


def run():
    """CLI entrypoint: analyze data/processed/portfolio.csv if present, else the built-in example."""
    pf = C.PROCESSED_DIR / "portfolio.csv"
    if pf.exists():
        weights, name = _load_portfolio_csv(pf), "portfolio"
    else:
        weights, name = EXAMPLE, "example"
    res = analyze_portfolio(weights, name=name)
    print(render(name, res))
    print(f"\n(written to {C.DIVERSIFICATION_DIR}/{name}.md and *_sector/country/stock.csv)")


if __name__ == "__main__":
    run()
