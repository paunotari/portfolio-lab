"""Within-interval rebalancing: does the constant-mix assumption (and its uncosted drift
turnover) change any verdict? (C1 / M22)

The walk-forward holds each contestant CONSTANT-MIX between annual refits — implicitly
rebalancing back to target every month — but only charges transaction costs on refit-date
turnover. Two stated limitations follow: the monthly drift-correction turnover is uncosted,
and the constant-mix choice itself was never compared to the obvious alternative. This
module closes both with measurement, from the walk-forward's own per-refit weights — no
re-optimization anywhere (weights are scheme-independent):

  A  constant-mix, refit costs only      — the shipped numbers (upper-bias: free drift trades)
  B  constant-mix, ALL turnover costed   — A plus 10 bps on every month's drift correction
  C  buy-and-hold within the interval    — weights drift with returns; refit turnover is
                                           charged from the DRIFTED weights (no monthly trades
                                           at all — the cheapest implementable scheme)

Overlay contestants (vol-target) are excluded — they are return-space transforms of a base,
not weight schedules. Output: outputs/analytics/optimizer/REPORT_rebalancing.md + CSV.

Run:  python -m portfolio_lab.portfolio.rebalancing        (CLI only, ~2 min: one walk-forward)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.engine import _perf_stats
from portfolio_lab.portfolio import optimizer as opt
from portfolio_lab.portfolio.validation import walk_forward


def _sharpe(net: pd.Series) -> float:
    lvl = pd.concat([pd.Series([100.0], index=[net.index[0] - pd.offsets.MonthEnd(1)]),
                     100.0 * (1 + net).cumprod()])
    return _perf_stats(lvl)["sharpe_rf0"]


def _schemes(wdf: pd.DataFrame, uni: pd.DataFrame, cost: float) -> dict:
    """Net monthly return series under schemes A/B/C + mean drift turnover, one contestant."""
    ra, rb, rc = [], [], []
    drift_turn = []
    prev_end_w = None                                    # scheme C's drifted weights at refit
    prev_w = None                                        # scheme A/B target at previous refit
    for i, start in enumerate(wdf.index):
        w = wdf.iloc[i].fillna(0.0)
        chunk = (uni.loc[start:wdf.index[i + 1]].iloc[:-1] if i + 1 < len(wdf.index)
                 else uni.loc[start:])
        chunk = chunk[w.index]
        if not len(chunk):
            continue
        # A/B: constant-mix
        r_cm = chunk @ w
        refit_cost_ab = 0.0 if prev_w is None else cost * float((w - prev_w).abs().sum() / 2)
        gross = pd.Series(r_cm, index=chunk.index)
        a = gross.copy(); a.iloc[0] -= refit_cost_ab
        b = a.copy()
        for t in range(len(chunk)):
            w_drift = w * (1 + chunk.iloc[t]) / (1 + r_cm.iloc[t])
            tv = float((w_drift - w).abs().sum() / 2)    # trade back to target next month
            drift_turn.append(tv)
            if t + 1 < len(chunk):
                b.iloc[t + 1] -= cost * tv
        # C: buy-and-hold — sleeve values compound, weights drift
        growth = (1 + chunk).cumprod()
        vals = growth.mul(w, axis=1)
        v = vals.sum(axis=1)
        r_bh = v.pct_change()
        r_bh.iloc[0] = v.iloc[0] - 1.0
        w_end = (vals.iloc[-1] / v.iloc[-1])
        refit_cost_c = 0.0 if prev_end_w is None else cost * float(
            (w - prev_end_w).abs().sum() / 2)
        cser = pd.Series(r_bh, index=chunk.index); cser.iloc[0] -= refit_cost_c
        prev_end_w, prev_w = w_end, w
        ra.append(a); rb.append(b); rc.append(cser)
    return dict(A=pd.concat(ra), B=pd.concat(rb), C=pd.concat(rc),
                drift=float(np.mean(drift_turn)))


def run() -> pd.DataFrame:
    C.ensure_dirs()
    cost = C.OPTIMIZER_TC_BPS / 10_000.0
    print("[rebalancing] one walk-forward for the per-refit weights ...")
    _, meta, _ = walk_forward()
    rets = opt.load_returns()
    rets_aw = (opt.load_returns(include_asset_classes=True)
               if C.ASSET_CLASS_MONTHLY.exists() else None)
    rows = []
    for name, wdf in meta["_weights"].items():
        uni = rets if list(wdf.columns) == list(rets.columns) else rets_aw
        if uni is None:
            continue
        s = _schemes(wdf, uni, cost)
        rows.append(dict(portfolio=name,
                         sharpe_cm_shipped=_sharpe(s["A"]),
                         sharpe_cm_fully_costed=_sharpe(s["B"]),
                         sharpe_buy_and_hold=_sharpe(s["C"]),
                         mean_monthly_drift_turnover=s["drift"]))
        print(f"[rebalancing] {name}: A {rows[-1]['sharpe_cm_shipped']:.3f}  "
              f"B {rows[-1]['sharpe_cm_fully_costed']:.3f}  "
              f"C {rows[-1]['sharpe_buy_and_hold']:.3f}  "
              f"drift {s['drift']:.2%}/mo")
    df = pd.DataFrame(rows).sort_values("sharpe_cm_shipped", ascending=False)
    df.to_csv(C.OPTIMIZER_DIR / "optimizer_rebalancing.csv", index=False)
    _write_report(df)
    return df


def _write_report(df: pd.DataFrame):
    L = ["# Within-interval rebalancing — is the constant-mix assumption load-bearing?", "",
         "Three implementations of the SAME weight schedules (no re-optimization): shipped "
         "constant-mix (drift trades free — the stated limitation), constant-mix with every "
         "drift trade costed at 10 bps, and within-interval buy-and-hold (no monthly trades; "
         "refit turnover charged from drifted weights). If rankings agree across columns, "
         "the limitation is quantified and harmless.", ""]
    L += ["| portfolio | CM (shipped) | CM fully costed | buy-and-hold | drift turnover/mo |",
          "|---|---|---|---|---|"]
    for r in df.itertuples():
        L += [f"| {r.portfolio} | {r.sharpe_cm_shipped:.3f} | "
              f"{r.sharpe_cm_fully_costed:.3f} | {r.sharpe_buy_and_hold:.3f} | "
              f"{r.mean_monthly_drift_turnover:.2%} |"]
    worst = float((df.sharpe_cm_shipped - df.sharpe_cm_fully_costed).max())
    rank_a = list(df.sort_values("sharpe_cm_shipped", ascending=False).portfolio)
    rank_c = list(df.sort_values("sharpe_buy_and_hold", ascending=False).portfolio)
    L += ["", f"Largest Sharpe overstatement from free drift trades: **{worst:.4f}**.",
          f"Ranking under buy-and-hold {'IDENTICAL to' if rank_a == rank_c else 'DIFFERS from'} "
          "the shipped ranking.", ""]
    (C.OPTIMIZER_DIR / "REPORT_rebalancing.md").write_text("\n".join(L))
    print(f"[rebalancing] wrote REPORT_rebalancing.md")


if __name__ == "__main__":
    run()
