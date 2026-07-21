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

## 6. A pedagogical walkthrough, checked (owner link 2026-07-21)

[sesen.ai — "Modern Portfolio Theory from Scratch: The Efficient Frontier"](https://sesen.ai/blog/modern-portfolio-theory-markowitz-efficient-frontier)
(blocked to WebFetch; read through the in-app browser). A code-first tutorial: 4 asset classes,
50k Dirichlet-random long-only portfolios plotted as the "bullet" cloud, the frontier extracted
by binning the cloud, then the closed forms for GMV `Σ⁻¹1/(1'Σ⁻¹1)` and tangency
`Σ⁻¹μ/(1'Σ⁻¹μ)`, the CML, Tobin separation and CAPM. **Nothing methodological here that we do
not already implement** (and its limitations section — correlations→1 in crises, fat tails,
Michaud's error maximization, "expected returns are impossible to estimate accurately" — is our
project's premise, restated for a general audience). Three things are still worth keeping.

### 6.1 The one adoptable artifact: the Monte-Carlo bullet cloud
Their central image is a scatter of thousands of random long-only portfolios, with the frontier
as its upper-left edge. **We have every piece already** — the optimizer's multi-start SLSQP
draws Dirichlet starts, `visualize.py` already plots a sleeve-vs-portfolio risk/return map — and
the cloud is the natural BACKGROUND for the Michaud resampled frontier recorded in TODO
(Phase-3 follow-ups). Cloud + resampled-frontier smear + the flagships on top is one figure that
carries the whole thesis.

**But the tutorial's frontier-extraction method does not survive our dimensionality, measured:**
a 200k-draw Dirichlet cloud on a 28-sleeve menu reaches the true long-only minimum variance
almost exactly (gap 0.12%) — the low-vol edge is fine — while it reaches only **68% of the
maximum attainable return** (against 99.8% at N=4). The Dirichlet concentrates near 1/N as N
grows, so the high-return corners are simply not sampled. ⇒ if we draw the cloud, the frontier
line must come from the OPTIMIZER (which is what we already do), never from binning the cloud.
Their binning works at N=4 and quietly breaks by N=10.

### 6.2 Their own worked example demonstrates error maximization — they do not say so
Same Σ, two portfolios, the only difference being that the tangency portfolio consumes μ:

| asset | GMV (no μ) | tangency (uses μ) |
|---|---|---|
| US Equity | 41.6% | 41.1% |
| Intl Equity | **−1.1%** | **39.5%** |
| Real Estate | 20.9% | 1.1% |
| Commodities | 38.7% | 18.2% |

Two positions move ~40 and ~20 points purely from introducing an estimated μ. We re-ran their
numbers and perturbed **one** input: moving Intl's expected return by ±1pp (0.16→0.15 / 0.17)
swings its own tangency weight 39.5% → **33.3% / 45.8%** and US Equity ~9pp the other way. A
1-point change in the least estimable input moves the allocation by twelve. That is
Chopra-Ziemba's 11× and Michaud's "error maximizer" in a tutorial's own arithmetic — a compact,
self-contained illustration worth borrowing for the paper's introduction and the dashboard's
Tier-2 explainer.

### 6.3 Two defects, flagged so nobody copies them
- **Their second worked example's covariance matrix is not a covariance matrix.** `[[0.10,
  0.30, 0.10], [0.30, 0.15, −0.20], [0.10, −0.20, 0.08]]` has eigenvalues (−0.295, 0.178,
  0.447) and implied correlations of **2.449** and **−1.826**. The printed "portfolio variance
  0.0811" is arithmetically correct and describes an impossible world. (Our own guard: every Σ
  in the engine comes out of `shrinkage.estimate_covariance`, which is PSD by construction, and
  the anchors are unit-tested for it.)
- **`w_tan = Σ⁻¹μ/(1'Σ⁻¹μ)` holds only at r_f = 0**, which they do assume but state in
  passing; the general form uses the excess vector `Σ⁻¹(μ − r_f·1)/(1'Σ⁻¹(μ − r_f·1))`. Our
  M-series switched the walk-forward tables to the excess convention for exactly this reason.

**⇒ net verdict:** no new method, one good figure idea (§6.1), one borrowable illustration
(§6.2). Filed here rather than in `frontier/` because it is pedagogy about the canon, not a
working paper.
