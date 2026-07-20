# Sharpe-ratio inference — Ledoit & Wolf (2008) + deflated Sharpe, implementation-grade

The paper-track gate (TODO "Paper track", item 1): every ranking claim in the walk-forward
table is a POINT ESTIMATE. This note carries everything needed to attach honest p-values to
Sharpe differences and a multiplicity-aware probability to any single Sharpe — codeable
without fetching the papers. Implemented in `src/portfolio_lab/portfolio/inference.py`.

## 1. Why the naive tests fail

- **t-test on mean returns** ignores that Sharpe has estimated vol in the denominator.
- **Jobson & Korkie (1981, JF; Memmel 2003 correction)** is the classic closed-form z-test for
  ΔSharpe of two correlated series — but it assumes **i.i.d. normal** returns. Monthly asset
  returns have autocorrelation (vol-targeted series doubly so) and heavy tails; JK over-rejects.
  Use it only as a cross-check.
- **Ledoit & Wolf (2008), "Robust performance hypothesis testing with the Sharpe ratio",
  *Journal of Empirical Finance* 15(5)**: delta-method standard error that is
  heteroskedasticity-and-autocorrelation-consistent (HAC), plus a **studentized circular block
  bootstrap** p-value that stays honest under heavy tails. This is the referee-standard test.

## 2. The Ledoit-Wolf test, exactly

Two paired return series x_t, y_t, t = 1..T (same months — inner-join first). Let
μ₁ = E[x], μ₂ = E[y], γ₁ = E[x²], γ₂ = E[y²]. Then σᵢ² = γᵢ − μᵢ² and

    Δ = SR₁ − SR₂ = μ₁/σ₁ − μ₂/σ₂        (per-period Sharpe; annualizing scales Δ by √12
                                          and the s.e. identically ⇒ p-values are unchanged)

**Delta method.** With v = (μ₁, μ₂, γ₁, γ₂) and f(v) = Δ, the gradient is

    ∇f = ( γ₁/σ₁³,  −γ₂/σ₂³,  −μ₁/(2σ₁³),  μ₂/(2σ₂³) )

(σᵢ³ = (γᵢ−μᵢ²)^{3/2}). Define the influence vector time series (T×4)

    V_t = ( x_t−μ̂₁,  y_t−μ̂₂,  x_t²−γ̂₁,  y_t²−γ̂₂ )

and Ψ̂ = HAC long-run covariance of V_t (kernel-weighted autocovariances):

    Ψ̂ = Γ̂₀ + Σ_{j=1}^{m} k(j/m) (Γ̂ⱼ + Γ̂ⱼᵀ),   Γ̂ⱼ = (1/T) Σ_t V_t V_{t−j}ᵀ

Parzen kernel k(z) = 1−6z²+6z³ for z ≤ ½, 2(1−z)³ for ½ < z ≤ 1. (LW use Parzen with
Andrews-Monahan prewhitening; we skip prewhitening — a documented simplification, second-order
because the bootstrap p-value is primary.) Bandwidth: Newey-West rule m = ⌊4(T/100)^{2/9}⌋.

    s.e.(Δ̂) = √( ∇fᵀ Ψ̂ ∇f / T ),    d = Δ̂ / s.e.,    p_HAC = 2Φ(−|d|)

**Studentized circular block bootstrap (the primary p-value).** Resample TIME INDICES in
blocks of length b, wrapping circularly, always applying the same indices to both series
(preserves cross-correlation). For each of B samples:

