# The estimator, formalized — era-agreement-gated long-history shrinkage for regime-conditioned means

The paper's candidate contribution (TODO "Paper track"), written up formally: notation,
definition, statistical interpretation, properties, positioning, and its measured record.
Implemented in `portfolio/views.py::regime_views` + `portfolio/optimizer.py::_anchor_mu_q`,
fed by `analytics/long_history.py::{msci_factor_prior, asset_class_prior, market_prior}`.

## 1. Setting and notation

- **States.** A deterministic classifier `c` maps macro history to quadrant states
  s ∈ S = {Goldilocks, Reflation, Deflationary bust, Stagflation} (growth trend ×
  inflation trend; `analytics/macro_state.py`). The same classifier labels both samples —
  no fitted latent-state model anywhere.
- **Modern sample.** Investable sleeves i = 1..N with monthly returns r_it over the modern
  window (1997+). Let n_s = #modern training months labeled s,
  μ̂_is = mean of r_it over those months (the modern conditional MLE), and ref(i) the
  region-Reference sleeve of i, with modern conditional excess ê_is = μ̂_is − μ̂_ref(i),s.
- **Long sample.** Research series j (Fama-French factors 1926+, asset-class proxies
  1962+), classifiable from 1960: m_s long months in state s, long conditional mean f̄_js,
  and its modern-window restriction f̄'_js (same series, modern months only).
- **Universe mapping.** Each factor sleeve family maps to a long counterpart j(i)
  (Enhanced Value → HML, Momentum → MOM; Quality → none), with loading β_j estimated once
  per family by OLS of the pooled modern sleeve excess on f_j over the modern overlap.
  Asset-class sleeves are their own long series (β = 1). Regional bases map to the market
  factor's total return with a per-region β (the M15 extension).

## 2. The estimator

