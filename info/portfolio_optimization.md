# Portfolio optimization — the unified method (v2, built 2026-07)

**Status: 3a (engine) + 3b (regime/maximin) + walk-forward validation are BUILT** —
`portfolio/shrinkage.py`, `portfolio/anchors.py`, `portfolio/views.py`,
`portfolio/optimizer.py`, `portfolio/validation.py`, wired as pipeline stage 10 with tests in
`tests/test_optimizer.py`. **3c (dashboard Optimizer tab) is the named follow-up** (TODO.md).

This v2 folds the literature pass ([literature.md](literature.md) §4's eight build directives,
deep dives in [literature/](literature/)) into the original v1 design. The v1 surface survives
(three Tier-1 sliders + one optional hard target, normalized-score blend, multi-start SLSQP,
scipy backend); what changed is *what the objectives are allowed to consume* and *what must
always be shown next to the result*. House principles throughout: **KISS**, **80/20**,
**Tier-1/Tier-2 layering**, **full transparency** (the user must be able to recover *why*),
and the FRED-ToS line (CLAUDE.md caveat #11 — everything below is closed-form / counting /
resampling; nothing fitted).

The one-sentence version (see
[literature/STATE-OF-THE-ART-IN-PLAIN-WORDS.md](literature/STATE-OF-THE-ART-IN-PLAIN-WORDS.md)):
*with 330 months of data your biggest enemy is your own estimation error — so build from the
stable structure of the assets, add opinions only in proportion to confidence, defend the worst
regime rather than chasing the best, and keep the equal-weight benchmark on screen.*

---

## The method — one pipeline, five stages

### 1. Estimate inputs defensively (`shrinkage.py`, monthly returns on the 330×21 common window)

- **Covariance: Ledoit-Wolf constant-correlation shrinkage** (the "Honey, I Shrunk…" variant;
  scaled-identity variant kept as test oracle). δ\* is reported in every output — free
  transparency about input quality (measured on our data: δ\* ≈ 0.14, i.e. the sample matrix is
  decent and gets a mild pull toward structure).