1. draw ⌈T/b⌉ uniform block starts, concatenate, trim to T;
2. compute Δ̂* and its own s.e.* — in the bootstrap world Ψ̂* uses the sample's natural
   block structure: with ζ_j = (1/√b) Σ_{t∈block j} V*_t (V* centered at the bootstrap
   sample's own moments), Ψ̂* = (1/ℓ) Σ_j ζ_j ζ_jᵀ over the ℓ = ⌈T/b⌉ blocks;
3. studentize against the ORIGINAL estimate:  d* = (Δ̂* − Δ̂) / s.e.*

    p_boot = ( #{ |d*| ≥ |d| } + 1 ) / ( B + 1 )

Block length: LW propose a calibration algorithm; the accepted practical default is
b ≈ T^{1/3} (≈ 6 for our ~210 OOS months). B = 4999. Both in `config.py`
(`OPTIMIZER_INFER_*`); a serious sensitivity pass varies b ∈ {3, 6, 10} (paper-track grid).

## 3. Deflated Sharpe — Bailey & López de Prado (2014, *JPM*)

A single portfolio's Sharpe must also survive **multiplicity**: we fielded N contestants and
looked at the best ones. The Probabilistic Sharpe Ratio of monthly (non-annualized) ŜR over
a benchmark SR₀, with skewness γ₃ and (non-excess) kurtosis γ₄ of the returns:

    PSR(SR₀) = Φ( (ŜR − SR₀) √(T−1) / √( 1 − γ₃·ŜR + ((γ₄−1)/4)·ŜR² ) )

The **deflated** version replaces SR₀ with the expected maximum of N zero-skill trials:

    SR₀* = √Var({ŜR_n}) · ( (1−γ)·Φ⁻¹(1−1/N) + γ·Φ⁻¹(1−1/(N·e)) ),   γ ≈ 0.5772 (Euler)

where Var({ŜR_n}) is the variance of the N contestants' monthly Sharpe estimates.
**DSR = PSR(SR₀*)** = P(true SR > 0 | we cherry-picked the best of N). DSR ≥ 0.95 is the
usual bar. Our N = the walk-forward roster (honest count: every contestant we fielded).

## 4. Our adaptation (what `inference.py` runs)

- Input: the walk-forward's NET monthly OOS returns (`optimizer_walkforward_returns.csv`) —
  the same series every ranking claim is based on.
- Pairwise LW test of **every contestant vs 1/N** (the DeMiguel bar) and **vs Min-variance**
  (the incumbent OOS winner); inner-join months per pair (the all-weather's coverage differs
  by 1-2 months).
- DSR per contestant with N = roster size.
- Output: `optimizer_inference.csv` + a standing report section. Multiple-testing note: with
  ~10 contestants ~20 p-values, expect ~1 false positive at 5% — the section says so.

## 5. Pitfalls

1. **Never test annualized series against monthly formulas** — compute monthly, annualize only
   for display (√12 scales Δ and s.e. identically; d and p are invariant).
2. **Do not studentize with the original s.e. in the bootstrap** (that's the naive percentile-t
   error): d* must use the bootstrap sample's OWN block s.e., else coverage collapses.
3. **p_boot needs the +1/(B+1) finite-sample correction** — a p of exactly 0 is impossible.
4. **Degenerate windows**: constant series (σ→0) or near-duplicate contestants (Δ≈0, s.e.→0) —
   guard and return NaN rather than ±∞.
5. **PBO (Bailey, Borwein, López de Prado & Zhu 2017, CSCV) — implemented** (`pbo_cscv`):
   drop NaN rows, split the T×N net-return matrix into S=16 contiguous blocks; for each of
   C(16,8)=12,870 half-splits, select the in-sample-best trial and compute its OUT-sample
   relative rank ω ∈ [0,1]; **PBO = P(ω ≤ ½)** — the probability that the trial you would
   have picked in-sample is no better than the median out of sample. PBO ≈ 0.5 ⇒ picking
   the in-sample winner is a coin flip; low PBO ⇒ the ranking carries real OOS information.
   Sharpes per split come from cached per-block sums (exact, fast). Pitfall: contiguous
   blocks preserve within-block autocorrelation but half-splits still mix eras — read PBO
   next to the sub-period diagnostics (M12), not instead of them.
6. Failing to reject is NOT "the methods are equal" — with ~210 months the power is modest;
   report the confidence interval alongside (Δ̂ ± 1.96·s.e.).
