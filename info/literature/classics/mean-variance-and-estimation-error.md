# Mean-variance optimization and why it fails — Markowitz (1952), Michaud (1989), Chopra-Ziemba (1993), DeMiguel et al. (2009)

Deep dive behind [literature.md](../literature.md) §1. This one file is the *reason* the rest of
the folder exists: the math of MVO, the mechanics of its failure, and the evidence that decides
our design.

## 1. Markowitz's math (the frame everything uses)

Portfolio of n assets, weights `w` (n×1), expected returns `μ`, covariance `Σ`:

```
expected return:   μ_p = wᵀμ
variance:          σ_p² = wᵀΣw
```

Classic problems (long-only adds `w ≥ 0`, budget adds `1ᵀw = 1`):

```
min-variance:      w_mv  = Σ⁻¹1 / (1ᵀΣ⁻¹1)
tangency (max SR): w_tan ∝ Σ⁻¹(μ − r_f·1)
utility form:      max wᵀμ − (λ/2)·wᵀΣw   ⇒   w* = (1/λ)·Σ⁻¹μ   (unconstrained)
```

The **efficient frontier** is the set of portfolios minimizing σ_p for each attainable μ_p; with
only linear constraints it's traced by quadratic programming (our SLSQP handles the general
constrained case).

## 2. The failure mechanism (Michaud 1989, "The Markowitz Optimization Enigma")

Every closed form above contains `Σ⁻¹μ`. Two amplifiers:

1. **Inverse covariance blows up noise.** Σ⁻¹ has eigenvalues 1/λᵢ — the *smallest* sample
   eigenvalues (the directions estimated worst, mostly noise when n is non-trivial vs T) get the
   *largest* weight in the solution. The optimizer literally leans hardest on the least reliable
   directions.
2. **Selection bias on μ.** The optimizer ranks assets by estimated mean; estimates = truth +
   error, so the top-ranked assets are disproportionately the ones with *positive error*. MVO
   "goes long the luckiest estimation errors" — Michaud's *error-maximization*.

**Chopra & Ziemba (1993)** quantified input sensitivity: at moderate risk aversion, errors in
**means are ~11× more costly** than errors in variances, and variance errors ~2× covariance
errors. Hierarchy of estimability is the inverse: covariances are the most estimable input, means
the least. ⇒ Any sane design spends its effort on Σ (shrinkage — see
[ledoit-wolf-shrinkage.md](ledoit-wolf-shrinkage.md)) and refuses to lean on raw μ̂.

## 3. The evidence (DeMiguel, Garlappi & Uppal 2009, RFS)

Out-of-sample horse race: 14 optimization models (sample MVO, Bayes-Stein, Black-Litterman-style,
min-var, constrained variants, mixtures…) vs **1/N equal weight**, on 7 datasets, rolling
windows. Results:

- **No model consistently beat 1/N** on Sharpe, certainty-equivalent, or turnover.
- Analytic break-even: for sample-based MVO to beat 1/N you need roughly
  **T ≈ 3,000 months for n=25 assets** (≈6,000 for n=50). Estimation error eats the
  optimality gain below that.
- Best performers among the 14 were the most constrained ones (min-variance with tight
  constraints) — constraints act as implicit shrinkage (Jagannathan & Ma 2003: a no-short
  constraint ≈ shrinking extreme covariances).

**Our numbers: T = 330 months, n = 21.** We are an order of magnitude below break-even.
Conclusions baked into [portfolio_optimization.md](../portfolio_optimization.md):

1. **1/N is the mandatory benchmark** displayed with every optimizer result.
2. **Never free-maximize μ̂.** Return enters as a constraint ("≥ X%/yr") or a
   confidence-weighted view ([black-litterman.md](black-litterman.md)).
3. **Constraints aren't just guardrails, they're statistics** — the sleeve caps/min-sleeves
   defaults literally improve expected out-of-sample performance.

## 4. Michaud's cure: Resampled Efficiency (for completeness)

Algorithm (patented, US 6,003,018 — expired 2019+; concept freely usable, exact commercial
implementation was New Frontier's):

1. Estimate (μ̂, Σ̂) from data.
2. For b = 1..B: draw a simulated history from N(μ̂, Σ̂) (or bootstrap), re-estimate (μ_b, Σ_b),
   compute the whole efficient frontier for that draw.
3. Average the weight vectors across draws *at each frontier rank* → the resampled frontier.

Effect: weights become smooth, diversified functions of the data instead of corner solutions.
**⇒ for us:** same spirit, cheaper route — our scenario engine already bootstraps histories;
*validating* a candidate allocation across those bootstraps (dispersion of its CAGR/maxDD)
delivers the honesty without running B full optimizations. If we ever want it, resampling the
optimizer is ~20 lines around the existing engine.

## 5. What survives for our build

| Piece | Verdict |
|---|---|
| Return/risk/simplex frame, SLSQP | keep — it's the lingua franca |
| Raw `Σ⁻¹μ̂` in any form | forbidden by evidence |
| Tight default constraints | keep — they're implicit shrinkage |
| μ̂-free engines (ERC/HRP) as default | see [risk-parity-erc.md](risk-parity-erc.md), [hierarchical-risk-parity.md](hierarchical-risk-parity.md) |
| 1/N on screen always | non-negotiable |

**Primary sources:** Markowitz, *JF* 1952 · Michaud, *FAJ* 45(1) 1989 · Chopra & Ziemba, *JPM*
19(2) 1993 · [DeMiguel et al., *RFS* 22(5) 2009](https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901)
· Jagannathan & Ma, *JF* 2003.
