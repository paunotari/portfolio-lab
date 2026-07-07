# Covariance shrinkage — Ledoit & Wolf (2003/2004), implementation-grade

Deep dive behind [literature.md](../literature.md) §1. The one estimator we adopt outright.
Two variants below; both are closed-form (no tuning, no optimization, no fitting loop — cleanly
on the allowed side of the FRED-ToS line, and it consumes MSCI returns anyway).

## 1. Principle

The sample covariance S is unbiased but *high-variance* entry-by-entry; a structured target F is
biased but low-variance. The optimal (squared-Frobenius-loss) combination is a convex blend:

```
Σ̂_shrunk = δ*·F + (1 − δ*)·S,     δ* ∈ [0, 1]
```

δ* has a closed form from the bias-variance trade-off. Extreme entries of S (the ones MVO loves —
see [mean-variance-and-estimation-error.md](mean-variance-and-estimation-error.md)) get pulled
toward the structure exactly in proportion to how noisy they are.

## 2. Variant A — scaled-identity target (Ledoit & Wolf 2004, *J. Multivariate Analysis*)

Simplest, fully exact, what `sklearn.covariance.LedoitWolf` implements. Data matrix X (T×n),
demeaned; S = XᵀX/T.

```
m  = tr(S)/n                              # grand mean of eigenvalues
d² = ‖S − m·I‖²_F / n                     # dispersion of S around target
b̄² = (1/T²) Σ_t ‖x_t x_tᵀ − S‖²_F / n     # estimation noise in S
b² = min(b̄², d²)
δ* = b²/d²
Σ̂ = δ*·m·I + (1 − δ*)·S
```

(‖·‖²_F = sum of squared entries.) ~10 lines of numpy. Guaranteed well-conditioned, invertible.

## 3. Variant B — constant-correlation target ("Honey, I Shrunk the Sample Covariance Matrix", *JPM* 2004) — the finance-tuned one

Better target for asset returns: keep each asset's own variance, set every correlation to the
average correlation r̄.

```
target:   f_ii = s_ii ;   f_ij = r̄·√(s_ii·s_jj),   r̄ = mean of all sample correlations (i≠j)
```

Optimal intensity `δ* = max(0, min(1, κ̂/T))` with `κ̂ = (π̂ − ρ̂)/γ̂`:

```
π̂  = Σ_ij (1/T) Σ_t (x_it·x_jt − s_ij)²                       # noise in S entries
γ̂  = Σ_ij (f_ij − s_ij)²                                      # target misspecification
ρ̂  = Σ_i π̂_ii                                                 # diagonal: cov(S,F) = var(s_ii)
     + Σ_{i≠j} (r̄/2)·( √(s_jj/s_ii)·θ̂_ii,ij + √(s_ii/s_jj)·θ̂_jj,ij )
       where θ̂_ii,ij = (1/T) Σ_t (x_it² − s_ii)(x_it·x_jt − s_ij)
```

~30 lines of numpy. Cross-check against the faithful reference implementation
([WLM1ke/LedoitWolf](https://github.com/WLM1ke/LedoitWolf/blob/master/ledoit_wolf.py)) and the
authors' own [covShrinkage MATLAB pack](https://www.mathworks.com/matlabcentral/fileexchange/106240-covshrinkage).

## 4. Which one for us

**Variant B (constant-correlation)** as the default — its target matches equity-index reality
(everything positively correlated at similar strength; exactly what our 21×21 matrix looks like),
and the paper's empirical result (lower OOS tracking error, higher information ratio without
touching any other step) was demonstrated on equity portfolios. Variant A is the fallback / test
oracle (compare both; they should agree on the broad structure).

With **n=21, T=330** (T/n ≈ 16) our S is not catastrophically noisy — expect a moderate δ*
(paper's typical range 0.1–0.5). If δ* comes out near 0, that's the estimator telling us S is
fine; near 1 means the sample matrix is untrustworthy. Either way, *report δ** in the optimizer
output — it's one number and it's free transparency about input quality.

## 5. Pitfalls

- Demean X first (returns, not levels — and subtract the sample mean per series).
- π̂, ρ̂, γ̂ are sums over the **full** matrix including diagonal for π̂/γ̂; follow the reference
  implementation on indexing before trusting a hand-rolled version — this is the classic
  off-by-a-term bug.
- Shrinkage fixes Σ, **not μ** — it makes min-var/ERC/HRP inputs sane; it does not license
  return-maximization (Chopra-Ziemba hierarchy still applies).
- Don't shrink twice: HRP consumes the correlation matrix — if we feed it a shrunk Σ, note it in
  the methodology (fine, but document).

**Primary sources:** [Ledoit & Wolf, *JPM* 30(4) 2004 — "Honey…"](http://www.ledoit.net/honey.pdf)
· Ledoit & Wolf, *JMVA* 88 2004 — "A well-conditioned estimator…" ·
[reference implementation](https://github.com/WLM1ke/LedoitWolf/blob/master/ledoit_wolf.py) ·
[sklearn LedoitWolf](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html).
