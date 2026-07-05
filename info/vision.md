# Vision — a macro-regime-aware portfolio platform for individuals

> Status: north-star document. The current codebase (see [CLAUDE.md](CLAUDE.md)) is the empirical
> foundation — step 1 of this vision. This file records where we are going so it can be amplified
> and checked over time. It is intentionally broader than what is built today.
> For the concrete, checkable task list, see **[TODO.md](TODO.md)**.

## The problem

The software that does what I want **already exists — but only in fragments, and mostly for
institutions.** No single, simple tool for an individual investor combines all of it:

| Tool | Strong at | Missing |
|---|---|---|
| Portfolio Visualizer | backtesting, optimization (Markowitz, max-Sharpe, min-vol), factor analysis, Monte Carlo | weak macro analysis |
| Portfolio Optimizer | mathematical optimization, constraints by sector/region/factor/risk | no macro / no tracking |
| Koyfin | macro data, valuation, factors, economic indicators | does not optimize portfolios |
| Morningstar Direct | overlap, geographic/sector/style/factor exposure, concentration | institutional, no macro-regime optimization |
| BlackRock Aladdin | macro scenarios, stress tests, risk, correlations, optimization | institutional, extremely expensive |

**The gap:** an integrated, affordable platform for a *particular* that ties portfolio
construction to **macroeconomics and regime analysis**, not just historical averages.

## What we are building

A program / app / interface that:

1. **Plans a portfolio** using not only the usual data (returns, vol, Sharpe, sector/country
   weights) but also **macro-indicator correlations and macro-regime behaviour** — including how
   each holding behaved in past crises and regimes (inflationary, deflationary, expansion,
   high-rates, etc.). *(Regime engine + look-through already exist today.)*
2. **Optimizes** the portfolio for user-specified objectives — diversification, volatility,
   return, drawdown, Sharpe, or a **combination** — via deterministic models and, later,
   probabilistic / reinforcement-learning approaches that adapt allocation to macro regimes.
3. **Tracks** day-to-day investments: not just math/stats/reports, but a live portfolio tracker —
   bringing together capabilities that today are scattered across several products, plus the
   predictive models normally locked inside expensive institutional software.

Concretely, the platform should:
- **Detect overlaps** automatically between ETFs and individual stocks.
- Compute **true exposure** by country, sector, currency, and factor (value / quality / momentum / size…).
- **Account for the macro regime** (high inflation, recession, expansion, high rates…).
- **Simulate historical and hypothetical scenarios.**
- **Propose rebalancing** when the environment changes.

## Signature feature — regime-targeted allocation

Let the user express *how they want to behave across macro states* rather than only chasing average
return. For the four macro quadrants (e.g. **inflationary / deflationary / growth / stagnation**):

- pick a **% of diversification** target, or
- set a desired **performance profile per scenario** ("do well in X, accept less in Y"), or
- split it evenly (25/25/25/25), or
- **weight by each regime's historical frequency** so coverage matches how often each regime
  actually occurs, or
- optimize for other characteristics entirely.

The optimizer then finds an allocation whose *regime-conditional* behaviour matches that target —
using the per-regime returns and correlations the engine already computes.

## Product design principle — layered UI, essentials on top

**The problem this solves:** existing tools (Portfolio Visualizer, screeners) hand you a pile of
data and expect *you* to interpret it and pick the %. Most people — even people who understand
investing — don't know what to do with a correlation matrix or a factor-loading regression. The
platform should never force that. But it also shouldn't hide real analysis behind a dumbed-down
toy; the depth should still be there, just underneath.

**The rule: every module in the UI has exactly two tiers.**

- **Tier 1 (top, always visible, default view).** A small number of plain-language verdicts,
  reduced from the underlying analysis — not a chart to interpret, a sentence or a headline
  number to read. This tier is also, deliberately, **the same thing the optimizer scores on** —
  there's one set of "what matters" per index/factor, not a separate simplified display and a
  separate real calculation.
- **Tier 2 (below, collapsed/secondary — "basic advanced").** The existing real analysis —
  correlation matrices, regime tables, macro betas, rolling charts — for anyone who wants to
  click in and see the work. This is genuinely useful, informed-investor-level depth, but it
  stops there deliberately: **not** hedge-fund/quant-desk depth (no raw factor-regression
  loadings, VaR/CVaR, skew/kurtosis, optimizer solver internals, Greeks, Monte Carlo path dumps).
  Those stay internal to the engine — usable by the optimizer's math, never a primary or
  secondary UI surface. If a genuine power user wants that later, it's a CSV export, not a tab.

**Per module (Tier 1 → Tier 2, current build in parentheses):**

