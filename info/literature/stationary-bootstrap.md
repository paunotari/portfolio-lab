# Block / stationary bootstrap — Politis & Romano (1994)

Deep dive behind [literature.md](../literature.md) §2. Short file: this is the theory our
scenario engine already implements; the value is knowing the exact correspondence and the one
tuning result worth importing.

## 1. Principle

The i.i.d. bootstrap (Efron 1979) resamples single observations — destroying serial dependence,
which financial and macro series have. **Block bootstraps** resample contiguous *runs* so
within-block autocorrelation survives:

- **Moving-block bootstrap** (Künsch 1989): fixed block length ℓ, random start points; the
  concatenated series is *not* stationary (seams every ℓ).
- **Stationary bootstrap** (Politis & Romano, *JASA* 89(428) 1994): block lengths are **random,
  geometric** — at each step, with probability p start a new block at a random position, with
  probability 1−p continue the current run. Expected block length 1/p. The resampled process is
  strictly stationary; asymptotics (consistency for means, variances, smooth functionals) hold
  under standard mixing conditions.

## 2. The correspondence to `analytics/scenario.py` (exact)

Our regime-persistent simulation is a **state-conditioned stationary bootstrap**:

| Politis-Romano | Our engine |
|---|---|
| geometric block length, mean 1/p | geometric spell duration, continuation prob = transition-matrix diagonal p_ss (mean 1/(1−p_ss)) |
| new block starts at uniform random position | new spell's months block-sampled from that state's historical runs (uniform start within the state's months) |
| unconditional | conditioned on the regime path (weights mode / markov-from-current mode) |
| univariate/multivariate series | whole cross-sectional month vectors (preserves cross-series correlation) |

So the engine inherits the stationary bootstrap's justification for preserving serial dependence,
with regime structure layered on top. **Action when next touching scenario.py: cite
Politis-Romano 1994 in the docstring** — the method has a name and asymptotic theory; saying so
is free credibility and helps any future reader search the literature.

## 3. The one tuning result worth knowing

**Politis & White (2004; correction Patton-Politis-White 2009)** give an automatic, data-driven
choice of expected block length (minimizing the bootstrap variance estimator's MSE, from the
autocorrelation structure). We don't need it today — our "block length" is economically pinned by
measured regime persistence (4–6 months expected duration), which is more honest than a purely
statistical tuning for our use case. But if anyone ever asks "why these block lengths?", the
answer is: regime-persistence-implied, and the statistical alternative exists and roughly agrees
in order of magnitude.

## 4. Boundaries

- Bootstrap preserves *dependence within* what it resamples; it cannot invent dynamics history
  didn't contain (our stated "future = re-sequenced 1997–2026" assumption is exactly this,
  formalized).
- Geometric durations are memoryless — real regimes may have duration memory (hazard rising with
  age). Checked implicitly by the calibration backtests; a semi-Markov (empirical-duration)
  variant is the upgrade if ever needed, still pure counting.

**Primary sources:** Politis & Romano, *JASA* 1994 · Künsch, *Ann. Statist.* 1989 · Politis &
White, *Econometric Reviews* 2004 (+ 2009 correction).
