"""4-quadrant macro-state classifier: growth trend x inflation trend.

This is a SYSTEMATIC, month-by-month classification computed directly from data -- distinct from
`analytics/regimes.py`'s 10 hand-dated historical eras (which are event-driven narrative labels:
"dot-com bust," "GFC," etc). Both are useful; this one answers "which of the 4 standard macro
quadrants was any given month in, including the most recent one" without needing a human to have
labeled it after the fact.

The framework (the standard growth/inflation quadrant used across macro research):

                    Inflation decelerating      Inflation accelerating
    Growth           Goldilocks                  Reflation
    accelerating     (disinflationary growth)     (overheating)
    Growth           Deflationary bust            Stagflation
    decelerating     (recession / slowdown)       (growth-inflation squeeze)

Growth proxy: indpro_yoy (industrial production YoY) -- the standard free monthly growth proxy
(no free monthly GDP exists). Inflation proxy: core_pce_yoy (the Fed's preferred gauge). "Trend"
means the smoothed value now vs N months ago is higher/lower -- i.e. is growth/inflation
ACCELERATING or DECELERATING, not merely whether growth is positive or inflation is high.

Two things this produces beyond the classification itself:
  1. Per-state performance for all 21 return series (mean/annualized return, vol, n months).
  2. Factor-level attribution: within each state's months, does a given FACTOR TYPE (Momentum /
     Enhanced Value / Quality) consistently beat its own region's reference? This turns "EM led
     1998-2010, USA Quality has led since" from an eyeballed observation into a measured,
     regime-conditional pattern -- see info/TODO.md's "regime-attribution narrative report" item.

Caveats (see info/CLAUDE.md):
  - "Current state" is only as fresh as the latest released macro print (~1 month lag) -- this
    is a property of all macro data, not a limitation of this code.
  - Per-state performance pools NON-CONTIGUOUS months together; annualized return is a simple
    (1+mean_monthly_return)**12-1, not a compounded path over skipped months -- treat it as "the
    average pace of return during months like this," not a literal achievable investment path.
  - This is a descriptive/correlational classification, not a forecast -- see the scenario
    simulation module for turning it into a probabilistic forward view, and info/CLAUDE.md's
    caveat on FRED's terms of use for why this stays statistical, not ML-based.

Run:  python -m portfolio_lab.analytics.macro_state
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C

STATES = {
    (True, False): "Goldilocks (disinflationary growth)",
    (True, True): "Reflation (overheating)",
    (False, False): "Deflationary bust (recession/slowdown)",
    (False, True): "Stagflation (growth-inflation squeeze)",
}


def _region(col): return col.split(" | ")[0]
def _factor(col): return col.split(" | ")[1]


def classify_states() -> pd.DataFrame:
    """Return a DataFrame indexed by month with growth/inflation trend booleans and the state
    label, starting once both smoothed+lagged comparisons have enough history.

    FRED's macro history goes back to 1854 (industrial production) / 1919 (PPI), far earlier than
    our return series (1997+). Classifying that far back would make "historical frequency of each
    state" meaningless -- it'd be dominated by 19th/early-20th-century depression-era data that
    has nothing to do with the indices we hold. So this clips to the return series' own history.
    """
    macro = pd.read_csv(C.MACRO_MONTHLY, index_col=0, parse_dates=True).sort_index()
    g_col, i_col = C.MACRO_STATE_GROWTH_INDICATOR, C.MACRO_STATE_INFLATION_INDICATOR
    smooth, lag = C.MACRO_STATE_SMOOTH_MONTHS, C.MACRO_STATE_TREND_LAG_MONTHS

    g_smooth = macro[g_col].rolling(smooth).mean()
    i_smooth = macro[i_col].rolling(smooth).mean()
    g_shift, i_shift = g_smooth.shift(lag), i_smooth.shift(lag)
    # pandas' `>` silently returns False (not NaN) when comparing NaNs -- without this explicit
    # mask, months with not-yet-released macro prints (industrial production / core PCE both lag
    # ~1-2 months behind e.g. VIX) would default to "decelerating" instead of being excluded.
    growth_up = (g_smooth > g_shift).where(g_smooth.notna() & g_shift.notna())
    infl_up = (i_smooth > i_shift).where(i_smooth.notna() & i_shift.notna())

    df = pd.DataFrame({
        "growth_value": macro[g_col], "growth_smooth": g_smooth, "growth_up": growth_up,
        "inflation_value": macro[i_col], "inflation_smooth": i_smooth, "inflation_up": infl_up,
    }).dropna(subset=["growth_up", "inflation_up"])
    df["state"] = [STATES[(bool(gu), bool(iu))] for gu, iu in zip(df.growth_up, df.inflation_up)]

    returns_start = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).index.min()
    return df.loc[returns_start:]


def state_performance(states: pd.DataFrame) -> pd.DataFrame:
    """Per (state, series): n_months, mean_monthly_return, annualized_return, ann_vol."""
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    rets = lv.pct_change()
    rows = []
    for state_name in sorted(states.state.unique()):
        months = states.index[states.state == state_name]
        for col in rets.columns:
            r = rets[col].reindex(months).dropna()
            if len(r) < 3:
                continue
            mean_m = r.mean()
            rows.append(dict(state=state_name, series=col, region=_region(col),
                             factor=_factor(col), n_months=len(r),
                             mean_monthly_return=mean_m,
                             annualized_return=(1 + mean_m) ** 12 - 1,
                             ann_vol=r.std() * np.sqrt(12)))
    return pd.DataFrame(rows)


def factor_attribution(states: pd.DataFrame) -> pd.DataFrame:
    """Within each state's months, does each FACTOR TYPE beat its own region's reference,
    averaged across all regions that have that factor? (excess monthly return + hit rate)."""
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    rets = lv.pct_change()
    rows = []
    for state_name in sorted(states.state.unique()):
        months = states.index[states.state == state_name]
        for reg in C.REGIONS:
            ref_col = f"{reg} | Reference"
            if ref_col not in rets.columns:
                continue
            ref_r = rets[ref_col].reindex(months).dropna()
            for col in [c for c in rets.columns if _region(c) == reg and _factor(c) != "Reference"]:
                r = rets[col].reindex(months).dropna()
                both = pd.concat([r, ref_r], axis=1, join="inner").dropna()
                if len(both) < 3:
                    continue
                exc = both.iloc[:, 0] - both.iloc[:, 1]
                rows.append(dict(state=state_name, region=reg, factor=_factor(col),
                                 n_months=len(both), avg_monthly_excess=exc.mean(),
                                 hit_rate=(exc > 0).mean()))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return (df.groupby(["state", "factor"])
              .apply(lambda g: pd.Series({
                  "n_region_month_obs": g.n_months.sum(),
                  "avg_monthly_excess": np.average(g.avg_monthly_excess, weights=g.n_months),
                  "hit_rate": np.average(g.hit_rate, weights=g.n_months),
                  "n_regions": len(g)}), include_groups=False)
              .reset_index())


def current_state(states: pd.DataFrame) -> dict:
    last = states.iloc[-1]
    prior = states.iloc[-1 - C.MACRO_STATE_TREND_LAG_MONTHS] if len(states) > C.MACRO_STATE_TREND_LAG_MONTHS else None
    return dict(
        as_of=str(states.index[-1].date()),
        state=last.state,
        growth_direction="accelerating" if last.growth_up else "decelerating",
        growth_value=last.growth_value, growth_smooth=last.growth_smooth,
        inflation_direction="accelerating" if last.inflation_up else "decelerating",
        inflation_value=last.inflation_value, inflation_smooth=last.inflation_smooth,
        months_in_current_state=int((states.state[::-1] == last.state).cumprod().sum()),
        prior_state=(prior.state if prior is not None else None),
    )


def run():
    C.ensure_dirs()
    states = classify_states()
    states.to_csv(C.MACRO_STATE_MONTHLY)

    perf = state_performance(states)
    perf.to_csv(C.MACRO_STATE_PERFORMANCE, index=False)

    attr = factor_attribution(states)
    attr.to_csv(C.MACRO_STATE_FACTOR_ATTRIBUTION, index=False)

    cur = current_state(states)
    _write_report(states, perf, attr, cur)

    freq = states.state.value_counts(normalize=True) * 100
    print(f"[macro_state] {len(states)} months classified ({states.index[0].date()}.."
          f"{states.index[-1].date()}), current = {cur['state']} "
          f"({cur['months_in_current_state']} months) -> {C.MACRO_STATE_DIR}")
    for s, pct in freq.items():
        print(f"    {pct:5.1f}%  {s}")


def _write_report(states, perf, attr, cur):
    def pct(x): return "n/a" if pd.isna(x) else f"{x*100:,.1f}%"
    freq = states.state.value_counts(normalize=True) * 100

    L = ["# 4-Quadrant Macro-State Report\n",
         "Systematic classification (growth trend x inflation trend), distinct from the 10 "
         "hand-dated historical regimes in `analytics/regimes.py`. See module docstring for the "
         "framework and caveats — this is descriptive, not a forecast.\n",
         "## Current state\n",
         f"**As of {cur['as_of']}: {cur['state']}** (in this state for "
         f"{cur['months_in_current_state']} consecutive month(s); prior state: {cur['prior_state']})",
         f"- Growth (industrial production YoY): **{cur['growth_direction']}** "
         f"(latest {cur['growth_value']:.1f}%, {C.MACRO_STATE_SMOOTH_MONTHS}m-avg {cur['growth_smooth']:.1f}%)",
         f"- Inflation (core PCE YoY): **{cur['inflation_direction']}** "
         f"(latest {cur['inflation_value']:.1f}%, {C.MACRO_STATE_SMOOTH_MONTHS}m-avg {cur['inflation_smooth']:.1f}%)\n",
         "## Historical frequency of each state\n"]
    for s, p in freq.items():
        L.append(f"- {p:.1f}%  {s}")

    L.append("\n## Per-state performance leaders (annualized return, pooled non-contiguous months)\n")
    for s in sorted(perf.state.unique()):
        sub = perf[perf.state == s].sort_values("annualized_return", ascending=False)
        n_months = states.state.value_counts().get(s, 0)
        L.append(f"### {s}  ({n_months} months, {freq.get(s, 0):.1f}% of history)")
        top, bot = sub.head(3), sub.tail(3)
        L.append("- **Best:** " + ", ".join(f"{r.series} {pct(r.annualized_return)}" for _, r in top.iterrows()))
        L.append("- **Worst:** " + ", ".join(f"{r.series} {pct(r.annualized_return)}" for _, r in bot.iterrows()))
        L.append("")

    L.append("## Factor attribution: does each factor consistently beat its reference, by state?\n")
    L.append("Averaged across all regions with that factor, weighted by region-month count.\n")
    L.append("| State | Factor | Avg monthly excess | Hit rate | Regions | Obs |")
    L.append("|---|---|---|---|---|---|")
    if not attr.empty:
        for _, r in attr.sort_values(["state", "avg_monthly_excess"], ascending=[True, False]).iterrows():
            L.append(f"| {r.state} | {r.factor} | {pct(r.avg_monthly_excess)} | {pct(r.hit_rate)} | "
                     f"{int(r.n_regions)} | {int(r.n_region_month_obs)} |")
    L.append("\n_A factor with positive avg excess AND hit rate > 50% across most/all regions in "
             "a state is doing so consistently — not just because of one region's one stretch._")

    C.MACRO_STATE_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    run()