| Module | Tier 1 — essential verdict | Tier 2 — basic-advanced detail (already built) |
|---|---|---|
| Performance | 4 numbers (CAGR, vol, Sharpe, max DD) + one line: *"led 1998–2010, has lagged since ~2010"* | Date-range picker, rebased cumulative growth chart, full per-series table |
| Factor vs Reference / Regimes | One line per factor: *"Momentum has beaten its regional benchmark in ~56% of months, especially in [state]"* | Regime explorer, factor-excess heatmap, per-regime performance table |
| Correlation / Diversification | One "diversification benefit" verdict (*"reduces portfolio vol by X%"*) + concentration flags (*"pushes Info Tech to 62%"*) | Full correlation matrix, rolling correlation chart, sector/country/stock look-through bars |
| Macro | Plain-language regime fingerprint per index/factor + a "current regime + trend" read (see TODO.md) | Index↔macro correlation heatmap, per-indicator time series with regime shading |
| Optimizer (future) | The recommended allocation + its "why," as the same essential bullets per holding | Exposed knobs for a curious user (max sector %, per-objective priority weighting) — still not solver internals |

This is a **display principle for later UI work**, not a rebuild of what exists — today's
dashboard tabs already are Tier 2. What's missing is the Tier-1 layer on top of each, and the
one-sentence "why" generation that turns the quant work into something a normal investor reads
in five seconds before deciding to trust the optimizer's number.

## Roadmap (rough, to be refined)

**Phase 0 — Foundation (DONE / in progress)**
- Reproducible ingest of MSCI factor/region data (returns + factsheet weights). ✅
- Analytics engine: performance, factor-vs-reference, 10 macro regimes, correlations. ✅
- Look-through diversification (sector / country / single-stock concentration). ✅
- Self-contained dashboard. ✅

**Phase 1 — Live data & macro (macro part DONE)**
- ✅ **FRED** ingest: 15 historical indicators (inflation, rates, curve, growth, unemployment,
  credit spread, VIX, USD, oil, PPI, breakeven inflation expectations, NBER recession flag),
  month-end aligned, API-key or keyless. (`ingest/macro.py`)
- Live index / holdings data feed. *Open question: where to source reliable live index data.*
- Compare each index's **current** behaviour vs its own history.

**Phase 2 — Macro correlation & simulation (DONE)**
- ✅ Correlations of individual indices **and factors** to the macro indicators over history —
  contemporaneous + lead/lag, level + change bases, with betas, **plus per-named-regime
  correlation matrices** (`analytics/macro_link.py`, full-sample part visualized in the
  dashboard's Macro tab).
- ✅ **4-quadrant macro-state classification** (growth × inflation trend → Goldilocks / Reflation
  / Deflationary bust / Stagflation), with per-state performance by region+factor and
  factor-level attribution (does Momentum/Value/Quality consistently beat its reference within a
  given state) — confirms e.g. Value leads in Deflationary bust, Momentum lags in Stagflation.
  Plus a current-regime + trend read. (`analytics/macro_state.py`, CLI/report only so far.)
- ✅ **Scenario simulation**: bootstrap Monte Carlo conditioned on macro-quadrant probability
  weights, resampling whole historical months to preserve real cross-series correlation.
  Explicitly a stated-assumption exercise ("future resembles reshuffled history"), not a
  forecast. (`analytics/scenario.py`, CLI/report only so far.)

**Phase 3 — Optimization**
- Deterministic optimizers: max-Sharpe, min-vol, min-drawdown, target-return, and **multi-objective
  blends**, with constraints on sector/country/factor exposure and look-through concentration.
- Regime-targeted allocation (the signature feature above).

**Phase 4 — Intelligence**
- Probabilistic models / reinforcement learning to adapt allocation across regimes instead of
  relying on historical averages. This is the genuinely novel, under-served niche.
- ⚠️ **Constraint:** FRED's terms of use prohibit using FRED data to train ML/AI systems. If this
  phase is built, macro features must come from a different source (OECD, World Bank, ECB, BLS…)
  — FRED stays limited to the statistical/deterministic layers (Phases 0–3).

**Phase 5 — Tracker & product**
- Day-to-day portfolio tracking, rebalancing alerts on regime change, reporting.
- Harden toward a real product (multi-portfolio, persistence, auth, packaging).

## Open questions to resolve as we go
- Best macro data APIs (FRED confirmed; what else — OECD, World Bank, ECB, BLS?).
- Reliable, affordable **live index/holdings** data source.
- How to define & detect the macro regime *in real time* (not just label history after the fact).
- Optimization backend (cvxpy / scipy / Riskfolio-Lib) and how to encode regime-conditional targets.

## Guiding principles
- **Integrated and simple** for an individual — the whole point is not needing five tools.
- **Structure over curve-fitting** — allocations driven by macro/structural logic, validated
  against (not dictated by) the recent past.
- **Reproducible and transparent** — every number regenerable from `scripts/run_pipeline.py`;
  assumptions written down, not buried.
