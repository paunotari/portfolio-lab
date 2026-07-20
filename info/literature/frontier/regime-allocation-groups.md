# The regime-allocation frontier — who is working our problem right now (2023-2026)

*Working papers from active groups doing regime-conditioned allocation — our nearest
neighbors. Purpose: positioning for the paper's related-work section + techniques worth
borrowing. Found 2026-07 via SSRN/arXiv sweeps.*

## 1. Bouyé & Teiletche — "Regime-Based Strategic Asset Allocation" (SSRN 4801115, 2024)

The closest neighbor with the best pedigree: Teiletche co-authored our ERC canon paper
(Maillard-Roncalli-Teiletche 2010). Strategic (not tactical) allocation built on macro
regimes, connecting mean-variance and risk-based investing under regime conditioning.
**⇒ for us:** the natural positioning anchor — cite it as the institutional-scale sibling;
our differentiators are (a) the era-agreement-gated long-history estimator for the regime
inputs, (b) the pre-registered virgin-universe validation, and (c) the retail data scale
framing. [SSRN 4801115](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4801115)

## 2. "Tactical Asset Allocation with Macroeconomic Regime Detection" (arXiv 2503.11499; Quantitative Finance 2026)

k-means/fuzzy clustering on FRED-MD (127 macro variables) → 6 data-driven regimes; ridge /
Black-Litterman allocation conditioned on regime probabilities; walk-forward with 48m
windows, 2000-2023.

Read in full (2026-07). What's genuinely useful to us:
- **Probabilistic regime conditioning**: they weight by regime membership probabilities
  rather than the hard label — we already do this in the Markov outlook and soft
  probabilities, but OUR per-quadrant means are hard-label pooled. A soft-weighted μ_q
  variant is a legitimate refinement candidate (would need a fresh confirmatory universe
  per our M16 discipline).
- **Nemenyi rank test** for MULTIPLE-comparison significance across contestants —
  complements our pairwise Ledoit-Wolf (answers "is there any significant ordering in the
  whole table?"). Cheap to add next to the LW table.
- **Random-regime placebo control**: they benchmark against allocations driven by RANDOM
  regime labels — a beautiful falsification test we could run in one evening (if our
  maximin beats its random-label twin, the regime signal itself is doing work; if not, the
  benefit is just the asset-class menu).
- Their honest finding — "regime information primarily enhances return generation rather
  than downside risk management" — is the OPPOSITE of our all-weather result (our regime
  layer buys a floor, not return). Contrast explicitly in the discussion section.
- Their regimes are fitted clusters (data-driven, harder to interpret, FRED-ToS-relevant
  for us); ours are observable quadrant rules. State the trade-off.
[arXiv 2503.11499](https://arxiv.org/html/2503.11499v1)

## 3. Shu et al. — "Dynamic Asset Allocation with Asset-Specific Regime Forecasts" (arXiv 2406.09578, 2024)

Per-ASSET regime models (each asset gets its own bull/bear state forecast) feeding
mean-variance/min-var/naive portfolios; reports outperformance across models.
**⇒ for us:** the per-asset-regime idea is the granular extreme of our per-quadrant means;
worth citing as the other end of the spectrum (we deliberately share ONE macro state across
assets — fewer parameters at our T). [arXiv 2406.09578](https://arxiv.org/pdf/2406.09578)

## 4. Chan, Fan, Sawal & Viville — "Conditional Portfolio Optimization" (SSRN 4383184, 2023)

Practitioner ML: condition the whole optimization on a large feature set of market/macro
state ("adapt capital allocations to market regimes" via machine learning).
**⇒ for us:** the ML mirror image of our deterministic design — cite as what we deliberately
do NOT do at this data scale (and cannot, under the FRED-ToS line, caveat #11); our
anti-overfitting apparatus (PBO, pre-registration) is the argument for the deterministic
side. [SSRN 4383184](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4383184)

## Follow-up tests these papers motivate (recorded in TODO, paper track)

1. **Random-regime placebo** for the maximin family (from #2) — cheapest new falsification
   we don't have.
2. **Nemenyi multiple-comparison test** next to the LW pairwise table (from #2).
3. Yuan-Zhou combination contestant (see `beating-1N-yuan-zhou.md`) — the priority one.
