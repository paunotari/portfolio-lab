"""Naive ex-ante tilt benchmarks and overlay variants (v2.0, round-2 review F10 / R8).

"Min-variance's edge is a tilt, not construction skill" is only testable against tilts an
investor could have chosen WITHOUT the optimizer. Three, each refit every January on the same
calendar as the walk-forward, constant-mix within the year, 10 bps on refit turnover:

- 1/N over the 7 Quality sleeves (the factor min-variance ends up holding, chosen ex ante);
- inverse-variance over all 28 sleeves (training-window variances — the covariance-free
  cousin of min-variance);
- 50/50 USA + World Quality — HINDSIGHT: the pair min-variance actually picked; an upper
  bound on what the tilt alone could earn, not a fair contestant.

Also: dual momentum with Antonacci's own absolute-momentum gate (trailing return above the
T-bill's) — the shipped contestant uses a zero threshold.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.portfolio import optimizer as opt
from portfolio_lab.portfolio import rules
from portfolio_lab.portfolio.validation import _base_history

HINDSIGHT = "USA+World Quality 50/50 (hindsight)"


def naive_tilts(oos_index: pd.DatetimeIndex, refit: int = None) -> pd.DataFrame:
    refit = refit or C.OPTIMIZER_WF_REFIT_MONTHS
    rets = opt.load_returns()
    start = rets.index.get_loc(oos_index[0])
    q = [c for c in rets.columns if c.endswith("| Quality")]
    out = {k: [] for k in ("1/N Quality sleeves", "Inverse-variance (28 sleeves)", HINDSIGHT)}
    prev = {}
    cost = C.OPTIMIZER_TC_BPS / 1e4
    for t in range(start, len(rets), refit):
        train, oos = rets.iloc[:t], rets.iloc[t:t + refit]
        w = {"1/N Quality sleeves": pd.Series(1 / len(q), index=q).reindex(rets.columns).fillna(0.0),
             "Inverse-variance (28 sleeves)": (1 / train.var()) / (1 / train.var()).sum(),
             HINDSIGHT: pd.Series({"USA | Quality": 0.5, "World | Quality": 0.5})
             .reindex(rets.columns).fillna(0.0)}
        for k, wk in w.items():
            r = oos @ wk
            if k in prev:
                r.iloc[0] -= cost * float((wk - prev[k]).abs().sum() / 2)
            prev[k] = wk
            out[k].append(r)
    return pd.DataFrame({k: pd.concat(v) for k, v in out.items()}).reindex(oos_index)


def dual_momentum_tbill_gate(tag: str, monthly: pd.DataFrame, warmup: int) -> pd.Series:
    """Antonacci's gate: hold the momentum portfolio while its trailing 12-month return
    exceeds the T-bill's over the same 12 months; cash (earning the T-bill) otherwise."""
    gross = pd.read_csv(C.V2_DIR / f"wf_gross_{tag}.csv", index_col=0, parse_dates=True)
    turn = pd.read_csv(C.V2_DIR / f"wf_turnover_{tag}.csv", index_col=0, parse_dates=True)
    base = "Momentum 12-1 (top 6)"
    rf = pd.read_csv(C.FF_FACTORS_MONTHLY, index_col=0, parse_dates=True)["rf"]
    rets = opt.load_returns()
    hist = _base_history(base, rets, rets.index.get_loc(monthly.index[0]))
    full_idx = hist.index.append(gross.index)
    rf_al = rules._align_cash(rf, full_idx)
    thr = (1 + rf_al).rolling(12).apply(np.prod, raw=True) - 1
    managed, extra = rules.trend_overlay(gross[base], mode="absmom", threshold=thr, cash=rf,
                                         history=hist)
    return managed - C.OPTIMIZER_TC_BPS / 1e4 * (turn[base] + extra)
