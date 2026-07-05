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
stats). **Not yet done:** wiring any of this into the dashboard (still CLI/report-only — see the
Tier-1 essentials section above; this is real Tier-2 depth waiting on a display layer, not
forgotten).

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

User's own framing after reviewing this: the classifier and the simulation both currently use a
narrow, mechanical rule, and there's probably real signal being left on the table before this is
good enough to lean on. Needs a proper review/redesign pass, not just tweaking constants.

- [ ] **4-quadrant classifier is currently only 2 inputs** (`indpro_yoy` growth trend ×
      `core_pce_yoy` inflation trend, both hard-thresholded into just "up/down"). Worth
      reconsidering:
  - Bring in more of the 15 macro indicators we already have (yield curve slope, credit spreads,
    unemployment trend, VIX, breakeven inflation, PPI) rather than 2 in isolation — a composite
    growth/inflation signal, not a single proxy series each.
  - Hard up/down threshold throws away magnitude and creates artificial certainty right at the
    boundary — a continuous/graded signal (or a soft probability of each quadrant, e.g. "70%
    Reflation / 30% Goldilocks") would be more honest than a forced hard bucket.
  - No persistence/transition modeling at all — real macro regimes last months to years, but
    nothing here captures how likely a transition is from one quadrant to another. A historical
    state-transition (Markov) matrix is the natural, still-non-ML way to add this.
- [ ] **Monte Carlo simulation draws each future month independently (i.i.d.)** — it has zero
      memory of the previous simulated month's state, so a simulated path can flip quadrant every
      single month, which doesn't look like real macro history (regimes persist). Candidates:
  - Use a historical transition matrix (see above) instead of a single static probability vector,
    so simulated sequences have realistic regime *duration*, not just correct long-run frequency.
  - Consider block-bootstrap (multi-month chunks) instead of single-month draws within a state, to
    preserve some within-regime serial correlation/momentum.
  - Consider conditioning the *starting* quadrant probabilities on where we currently are/where
    trend is heading (from `current_state()`) rather than always starting from the unconditional
    scenario weights — a simulation run today should plausibly reflect that we're already inside
    a state, not agnostic to it.
- [ ] Before redesigning, explicitly decide: how much of this can use richer statistics/Markov
      models (still not "AI" under FRED's terms) vs. where the line to Phase 4 ML actually is —
      revisit `info/CLAUDE.md` caveat #11 when scoping this so we don't accidentally cross it.

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
