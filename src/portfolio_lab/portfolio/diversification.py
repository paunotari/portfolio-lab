"""Look-through diversification / concentration analysis.

Given a portfolio (index sleeves + weights), roll the underlying sector, country and single-stock
exposures up to the portfolio level and flag concentration (Herfindahl + threshold breaches).

    from portfolio_lab.portfolio.diversification import analyze_portfolio
    analyze_portfolio({"MSCI USA Momentum Index": 0.4, "MSCI Emerging Markets Index": 0.6})

Notes:
- Sector & country roll-ups are EXACT (source weights sum to ~100% per index).
- USA indices carry no country chart (single country) -> injected as 100% United States.
- Single-stock roll-up uses each index's TOP-10 only, so stock exposure is a LOWER BOUND.

Run:  python -m portfolio_lab.portfolio.diversification   (uses data/processed/portfolio.csv or example)
"""
from __future__ import annotations
import csv
from collections import defaultdict

from portfolio_lab import config as C

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
    usa = {r["index_name"] for r in _load(C.INDEX_META) if r["region"] == "USA"}
    return sec, ctry, stk, usa


def _hhi(weights_pct):
    f = [w / 100.0 for w in weights_pct.values()]
    h = sum(x * x for x in f)
    return h, (1.0 / h if h else float("nan"))


def analyze_portfolio(weights: dict, name: str = "portfolio", write: bool = True) -> dict:
    sec_by, ctry_by, stk_by, usa_idx = _load_tables()
    known = sorted(sec_by)
    bad = [k for k in weights if k not in known]
    if bad:
        raise ValueError(f"unknown index name(s): {bad}\nknown:\n  " + "\n  ".join(known))
    tot = sum(weights.values())
    w = {k: v / tot for k, v in weights.items() if v}

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

    result = dict(weights=w, sector=sec, country=ctry, stock=stk, hhi=hhi, flags=flags)
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
