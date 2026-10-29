"""Shorter training window — does the race change once it contains a real bear market?

The v1 walk-forward warms up on 120 months, so with data opening in 1999 scoring starts in
2009-01 and the whole 210-month race sits inside one post-crisis expansion (the paper's own
sharpest limitation). Warming up on 60 or 80 months instead starts scoring in 2004-01 or
2005-09, which puts the 2007-09 bear market inside the out-of-sample window. The price is
noisier estimation (fewer months per covariance and per macro quadrant), so the 120-month
baseline is re-run with the same code and data and the comparison is reported both on the
full window and on the 2009+ months the three runs share.

Nothing here changes the protocol: same contestants, expanding window, annual refits, 10 bps
costs. Only `warmup` moves, through the parameter `validation.walk_forward` already takes.

Run:  python -m portfolio_lab.v2.short_warmup              # 60, 80 and the 120 baseline
      python -m portfolio_lab.v2.short_warmup 60          # one warmup only
"""
from __future__ import annotations
import argparse
import json
import time

import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.portfolio import validation


def returns_path(warmup: int):
    return C.V2_DIR / f"wf_returns_warmup{warmup}.csv"


def run_one(warmup: int) -> pd.DataFrame:
    """One full walk-forward at this warmup; caches returns, summary, attribution, meta."""
    C.V2_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    summary, meta, monthly = validation.walk_forward(warmup=warmup)
    monthly.to_csv(returns_path(warmup))
    summary.to_csv(C.V2_DIR / f"wf_summary_warmup{warmup}.csv", index=False)
    validation.sleeve_attribution(meta).to_csv(
        C.V2_DIR / f"wf_attribution_warmup{warmup}.csv", index=False)
    # pre-cost pieces and per-refit weights, so fee schedules (v2/fees.py) can be charged
    # without re-running the optimization
    meta["_gross"].to_csv(C.V2_DIR / f"wf_gross_warmup{warmup}.csv")
    meta["_turnover"].to_csv(C.V2_DIR / f"wf_turnover_warmup{warmup}.csv")
    pd.concat({n: w for n, w in meta["_weights"].items()}, names=["portfolio", "refit"]) \
        .to_csv(C.V2_DIR / f"wf_weights_warmup{warmup}.csv")
    info = {k: v for k, v in meta.items() if not k.startswith("_")}
    info["runtime_s"] = round(time.time() - t0, 1)
    (C.V2_DIR / f"wf_meta_warmup{warmup}.json").write_text(json.dumps(info, indent=2))
    print(f"[v2.short_warmup] warmup {warmup}: OOS {info['oos_start']} -> {info['oos_end']} "
          f"({info['oos_months']} months, {info['n_refits']} refits) in {info['runtime_s']}s")
    return monthly


def load(warmup: int) -> pd.DataFrame:
    p = returns_path(warmup)
    if not p.exists():
        return run_one(warmup)
    return pd.read_csv(p, index_col=0, parse_dates=True)


def run(warmups=None):
    warmups = warmups or (C.V2_BASELINE_WARMUP,) + tuple(C.V2_WARMUPS)
    return {w: run_one(w) for w in warmups}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="v2 shorter-warmup walk-forwards")
    ap.add_argument("warmups", nargs="*", type=int)
    args = ap.parse_args()
    run(tuple(args.warmups) or None)