- **Expected returns: never raw historical means** (Michaud's error-maximization; Chopra-Ziemba's
  11×; DeMiguel's 3,000-month break-even). The only μ any objective ever sees is the
  Black-Litterman posterior μ_BL from stage 3.
- **Per-quadrant mean returns μ̂_q** (pooled state months, recomputable on any window) feed the
  regime objectives — linear in w, cheap inside the solver.

### 2. Anchor on structure, not estimates (`anchors.py`)

- **Neutral anchor w₀ = ERC** (equal risk contribution) on the shrunk covariance — solved via
  Spinu's convex form; unique, explainable, built from the input we actually trust.
- **1/N, HRP and min-variance are computed on every run** and displayed as the benchmark table.
  1/N is non-negotiable (DeMiguel); HRP's cluster tree doubles as a Tier-2 explanation and a
  data-pipeline sanity check. The walk-forward table (stage 5) is the evidence that will
  eventually confirm or flip ERC vs HRP as default anchor.

### 3. Opinions tilt in proportion to confidence (`views.py`, the BL pattern)

- **Π = δ·Σ·w₀** (reverse optimization; δ calibrated so the anchor's implied return matches its
  own historical mean — one scalar, reported). Saying nothing returns exactly w₀: garbage-in is
  structurally impossible at this stage, and `mu_BL == Π` with zero views is a unit test.
- **Regime views — the signature pipe from the macro module:** one *relative* view per factor
  type ("Momentum/Value/Quality vs their own regions' Reference"), with Q = the per-quadrant
  excess weighted by the 3-month Markov outlook, and confidence = the outlook's own probability
  mass. A 34%-confidence stagflation call tilts 34%-hard, not 100%-hard. Relative views only —
  absolute "asset X returns Y%" claims would smuggle raw means back in.
- Fixed conventions, never user-exposed: τ = 1/T, He-Litterman diagonal Ω scaled by per-view
  confidence, confidence capped at 0.95 (a 100%-confidence view degenerates BL into constrained
  MVO on itself).

### 4. Preferences select along the frontier (`optimizer.py`)

Tier-1 stays three sliders + one optional hard target ("CAGR ≥ X%/yr" or "maxDD ≤ Y%").
Internally every objective is normalized to a **0–100 score on its own attainable range** over
the capped simplex (utopia/nadir; linear objectives solved exactly by greedy cap-filling,
nonlinear by multi-start SLSQP) — so "Return 5 / Risk 5" is genuinely balanced and the
**scorecard falls out of the method for free**.

| Objective | Consumes | Notes |
|---|---|---|
| Return | w·μ_BL | tilts, never dominates — the literature's hardest rule |
| Risk | vol from shrunk Σ (default) · empirical blended maxDD (Tier-2 toggle) | CVaR-95 parked ([cvar-optimization.md](literature/cvar-optimization.md) has the un-parking route: feed the Rockafellar-Uryasev LP with scenario-engine months) |
| Diversification | geometric mean of look-through effective bets (1/HHI over sector/country/stock, exact quadratic forms w·AAᵀ·w) | geometric because stock-level bets run ~100× sector-level (top-10-only data, caveat #4) |
| Regime row (Tier-2) | Σ_q importance_q × score_q(w·μ̂_q), each quadrant scored on its own range | presets: historical frequency / even 25×4 / Markov-outlook-weighted |
| **Maximin (mode)** | max_w min_q w·μ̂_q, epigraph reformulation | one checkbox; All Weather's philosophy; targets exactly where Ang-Bekaert located the value (not being destroyed in the bad state) |

- **Solver:** multi-start SLSQP (equal-weight + anchor + 50 Dirichlet starts), `w ≥ 0`,
  `Σw = 100%` (never silently rescaled — the house invariant).
- **Constraints are statistics, not apologies** (Jagannathan-Ma): default cap 40%/sleeve
  (mathematically forces ≥ 3 sleeves; forcing ≥ m means capping just under 1/(m−1)), both
  Tier-2 overridable. Hard targets enter as SLSQP constraints; infeasible targets are *reported*
  ("NOT ACHIEVABLE"), never silently relaxed.
- **Degenerate honesty:** all sliders zero ⇒ the ERC anchor, by construction. Return slider
  alone ⇒ tilts to the best μ_BL sleeves but stays capped, with the corner warning below.

### 5. Judge like a skeptic (`optimizer.py` reporting + `validation.py` + scenario engine)

Every recommendation ships with: the scorecard · the risk-contribution vector ("where your risk
actually sits", Euler decomposition) · per-quadrant mean returns · δ\* · Π-vs-μ_BL view list ·
the benchmark table · a **corner-solution warning** when weights sit at the caps ("this is a bet
on one index's past — the caps are doing the diversifying") · the label **"historically optimal
under your priorities — not a forecast."**

- **Scenario engine = validator, not objective.** The final weights run through the
  regime-persistent bootstrap (`analytics/scenario.py::portfolio_cone`, `current_conditions`
  mode) → portfolio-level CAGR cone + P(loss). Optimizing *through* the Monte Carlo would be
  slow and overfit noise; validating through it is honest and cheap.
- **Walk-forward out-of-sample backtest** (`validation.py`): expanding window, 120m warmup,
  annual refits, everything re-estimated on the training window only; contestants 1/N /
  min-var / ERC / HRP / balanced sliders / maximin, with turnover reported. **First result
  (2026-07, OOS 2009–2026): min-variance had the best OOS Sharpe (1.06); the balanced-slider
  blend (0.70) did NOT beat 1/N (0.84).** Exactly the DeMiguel humility the method predicts,
  printed in the report — the honest framing is that the optimizer's value is *expressing
  preferences and regime robustness transparently*, not beating equal weight.

---

## Where things live

| Piece | Module |
|---|---|
| Ledoit-Wolf shrinkage (2 variants) | `portfolio/shrinkage.py` |
| 1/N · ERC · HRP · min-var · risk contributions | `portfolio/anchors.py` |
| Π, BL posterior, regime views | `portfolio/views.py` |
| objectives, normalization, SLSQP, maximin, scorecard, report, CLI | `portfolio/optimizer.py` |
| walk-forward OOS backtest | `portfolio/validation.py` |
| comparison charts (7 captioned Plotly figures) | `portfolio/visualize.py` → `optimizer_viz.html` |
| portfolio-level scenario cone | `analytics/scenario.py::portfolio_cone` |
| config constants (`OPTIMIZER_*`) | `config.py` |
| outputs | `outputs/analytics/optimizer/` (`REPORT_optimizer.md`, `optimizer_portfolios.csv`, `optimizer_walkforward.csv`) |

```bash
python -m portfolio_lab.portfolio.optimizer --return 5 --risk 5 --div 5   # one-off run
python -m portfolio_lab.portfolio.optimizer --maximin                     # robust mode
python -m portfolio_lab.portfolio.validation                             # walk-forward only
python -m portfolio_lab.portfolio.visualize                              # comparison charts (HTML)
```

## Follow-ups (tracked in TODO.md)

- **3c — dashboard "Optimizer" tab**: live sliders in the browser (JS mirror of the objective;
  the caveat-#12 dual-implementation warning will apply), Tier-2 panel, frontier strip.
- CVaR-95 as a third Tier-2 risk metric (un-parking route documented in the deep dive).
- Per-sleeve/per-region **risk budgeting** (`RC_i = b_i·σ_p` — same convex program, one line).
- Revisit ERC-vs-HRP default anchor once more walk-forward evidence accumulates.
