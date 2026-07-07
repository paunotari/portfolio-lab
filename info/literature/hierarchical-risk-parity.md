# Hierarchical Risk Parity — López de Prado (2016), implementation-grade

Deep dive behind [literature.md](../literature.md) §1. Candidate default engine for our
optimizer. ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678), *JPM* 42(4) 2016,
"Building Diversified Portfolios that Outperform Out-of-Sample"; developed at Guggenheim.)

## 1. Principle

Quadratic optimizers fail because they invert Σ (see
[mean-variance-and-estimation-error.md](mean-variance-and-estimation-error.md)) and because they
treat all assets as potential substitutes for each other (a fully connected graph — one bad
correlation estimate anywhere can flip weights everywhere). HRP replaces inversion with
**hierarchy**: cluster assets by correlation similarity, then split capital top-down through the
tree, so estimation error stays *local* to its cluster. No matrix inversion anywhere; works even
when Σ is singular.

## 2. The algorithm (exact, 3 stages)

Inputs: correlation matrix ρ (n×n), covariance Σ. Ours: 21 sleeves, optionally on the shrunk Σ
([ledoit-wolf-shrinkage.md](ledoit-wolf-shrinkage.md)) — document if so.

**Stage 1 — Tree clustering.**

```
distance:        d_ij = √( (1 − ρ_ij) / 2 )            ∈ [0,1]
```

Run agglomerative hierarchical clustering on d (paper uses **single linkage**;
scipy: `scipy.cluster.hierarchy.linkage(squareform(d), method='single')`).

**Stage 2 — Quasi-diagonalization.** Reorder the assets in dendrogram-leaf order
(`scipy...leaves_list`). Similar assets become adjacent; big correlations concentrate near the
diagonal. No math, just a permutation.

**Stage 3 — Recursive bisection.** Start with the full ordered list, weight 1 on all.

```
for each list L (recursively split into contiguous halves L1, L2):
    for each half: cluster variance with inverse-variance weights
        w̃_i  = (1/Σ_c[i,i]) / Σ_j (1/Σ_c[j,j])        (within the half, Σ_c = its sub-covariance)
        V_c  = w̃ᵀ Σ_c w̃
    split factor:   α = 1 − V_{L1} / (V_{L1} + V_{L2})
    w_i ← w_i · α        for i ∈ L1
    w_i ← w_i · (1−α)    for i ∈ L2
recurse until single assets remain
```

Weights are automatically long-only and sum to 1. Complexity O(n²); deterministic given the data.
Whole thing is ~60 lines of numpy/scipy.

## 3. Evidence and adoption

Monte Carlo in the paper: HRP delivers **lower out-of-sample variance than CLA (min-variance)** —
even though min-var is CLA's own objective — and than naive inverse-vol risk parity. Adoption is
young but real (standard chapter in the ML-for-asset-management canon; implementations in every
quant library, e.g. PyPortfolioOpt, Riskfolio-Lib). It is not (yet) a Bridgewater-scale
production standard — treat it as "best-of-breed robust engine," not "industry default."

## 4. Why it fits us unusually well

- **The tree is the explanation.** For 21 region/factor sleeves the dendrogram should rediscover
  our structure (regions cluster, factors cluster within) — plotting it is a free Tier-2
  visualization and a sanity check of the whole data pipeline. "Your money splits where
  correlations split" is a sentence a user can trust.
- No μ̂ anywhere; no inversion; stable under our T/n.
- Deterministic and fast enough to re-run per regime (per-quadrant HRP on state-conditioned
  months — a KISS regime-aware variant worth testing against the BL route).

## 5. Pitfalls

- **Single linkage chains** (clusters connected by one lucky pair). Alternatives: average/ward
  linkage — literature (Raffinot's HERC etc.) often prefers them. Decide by walk-forward test,
  report choice in methodology.
- Tree instability near ties: small data changes can flip merge order → weight jumps between
  rebalances. Mitigation: shrunk Σ input + linkage choice; monitor turnover in backtest.
- Ignores expected returns *entirely* — that's the point, but it means return views need the
  BL layer on top, not HRP itself.
- Bisection splits the *ordered list* in half, not the dendrogram's own clusters (paper's
  simplification); HERC variants split at the tree's actual branches. Test both; keep simpler
  unless clearly worse.

## 6. Unit tests when building

- 2 assets: HRP = inverse-variance split (α from the formula, verify by hand).
- Block-diagonal toy Σ (two independent clusters): weights split ~by inverse cluster variance,
  and the dendrogram separates the blocks.
- Permutation invariance: shuffling input asset order must not change final weights.

**Primary sources:** [López de Prado, SSRN 2708678](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678) /
*JPM* 42(4) 2016 · López de Prado, *Advances in Financial Machine Learning* (2018), ch. 16 ·
Raffinot 2017 (HERC).
