"""Analytics engine: turns processed level series + regime map into metrics and a report.

Outputs (to outputs/analytics/):
  performance_summary.csv      CAGR, ann vol, Sharpe(rf=0), max drawdown over the common window
                               (all 21 series present); the dashboard lets the user pick a
                               different date range and recomputes these client-side
  factor_vs_reference.csv      each factor's excess CAGR & monthly hit-rate vs its region reference
  regime_performance.csv       per-regime total & annualized return, vol, annualized excess vs ref
  correlation_full.csv         static monthly-return correlation matrix (common window)
  correlation_by_regime/*.csv  one correlation matrix per regime
  rolling_avg_correlation.csv  36m rolling avg pairwise correlation across the 7 references
  REPORT.md                    narrative combining regime annotations with computed numbers

Run:  python -m portfolio_lab.analytics.engine
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.regimes import REGIMES


def _region(col): return col.split(" | ")[0]
def _factor(col): return col.split(" | ")[1]


def _perf_stats(level: pd.Series) -> dict:
    s = level.dropna()
    r = s.pct_change().dropna()
    n = len(r)
    cagr = (s.iloc[-1] / s.iloc[0]) ** (12.0 / n) - 1
    vol = r.std() * np.sqrt(12)
    sharpe = (r.mean() * 12) / vol if vol else np.nan
    dd = (s / s.cummax() - 1).min()
    return dict(months=n, start=str(s.index[0].date()), end=str(s.index[-1].date()),
                CAGR=cagr, ann_vol=vol, sharpe_rf0=sharpe, max_drawdown=dd)


def _cagr(level: pd.Series) -> float:
    s = level.dropna()
    return (s.iloc[-1] / s.iloc[0]) ** (12 / (len(s) - 1)) - 1


def run():
    C.ensure_dirs()
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    rets = lv.pct_change()
    common_start = lv.dropna(how="any").index.min()
    lv_c = lv.loc[common_start:]
    rets_c = rets.loc[common_start:].dropna(how="any")

    # 1. performance summary — one CAGR/vol/Sharpe/maxDD per series, computed over the common
    # window (all 21 series present) so every row is directly comparable. The dashboard lets the
    # user pick a different date range and recomputes these same stats client-side; this CSV/
    # report always reflects the default common window.
    rows = []
    for col in lv.columns:
        stats = _perf_stats(lv_c[col])
        rows.append(dict(series=col, region=_region(col), factor=_factor(col), **stats))
    perf = pd.DataFrame(rows).sort_values(["region", "factor"])
    perf.to_csv(C.PERFORMANCE_SUMMARY, index=False)

    # 2. factor vs reference
    fvr = []
    for reg in C.REGIONS:
        ref = f"{reg} | Reference"
        if ref not in lv.columns:
            continue
        for col in [c for c in lv.columns if _region(c) == reg and _factor(c) != "Reference"]:
            pair = lv[[ref, col]].dropna()
            rr = pair.pct_change().dropna()
            fvr.append(dict(region=reg, factor=_factor(col),
                            ref_CAGR=_cagr(pair[ref]), factor_CAGR=_cagr(pair[col]),
                            excess_CAGR=_cagr(pair[col]) - _cagr(pair[ref]),
                            monthly_hit_rate=(rr[col] > rr[ref]).mean(),
                            overlap_start=str(pair.index[0].date())))
    pd.DataFrame(fvr).sort_values(["region", "excess_CAGR"], ascending=[True, False]) \
        .to_csv(C.FACTOR_VS_REFERENCE, index=False)

    # 3. regime performance (annualized excess vs reference -> comparable across regime lengths)
    reg_rows = []
    for rg in REGIMES:
        win = lv.loc[rg["start"]:rg["end"]]
        if len(win) < 2:
            continue
        for col in lv.columns:
            s = win[col].dropna()
            if len(s) < 2:
                continue
            tot = s.iloc[-1] / s.iloc[0] - 1
            ann = (1 + tot) ** (12 / (len(s) - 1)) - 1
            vol = s.pct_change().dropna().std() * np.sqrt(12)
            ref = f"{_region(col)} | Reference"
            exc = np.nan
            if ref in win.columns and _factor(col) != "Reference":
                rs = win[ref].dropna()
                if len(rs) >= 2:
                    exc = ann - ((rs.iloc[-1] / rs.iloc[0]) ** (12 / (len(rs) - 1)) - 1)
            reg_rows.append(dict(regime=rg["id"], regime_name=rg["name"], start=rg["start"],
                                 end=rg["end"], months=len(s) - 1, series=col,
                                 region=_region(col), factor=_factor(col),
                                 total_return=tot, annualized=ann, ann_vol=vol, excess_vs_ref=exc))
    regime_perf = pd.DataFrame(reg_rows)
    regime_perf.to_csv(C.REGIME_PERFORMANCE, index=False)

    # 4/5. correlation matrices
    rets_c.corr().to_csv(C.CORRELATION_FULL)
    for rg in REGIMES:
        r = rets.loc[rg["start"]:rg["end"]].dropna(how="any")
        if len(r) >= 4:
            r.corr().to_csv(C.CORR_REGIME_DIR / f"{rg['id']}.csv")

    # 6. rolling average pairwise correlation across references
    def avg_pairwise(w):
        c = w.corr().values
        iu = np.triu_indices_from(c, k=1)
        return np.nanmean(c[iu])
    ref_cols = [f"{r} | Reference" for r in C.REGIONS if f"{r} | Reference" in rets.columns]
    rr = rets[ref_cols].dropna(how="any")
    W = C.ROLLING_WINDOW_MONTHS
    roll = [(rr.index[i - 1], avg_pairwise(rr.iloc[i - W:i])) for i in range(W, len(rr) + 1)]
    roll_df = pd.DataFrame(roll, columns=["date", f"avg_pairwise_corr_references_{W}m"]).set_index("date")
    roll_df.to_csv(C.ROLLING_CORRELATION)

    _write_report(perf, pd.DataFrame(fvr), regime_perf, roll_df, common_start, lv, rets_c)
    print(f"[analytics] window {common_start.date()}..{lv.index[-1].date()} "
          f"({len(rets_c)} months) -> {C.ANALYTICS_DIR}")


def _write_report(perf, fvr, regime_perf, roll_df, common_start, lv, rets_c):
    def pct(x): return "n/a" if pd.isna(x) else f"{x*100:,.1f}%"
    L = ["# MSCI Factor / Region Analytics Report\n",
         f"Common comparison window: **{common_start.date()} → {lv.index[-1].date()}** "
         f"({len(rets_c)} months, all {lv.shape[1]} series present).\n",
         "## 1. Full-sample performance (common window)\n",
         "| Series | CAGR | Ann Vol | Sharpe(rf0) | Max DD |", "|---|---|---|---|---|"]
    for _, r in perf.sort_values("CAGR", ascending=False).iterrows():
        L.append(f"| {r.series} | {pct(r.CAGR)} | {pct(r.ann_vol)} | "
                 f"{r.sharpe_rf0:.2f} | {pct(r.max_drawdown)} |")
    L += ["\n## 2. Does each factor beat its region reference? (full overlap)\n",
          "| Region | Factor | Ref CAGR | Factor CAGR | Excess | Monthly win-rate |",
          "|---|---|---|---|---|---|"]
    for _, r in fvr.sort_values(["region", "excess_CAGR"], ascending=[True, False]).iterrows():
        L.append(f"| {r.region} | {r.factor} | {pct(r.ref_CAGR)} | {pct(r.factor_CAGR)} | "
                 f"{pct(r.excess_CAGR)} | {pct(r.monthly_hit_rate)} |")
    L.append("\n## 3. Regimes: macro narrative vs realized numbers\n")
    for rg in REGIMES:
        sub = regime_perf[regime_perf.regime == rg["id"]]
        if sub.empty:
            continue
        best, worst = sub.loc[sub.annualized.idxmax()], sub.loc[sub.annualized.idxmin()]
        L += [f"### {rg['name']}  ({rg['start']} → {rg['end']})",
              f"- **Macro:** {rg['macro']}", f"- **Expected factor leadership:** {rg['factors']}",
              f"- **Expected regional impact:** {rg['regions']}", f"- **Geographic shift:** {rg['shift']}",
              f"- **Realized (annualized):** best = {best.series} {pct(best.annualized)}; "
              f"worst = {worst.series} {pct(worst.annualized)}"]
        fx = sub.dropna(subset=["excess_vs_ref"]).groupby("factor")["excess_vs_ref"].mean()
        if not fx.empty:
            L.append("- **Realized avg factor excess vs reference (annualized):** " +
                     ", ".join(f"{k} {pct(v)}" for k, v in fx.sort_values(ascending=False).items()))
        L.append("")
    col = roll_df.columns[0]
    L += ["## 4. Diversification over time\n",
          f"36-month rolling average pairwise correlation across the 7 regional references — "
          f"latest = {roll_df.iloc[-1, 0]:.2f}; range {roll_df[col].min():.2f}–{roll_df[col].max():.2f}. "
          f"Peaks mark crisis co-movement (diversification failing); troughs mark regime dispersion.\n",
          "_Regime annotations are analyst priors; realized figures are computed from the data and "
          "should confirm or challenge them._\n"]
    C.ANALYTICS_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    run()
