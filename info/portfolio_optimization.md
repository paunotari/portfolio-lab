# Portfolio optimization — design (vision.md Phase 3)

**Status: design only, not yet built.** This is the agreed plan for the multi-objective optimizer
and the regime-targeted allocation (the two open items under "Portfolio optimization" in
[TODO.md](TODO.md)). It exists so the design isn't lost between now and implementation. When we
build it, keep [CLAUDE.md](CLAUDE.md) and [TODO.md](TODO.md) current per the standing workflow.

Shaped entirely by the house principles: **KISS**, the **80/20 Pareto** rule, the **layered
Tier-1/Tier-2 UI**, and **full transparency** (the user must be able to recover *why* an
allocation was recommended). See [vision.md](vision.md) for the product framing.

Everything it needs already exists after Phase 2: 100%-sum-constrained blended portfolio stats
(`portfolio/diversification.py::portfolio_performance`), look-through concentration / HHI, the
4-quadrant classifier + per-state performance (`analytics/macro_state.py`), and the
regime-persistent scenario engine (`analytics/scenario.py`).

---

## 1. How many preferences to expose — three, at Tier-1

The user reasons about exactly three things, and the TODO's own examples name all three. Stop
there — more than three objectives makes the trade-off surface unexplainable, which breaks the
transparency principle.

1. **Return** — historical CAGR of the constant-mix blend.
2. **Risk** — annualized volatility by default; max-drawdown selectable at Tier-2 (people *feel*
   drawdown, not vol).
3. **Diversification** — effective number of independent bets (from the look-through HHI already
   computed), not just sleeve count.

**Tier-1 surface = three importance sliders + one optional hard target.** The target is either
"must achieve ≥ X %/yr" **or** "max drawdown ≤ Y %". That single surface covers every mode the
TODO asks for:

| TODO mode | How the three sliders express it |
|---|---|
| Single-objective ("max return") | one slider maxed, others at 0 — will honestly degenerate to ~100% in the best historical performer (expected, and flagged, not hidden) |
| Single-objective ("min volatility") | risk slider maxed, others at 0 |
| Multi-objective blend (return **and** risk **and** diversification) | mixed slider positions |
| User-tunable priority ("accept more risk to chase return") | just move the sliders |
| Constrained target ("≥12%/yr, then max diversification + min risk") | slider mix **+** the hard target as a constraint |

Everything else is **Tier-2, collapsed, with good defaults** so a zero-touch run still produces a
sound portfolio:

- **Regime row** (the signature feature — see §3): per-quadrant importance. Presets: historical
  frequency / even 25×4 / weighted by the current 3-month Markov outlook / custom.
- Risk-metric choice (vol ↔ max drawdown).
- Per-sleeve or per-region caps; minimum number of sleeves.

---

## 2. Internal method — explainable, no black box

**Normalize before blending.** CAGR, vol and HHI are in different units, so a raw weighted sum
makes the sliders meaningless. Instead:

1. Optimize each objective **alone** to find its best and worst attainable value (its "utopia" and
   "nadir" points) across the feasible set.
2. Rescale every objective to **0–100** on that range.

Now "Return 5 / Risk 5" is genuinely balanced, and — crucially for transparency — every
recommended portfolio ships with a **scorecard**: e.g. *Return 82/100 · Risk 64/100 ·
Diversification 71/100*. The "why" falls out of the method for free.

**Objective:** maximize the priority-weighted sum of the normalized scores, subject to
`weights ≥ 0`, `Σ weights = 100%` (the existing invariant — never silently rescale), plus any
Tier-2 caps and the optional hard target expressed as a constraint.

**Solver: multi-start SLSQP from `scipy.optimize`.** With 21 assets and objectives that are just
arithmetic on the 330-month return matrix, ~50 random starts + an equal-weight start solve in well
under a second and avoid local minima.

