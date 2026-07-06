# TODO — task backlog

Actionable backlog for `portfolio_lab`. `vision.md` is the narrative roadmap (why, phases);
this file is the concrete, checkable list derived from it plus ad-hoc engineering tasks. When a
phase in `vision.md` completes, update its status there too — this file doesn't replace it.

Check items off as completed. Add new ones as they come up; keep entries short and specific.

---

## Now / quick wins

_(both done — see Portfolio optimization below for what builds on them next)_

## Dashboard: Tier-1 essentials layer (vision.md "Product design principle")

- [ ] Add a Tier-1 summary to each existing dashboard tab (Performance, Factor vs Reference /
      Regimes, Correlations/Diversification, Macro) per `vision.md`'s layering table: a small set
      of plain-language verdicts on top, with today's charts/tables becoming the Tier-2 detail
      underneath (collapsed or scrolled-to, not removed). Needs a "verdict generation" step per
      module (e.g. "led 1998–2010, has lagged since ~2010") — mostly template/text generation
      from analytics already computed, not new analysis.
- [ ] When the optimizer (Phase 3) exists, its Tier-1 output must be the recommended allocation +
      a "why" using the same essential bullets per holding — not a separate simplified summary
      disconnected from what the optimizer actually scored on.

## Dashboard: Macro State quadrant visualization

- [x] **4-quadrant position chart with trajectory and forecast** — DONE 2026-07. Lives at the top
      of the Macro State tab (right under the Tier-1 verdict card): current dot on continuous
      composite scores (can straddle borders), selectable trail (12/24/36m/full), month picker
      that also shows the actual forward path from any past date (hollow dots), momentum
      extrapolation arrow, and a collapsible "How is this computed?" block documenting smoothing,
      lag, z-scoring, probability mapping and the forecast method. Enabled by the classifier v2
      redesign below (continuous scores + soft probabilities).

## Portfolio optimization (vision.md Phase 3)

- [ ] **Design the multi-objective portfolio optimizer.** Goal: given the return/risk/exposure
      data already computed, find weights that best satisfy user-specified objectives, not just
      a single fixed formula. Needs to support, at minimum:
  - Single-objective modes, e.g. "maximize historical return" (degenerates to 100% in the best
    performer) or "minimize volatility."
  - Multi-objective modes with 2–3 goals at once, e.g. "maximize return **and** minimize risk
    **and** maximize sector diversification," blended.
  - **User-tunable priority weighting** across objectives — e.g. "I don't care about minimizing
    risk, I'll accept more of it to chase return" vs. "diversification matters most to me, return
    and risk matter less."
  - **Constrained targets**, e.g. "the best achievable return across these indexes is ~14%/yr —
    give me the allocation with maximum diversification and minimum risk subject to achieving at
    least 12%/yr."
  - This is explicitly complex and depends on other pieces landing first (see Depends-on below).
  - **Depends on:** ✅ the 100%-weight constraint and portfolio-level performance stats (both now
    in `portfolio/diversification.py`); a settled set of risk metrics (vol, max DD, maybe CVaR);
    ideally the regime-conditional data from Phase 2 if we want regime-aware optimization, not
    just full-sample optimization.
  - **Open question (from vision.md):** optimization backend — `scipy.optimize`, `cvxpy`, or
    `Riskfolio-Lib`. Needs a decision before implementation starts.
- [ ] **Regime-targeted allocation** (the signature feature). Let the user express a desired
      performance profile *per macro regime/quadrant* rather than only an average — e.g. split
      evenly (25/25/25/25 across inflationary/deflationary/growth/stagnation), weight by each
      regime's historical frequency, or set custom per-regime targets ("do well in X, accept
      less in Y") — then optimize the allocation to match. Builds directly on the multi-objective
      optimizer above plus the 4-quadrant classification below.

## Macro & regime analysis (vision.md Phase 2 remainder)

