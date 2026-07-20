# Nowcasting & dynamic factor models — Stock-Watson, Giannone-Reichlin-Small (2008), GDPNow, NY Fed Nowcast

Deep dive behind [literature.md](../literature.md) §2. The grown-up version of our composite
z-score; mostly a map of the upgrade path and what's worth stealing *now*.

## 1. Principle

Dozens of macro releases, all noisy, all lagging differently, arriving on a ragged calendar. The
insight (Stock & Watson's diffusion indexes, 1990s–2002): they co-move because a small number of
latent factors drive them — so estimate the factor, not the individual series.

**Dynamic factor model:**

```
observation:   X_t = Λ·f_t + ε_t        (X_t = many standardized indicators)
state:         f_t = A·f_{t−1} + u_t    (factor evolves; VAR(1) typically)
```

Estimated with PCA (static) or Kalman filter + EM (dynamic). The **Kalman filter is what handles
the ragged edge** — series missing at the end (not yet released) are simply skipped in that
period's update, so the factor estimate is always current with whatever has been published.
"News decomposition": each release moves the nowcast by (Kalman gain × surprise), so you can
attribute every revision to a specific data release.

## 2. Production record (this is central-bank production software)

- **Atlanta Fed [GDPNow](https://ideas.repec.org/p/fip/fedawp/2014-07.html)** (2014– ): bridge
  equations mapping monthly releases to the 13 BEA subcomponents of GDP + factor-model elements;
  published continuously, moves markets.
- **[NY Fed Staff Nowcast](https://www.newyorkfed.org/research/policy/nowcast/methodology.html)**
  (2016– , lineage Bok-Giannone et al. 2018): a full DFM updated weekly with news decomposition.
- Foundational paper: **Giannone, Reichlin & Small, *J. Monetary Economics* 2008** — formalized
  "nowcasting" and the real-time informational content of the release calendar.

## 3. Honest placement of our method

Our composite growth/inflation score IS a degenerate DFM: one factor per axis, loadings fixed at
±1/k (equal weights), no dynamics, no Kalman filter, z-scored trends instead of filtered levels.
That's not an insult — it's the KISS point on the same spectrum, and our walk-forward tests
showed the marginal value of more inputs is small *at monthly frequency with our sample*
(TODO.md round 2: adding 9 indicator trends to the k-NN made things worse).

**Upgrade path, in order of value per complexity:**

1. **Steal the calendar discipline, not the model** (now): our prints lag 1–2 months; a DFM's
   main practical win is using *this week's* releases. Same win for us comes from the Phase-1
   live-data feed — data recency > model sophistication. (Matches our own backtest conclusion.)
2. **PCA loadings instead of equal weights** (cheap, borderline): still linear algebra on
   history, but loadings are *estimated* — nudges against the ToS line; document if ever done.
3. **Full Kalman DFM** (Phase 4, non-FRED data): this is "fitting a model" without ambiguity.

## 4. What to remember when the optimizer meets live data

The nowcasting literature's core lesson transfers: **the bottleneck is information timing, not
functional form**. Whatever allocation engine we ship, its regime input improves more from
fresher indicator data than from a cleverer classifier — budget accordingly in vision.md Phase 1
(live feed) before any Phase 4 modeling.

**Primary sources:** Stock & Watson, *JASA* 2002 (diffusion indexes) · Giannone, Reichlin &
Small, *JME* 2008 · [GDPNow working paper](https://ideas.repec.org/p/fip/fedawp/2014-07.html) ·
[NY Fed Nowcast methodology](https://www.newyorkfed.org/research/policy/nowcast/methodology.html)
· Bok, Caratelli, Giannone, Sbordone & Tambalotti 2018.
