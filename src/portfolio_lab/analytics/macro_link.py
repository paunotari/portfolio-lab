"""Macro-link engine: correlates index/factor returns with macro indicators.

For each of the 21 return series and each macro indicator, two feature bases are used:
  level : the indicator value as stored (rates, spreads, YoY rates...) — regime/state context.
  chg   : first difference (month-over-month change) — the "surprise", statistically the
          sounder basis for return correlation (levels are persistent/near-non-stationary and
          can produce spurious correlations; treat level-basis numbers as context only).

Computed per (series, indicator, basis):
  * contemporaneous correlation corr(ret_t, feat_t)
  * lagged correlations corr(ret_t, feat_{t-k}) for k in MACRO_LAGS (macro LEADS returns)
  * univariate OLS beta of ret on chg-basis feature (lag 0): beta, r2, n

Pairs with fewer than MACRO_MIN_OVERLAP_MONTHS overlapping months are reported with corr=NaN and
flagged insufficient rather than yielding a noisy estimate.

This analysis is exploratory/descriptive: many pairwise tests are computed and no significance
claims are made. Use it to rank and visualize sensitivities, not as proof of causal links.

Outputs (to outputs/analytics/macro/):
  macro_correlations.csv        long: series, region, factor, indicator, basis, lag, corr, n, insufficient
  macro_corr_contemp_level.csv  wide 21 series x indicators (lag 0, level basis)
  macro_corr_contemp_chg.csv    wide 21 series x indicators (lag 0, chg basis)
  macro_sensitivity_beta.csv    series x indicator OLS beta / r2 / n (chg basis, lag 0)
  REPORT_macro.md               narrative: top drivers per factor, most-sensitive per indicator,
                                indicators more predictive at lag>0

Run:  python -m portfolio_lab.analytics.macro_link
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C


def _region(col): return col.split(" | ")[0]
def _factor(col): return col.split(" | ")[1]


def _load_inputs():
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    rets = lv.pct_change()
    macro = pd.read_csv(C.MACRO_MONTHLY, index_col=0, parse_dates=True).sort_index()
    meta = pd.read_csv(C.MACRO_META)
    return rets, macro, meta


def _features(macro: pd.DataFrame) -> dict:
    """{(indicator, basis): series} for both bases."""
    out = {}
    for col in macro.columns:
        out[(col, "level")] = macro[col]
        out[(col, "chg")] = macro[col].diff()
    return out


def _pair_corr(ret: pd.Series, feat: pd.Series, lag: int):
    """corr(ret_t, feat_{t-lag}) on overlapping months; returns (corr, n)."""
    df = pd.concat([ret, feat.shift(lag)], axis=1, keys=["r", "f"], sort=False).dropna()
    n = len(df)
    if n < C.MACRO_MIN_OVERLAP_MONTHS:
        return np.nan, n
    return df["r"].corr(df["f"]), n


def _pair_beta(ret: pd.Series, feat: pd.Series):
    """Univariate OLS ret = a + b*feat (lag 0). Returns (beta, r2, n)."""
    df = pd.concat([ret, feat], axis=1, keys=["r", "f"], sort=False).dropna()
    n = len(df)
    if n < C.MACRO_MIN_OVERLAP_MONTHS:
        return np.nan, np.nan, n
    x, y = df["f"].values, df["r"].values
    vx = x.var()
    if vx == 0:
        return np.nan, np.nan, n
    beta = np.cov(x, y, bias=True)[0, 1] / vx
    r = np.corrcoef(x, y)[0, 1]
    return beta, r * r, n


def run():
    C.ensure_dirs()
    rets, macro, meta = _load_inputs()
    feats = _features(macro)
    indicators = list(macro.columns)

    long_rows, beta_rows = [], []
    for col in rets.columns:
        ret = rets[col]
        for (ind, basis), feat in feats.items():
            for lag in C.MACRO_LAGS:
                corr, n = _pair_corr(ret, feat, lag)
                long_rows.append(dict(series=col, region=_region(col), factor=_factor(col),
                                      indicator=ind, basis=basis, lag=lag,
                                      corr=corr, n=n,
                                      insufficient=n < C.MACRO_MIN_OVERLAP_MONTHS))
        for ind in indicators:
            beta, r2, n = _pair_beta(ret, feats[(ind, "chg")])
            beta_rows.append(dict(series=col, region=_region(col), factor=_factor(col),
                                  indicator=ind, beta=beta, r2=r2, n=n))

    long_df = pd.DataFrame(long_rows)
    long_df.to_csv(C.MACRO_CORRELATIONS, index=False)

    def wide(basis):
        sub = long_df[(long_df.basis == basis) & (long_df.lag == 0)]
        return sub.pivot(index="series", columns="indicator", values="corr")[indicators]
    wide_level, wide_chg = wide("level"), wide("chg")
    wide_level.to_csv(C.MACRO_CORR_CONTEMP_LEVEL)
    wide_chg.to_csv(C.MACRO_CORR_CONTEMP_CHG)

    beta_df = pd.DataFrame(beta_rows)
    beta_df.to_csv(C.MACRO_BETA, index=False)

    _write_report(long_df, beta_df, meta)
    n_ok = (~long_df.insufficient).sum()
    print(f"[macro_link] {len(long_df)} pair-lag rows ({n_ok} sufficient), "
          f"{len(beta_df)} betas -> {C.MACRO_ANALYTICS_DIR}")


def _write_report(long_df: pd.DataFrame, beta_df: pd.DataFrame, meta: pd.DataFrame):
    units = dict(zip(meta["name"], meta["units"]))

    def fmt(x): return "n/a" if pd.isna(x) else f"{x:+.2f}"

    L = ["# Macro-link report — index/factor returns vs macro indicators\n",
         f"Bases: **chg** = month-over-month change of the indicator (sensitivity to surprises; "
         f"the statistically sounder basis); **level** = indicator value as stored (regime "
         f"context; persistent series — interpret with care). Pairs with < "
         f"{C.MACRO_MIN_OVERLAP_MONTHS} overlapping months are excluded as insufficient. "
         f"Exploratory/descriptive only — no significance claims.\n"]

    contemp = long_df[(long_df.lag == 0) & (long_df.basis == "chg") & (~long_df.insufficient)]

    # 1. top drivers per factor bucket
    L.append("## 1. Top macro drivers per factor (avg contemporaneous corr, chg basis)\n")
    fac_ind = contemp.groupby(["factor", "indicator"])["corr"].mean().reset_index()
    for fac in sorted(fac_ind.factor.unique()):
        sub = fac_ind[fac_ind.factor == fac].sort_values("corr")
        neg, pos = sub.iloc[:3], sub.iloc[-3:][::-1]
        L.append(f"### {fac}")
        L.append("- strongest positive: " + ", ".join(f"{r.indicator} {fmt(r['corr'])}" for _, r in pos.iterrows()))
        L.append("- strongest negative: " + ", ".join(f"{r.indicator} {fmt(r['corr'])}" for _, r in neg.iterrows()))
        L.append("")

    # 2. most-sensitive series per indicator
    L.append("## 2. Most-sensitive series per indicator (|corr|, chg basis, lag 0)\n")
    L.append("| Indicator | Units | Most sensitive series | corr |")
    L.append("|---|---|---|---|")
    for ind in sorted(contemp.indicator.unique()):
        sub = contemp[contemp.indicator == ind]
        top = sub.loc[sub["corr"].abs().idxmax()]
        L.append(f"| {ind} | {units.get(ind, '')} | {top.series} | {fmt(top['corr'])} |")

    # 3. indicators more predictive at lag>0
    L.append("\n## 3. Lead/lag: indicators notably more predictive with a lead (chg basis)\n")
    lag_any = long_df[(long_df.basis == "chg") & (~long_df.insufficient)]
    flagged = 0
    for (series, ind), grp in lag_any.groupby(["series", "indicator"]):
        g = grp.set_index("lag")["corr"]
        if 0 not in g.index:
            continue
        best_lag = g.abs().idxmax()
        if best_lag != 0 and abs(g[best_lag]) - abs(g[0]) > 0.10:
            L.append(f"- {series} vs {ind}: |corr| {abs(g[0]):.2f} at lag 0 -> "
                     f"{abs(g[best_lag]):.2f} at lag {best_lag}m")
            flagged += 1
    if flagged == 0:
        L.append("- none exceed the +0.10 |corr| improvement threshold — contemporaneous "
                 "relationships dominate at monthly frequency.")

    # 4. largest betas
    L.append("\n## 4. Largest univariate sensitivities (OLS beta on chg, lag 0)\n")
    bd = beta_df.dropna(subset=["beta"])
    top = bd.reindex(bd.r2.sort_values(ascending=False).index).head(10)
    L.append("| Series | Indicator | beta (ret per unit chg) | r2 | n |")
    L.append("|---|---|---|---|---|")
    for _, r in top.iterrows():
        L.append(f"| {r.series} | {r.indicator} | {r.beta:+.4f} | {r.r2:.2f} | {int(r.n)} |")

    C.MACRO_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    run()