- **Backend decision (resolves the TODO open question): `scipy`.** It's already installed
  (transitive dep — add it explicitly to `pyproject.toml` when we build this). Rejected
  alternatives: **cvxpy** forbids exactly the objectives we care about (max-drawdown and
  per-regime blends aren't convex); **Riskfolio-Lib** is a heavy, opinionated dependency that
  makes the method *less* transparent — the opposite of the house style.

---

## 3. Signature feature — regime-targeted allocation

Per-quadrant portfolio return is already computable from `macro_state_performance`'s pooled
months, so a regime target is just **another normalized objective**:
`Σ (quadrant importance × that quadrant's score)`.

Two modes worth shipping:

- **Weighted blend** — the TODO's 25/25/25/25, frequency-weighted, or custom per-quadrant targets
  ("do well in X, accept less in Y").
- **Maximin** — maximize the *worst* quadrant's performance. This is the KISS crown jewel: "a
  portfolio that holds up no matter which macro state comes," one checkbox, deeply aligned with
  the whole macro module.

**Scenario engine = validator, not objective.** Run the final recommended allocation through the
regime-persistent Monte Carlo (`current_conditions`) and show its CAGR cone + P(loss) next to the
recommendation. Optimizing *through* the Monte Carlo would be slow and overfit noise; validating
*through* it is honest and cheap.

---

## 4. Guardrails — where optimizers lie

An unconstrained optimizer on 28 years of history is a hindsight machine. Three cheap defenses:

- Default (overridable) caps: max ~40 % per sleeve, min 3 sleeves.
- A visible warning when the solution sits at a corner: "this is a bet on one index's past, not an
  allocation."
- Always show the per-regime breakdown + scenario cone so a fragile portfolio exposes itself.
- Label the output honestly: **historically optimal under your priorities** — not a forecast, not
  a promise.

---

## 5. Build order

- **3a — Python engine** (`portfolio/optimizer.py`): blend + constraints + multi-start SLSQP, a
  CLI + report, tests that single-objective modes degenerate correctly (max-return → best
  performer; min-vol → lowest-vol blend). This alone completes most of the TODO item.
- **3b — regime objectives + maximin + scenario validation** of the final candidate(s).
- **3c — dashboard "Optimizer" tab**: the three sliders run live in the browser (level series are
  already baked, so a JS mirror of the objective + a simple multi-start/projected-gradient solver
  keeps the dashboard serverless — same dual-implementation pattern as `computeSeriesStats`, and
  the same "keep the two in sync" caveat #12 applies). Tier-2 panel + a small frontier strip
  showing the chosen portfolio vs. its neighbors, so users *see* what moving a slider buys.

---

## 6. Dependencies (all satisfied after Phase 2)

- ✅ 100 %-weight constraint + blended portfolio stats — `portfolio/diversification.py`.
- ✅ Settled risk metrics (vol, max DD; CVaR optional later) — `analytics/engine.py::_perf_stats`.
- ✅ Regime-conditional data for regime-aware optimization — `analytics/macro_state.py`,
  `analytics/scenario.py`.
- ✅ Backend chosen — `scipy` (§2).

## 7. Read the literature first — this is NOT pure math

The *mechanics* here are trivial (SLSQP + weighted sums), but **naive mean-variance optimization
on historical returns is a documented failure mode** — Michaud (1989) called it an
"error-maximizer" because it overweights whatever assets had the luckiest past estimates. The
§4 guardrails are first-principles reasoning, not the known, better solutions. Before building,
do the "Portfolio construction" literature pass in [TODO.md](TODO.md) → `info/literature.md`:
covariance shrinkage (Ledoit-Wolf), Black-Litterman, resampled efficiency, risk parity, and
especially **Hierarchical Risk Parity (López de Prado)** — a robust, KISS-compatible alternative
that may be a better default than raw MVO for our 21-asset, 330-month set. The estimation-error
robustness is the whole game; the optimizer is the *last* place to trust naive history.
