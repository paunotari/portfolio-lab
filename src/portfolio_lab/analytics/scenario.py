"""Scenario simulation: regime-persistent bootstrap of forward returns by macro quadrant.

This is the "simulate future behaviour conditioned on macro characteristics" item from
info/TODO.md / vision.md. It is deliberately a SIMPLE, non-ML statistical method (see
info/CLAUDE.md's caveat on FRED's terms of use prohibiting ML/AI training on FRED-derived data --
resampling historical data with empirical transition counts is descriptive statistics, not that).

METHOD (v2, 2026-07 -- replaced the original i.i.d. monthly draws):

The original version drew each simulated month's quadrant independently, so a path could flip
quadrant every single month -- nothing like real macro history, where regimes persist for many
months. v2 simulates in REGIME SPELLS instead:

1. STATE SEQUENCE with realistic durations. A spell's length is drawn geometrically from that
   state's month-over-month continuation probability (the diagonal of the empirical Markov
   transition matrix from analytics/macro_state.py) -- so simulated regime durations match the
   historically observed persistence (expected duration = 1/(1 - p_stay)), not one-month noise.
   Two ways to pick which state each spell is in:
     * weights mode (simulate_scenario): spell states are drawn i.i.d. with probability
       proportional to weight[s] * (1 - p_stay[s]), which makes the long-run SHARE OF MONTHS in
       each state converge to the requested weights (renewal-reward identity) while keeping real
       durations. This keeps the custom-weights API the future optimizer needs.
     * markov mode (simulate_from_current): the path STARTS IN TODAY'S ACTUAL STATE and each
       subsequent spell is drawn from the historical state-to-state transition probabilities --
       "given where we actually are, what does a future that behaves like measured history look
       like." This is the new default headline scenario (current_conditions).

2. BLOCK BOOTSTRAP within a spell. Months inside a spell are filled by sampling CONTIGUOUS runs
   of real historical months from that state's own history (falling back to shorter chunks near
   run boundaries), so within-regime serial correlation/momentum is partially preserved -- not
   single months shuffled independently. As before, each sampled month is a WHOLE cross-section:
   all 21 series' returns from the same real month, preserving actual cross-series correlation.

This remains "what would a similar macro mix have historically produced," not a forecast of what
WILL happen -- it assumes the future resembles a re-sequenced version of 1997-2026 history, a
real, stated assumption, not a hidden one.

LINEAGE: this is a state-conditioned STATIONARY BOOTSTRAP (Politis & Romano, JASA 1994) -- their
random geometric block lengths are our geometric spell durations (continuation probability = the
transition matrix diagonal), their uniform block starts are our within-state block sampling, with
the regime path conditioning layered on top. The method has a name and asymptotic theory; see
info/literature/stationary-bootstrap.md for the exact correspondence. Our expected block length
is economically pinned by measured regime persistence (~4-6 months), rather than statistically
tuned (Politis-White 2004 is the alternative, and roughly agrees in order of magnitude).

Built-in scenarios:
  current_conditions    markov mode from today's actual quadrant (headline)
  historical_frequency  weights mode, each quadrant weighted by its 1997-2026 share of months
  even_25_25_25_25      weights mode, equal 25% month-share per quadrant

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
from portfolio_lab.analytics.macro_state import classify_states, transition_matrix, STATE_ORDER


def _region(col): return col.split(" | ")[0]
def _factor(col): return col.split(" | ")[1]


def build_universe() -> dict:
    """Everything the simulators need, computed once:
    rets (T x 21 array of real monthly returns on the common window), series names, per-state
    positions into rets (chronological), the empirical transition matrix, and the current state.
    """
    states = classify_states()
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    rets = lv.pct_change().reindex(states.index)
    ok = rets.notna().all(axis=1)          # restrict to months where every series has a return
    rets, st = rets.loc[ok], states.state.loc[ok]

    state_pos = {s: np.flatnonzero((st == s).values) for s in st.unique()
                 if (st == s).sum() >= 3}
    trans = transition_matrix(states)
    return dict(rets=rets.values, series=list(rets.columns), state_pos=state_pos,
                trans=trans, current_state=states.state.iloc[-1],
                hist_weights=st.value_counts(normalize=True).to_dict())


def _block_fill(rng, positions, need: int) -> list[int]:
    """Sample `need` historical month positions for one state as contiguous blocks: pick a random
    month of that state, then extend forward while history stays consecutive (same state, adjacent
    months). Preserves some within-regime serial correlation vs independent single-month draws."""
    out = []
    while len(out) < need:
        k = rng.integers(0, len(positions))
        out.append(int(positions[k]))
        j = k + 1
        while len(out) < need and j < len(positions) and positions[j] == positions[j - 1] + 1:
            out.append(int(positions[j]))
            j += 1
    return out[:need]


def _state_sequence(rng, n_periods, states_avail, stay, first_probs, spell_probs=None,
                    next_probs=None) -> np.ndarray:
    """One trial's month-by-month state indices. Spell durations ~ Geometric(1 - stay[s]).
    Next spell's state: i.i.d. `spell_probs` (weights mode) or `next_probs[s]` row (markov mode).
    """
    seq = np.empty(n_periods, dtype=int)
    s = rng.choice(len(states_avail), p=first_probs)
    t = 0
    while t < n_periods:
        p_stay = stay[s]
        d = int(rng.geometric(1.0 - p_stay)) if p_stay < 1.0 else n_periods - t
        d = min(d, n_periods - t)
        seq[t:t + d] = s
        t += d
        if t < n_periods:
            s = rng.choice(len(states_avail), p=spell_probs if spell_probs is not None
                           else next_probs[s])
    return seq


def _simulate_month_returns(uni, states_avail, stay, first_probs, years, n_trials, seed,
                            spell_probs=None, next_probs=None) -> np.ndarray:
    """(n_trials, n_periods, n_series) simulated monthly returns — the raw material both the
    per-series summary and the portfolio-level cone are computed from."""
    rng = np.random.default_rng(C.SCENARIO_SEED if seed is None else seed)
    n_periods = (years or C.SCENARIO_YEARS) * 12
    n_trials = n_trials or C.SCENARIO_TRIALS
    rets = uni["rets"]

    month_returns = np.empty((n_trials, n_periods, rets.shape[1]))
    for trial in range(n_trials):
        seq = _state_sequence(rng, n_periods, states_avail, stay, first_probs,
                              spell_probs=spell_probs, next_probs=next_probs)
        hist_idx = np.empty(n_periods, dtype=int)
        t = 0
        while t < n_periods:
            end = t
            while end < n_periods and seq[end] == seq[t]:
                end += 1
            pos = uni["state_pos"][states_avail[seq[t]]]
            hist_idx[t:end] = _block_fill(rng, pos, end - t)
            t = end
        month_returns[trial] = rets[hist_idx]
    return month_returns


def _run_trials(uni, states_avail, stay, first_probs, years, n_trials, seed,
                spell_probs=None, next_probs=None) -> pd.DataFrame:
    """Common core: simulate paths, compound them, summarize CAGR/maxDD percentiles per series."""
    years = years or C.SCENARIO_YEARS
    series = uni["series"]
    month_returns = _simulate_month_returns(uni, states_avail, stay, first_probs, years,
                                            n_trials, seed, spell_probs, next_probs)

    growth = 1.0 + month_returns
    cum = np.cumprod(growth, axis=1)                        # (trials, periods, series)
    terminal = cum[:, -1, :]
    running_max = np.maximum.accumulate(cum, axis=1)
    max_dd = (cum / running_max - 1.0).min(axis=1)
    cagr = terminal ** (1.0 / years) - 1.0
    prob_loss = (terminal < 1.0).mean(axis=0)

    rows = []
    for j, col in enumerate(series):
        c, d = cagr[:, j], max_dd[:, j]
        rows.append(dict(series=col, region=_region(col), factor=_factor(col),
                         cagr_p5=np.percentile(c, 5), cagr_p25=np.percentile(c, 25),
                         cagr_p50=np.percentile(c, 50), cagr_p75=np.percentile(c, 75),
                         cagr_p95=np.percentile(c, 95),
                         maxdd_p5=np.percentile(d, 5), maxdd_p50=np.percentile(d, 50),
                         maxdd_p95=np.percentile(d, 95),
                         prob_cumulative_loss=prob_loss[j]))
    return pd.DataFrame(rows)


def simulate_scenario(weights: dict, uni: dict = None, years: int = None,
                      n_trials: int = None, seed: int = None) -> pd.DataFrame:
    """Weights mode: long-run share of simulated months per state converges to `weights`, while
    each regime spell keeps its historically observed duration. Custom weights supported -- this
    is the API a future optimizer calls."""
    uni = uni or build_universe()
    states_avail = [s for s in STATE_ORDER if s in weights and s in uni["state_pos"] and weights[s] > 0]
    if not states_avail:
        raise ValueError(f"none of the requested states have data: {list(weights)}")
    stay = np.array([uni["trans"].loc[s, s] for s in states_avail])
    # spell-state probability q_s ∝ w_s * (1 - p_stay): month-share then ∝ q_s * E[duration] = w_s
    q = np.array([weights[s] for s in states_avail]) * (1.0 - stay)
    q = q / q.sum()
    return _run_trials(uni, states_avail, stay, first_probs=q, years=years,
                       n_trials=n_trials, seed=seed, spell_probs=q)


def simulate_from_current(uni: dict = None, years: int = None, n_trials: int = None,
                          seed: int = None) -> pd.DataFrame:
    """Markov mode: start in today's ACTUAL quadrant; each subsequent spell drawn from the
    historical state-to-state transition probabilities."""
    uni = uni or build_universe()
    states_avail = [s for s in STATE_ORDER if s in uni["state_pos"]]
    stay = np.array([uni["trans"].loc[s, s] for s in states_avail])
    # next-spell distribution per state: transition row without the diagonal, renormalized
    next_probs = []
    for s in states_avail:
        row = uni["trans"].loc[s, states_avail].values.astype(float).copy()
        row[states_avail.index(s)] = 0.0
        next_probs.append(row / row.sum() if row.sum() > 0 else
                          np.ones(len(states_avail)) / len(states_avail))
    first = np.zeros(len(states_avail))
    first[states_avail.index(uni["current_state"])] = 1.0
    return _run_trials(uni, states_avail, stay, first_probs=first, years=years,
                       n_trials=n_trials, seed=seed, next_probs=np.array(next_probs))


def portfolio_cone(weights: dict, uni: dict = None, years: int = None,
                   n_trials: int = None, seed: int = None) -> dict:
    """Portfolio-level current_conditions cone: run a WEIGHTED BLEND of series through the same
    markov-mode simulation and summarize its simulated CAGR / max-drawdown percentiles and
    probability of cumulative loss. This is the optimizer's validator (scenario engine as judge,
    not objective — info/portfolio_optimization.md): the recommendation's forward cone under the
    stated "future = re-sequenced history" assumption.

    `weights`: {series column name: weight fraction}, summing to 1 over uni['series'] members.
    """
    uni = uni or build_universe()
    w = np.zeros(len(uni["series"]))
    for name, val in weights.items():
        if name not in uni["series"]:
            raise ValueError(f"unknown series {name!r}")
        w[uni["series"].index(name)] = val
    if abs(w.sum() - 1.0) > C.PORTFOLIO_WEIGHT_TOLERANCE_PCT / 100.0:
        raise ValueError(f"portfolio weights must sum to 100% (got {w.sum():.1%})")

    states_avail = [s for s in STATE_ORDER if s in uni["state_pos"]]
    stay = np.array([uni["trans"].loc[s, s] for s in states_avail])
    next_probs = []
    for s in states_avail:
        row = uni["trans"].loc[s, states_avail].values.astype(float).copy()
        row[states_avail.index(s)] = 0.0
        next_probs.append(row / row.sum() if row.sum() > 0 else
                          np.ones(len(states_avail)) / len(states_avail))
    first = np.zeros(len(states_avail))
    first[states_avail.index(uni["current_state"])] = 1.0

    years = years or C.SCENARIO_YEARS
    month_returns = _simulate_month_returns(uni, states_avail, stay, first, years,
                                            n_trials, seed, next_probs=np.array(next_probs))
    blended = month_returns @ w                              # (trials, periods)
    cum = np.cumprod(1.0 + blended, axis=1)
    terminal = cum[:, -1]
    cagr = terminal ** (1.0 / years) - 1.0
    max_dd = (cum / np.maximum.accumulate(cum, axis=1) - 1.0).min(axis=1)
    return dict(scenario="current_conditions", years=years,
                cagr_p5=float(np.percentile(cagr, 5)), cagr_p25=float(np.percentile(cagr, 25)),
                cagr_p50=float(np.percentile(cagr, 50)), cagr_p75=float(np.percentile(cagr, 75)),
                cagr_p95=float(np.percentile(cagr, 95)),
                maxdd_p5=float(np.percentile(max_dd, 5)), maxdd_p50=float(np.percentile(max_dd, 50)),
                maxdd_p95=float(np.percentile(max_dd, 95)),
                prob_cumulative_loss=float((terminal < 1.0).mean()))


def run(years: int = None, n_trials: int = None):
    C.ensure_dirs()
    uni = build_universe()
    even = {s: 0.25 for s in STATE_ORDER}

    scenarios = {
        "current_conditions": ("markov", None),
        "historical_frequency": ("weights", uni["hist_weights"]),
        "even_25_25_25_25": ("weights", even),
    }
    all_rows, weights_used = [], {}
    for name, (mode, weights) in scenarios.items():
        df = (simulate_from_current(uni, years=years, n_trials=n_trials) if mode == "markov"
              else simulate_scenario(weights, uni, years=years, n_trials=n_trials))
        df.insert(0, "scenario", name)
        all_rows.append(df)
        weights_used[name] = weights
    summary = pd.concat(all_rows, ignore_index=True)
    summary.to_csv(C.SCENARIO_SUMMARY, index=False)

    _write_report(summary, weights_used, uni, years or C.SCENARIO_YEARS,
                  n_trials or C.SCENARIO_TRIALS)
    print(f"[scenario] {len(scenarios)} scenarios x {len(uni['series'])} series, "
          f"{n_trials or C.SCENARIO_TRIALS} trials x {years or C.SCENARIO_YEARS}y "
          f"(regime-persistent spells, block bootstrap) -> {C.SCENARIO_DIR}")


def _write_report(summary: pd.DataFrame, weights_used: dict, uni: dict, years: int, n_trials: int):
    def pct(x): return f"{x*100:,.1f}%"

    L = ["# Scenario Simulation Report\n",
         f"Regime-persistent bootstrap Monte Carlo: {n_trials} simulated {years}-year paths per "
         "scenario. Regime spells last as long as history says they do (geometric durations from "
         "the empirical transition matrix), months within a spell are sampled as contiguous "
         "blocks of real history (whole cross-sections, preserving real cross-series "
         "correlation). **This assumes the future resembles a re-sequenced version of 1997-2026 "
         "history — a stated assumption, not a forecast.**\n"]

    for name in summary.scenario.unique():
        L.append(f"## Scenario: {name}")
        w = weights_used.get(name)
        if w is None:
            L.append(f"Starts in today's actual state (**{uni['current_state']}**); subsequent "
                     "regime spells follow the historical state-to-state transition probabilities.")
        else:
            L.append("Target long-run month shares: " + ", ".join(
                f"{s} {pct(v)}" for s, v in sorted(w.items(), key=lambda x: -x[1])))
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