Motivating observation (2026-07): over the full 28y, AC Asia ex Japan / EM (esp. Enhanced Value)
top the CAGR table — but that's almost entirely a 1998–2010 story. From ~2010–2026 the leaders
flip to USA Quality, World Momentum/Quality generally, with visibly lower volatility. The
regime/leadership question isn't "who won in 28 years," it's "why did leadership flip, what macro
backdrop was each era in, and can we read the current backdrop to reason about what's more likely
to work now." That's the goal of this section — go beyond who-won-historically to a macro-aware
read of *why*, tying directly into the regime-targeted optimizer above.

**Status (2026-07): all 5 items below are DONE.** Added `breakeven_10y`/`breakeven_5y`
(T10YIE/T5YIE, market inflation expectations) and `us_recession` (NBER USREC) to `ingest/macro.py`
first, as free supporting data for the classifier. See `info/CLAUDE.md` §4 for module details and
§7 caveats #13-15 for the two real bugs found and fixed along the way (pandas NaN-comparison
pitfall in the trend classifier; depression-era history needed clipping out of the frequency
stats). **Now in the dashboard too** (2026-07): the "Macro State" tab shows the Tier-1
current-quadrant verdict, the colored month-by-month state timeline, per-state index performance,
factor edge by state, and the Monte Carlo scenario ranges — the first tab actually built to the
Tier-1/Tier-2 layering principle.

- [x] **Per-regime macro correlations** — `analytics/macro_link.py::regime_correlations()`, one
      matrix per named regime (chg basis, lag 0), written to `correlation_by_regime/*.csv`.
- [x] **4-quadrant macro-state classification** — `analytics/macro_state.py`, growth (indpro_yoy)
      × inflation (core_pce_yoy) trend → Goldilocks/Reflation/Deflationary-bust/Stagflation, with
      per-state performance broken down by series (region+factor) in `macro_state_performance.csv`.
- [x] **Regime-attribution narrative report** — same module's `factor_attribution()`: for each
      state, does each factor type consistently beat its own region's reference, averaged across
      regions (`macro_state_factor_attribution.csv`). Confirms e.g. Value leads in Deflationary
      bust (61.5% hit rate), Momentum leads in Goldilocks/Reflation but notably lags in Stagflation
      (-0.1% excess) — matching the known 2022 rate-shock pattern.
- [x] **Current-regime + trend read** — `macro_state.current_state()`: as of the latest complete
      macro print, which quadrant, which direction growth/inflation are trending, and how many
      consecutive months in that state. Explicitly labeled descriptive, not a forecast.
- [x] **Scenario simulation** — `analytics/scenario.py`: bootstrap Monte Carlo, resampling whole
      historical months (preserving real cross-series correlation) weighted by quadrant
      probability. Two built-in scenarios (historical-frequency-weighted, even 25/25/25/25);
      `simulate_scenario()` takes arbitrary custom weights for later optimizer use.
- [x] *(Explicitly out of scope, confirmed)* an actual predictive model (ML/probabilistic) of
      regime transitions or forward returns stays vision.md Phase 4 territory — same FRED-ToS
      constraint as the deferred ML/RL item below. Everything built here is descriptive/
      correlational + a stated-assumption bootstrap, not a forecast.

### Follow-up: revisit both methods — likely too simple as-is (2026-07)

**Status: DONE 2026-07 — both methods redesigned (v2), all three items landed.** See
`analytics/macro_state.py` / `analytics/scenario.py` docstrings and `info/CLAUDE.md` §4 + caveats
#11/#17 for the full method; the dashboard's "How is this computed?" block mirrors it for users.

