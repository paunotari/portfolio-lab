# Regime switching — Hamilton (1989), Ang & Bekaert (2002/2004), Guidolin & Timmermann

Deep dive behind [literature.md](../literature.md) §2. The lineage of our quadrant machinery, and
the precise boundary between what we do (counting) and what stays Phase 4 (fitting).

## 1. Hamilton (1989) — the framework everything descends from

*"A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle,"
Econometrica 57(2).* The economy is in a hidden state s_t ∈ {1..K} following a Markov chain
(transition matrix P); observed data y_t is drawn from a state-dependent distribution
f(y_t | s_t = k; θ_k).

**The Hamilton filter** (inference about the hidden state, runs forward through time):

```
predict:   ξ̂_{t|t−1} = Pᵀ · ξ̂_{t−1|t−1}                      (ξ̂ = prob. vector over states)
update:    ξ̂_{t|t}   ∝ ξ̂_{t|t−1} ⊙ f_t                        (⊙ elementwise; f_t = likelihoods)
log-lik:   Σ_t ln( 1ᵀ( ξ̂_{t|t−1} ⊙ f_t ) )
```

Parameters (P, θ_k) estimated by **maximum likelihood / EM**; a backward *smoother* (Kim 1994)
gives ξ̂_{t|T} using all data. Two regimes on US GNP growth reproduced NBER recession dating from
data alone — the result that made the framework canonical.

**Where we stand relative to it:** our classifier makes the state *observable* (composite scores
define the quadrant), so no filter and no EM are needed — the transition matrix is estimated by
**counting observed transitions**, which is the maximum-likelihood estimator *for an observed
Markov chain*. Same mathematical object, no model fitting. That's the exact technical content of
the FRED-ToS line (`CLAUDE.md` caveat #11): Hamilton's *hidden*-state estimation (EM on FRED
data = training a model) is Phase 4 / non-FRED; our observed-chain counting is not.

Honesty note: our soft probabilities play the role of ξ̂_{t|t} but come from Φ(scores), not from a
filter — they carry no likelihood model. The backtest calibration (TODO.md round 2: 10–20% bin →
10.6% realized, etc.) is what licenses them instead.

## 2. Ang & Bekaert — regimes earn their keep in allocation

*"International Asset Allocation with Regime Shifts" (RFS 2002); "How Do Regimes Affect Asset
Allocation?" (FAJ 2004).* Two-regime models on international equities find:

- A **high-volatility bear regime in which cross-country correlations spike** — diversification
  fails exactly when needed (our 36m rolling-correlation chart is this fact, measured).
- Regime-aware dynamic allocation produces **economically meaningful welfare gains** out of
  sample vs static mean-variance; among the first out-of-sample demonstrations.
- The gains come mostly from **cutting risk exposure in the bad regime** — not from clever
  in-regime stock-picking.

Guidolin & Timmermann (multiple papers, mid-2000s) extend to **four states** (crash, slow growth,
bull, recovery) with size/value portfolios — regime-dependent factor performance, four states as
a defensible granularity. Comfortingly, our quadrant count and our factor-attribution findings
sit inside their result space.

**⇒ for us:** the academic license for regime-targeted allocation, plus a design steer we
already encoded: the *maximin* mode (protect the worst quadrant) targets exactly where the
literature says the value is. Also a warning: their gains assume you can *identify* the regime in
time — our ~1–2 month print lag and 52–57% 3-month hard-call hit rate bound how much of the
theoretical welfare gain is reachable. Never present regime-aware allocation as free alpha.

## 3. Implementation notes for the optimizer (3b)

- Per-quadrant portfolio return of candidate weights: `r_q(w) = wᵀ·μ̂_q` with μ̂_q = mean monthly
  return vector over state-q months (already in `macro_state_performance.csv` per series) —
  linear in w, cheap inside the objective.
- Per-quadrant risk: Σ̂_q from state-q months is noisy (76–101 months per state; shrink it —
  [ledoit-wolf-shrinkage.md](ledoit-wolf-shrinkage.md) with stronger δ expected). Use for
  reporting; be reluctant to *optimize* on per-state Σ.
- Maximin: `max_w min_q r_q(w)` → standard epigraph reformulation: `max_{w,z} z` s.t.
  `wᵀμ̂_q ≥ z ∀q` + budget/caps — linear, SLSQP-trivial.
- Regime views for the BL route: see [black-litterman.md](black-litterman.md) §4.

**Primary sources:** Hamilton, *Econometrica* 1989 · Kim, *J. Econometrics* 1994 · Ang & Bekaert,
*RFS* 2002 & *FAJ* 2004 · Guidolin & Timmermann, *JEDC/REStat* 2000s · survey:
[Ang & Timmermann, "Regime Changes and Financial Markets" (NBER w17182)](https://www.nber.org/system/files/working_papers/w17182/w17182.pdf).
