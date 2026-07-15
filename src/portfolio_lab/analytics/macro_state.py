"""4-quadrant macro-state classifier: composite growth trend x composite inflation trend.

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

METHOD (v2, 2026-07 -- replaced the original 2-indicator hard-threshold rule):

1. COMPOSITE SIGNALS, not single proxies. Growth and inflation are each measured by several
   indicators (see config.MACRO_STATE_GROWTH_COMPONENTS / _INFLATION_COMPONENTS). For each
   component: smooth with a 3-month mean, take the trend (smoothed value now minus 6 months ago
   -- ACCELERATING vs DECELERATING, not the raw level), z-score that trend by its own full-sample
   standard deviation, and sign-adjust (e.g. unemployment rising counts as growth *down*). The
   composite score is the average of the available component z-scores, re-standardized. The
   primary indicator (indpro_yoy / core_pce_yoy) must be present for a month to be classified;
   secondary components with shorter histories (breakevens 2003+, Baa spread 1986+) simply join
   when they exist.

2. CONTINUOUS + SOFT, not a binary bucket. The composite scores are continuous, so a month can
   sit *near the border* between quadrants instead of being forced into one. Each month also gets
   a soft probability per quadrant: p(growth up) = Phi(growth_score) (the normal CDF -- score 0 =
   50/50 border, score +1 = 84% up), independently for inflation, and the quadrant probability is
   the product (e.g. p_reflation = p_growth_up * p_inflation_up). The hard label (used by
   per-state performance, the scenario module, and the timeline) is simply the most probable
   quadrant = the sign of the two scores, so it stays consistent with the soft view.

3. PERSISTENCE via a state-transition (Markov) matrix. From the monthly hard-label sequence we
   count how often each state moves to each other state month-over-month -> a 4x4 row-stochastic
   matrix (macro_state_transitions.csv) with each state's implied expected duration
   1/(1 - p_stay). This is what gives the scenario simulation realistic regime *durations*
   instead of i.i.d. monthly quadrant flips.

Normalization caveat: z-scoring uses each component's FULL-SAMPLE trend std -- a mild look-ahead
that affects only the scale/weighting of components, never the sign of the primary trend. It
keeps the method simple and reproducible; an expanding window would jitter early history for no
classification benefit.

FRED terms-of-use line (the "statistics vs ML" decision from info/TODO.md): everything here is
deterministic descriptive statistics COMPUTED from the data -- rolling means, z-scores, empirical
transition counts, normal CDF mapping. Nothing is *fitted/trained to predict* (no regression
forecasts, no EM-fitted hidden-Markov model, no ML). That is the line: counting and normalizing
history = fine under FRED's ToS; training a predictive model on FRED data = Phase 4, and would
need a non-FRED data source (info/CLAUDE.md caveat #11).

Sanity check baked into the report: the share of each state's months that fall inside NBER-dated
recessions (us_recession) -- Deflationary bust should, and does, capture most of them.

Caveats (see info/CLAUDE.md):
  - "Current state" is only as fresh as the latest released macro print (~1 month lag) -- this
    is a property of all macro data, not a limitation of this code.
  - Per-state performance pools NON-CONTIGUOUS months together; annualized return is a simple
    (1+mean_monthly_return)**12-1, not a compounded path over skipped months -- treat it as "the
    average pace of return during months like this," not a literal achievable investment path.
  - This is a descriptive/correlational classification, not a forecast -- see the scenario
    simulation module for turning it into a probabilistic forward view.

Run:  python -m portfolio_lab.analytics.macro_state
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

from portfolio_lab import config as C

STATES = {
    (True, False): "Goldilocks (disinflationary growth)",
    (True, True): "Reflation (overheating)",
    (False, False): "Deflationary bust (recession/slowdown)",
    (False, True): "Stagflation (growth-inflation squeeze)",
}
# canonical display/matrix order
STATE_ORDER = [
    "Goldilocks (disinflationary growth)",
    "Reflation (overheating)",
    "Stagflation (growth-inflation squeeze)",
    "Deflationary bust (recession/slowdown)",
]
# state name -> its probability column in macro_state_monthly.csv
PROB_COLS = {
    "Goldilocks (disinflationary growth)": "p_goldilocks",
    "Reflation (overheating)": "p_reflation",
    "Stagflation (growth-inflation squeeze)": "p_stagflation",
    "Deflationary bust (recession/slowdown)": "p_deflationary_bust",
}


def _region(col): return col.split(" | ")[0]
def _factor(col): return col.split(" | ")[1]


def _norm_cdf(z: pd.Series) -> pd.Series:
    """Standard normal CDF, elementwise, NaN-preserving (no scipy dependency)."""
    return z.map(lambda v: np.nan if pd.isna(v) else 0.5 * (1.0 + math.erf(v / math.sqrt(2.0))))


def _composite_score(macro: pd.DataFrame, components: dict[str, int], primary: str) -> pd.Series:
    """Average of the components' sign-adjusted, z-scored trends, re-standardized.

    Trend = 3m-smoothed value now minus 6m ago (config). Arithmetic on NaN propagates NaN
    naturally, so months without a released print drop out instead of silently defaulting --
    the boolean-comparison pitfall from info/CLAUDE.md caveat #14 can't occur here. Months where
    the PRIMARY component is missing are masked out entirely; secondary components are optional.
    """
    smooth, lag = C.MACRO_STATE_SMOOTH_MONTHS, C.MACRO_STATE_TREND_LAG_MONTHS
    zs = {}
    for name, sign in components.items():
        if name not in macro.columns:
            continue  # tolerate a partially failed FRED fetch for secondary components
        s = macro[name].rolling(smooth).mean()
        trend = s - s.shift(lag)
        sd = trend.std()
        if not np.isfinite(sd) or sd == 0:
            continue
        zs[name] = sign * trend / sd
    if primary not in zs:
        raise KeyError(f"primary macro-state indicator '{primary}' missing from macro data")
    zdf = pd.DataFrame(zs)
    score = zdf.mean(axis=1, skipna=True).where(zdf[primary].notna())
    return score / score.std()


def classify_states(start: str = None) -> pd.DataFrame:
    """Return a DataFrame indexed by month with composite growth/inflation scores, soft quadrant
    probabilities, hard up/down booleans and the hard state label, starting once both primary
    indicators have enough history.

    FRED's macro history goes back to 1854 (industrial production) / 1919 (PPI), far earlier than
    our return series (1997+). Classifying that far back would make "historical frequency of each
    state" meaningless -- it'd be dominated by 19th/early-20th-century depression-era data that
    has nothing to do with the indices we hold. So this clips to the return series' own history
    BY DEFAULT. Pass `start` to clip elsewhere (analytics/long_history.py uses the full
    classifiable range for the Fama-French proxy study); the composite scores themselves are
    identical either way -- they are computed on the full macro history before clipping, so a
    different `start` never changes a month's label, only which months are returned.
    """
    macro = pd.read_csv(C.MACRO_MONTHLY, index_col=0, parse_dates=True).sort_index()
    g_col, i_col = C.MACRO_STATE_GROWTH_PRIMARY, C.MACRO_STATE_INFLATION_PRIMARY

    g_score = _composite_score(macro, C.MACRO_STATE_GROWTH_COMPONENTS, g_col)
    i_score = _composite_score(macro, C.MACRO_STATE_INFLATION_COMPONENTS, i_col)
    p_g_up, p_i_up = _norm_cdf(g_score), _norm_cdf(i_score)

    df = pd.DataFrame({
        "growth_value": macro[g_col],
        "growth_smooth": macro[g_col].rolling(C.MACRO_STATE_SMOOTH_MONTHS).mean(),
        "growth_score": g_score,
        "inflation_value": macro[i_col],
        "inflation_smooth": macro[i_col].rolling(C.MACRO_STATE_SMOOTH_MONTHS).mean(),
        "inflation_score": i_score,
        "p_goldilocks": p_g_up * (1 - p_i_up),
        "p_reflation": p_g_up * p_i_up,
        "p_stagflation": (1 - p_g_up) * p_i_up,
        "p_deflationary_bust": (1 - p_g_up) * (1 - p_i_up),
    }).dropna(subset=["growth_score", "inflation_score"])
    df["growth_up"] = df.growth_score > 0
    df["inflation_up"] = df.inflation_score > 0
    df["state"] = [STATES[(bool(gu), bool(iu))] for gu, iu in zip(df.growth_up, df.inflation_up)]

    if start is None:
        start = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).index.min()
    return df.loc[start:]


def transition_matrix(states: pd.DataFrame) -> pd.DataFrame:
    """Empirical monthly state-transition (Markov) matrix: P(state_{t+1} = col | state_t = row).

    Rows sum to 1. The diagonal is each state's month-over-month continuation probability, so its
    implied expected duration is 1/(1 - diagonal). Plain transition counting -- descriptive
    statistics, not a fitted model.
    """
    cur = pd.Series(states.state.values[:-1], name="from")
    nxt = pd.Series(states.state.values[1:], name="to")
    counts = pd.crosstab(cur, nxt).reindex(index=STATE_ORDER, columns=STATE_ORDER, fill_value=0)
    return counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0)


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


def nber_overlap(states: pd.DataFrame) -> pd.Series:
    """Share of each state's months that fall inside an NBER-dated recession (sanity check --
    Deflationary bust should capture most recession months). Empty Series if us_recession is
    unavailable."""
    macro = pd.read_csv(C.MACRO_MONTHLY, index_col=0, parse_dates=True)
    if "us_recession" not in macro.columns:
        return pd.Series(dtype=float)
    rec = macro["us_recession"].reindex(states.index)
    return rec.groupby(states.state).mean()


def quadrant_outlook(states: pd.DataFrame, trans: pd.DataFrame, months: int = None) -> dict:
    """P(quadrant in `months` months) = soft probability vector today x transition matrix^months.

    Chosen by a 2026-07 walk-forward backtest (info/TODO.md): of persistence, momentum-arrow
    extrapolation, Markov and nearest-analog methods, this h-step Markov distribution had the
    best calibration (Brier score) at every tested horizon. Starting from the SOFT vector (not
    the one-hot hard label) carries today's border-straddling uncertainty into the outlook.
    Still counting statistics -- matrix power of empirical transition counts, nothing fitted.
    """
    months = months or C.MACRO_STATE_OUTLOOK_MONTHS
    v = states.iloc[-1][[PROB_COLS[s] for s in STATE_ORDER]].values.astype(float)
    P = trans.loc[STATE_ORDER, STATE_ORDER].values
    out = v @ np.linalg.matrix_power(P, months)
    return dict(zip(STATE_ORDER, out.astype(float)))


def current_state(states: pd.DataFrame, trans: pd.DataFrame) -> dict:
    last = states.iloc[-1]
    prior = states.iloc[-1 - C.MACRO_STATE_TREND_LAG_MONTHS] if len(states) > C.MACRO_STATE_TREND_LAG_MONTHS else None
    probs = {s: float(last[PROB_COLS[s]]) for s in STATE_ORDER}
    trow = trans.loc[last.state]
    return dict(
        as_of=str(states.index[-1].date()),
        state=last.state,
        probs=probs,
        growth_direction="accelerating" if last.growth_up else "decelerating",
        growth_value=last.growth_value, growth_smooth=last.growth_smooth,
        growth_score=float(last.growth_score),
        inflation_direction="accelerating" if last.inflation_up else "decelerating",
        inflation_value=last.inflation_value, inflation_smooth=last.inflation_smooth,
        inflation_score=float(last.inflation_score),
        months_in_current_state=int((states.state[::-1] == last.state).cumprod().sum()),
        prior_state=(prior.state if prior is not None else None),
        stay_prob=float(trow[last.state]),
        expected_duration_months=float(1.0 / (1.0 - trow[last.state])) if trow[last.state] < 1 else float("inf"),
        likely_next=(trow.drop(last.state).idxmax() if trow.drop(last.state).sum() > 0 else None),
    )


def run():
    C.ensure_dirs()
    states = classify_states()
    states.to_csv(C.MACRO_STATE_MONTHLY)

    trans = transition_matrix(states)
    trans.to_csv(C.MACRO_STATE_TRANSITIONS)

    perf = state_performance(states)
    perf.to_csv(C.MACRO_STATE_PERFORMANCE, index=False)

    attr = factor_attribution(states)
    attr.to_csv(C.MACRO_STATE_FACTOR_ATTRIBUTION, index=False)

    cur = current_state(states, trans)
    outlook = quadrant_outlook(states, trans)
    _write_report(states, perf, attr, cur, trans, outlook)

    freq = states.state.value_counts(normalize=True) * 100
    print(f"[macro_state] {len(states)} months classified ({states.index[0].date()}.."
          f"{states.index[-1].date()}), current = {cur['state']} "
          f"({cur['months_in_current_state']} months, p={cur['probs'][cur['state']]:.0%}) "
          f"-> {C.MACRO_STATE_DIR}")
    for s, pct in freq.items():
        print(f"    {pct:5.1f}%  {s}")


def _write_report(states, perf, attr, cur, trans, outlook):
    def pct(x): return "n/a" if pd.isna(x) else f"{x*100:,.1f}%"
    freq = states.state.value_counts(normalize=True) * 100
    g_parts = ", ".join(f"{n} ({'+' if s > 0 else '-'})" for n, s in C.MACRO_STATE_GROWTH_COMPONENTS.items())
    i_parts = ", ".join(f"{n} ({'+' if s > 0 else '-'})" for n, s in C.MACRO_STATE_INFLATION_COMPONENTS.items())
    top2 = sorted(cur["probs"].items(), key=lambda x: -x[1])[:2]

    L = ["# 4-Quadrant Macro-State Report\n",
         "Systematic classification (composite growth trend x composite inflation trend), distinct "
         "from the 10 hand-dated historical regimes in `analytics/regimes.py`. See the module "
         "docstring for the full method — this is descriptive statistics, not a forecast and not ML.\n",
         "## Method (transparency)\n",
         f"- **Growth composite:** {g_parts}",
         f"- **Inflation composite:** {i_parts}",
         f"- Each component: {C.MACRO_STATE_SMOOTH_MONTHS}m-smoothed, trend vs "
         f"{C.MACRO_STATE_TREND_LAG_MONTHS}m ago, z-scored, sign-adjusted; composite = mean of "
         "available components, re-standardized. Primary indicators (indpro_yoy / core_pce_yoy) "
         "must be present; shorter-history components join when available.",
         "- Soft view: p(growth up) = Phi(growth_score); quadrant probability = product of the "
         "two axis probabilities. Hard label = most probable quadrant (sign of the scores).\n",
         "## Current state\n",
         f"**As of {cur['as_of']}: {cur['state']}** (in this state for "
         f"{cur['months_in_current_state']} consecutive month(s); prior state: {cur['prior_state']})",
         f"- Soft read: " + " / ".join(f"{pct(p)} {s.split(' (')[0]}" for s, p in top2),
         f"- Growth composite score {cur['growth_score']:+.2f} → **{cur['growth_direction']}** "
         f"(indpro {cur['growth_value']:.1f}% YoY, {C.MACRO_STATE_SMOOTH_MONTHS}m-avg {cur['growth_smooth']:.1f}%)",
         f"- Inflation composite score {cur['inflation_score']:+.2f} → **{cur['inflation_direction']}** "
         f"(core PCE {cur['inflation_value']:.1f}% YoY, {C.MACRO_STATE_SMOOTH_MONTHS}m-avg {cur['inflation_smooth']:.1f}%)",
         f"- Persistence: historically this state continues month-over-month with "
         f"{pct(cur['stay_prob'])} probability (expected duration ~{cur['expected_duration_months']:.1f} months); "
         f"most likely next state: {cur['likely_next']}\n",
         f"## {C.MACRO_STATE_OUTLOOK_MONTHS}-month outlook (Markov)\n",
         "Soft probability vector today x transition matrix^"
         f"{C.MACRO_STATE_OUTLOOK_MONTHS}. Best-calibrated method in the 2026-07 walk-forward "
         "backtest (see info/TODO.md) — counting statistics, not a fitted model.\n"]
    for s, p in sorted(outlook.items(), key=lambda x: -x[1]):
        L.append(f"- {pct(p)}  {s}")
    L += ["", "## Historical frequency of each state\n"]
    for s, p in freq.items():
        L.append(f"- {p:.1f}%  {s}")

    L.append("\n## Monthly state-transition (Markov) matrix\n")
    L.append("P(next month's state = column | this month's state = row). Diagonal = persistence.\n")
    short = {s: s.split(" (")[0] for s in STATE_ORDER}
    L.append("| From \\ To | " + " | ".join(short[s] for s in STATE_ORDER) + " | Expected duration |")
    L.append("|---|" + "---|" * (len(STATE_ORDER) + 1))
    for s in STATE_ORDER:
        row = trans.loc[s]
        dur = 1.0 / (1.0 - row[s]) if row[s] < 1 else float("inf")
        L.append(f"| {short[s]} | " + " | ".join(pct(row[t]) for t in STATE_ORDER)
                 + f" | {dur:.1f} mo |")

    nber = nber_overlap(states)
    if not nber.empty:
        L.append("\n## Sanity check: overlap with NBER-dated recessions\n")
        L.append("Share of each state's months that fall inside an official NBER recession:")
        for s in STATE_ORDER:
            if s in nber.index:
                L.append(f"- {short[s]}: {pct(nber[s])}")

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