- [x] **Classifier v2 — composite, continuous, with persistence.** Growth = z-scored trend
      composite of indpro_yoy, unemployment(−), yield-curve slope, VIX(−), Baa−10Y credit
      spread(−) (BAA10Y newly ingested — full history, unlike the 2023+ HY OAS); inflation =
      core PCE, CPI, PPI commodities, 10y breakeven. Continuous scores + soft quadrant
      probabilities (Φ-mapped, e.g. "45% Stagflation / 38% Reflation") instead of a forced
      bucket; hard label = most probable quadrant, keeping downstream compatibility. Empirical
      monthly Markov transition matrix (`macro_state_transitions.csv`) with per-state persistence
      and expected durations (~4–6 months), plus an NBER-recession overlap sanity check.
- [x] **Scenario v2 — regime-persistent simulation.** Paths are built in regime *spells*
      (geometric durations from the transition matrix) with contiguous block bootstrap within
      each spell — no more month-by-month i.i.d. quadrant flipping. New headline scenario
      `current_conditions` starts from today's actual quadrant and evolves by historical
      transition probabilities; the weighted scenarios (historical/even/custom via
      `simulate_scenario(weights)`) still converge to target long-run month shares (q ∝
      w·(1−p_stay)), so the future optimizer API is unchanged.
- [x] **Statistics-vs-ML line decided** and recorded in `info/CLAUDE.md` caveat #11: counting/
      normalizing/resampling history (z-scores, transition counts, bootstrap, momentum
      extrapolation) = fine under FRED ToS; anything fitted/trained to predict (regression
      forecasts, EM-fitted HMMs, ML) = Phase 4, non-FRED data. v2 stays entirely on the allowed
      side.

### Next: 2–3 month probabilistic quadrant outlook (backtest evidence gathered 2026-07)

