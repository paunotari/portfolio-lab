# TODO — task backlog

Actionable backlog for `portfolio_lab`. `vision.md` is the narrative roadmap (why, phases);
this file is the concrete, checkable list derived from it plus ad-hoc engineering tasks. When a
phase in `vision.md` completes, update its status there too — this file doesn't replace it.

Check items off as completed. Add new ones as they come up; keep entries short and specific.

---

## Now / quick wins

_(both done — see Portfolio optimization below for what builds on them next)_

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

- [ ] **Per-regime macro correlations** — extend `analytics/macro_link.py` to compute one
      index↔macro correlation matrix per regime (currently only full-sample). Cheap, additive.
- [ ] **4-quadrant macro-state classification** (inflationary / deflationary / growth /
      stagnation) with per-state historical performance. This is the direct input the
      regime-targeted optimizer needs — do this before or alongside that optimizer work.
- [ ] **Scenario simulation**: simulate future index/factor behaviour conditioned on a chosen
      macro characteristic or state, building on the correlations already computed.

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
