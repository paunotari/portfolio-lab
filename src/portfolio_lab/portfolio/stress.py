"""Named-episode stress library (research roadmap A3): replay history's worst stretches.

Percentile cones say "how bad could it get, statistically"; this module answers the question
people actually ask: **"what would this portfolio have done in 2008? In the 1970s?"** Two
tables, one method (subset the real return matrix to a hand-dated episode, compound):

1. MODERN — the optimizer's flagship portfolios (balanced, the maximin family) and the anchor
   benchmarks, through every named episode inside the MSCI window (dot-com, GFC, COVID, 2022).
   Weights are today's recommendations held constant-mix through the episode — a stress replay,
   not a backtest of past decisions.
2. HISTORIC — four static ARCHETYPE allocations (pure equity, 60/40, all-weather static)
   through a century of episodes on the proxy universe (OPEC stagflation, Volcker, 1987, ...).
   Archetypes are deliberately static and simple: the point is how ALLOCATION SHAPES behave in
   each kind of storm, uncontaminated by any optimizer's estimates.

Outputs: outputs/analytics/stress/{stress_summary.csv, REPORT_stress.md}. Episode dates in
config.STRESS_EPISODES_*; all replay caveats of the underlying data apply (proxy sleeves are
research constructs; gold pre-1971 managed).

Run:  python -m portfolio_lab.portfolio.stress
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.portfolio import optimizer as opt
from portfolio_lab.portfolio.proxy_backtest import load_universes


def _episode_stats(rets: pd.DataFrame, w: dict, start: str, end: str) -> dict | None:
    """Cumulative return, max drawdown and worst month of a constant-mix allocation inside
    [start, end] — None if the window isn't covered by the data."""
    win = rets.loc[start:end]
    if len(win) < 2 or win.index[0] > pd.Timestamp(start) + pd.offsets.MonthEnd(2):
        return None
    wv = np.array([w.get(c, 0.0) for c in rets.columns])
    r = win.values @ wv
    cum = np.cumprod(1.0 + r)
    return dict(cum_return=float(cum[-1] - 1.0),
                max_drawdown=float((cum / np.maximum.accumulate(cum) - 1.0).min()),
                worst_month=float(r.min()), n_months=len(win))


def _modern_portfolios() -> tuple[pd.DataFrame, dict[str, dict]]:
    """(MSCI-window returns, {portfolio: weights-by-column}) for flagships + anchors."""
    inp = opt.build_inputs()
    ports = {name: dict(zip(inp["series"], map(float, w))) for name, w in inp["anchors"].items()}
    flag = {"Balanced sliders (5/5/5)": opt.optimize(
        prefs={"return": 5, "risk": 5, "diversification": 5}, inputs=inp)}
    if inp["mu_q"] is not None:
        div_kw = dict(cap=C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT / 100.0,
                      geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0,
                      factor_cap=C.OPTIMIZER_FACTOR_CAP_PCT / 100.0)
        flag["Maximin (diversified)"] = opt.optimize(maximin=True, inputs=inp, **div_kw)
        if C.ASSET_CLASS_MONTHLY.exists():
            try:
                inp_aw = opt.build_inputs(include_asset_classes=True)
                if inp_aw["mu_q"] is not None:
                    flag["Maximin (all-weather)"] = opt.optimize(maximin=True, inputs=inp_aw,
                                                                **div_kw)
            except Exception as e:
                print(f"[stress] WARN all-weather skipped ({e})")
    rets = opt.load_returns(include_asset_classes=C.ASSET_CLASS_MONTHLY.exists())
    for name, res in flag.items():
        ports[name] = dict(zip(res["all_series"], map(float, res["w"])))
    return rets, ports


def _archetype_weights(cols: list[str]) -> dict[str, dict]:
    """Expand config archetypes onto the proxy universe columns ('equity_equal' spreads over
    the FF equity portfolios)."""
    eq_cols = [c for c in cols if c.startswith("Proxy | ")]
    out = {}
    for name, spec in C.STRESS_ARCHETYPES.items():
        w = {}
        for key, frac in spec.items():
            if key == "equity_equal":
                for c in eq_cols:
                    w[c] = w.get(c, 0.0) + frac / len(eq_cols)
            elif key in cols:
                w[key] = w.get(key, 0.0) + frac
        if abs(sum(w.values()) - 1.0) < 0.01:
            out[name] = w
    return out


def run():
    C.ensure_dirs()
    rows = []

    if C.LEVELS_WIDE.exists():
        rets_m, ports = _modern_portfolios()
        for ep, (s, e) in C.STRESS_EPISODES_MODERN.items():
            for name, w in ports.items():
                st = _episode_stats(rets_m, w, s, e)
                if st:
                    rows.append(dict(table="modern", episode=ep, start=s[:7], end=e[:7],
                                     portfolio=name, **st))

    proxies = load_universes().get("multi_asset")
    if proxies is not None:
        for ep, (s, e) in C.STRESS_EPISODES_HISTORIC.items():
            for name, w in _archetype_weights(list(proxies.columns)).items():
                st = _episode_stats(proxies, w, s, e)
                if st:
                    rows.append(dict(table="historic", episode=ep, start=s[:7], end=e[:7],
                                     portfolio=name, **st))

    if not rows:
        print("[stress] no inputs available — skipping")
        return
    df = pd.DataFrame(rows)
    df.to_csv(C.STRESS_SUMMARY, index=False)
    _write_report(df)
    print(f"[stress] wrote {C.STRESS_SUMMARY} and {C.STRESS_REPORT}")
    return df


def _write_report(df: pd.DataFrame):
    L = ["# Named-episode stress library", "",
         "Real months, real episodes, constant-mix replay. Modern table: today's recommended "
         "weights through each storm in the MSCI window (a stress replay, not a claim the "
         "optimizer would have held them then). Historic table: static allocation archetypes "
         "through a century of storms on the proxy universe — how allocation SHAPES behave, "
         "free of any optimizer's estimates.", ""]
    for table, title in (("modern", "Flagships & anchors — MSCI window"),
                         ("historic", "Archetypes — a century of storms (proxy universe)")):
        sub = df[df.table == table]
        if sub.empty:
            continue
        L += [f"## {title}", ""]
        for ep in sub.episode.unique():
            g = sub[sub.episode == ep].sort_values("cum_return", ascending=False)
            L += [f"### {ep} ({g.iloc[0].start} → {g.iloc[0].end})", "",
                  "| portfolio | cumulative | maxDD | worst month |", "|---|---|---|---|"]
            for _, r in g.iterrows():
                L += [f"| {r.portfolio} | {r.cum_return:+.1%} | {r.max_drawdown:.1%} | "
                      f"{r.worst_month:.1%} |"]
            L += [""]
    C.STRESS_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    run()
