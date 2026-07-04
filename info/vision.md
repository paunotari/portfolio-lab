# Vision — a macro-regime-aware portfolio platform for individuals

> Status: north-star document. The current codebase (see [CLAUDE.md](CLAUDE.md)) is the empirical
> foundation — step 1 of this vision. This file records where we are going so it can be amplified
> and checked over time. It is intentionally broader than what is built today.

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

## Roadmap (rough, to be refined)

**Phase 0 — Foundation (DONE / in progress)**
- Reproducible ingest of MSCI factor/region data (returns + factsheet weights). ✅
- Analytics engine: performance, factor-vs-reference, 10 macro regimes, correlations. ✅
- Look-through diversification (sector / country / single-stock concentration). ✅
- Self-contained dashboard. ✅

**Phase 1 — Live data & macro**
- Connect to **FRED** and other macro sources for live indicators (inflation, rates, growth,
  unemployment, yield curve, PMI…). *Open question: best free/affordable APIs.*
- Live index / holdings data feed. *Open question: where to source reliable live index data.*
- Compare each index's **current** behaviour vs its own history.

**Phase 2 — Macro correlation & simulation**
- Estimate correlations of individual indices **and factors** to the **most important macro
  indicators** over history — the core input for regime-conditional forecasting.
- Simulate future behaviour/returns conditioned on macro characteristics (scenario engine).

**Phase 3 — Optimization**
- Deterministic optimizers: max-Sharpe, min-vol, min-drawdown, target-return, and **multi-objective
  blends**, with constraints on sector/country/factor exposure and look-through concentration.
- Regime-targeted allocation (the signature feature above).

**Phase 4 — Intelligence**
- Probabilistic models / reinforcement learning to adapt allocation across regimes instead of
  relying on historical averages. This is the genuinely novel, under-served niche.

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
