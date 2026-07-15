"""Walk-forward out-of-sample validation — the optimizer's honesty protocol.

Directive 7 of the literature synthesis (info/literature.md §4): validate like we forecast.
Every contestant re-estimates EVERYTHING (shrunk covariance, anchors, BL posterior, per-quadrant
means, transition matrix, outlook) on an expanding training window, holds the resulting weights
constant-mix for the next refit interval, and is judged only on months it never saw. Same
warmup/refit discipline as the quadrant-forecasting backtests (info/TODO.md, 2026-07).

Contestants: 1/N (the DeMiguel benchmark — with 330 months it may well win, and saying so is a
feature, not a failure), min-variance, ERC (the anchor), HRP, the balanced-slider default
(return 5 / risk 5 / diversification 5) and maximin. This table is also the evidence that will
eventually confirm or flip ERC vs HRP as the default anchor.

Honesty caveats, stated not hidden:
- The macro-state labels carry the classifier's mild full-sample z-normalization look-ahead
  (CLAUDE.md caveat #17) — it affects component weighting, never the primary trend's direction.
  Per-quadrant means, transitions and the outlook are recomputed on the training window only.
- Turnover is reported (mean one-way turnover per refit); no transaction costs are modeled —
  at annual refits on index sleeves the ranking is unlikely to flip, but the number is shown so
  the reader can apply their own cost assumption.

Run:  python -m portfolio_lab.portfolio.validation
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.engine import _perf_stats
from portfolio_lab.portfolio import optimizer as opt
from portfolio_lab.portfolio import rules

# base portfolios the volatility-targeting overlay is tested on (one naive, one that already wins)
VOLTARGET_BASES = ["1/N", "Min-variance"]


def _contestants(inp: dict, n_starts: int, seed: int) -> dict:
    """name -> weight vector, all estimated from the training-window inputs only."""
    out = dict(inp["anchors"])                              # 1/N, ERC (anchor), HRP, Min-variance
    out["Balanced sliders (5/5/5)"] = opt.optimize(
        prefs={"return": 5, "risk": 5, "diversification": 5},
        inputs=inp, n_starts=n_starts, seed=seed)["w"]
    out[f"Momentum {C.OPTIMIZER_MOMENTUM_LOOKBACK}-{C.OPTIMIZER_MOMENTUM_SKIP} "
        f"(top {C.OPTIMIZER_MOMENTUM_K})"] = rules.momentum_weights(inp["rets"])
    if inp["mu_q"] is not None and len(inp["mu_q"]) >= 2:
        out["Maximin (worst quadrant)"] = opt.optimize(
            maximin=True, inputs=inp, n_starts=n_starts, seed=seed)["w"]
        out[f"Maximin (geo ≤{C.OPTIMIZER_GEO_CAP_PCT:.0f}%)"] = opt.optimize(
            maximin=True, geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0,
            inputs=inp, n_starts=n_starts, seed=seed)["w"]
    return out


def walk_forward(warmup: int = None, refit: int = None, n_starts: int = None,
                 seed: int = None) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Expanding-window backtest. Returns (summary DataFrame, meta dict, monthly OOS returns
    DataFrame — one column per contestant, used by portfolio/visualize.py for the cumulative
    comparison curves)."""
    warmup = warmup or C.OPTIMIZER_WF_WARMUP_MONTHS
    refit = refit or C.OPTIMIZER_WF_REFIT_MONTHS
    n_starts = n_starts or C.OPTIMIZER_WF_N_STARTS
    seed = C.OPTIMIZER_SEED if seed is None else seed

    rets = opt.load_returns()
    T = len(rets)
    if T <= warmup + refit:
        raise ValueError(f"not enough history for walk-forward (T={T}, warmup={warmup})")

    # per contestant: gross monthly return + monthly one-way turnover (only rebalance months > 0)
    gross_chunks: dict[str, list] = {}
    turn_chunks: dict[str, list] = {}
    prev_w: dict[str, np.ndarray] = {}
    refit_dates = []
    for t in range(warmup, T, refit):
        inp = opt.build_inputs(rets.iloc[:t])
        refit_dates.append(str(rets.index[t - 1].date()))
        oos = rets.iloc[t:t + refit].values
        for name, w in _contestants(inp, n_starts, seed).items():
            chunk = oos @ w
            tmonth = np.zeros(len(chunk))
            if name in prev_w:                              # trading happens on the first month
                tmonth[0] = float(np.abs(w - prev_w[name]).sum() / 2)
            prev_w[name] = w
            gross_chunks.setdefault(name, []).append(chunk)
            turn_chunks.setdefault(name, []).append(tmonth)

    oos_index = rets.index[warmup:]
    gross = {n: pd.Series(np.concatenate(c), index=oos_index[:sum(map(len, c))])
             for n, c in gross_chunks.items()}
    turn = {n: pd.Series(np.concatenate(c), index=oos_index[:sum(map(len, c))])
            for n, c in turn_chunks.items()}

    # volatility-targeting overlays on selected bases (their own leverage-change turnover is
    # charged on top of the base's rebalancing turnover)
    for base in VOLTARGET_BASES:
        if base not in gross:
            continue
        managed, extra_turn = rules.vol_managed(gross[base])
        vt = f"{base} + vol-target"
        gross[vt] = managed
        turn[vt] = turn[base] + extra_turn

    cost = C.OPTIMIZER_TC_BPS / 10_000.0
    rows, monthly = [], {}
    for name in gross:
        net = gross[name] - cost * turn[name]              # charge transaction costs
        monthly[name] = net
        lvl = pd.concat([pd.Series([100.0], index=[oos_index[0] - pd.offsets.MonthEnd(1)]),
                         100.0 * (1 + net).cumprod()])
        p = _perf_stats(lvl)
        gp = _perf_stats(pd.concat([pd.Series([100.0], index=[lvl.index[0]]),
                                    100.0 * (1 + gross[name]).cumprod()]))
        rows.append(dict(portfolio=name, oos_CAGR=p["CAGR"], oos_ann_vol=p["ann_vol"],
                         oos_sharpe_rf0=p["sharpe_rf0"], oos_max_drawdown=p["max_drawdown"],
                         oos_sharpe_gross=gp["sharpe_rf0"],
                         mean_turnover_per_refit=float(turn[name].sum() / max(1, len(refit_dates)))))
    summary = pd.DataFrame(rows).sort_values("oos_sharpe_rf0", ascending=False)
    meta = dict(warmup_months=warmup, refit_months=refit, n_refits=len(refit_dates),
                oos_start=str(oos_index[0].date()), oos_end=str(oos_index[-1].date()),
                oos_months=len(oos_index), tc_bps=C.OPTIMIZER_TC_BPS)
    return summary, meta, pd.DataFrame(monthly)


def run():
    C.ensure_dirs()
    summary, meta, monthly = walk_forward()
    summary.to_csv(C.OPTIMIZER_WALKFORWARD, index=False)
    monthly.to_csv(C.OPTIMIZER_WALKFORWARD_RETURNS)
    print(f"[validation] walk-forward: {meta['n_refits']} refits, OOS "
          f"{meta['oos_start']} -> {meta['oos_end']} ({meta['oos_months']} months)")
    print(summary.to_string(index=False))
    return summary, meta, monthly


if __name__ == "__main__":
    run()
