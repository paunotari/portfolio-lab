# Black-Litterman — the prior + views pattern, implementation-grade

Deep dive behind [literature.md](../literature.md) §1. Developed at Goldman Sachs 1990 (Black &
Litterman, *FAJ* 1992); the clearest exposition is [He & Litterman 1999](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=334304).
This is the pattern our regime tilt will use.

## 1. Principle

MVO's poison is the raw μ̂. BL replaces it in two moves:

1. **Start from a portfolio, not from return estimates.** Take a defensible neutral allocation
   `w_prior` and *reverse-optimize* the returns that would make it optimal — the "implied
   equilibrium returns" Π. If you say nothing else, the optimizer hands you back exactly
   `w_prior`. Garbage-in is structurally impossible at this stage.
2. **State views as a Bayesian update.** Each view is a statement about a portfolio of assets
   with an uncertainty; low-confidence views barely move the allocation, high-confidence views
   tilt it hard. Tilts are *proportional to conviction* — the property we want for sliders.

## 2. The math

Reverse optimization (from the utility form `max wᵀμ − (δ/2)wᵀΣw`):

```
Π = δ·Σ·w_prior            δ = risk-aversion scalar; classically (E[R_mkt] − r_f)/σ_mkt²
```

Views: k views on n assets.

```
P  (k×n): pick matrix — each row selects the portfolio the view is about
           (single asset: one-hot row; relative view: +1/−1 pair; group view: weights)
Q  (k×1): the view returns ("this portfolio will earn q per year")
Ω  (k×k): view uncertainty, usually diagonal.
           He-Litterman default: Ω_kk = (τ·P Σ Pᵀ)_kk / c_k, with c_k = confidence in view k
```

Posterior (the master formula):

```
μ_BL = [ (τΣ)⁻¹ + PᵀΩ⁻¹P ]⁻¹ · [ (τΣ)⁻¹·Π + PᵀΩ⁻¹·Q ]
M    = [ (τΣ)⁻¹ + PᵀΩ⁻¹P ]⁻¹          (uncertainty of the posterior mean)
```

Feed `μ_BL` (and Σ, or Σ+M for the purist predictive covariance) to the constrained optimizer.
τ scales prior looseness; convention: small (0.01–0.05) or 1/T. With no views (k=0), μ_BL = Π and
the output is w_prior — the safety property, and the unit test.

## 3. Production record

Run at Goldman since ~1990 ([their own history page](https://www.goldmansachs.com/our-firm/history/moments/1990-black-litterman-model));
the standard SAA anchor at large allocators (sovereign funds, endowments). It won because it
solved the *workflow* problem: portfolio managers have opinions about a few things, not a full
μ vector — BL lets them say only what they believe, with how strongly, and stay diversified
otherwise.

## 4. Our adaptation (this is the design, not just notes)

No market-cap equilibrium exists for a menu of 21 overlapping MSCI indices, but reverse
optimization only needs *a* defensible neutral portfolio:

- **Prior `w_prior`:** ERC weights ([risk-parity-erc.md](risk-parity-erc.md)) on the shrunk Σ
  ([ledoit-wolf-shrinkage.md](ledoit-wolf-shrinkage.md)); 1/N as the trivial alternative.
- **Π** from `Π = δΣw_prior`, δ calibrated so Π's scale matches historical portfolio-level
  returns (one scalar, reported).
- **User sliders as views:** the Return slider raises confidence in return-tilted views rather
  than switching the objective to raw μ̂-maximization.
- **Regime views (the signature):** per-quadrant performance differentials from
  `macro_state_performance` become relative views (P rows like "Quality − Reference within
  region"), with **Q from the outlook-weighted quadrant mix and Ω from the Markov outlook's
  calibrated probabilities** — a 34%-confidence Stagflation call tilts 34%-hard, not 100%-hard.
  This is the principled pipe from the macro module into allocation.
- Transparency: display Π vs μ_BL side by side — "what neutral believes" vs "what your views
  changed" — the whole update is auditable.

## 5. Pitfalls

- Ω and τ are the famous fudge factors; fix conventions (He-Litterman Ω, τ=1/T), document, and
  never expose both to the user — expose only per-view *confidence* c_k ∈ (0,1].
- Views must be about portfolios with nonzero risk (PΣPᵀ invertible).
- BL fixes μ; it does nothing for Σ estimation error — always pair with shrinkage.
- Degenerate trap: one 100%-confidence view reduces to constrained MVO on that view — cap c_k
  below 1 in the UI.

**Primary sources:** Black & Litterman, *FAJ* 48(5) 1992 ·
[He & Litterman, Goldman Sachs 1999 (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=334304) ·
Idzorek 2005 (confidence-based Ω) · [Goldman history](https://www.goldmansachs.com/our-firm/history/moments/1990-black-litterman-model).
