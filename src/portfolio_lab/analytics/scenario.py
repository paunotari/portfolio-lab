"""Scenario simulation: bootstrap forward returns conditioned on macro-quadrant weights.

This is the "simulate future behaviour conditioned on macro characteristics" item from
info/TODO.md / vision.md. It is deliberately a SIMPLE, non-ML statistical method (see
info/CLAUDE.md's caveat on FRED's terms of use prohibiting ML/AI training on FRED-derived data --
plain Monte Carlo resampling of historical data is not that): for a chosen set of probability
weights across the 4 macro quadrants (from analytics/macro_state.py), it simulates many possible
future paths by repeatedly (a) drawing a quadrant per future month according to the weights, then
(b) drawing one HISTORICAL MONTH at random from that quadrant's actual observed months and using
its REAL, whole-month return vector across all 21 series. Sampling the whole month (not each
series independently) preserves real historical cross-series/cross-factor correlation structure
within the simulated path, rather than fabricating independent series that never actually
co-occurred.

This is explicitly a "what would a similar macro mix probably look like" exercise, not a forecast
of what WILL happen -- it assumes the future resembles a reshuffled version of 1997-2026 history,
which is a real, stated assumption, not a hidden one.

Two built-in scenarios are run by default (matching vision.md's signature-feature examples):
  historical_frequency  weight each quadrant by how often it actually occurred (1997-2026)
  even_25_25_25_25      equal 25% weight across all 4 quadrants

Custom weights can be passed to simulate_scenario() directly (e.g. for a future optimizer to
explore "what if I think stagflation risk is elevated").

Outputs (to outputs/analytics/scenario/):
  scenario_summary.csv   scenario x series: simulated CAGR percentiles (5/25/50/75/95), max
                         drawdown percentiles, probability of a cumulative loss over the horizon
  REPORT_scenario.md     narrative: best/worst simulated performers per scenario

Run:  python -m portfolio_lab.analytics.scenario
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.macro_state import classify_states


def _region(col): return col.split(" | ")[0]
def _factor(col): return col.split(" | ")[1]


def _return_pools(states: pd.DataFrame) -> tuple[dict, list]:
    """{state_name: (n_months, 21) numpy array of that state's real monthly returns}, series list."""
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    rets = lv.pct_change().reindex(states.index)
    series = list(rets.columns)
    pools = {}
    for state_name in states.state.unique():
        sub = rets.loc[states.index[states.state == state_name]].dropna(how="any")
        if len(sub) >= 3:
            pools[state_name] = sub.values
    return pools, series


def simulate_scenario(weights: dict, pools: dict, series: list, years: int = None,
                      n_trials: int = None, seed: int = None) -> pd.DataFrame:
    """Simulate `n_trials` independent `years`-long monthly paths under the given quadrant
    weights, sampling whole historical months (with replacement) from each quadrant's pool.
    Returns a DataFrame: one row per series, with simulated CAGR/maxDD percentiles."""
    years = years or C.SCENARIO_YEARS
    n_trials = n_trials or C.SCENARIO_TRIALS
    seed = C.SCENARIO_SEED if seed is None else seed
    rng = np.random.default_rng(seed)
    n_periods = years * 12

    states_avail = [s for s in weights if s in pools and weights[s] > 0]
    if not states_avail:
        raise ValueError(f"none of the requested states have data: {list(weights)}")
    w = np.array([weights[s] for s in states_avail], dtype=float)
    w = w / w.sum()

    # (n_trials, n_periods) matrix of which state each simulated month belongs to
    state_draw = rng.choice(len(states_avail), size=(n_trials, n_periods), p=w)
    n_series = len(series)
    month_returns = np.empty((n_trials, n_periods, n_series))
    for i, s in enumerate(states_avail):
        mask = state_draw == i
        n_needed = mask.sum()
        if n_needed == 0:
            continue
        pool = pools[s]
        picks = rng.integers(0, len(pool), size=n_needed)
        month_returns[mask] = pool[picks]

    # compound each trial's path per series -> terminal value (base 1.0), and running max for maxDD
    growth = 1.0 + month_returns
    cum = np.cumprod(growth, axis=1)                       # (trials, periods, series)
    terminal = cum[:, -1, :]                                # (trials, series)
    running_max = np.maximum.accumulate(cum, axis=1)
    drawdown = cum / running_max - 1.0
    max_dd = drawdown.min(axis=1)                           # (trials, series)

    cagr = terminal ** (1.0 / years) - 1.0                  # (trials, series)
    prob_loss = (terminal < 1.0).mean(axis=0)

    rows = []
    for j, col in enumerate(series):
        c = cagr[:, j]
        d = max_dd[:, j]
        rows.append(dict(series=col, region=_region(col), factor=_factor(col),
                         cagr_p5=np.percentile(c, 5), cagr_p25=np.percentile(c, 25),
                         cagr_p50=np.percentile(c, 50), cagr_p75=np.percentile(c, 75),
                         cagr_p95=np.percentile(c, 95),
                         maxdd_p5=np.percentile(d, 5), maxdd_p50=np.percentile(d, 50),
                         maxdd_p95=np.percentile(d, 95),
                         prob_cumulative_loss=prob_loss[j]))
    return pd.DataFrame(rows)


def _historical_frequency_weights(states: pd.DataFrame) -> dict:
    return (states.state.value_counts(normalize=True)).to_dict()


def _even_weights(states: pd.DataFrame) -> dict:
    uniq = states.state.unique()
    return {s: 1.0 / len(uniq) for s in uniq}


def run(years: int = None, n_trials: int = None):
    C.ensure_dirs()
    states = classify_states()
    pools, series = _return_pools(states)

    scenarios = {
        "historical_frequency": _historical_frequency_weights(states),
        "even_25_25_25_25": _even_weights(states),
    }

    all_rows = []
    for name, weights in scenarios.items():
        df = simulate_scenario(weights, pools, series, years=years, n_trials=n_trials)
        df.insert(0, "scenario", name)
        all_rows.append(df)
    summary = pd.concat(all_rows, ignore_index=True)
    summary.to_csv(C.SCENARIO_SUMMARY, index=False)

    _write_report(summary, scenarios, years or C.SCENARIO_YEARS, n_trials or C.SCENARIO_TRIALS)
    print(f"[scenario] {len(scenarios)} scenarios x {len(series)} series, "
          f"{n_trials or C.SCENARIO_TRIALS} trials x {years or C.SCENARIO_YEARS}y -> {C.SCENARIO_DIR}")


def _write_report(summary: pd.DataFrame, scenarios: dict, years: int, n_trials: int):
    def pct(x): return f"{x*100:,.1f}%"

    L = ["# Scenario Simulation Report\n",
         f"Bootstrap Monte Carlo: {n_trials} simulated {years}-year paths per scenario, sampling "
         "whole historical months (preserving real cross-series correlation) from "
         "`analytics/macro_state.py`'s 4-quadrant classification, weighted by the scenario's "
         "quadrant probabilities. **This assumes the future resembles a reshuffled version of "
         "1997-2026 history — a stated assumption, not a forecast.**\n"]

    for name, weights in scenarios.items():
        L.append(f"## Scenario: {name}")
        L.append("Quadrant weights: " + ", ".join(f"{s} {pct(w)}" for s, w in
                 sorted(weights.items(), key=lambda x: -x[1])))
        sub = summary[summary.scenario == name].sort_values("cagr_p50", ascending=False)
        L.append(f"\n| Series | CAGR p5 | CAGR p50 | CAGR p95 | MaxDD p50 | P(loss over {years}y) |")
        L.append("|---|---|---|---|---|---|")
        for _, r in sub.iterrows():
            L.append(f"| {r.series} | {pct(r.cagr_p5)} | {pct(r.cagr_p50)} | {pct(r.cagr_p95)} | "
                     f"{pct(r.maxdd_p50)} | {pct(r.prob_cumulative_loss)} |")
        L.append("")

    C.SCENARIO_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    run()