A walk-forward backtest (~230 eval months, warmup 120) of the dashboard arrow vs alternatives was
run 2026-07 to decide how to upgrade "a simple arrow" into a proper short-horizon cone. Findings
worth keeping (statistics only, no ML — all within the caveat-#11 line):

- **Arrow (momentum extrapolation):** best *hard* single-quadrant call at every horizon — h=3 hit
  rate 57.4% vs 51.7% persistence — and the best transition-catcher (21.6% of actual quadrant
  flips at h=3 vs 0% for persistence). BUT in score space it overshoots: extrapolated dot position
  is *worse* than assuming no movement (MAE 1.50 vs 1.10 at h=3). Direction useful, length
  exaggerated.
- **Markov h-step (P^h from the transition matrix):** argmax collapses to persistence, but as a
  *probability distribution* it is the best-calibrated forecast at every horizon (Brier 0.168 at
  h=3 vs 0.241 persistence / 0.213 arrow). This is the natural "cone" — and the matrix is already
  computed and baked into the dashboard.
- **Analog (k=20 nearest past months by scores+velocities):** competitive Brier (0.175 at h=3),
  catches 15–20% of transitions, and doubles as narrative ("today most resembles …, here's what
  followed"). Slight full-sample standardization leakage in the quick test — redo clean if built.

- [x] Dashboard: **3-month probabilistic outlook** — DONE 2026-07. `quadrant_outlook()` (soft
      vector × P^3) in the report; outlook pills in the verdict card AND a per-selected-month
      outlook line on the quadrant chart (recomputed client-side from the baked matrix, so it
      follows the date picker).
- [x] Quadrant chart **empirical cone** — DONE 2026-07. 25–75 + 10–90 percentile boxes of
      realized (Δg, Δi) over the next 3 months across all months sharing the selected month's
      state, plus the individual re-anchored outcome dots colored by landing quadrant. Arrow
      kept at FULL length but relabeled direction-only: the damping sweep showed λ=1 gives the
      best hard quadrant call while ANY λ>0 worsens position MAE — so no damping constant,
      direction from the arrow, range from the cone.
- [x] **"Analog months" panel** — DONE 2026-07. k=20 nearest past months (scores + 6m
      velocities, z-scaled, ±6m exclusion), outcome summary pills, top-10 table, optional
      top-5 path overlay on the chart. Follows the date picker.
- ML verdict (recorded): not warranted at this horizon — ~350 monthly obs and ~50–80 observed
  transitions is too small for ML to beat counting; more/longer/higher-frequency data (non-FRED,
  Phase 4) would matter more than model class.

**Round 2 (2026-07): "should the prediction condition on more information?" — tested.** User
hypothesis: analogs/outlook should use trajectory, the underlying macro indicators, and index
trends, not just the quadrant summary. Walk-forward results (h=3, k=20, ~230 eval months):

- [x] **Trajectory: confirmed, shipped.** Analog features already included 6m velocities
      (entering ≠ exiting); adding 3m *accelerations* lifted transition-catching 16.2%→24.3% at
      no calibration cost → now in the dashboard (6-dim feature space).
- **Raw indicator trends in the k-NN: tested, REJECTED.** Adding the 9 component z-trends made
  everything worse (hit 42.2%→39.1%, Brier 0.177→0.192); + index features worse still. The
  composite scores already summarize the indicators — re-adding them as raw dimensions
  double-counts noise (curse of dimensionality at ~350 candidate months). More conditioning
  variables ≠ more signal at this sample size; more DATA would be the lever (Phase 4).
- **Border-distance conditioning: real signal, marginal gain, not implemented.** P(quadrant
  change within 3m) is 64% for months nearest the border vs 32–40% deepest in the quadrant —
  the quadrant label alone is indeed "vague." But an 8-state (quadrant × near/deep) transition
  matrix only improves Brier 0.168→0.161, because the soft-start vector already encodes border
  proximity. Left out for KISS; revisit if a use-case needs the extra ~4% calibration.
- **Markov outlook calibration (answer to "is it precise?"):** predicted 10–20% → realized
  10.6%; 20–30% → 20.7%; 30–40% → 46%; 50–70% → 71%. Mid-range is well calibrated; when it
  leans hard it is *under*confident (errs safe). Hard 3-month calls are right ~52–57% of the
  time vs 25% chance — probabilities honest, certainty impossible at this sample.

## Data sources

- [x] **Index registry** (`data/index_registry.csv`) — explicit manifest of tracked indexes;
      ingest is registry-driven so adding an MSCI index = add a row + drop the file(s), no code
      edit. See `info/CLAUDE.md` §5.
- [ ] **API data source** — add a `source=api` branch in `ingest/returns.py` so indexes can be
      pulled from an API (e.g. a ticker feed) instead of local MSCI files, using the same registry
      contract. Keep the index set small/curated (KISS — the main indexes, not 200 niche ones).
- [ ] Optionally move the 2 hardcoded AC Asia ex Japan web-image weights out of
      `ingest/asia_images.py` into a small CSV, so *all* weight data is file-driven.

## Live data (vision.md Phase 1 remainder)

- [ ] Source a reliable, affordable **live index/holdings data feed** (open question — no
      provider chosen yet). Would plug in via the `api` source above.
- [ ] Compare each index's **current** behaviour vs. its own history (needs the live feed above).

## Tracker & product (vision.md Phase 5)

- [ ] Day-to-day portfolio tracking (positions, cost basis, live valuation).
- [ ] Rebalancing alerts triggered by regime change.
- [ ] Reporting (periodic summaries, exportable).
- [ ] Harden toward a real product: multi-portfolio support, persistence layer, auth, packaging.

## Open questions (from vision.md — resolve as we go, not blocking)

- Additional macro data APIs beyond FRED (OECD, World Bank, ECB, BLS?).
- How to define & detect the macro regime **in real time**, not just label history after the fact.
- Optimization backend choice (`scipy` / `cvxpy` / `Riskfolio-Lib`) — also listed above since it
  directly blocks the optimizer task.

## Deferred / explicitly out of scope for now

- **ML / reinforcement learning allocation** (vision.md Phase 4). Blocked in part by FRED's terms
  of use, which prohibit training ML/AI systems on FRED data — if this is ever built, its macro
  features must come from a different source than FRED (see `info/CLAUDE.md` caveat #11).