**The gate.** For each (long series j, state s):

    g_js = 1{ sign(f̄_js) = sign(f̄'_js) }            (era sign-agreement of j's own record)

**Factor-sleeve cells** (the excess is what transfers, on top of the regional base):

    ẽ_is = g_js · [ n_s ê_is + m_s β_j f̄_js ] / (n_s + m_s)  +  (1 − g_js) · ê_is
    μ̃_is = μ̂_ref(i),s + ẽ_is

**Asset-class cells** (the series is its own long counterpart):

    μ̃_is = g_is · [ n_s μ̂_is + m_s μ̄^long_is ] / (n_s + m_s)  +  (1 − g_is) · μ̂_is

**Exclusions on principle.** Cash is never anchored: its conditional "mean" is the era's
policy-rate level, not transferable behavior. Sleeves without a long counterpart (Quality)
keep modern excesses.

**Consumers.** The blended cells enter (a) the Black-Litterman view vector Q (view
confidence comes separately, from the Markov outlook's probability mass — M5), and (b) the
maximin/regime objectives' per-quadrant means μ_q^obj (M10). Descriptive reporting always
keeps the raw modern μ̂ — blending is for decisions, never for the record.

## 3. Statistical interpretation

The blend is a **precision-weighted pooling under exchangeability**: if each β-mapped long
observation is treated as one modern-equivalent observation of the cell, the minimum-
variance combination of the two conditional means weights them by sample size — exactly
n_s : m_s. Equivalently, in **empirical-Bayes** terms: prior mean β_j f̄_js with prior
strength m_s pseudo-observations, posterior mean = the blend. Because m_s ≫ n_s in every
state (789 classifiable long months vs ~330 modern), the anchor dominates wherever the
gate opens — by design: the modern conditional mean is the noisiest object in the system
(30-90 months per cell).

The gate is a **pretest estimator** (Judge & Bock 1978 lineage): a hard model-selection
step that asks "is the cross-era pooling assumption tenable?" with the crudest sufficient
statistic — the sign. Relative to James-Stein — which shrinks toward a target with
data-optimal intensity — this trades theoretical risk-optimality for two things a
practitioner audit needs: the intensity is **fixed and interpretable** (months of
evidence), and the pooling decision is **binary and inspectable** (a table of 16 cells,
each marked agree/disagree, ships with every report).

## 4. Properties (each measured, not asserted)

- **P1 — Conservatism / self-limitation.** Where eras disagree, the estimator returns the
  modern MLE untouched: it never imports a sign it cannot confirm. Measured consequence
  (M15): extending the anchor to regional bases is a no-op for the equity maximin, because
  its binding quadrant (Stagflation) is the market's one era-flipped cell — the gate
  closes exactly where discipline was hoped for. Where the eras disagree there is nothing
  transferable, *and the estimator knows it*.
- **P2 — Vanishing influence.** As n_s → ∞ the anchor's weight m_s/(n_s+m_s) → constant
  < 1 only because m_s is finite; in the regime n_s ≫ m_s the blend converges to the
  modern mean. The device matters precisely in the small-n_s cells it was built for.
- **P3 — Directional honesty.** The gate conditions on j's OWN two eras (long vs modern
  restriction), never on the sleeve's realized performance — no peeking at the quantity
  being estimated.
- **P4 — Scale transfer.** β maps academic long-short factor units into long-only sleeve
  excess units (measured β ≈ 0.19-0.28), so the anchor is magnitude-appropriate, not just
  sign-appropriate.

## 5. Positioning against the literature

- **Ang & Bekaert (2002 RFS; 2004 FAJ)** established that regime-dependent moments matter
  for allocation — estimated via fitted Markov regime-switching models (EM on latent
  states). **Guidolin & Timmermann (2007, 2008)** richer latent-state dynamics, same
  estimation philosophy. Ours differs in kind: states are *observable* (macro classifier,
  deterministic), conditional moments are *pooled sample means*, and the only estimation
  refinement is cross-era shrinkage. Nothing is fitted to predict; every number is an
  average someone can recompute by hand.
- **Black-Litterman (1992)** tells you how to blend views with an equilibrium prior but is
  silent on where views come from. The estimator is an answer to that silence: Q is the
  gated cross-era blend, confidence is the outlook's probability mass — the BL machinery
  is kept, its free parameter is disciplined.
- **Jorion (1986) Bayes-Stein; Frost & Savarino (1986)** shrink unconditional means
  toward a grand mean within one sample. Ours shrinks *conditional* (regime) means toward
  *another era's* evidence, with a tenability gate — the target carries genuinely new
  information (the 1970s) rather than a within-sample average.
- **DeMiguel et al. (2009)** is the reason the estimator exists at all: with ~330 months,
  unconditional mean estimates are unusable (their break-even ≈ 3,000 months), and
  conditional ones are 4× worse. The design response is to (i) never let raw means into
  objectives, (ii) import 2.4× more conditional evidence where tenable, (iii) accept the
  modern MLE elsewhere and say so.

## 6. Measured record (the ledger entries that discipline every claim above)

| Entry | What it measured | Verdict |
|---|---|---|
| M5 | Views anchored (β·f̄ blend) | EV view tempered +0.44→+0.15%/mo; OOS-neutral (input robustness) |
| M10 | Objectives anchored | every maximin variant improves OOS (all-weather 0.942→0.954, vol 10.6→8.7%) |
| M15 | Regional extension | measured no-op — the gate self-limits (P1); default off |
| M16 | Pre-registered virgin universe | CONFIRMS: Δ+0.002/+0.016, 307 untouched OOS months incl. two bears |
| M19 | Real-time discipline (labels lagged 2m) | no look-ahead subsidy — regime results improve or hold |

The record's honest summary sentence: *the estimator never hurt out of sample in any test
we ran, improved the regime-dependent objectives on three universes (one virgin and
pre-registered), and refuses — by construction, verifiably — to act where the two eras of
history disagree.*
