"""Net-of-fees check (v2.0): charge illustrative ETF expense ratios on the weights held.

The race charges trading costs (10 bps per unit of turnover) but, like v1, no ongoing fund
fee, because it measures indices. An investor holds ETFs, and factor ETFs cost roughly twice
what plain market-cap ETFs do. This module charges a TER schedule (config.V2_TER_BPS —
assumptions, stated as such) on the sleeve weights each contestant actually held between
refits, and re-runs the comparisons on the net-of-fees returns:

- against 1/N (Sharpe difference, information ratio), the paper's question; and
- against the plain cap-weighted MSCI ACWI Reference, charged the plain-index fee — the
  "naive factor menu versus the market" question the factor-ETF debate is usually about.

Overlays (vol-target, trend) pay the base portfolio's fee only on the share they hold
invested (the exposure series the walk-forward records); cash pays nothing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.portfolio import inference as I
from portfolio_lab.v2 import risk_adjusted as R

OVERLAY_BASE = {"1/N + vol-target": "1/N", "Min-variance + vol-target": "Min-variance",
                "1/N + trend (Faber 10m SMA)": "1/N",
                "Dual momentum (Antonacci)": "Momentum 12-1 (top 6)"}


def sleeve_ter(sleeve: str) -> float:
    """Annual TER (fraction) for one sleeve label under the config schedule."""
    t = C.V2_TER_BPS
    if sleeve in t:
        return t[sleeve] / 1e4
    region, factor = sleeve.split(" | ")
    bps = t["Reference"] if factor == "Reference" else t["factor"]
    if region in ("EM", "AC_Asia_ex_Japan"):
        bps += t["em_asia_extra"]
    return bps / 1e4


def fee_drag(tag: str, monthly: pd.DataFrame) -> pd.DataFrame:
    """Monthly fee (fraction) per contestant, aligned to `monthly`. `tag` names the cached
    walk-forward (e.g. 'warmup120', see v2/short_warmup.tag)."""
    W = pd.read_csv(C.V2_DIR / f"wf_weights_{tag}.csv", index_col=[0, 1], parse_dates=[1])
    expo_path = C.V2_DIR / f"wf_exposure_{tag}.csv"
    expo_all = (pd.read_csv(expo_path, index_col=0, parse_dates=True)
                if expo_path.exists() else None)
    out = pd.DataFrame(index=monthly.index)
    for name in W.index.get_level_values(0).unique():
        w = W.loc[name].dropna(axis=1, how="all").fillna(0.0)
        ter = pd.Series({c: sleeve_ter(c) for c in w.columns})
        annual = (w * ter).sum(axis=1)                      # fee rate per refit interval
        out[name] = annual.reindex(monthly.index, method="ffill") / 12.0
    for ov, base in OVERLAY_BASE.items():               # overlays pay on invested exposure only
        if ov in monthly.columns and base in out.columns:
            expo = (expo_all[ov].reindex(monthly.index).fillna(1.0)
                    if expo_all is not None and ov in expo_all else 1.0)
            out[ov] = expo * out[base]
    return out[monthly.columns]


def acwi_benchmark(index: pd.DatetimeIndex) -> pd.Series:
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    r = lv["ACWI | Reference"].pct_change()
    r.index = r.index.to_period("M")
    r = r.reindex(index.to_period("M"))
    r.index = index
    return r - sleeve_ter("ACWI | Reference") / 12.0


def factor_premium_net(start: str, fee_gap: float = None) -> dict:
    """Region-neutral factor premium net of the fee difference (round-2 review, F9): in each
    region, equal-weight its factor sleeves minus its own Reference sleeve, minus the TER gap
    between factor and plain ETFs; pooled across regions in equal weight. Newey-West t."""
    from portfolio_lab.portfolio import optimizer as opt
    rets = opt.load_returns().loc[start:]
    gap = (C.V2_TER_BPS["factor"] - C.V2_TER_BPS["Reference"]) / 1e4 if fee_gap is None else fee_gap
    spreads = []
    for reg in sorted({c.split(" | ")[0] for c in rets.columns}):
        f = [c for c in rets.columns if c.startswith(reg + " | ") and not c.endswith("Reference")]
        if f:
            spreads.append(rets[f].mean(axis=1) - rets[f"{reg} | Reference"] - gap / 12)
    x = pd.concat(spreads, axis=1).mean(axis=1).to_numpy(float)
    h = R.hac_ols(x, np.empty((len(x), 0)))
    return dict(start=start, months=len(x), premium_ann=float(x.mean() * 12),
                t=float(h["t"][0]), p=float(h["p"][0]))


def net_of_fees_table(tag: str, monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(table, net monthly returns). Columns: average TER, Sharpe net of fees (excess), its gap
    and p against 1/N, information ratio against 1/N and against the plain ACWI ETF."""
    fees = fee_drag(tag, monthly)
    net = monthly - fees
    acwi = acwi_benchmark(monthly.index)
    fac = R.factor_frame(monthly)
    ex = net.sub(fac["rf"], axis=0)
    ex_acwi = acwi - fac["rf"]
    rows = []
    for name in list(net.columns) + ["MSCI ACWI (plain ETF)"]:
        e = ex_acwi if name.startswith("MSCI ACWI") else ex[name]
        r = acwi if name.startswith("MSCI ACWI") else net[name]
        row = dict(portfolio=name,
                   ter_ann=float(sleeve_ter("ACWI | Reference") if name.startswith("MSCI ACWI")
                                 else fees[name].mean() * 12),
                   sharpe=R.sharpe(e.dropna().to_numpy(float)))
        if name != "1/N":
            t = I.sharpe_diff_test(e, ex["1/N"])
            act = (r - net["1/N"]).dropna()
            row.update(d_sharpe=t["delta"] * np.sqrt(12), p_sharpe=t["p_boot"],
                       ir_vs_1n=float(act.mean() / act.std() * np.sqrt(12)))
        if not name.startswith("MSCI ACWI"):
            act = (r - acwi).dropna().to_numpy(float)
            h = R.hac_ols(act, np.empty((len(act), 0)))
            row.update(ir_vs_acwi=float(act.mean() / act.std(ddof=1) * np.sqrt(12)),
                       p_ir_vs_acwi=float(h["p"][0]))
        rows.append(row)
    return (pd.DataFrame(rows).sort_values("sharpe", ascending=False).reset_index(drop=True),
            net)
