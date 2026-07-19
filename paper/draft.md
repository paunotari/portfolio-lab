# Robust Portfolio Construction at Retail Data Scale: Structure, Constraints, and an Era-Agreement-Gated Shrinkage Estimator for Regime-Conditioned Inputs

**Working paper — draft v0.1 (2026-07). Prepared for SSRN; target outlets: *Journal of
Portfolio Management* / *Journal of Asset Management*.**

*Author: [owner]. Full reproducibility: every number in this paper is an entry in the
project's critical-findings ledger (MILESTONES M1–M21), names the module that produces it,
and regenerates from public data with one command. Repository: [URL on publication].*

---

## Abstract

We ask which portfolio-construction rules an individual investor with realistic data — about
330 monthly observations of 28 MSCI region×factor indices — should actually trust, and we
answer with an adjudication that applies, in public, the full checklist a referee would:
exposure decomposition, leave-one-region-out re-races, statistical significance for every
Sharpe comparison, backtest-overfitting probability, sensitivity grids, real-time label
discipline, and a pre-registered confirmatory test on a universe never touched during
development. Three findings survive everything we throw at them. First, the humility result:
no estimation-based rule beats equal weight with statistical significance at this data scale
— the modern winner's edge (minimum variance, +0.20 annualized Sharpe) sits at a bootstrap
p-value of 0.055, crosses 5% only under the least conservative block length, and attribution
shows the "optimizer" is in fact a defensive Quality bet (82% of its out-of-sample return);
meanwhile several popular overlays are *significantly worse* than equal weight. Second,
structure and constraints beat estimation: equal-risk-contribution and hierarchical risk
parity beat equal weight in 98–100% of rolling windows and in 100% of shifted-start variants
of a 90-year proxy race, and hard diversification caps *improve* out-of-sample performance
in every grid cell (constraints as implicit shrinkage, measured live). Third, our
methodological contribution — **era-agreement-gated long-history shrinkage** for
regime-conditioned inputs, a transparent two-line estimator that pools each regime cell with
66 years of evidence only where both eras agree on the sign — improves every regime-dependent
construction out of sample on three universes, one of them virgin and pre-registered, never
hurts, and refuses by construction to act where history disagrees with itself. The flagship
this machinery selects — a capped worst-quadrant maximin over equities, Treasuries and gold —
delivers Sharpe 0.95 at 8.7% volatility and −16.7% maximum drawdown (2009–2026), is
statistically indistinguishable from the era-flagged winner at two-thirds of its volatility,
and survives lagged regime labels, the live-index era, region removal, and cost/refit/cap
grids.

**Keywords:** portfolio choice, estimation error, regime switching, shrinkage, backtest
overfitting, 1/N. **JEL:** G11, C58.

---

## 1. Introduction

An individual investor who assembles the best data realistically available — a few decades
of monthly index returns — faces an estimation regime the literature has mapped precisely:
errors in expected returns cost roughly eleven times errors in covariances (Chopra & Ziemba
1993); optimizers amplify exactly those errors (Michaud 1989); and sample-based mean-variance
needs on the order of 3,000 months to reliably beat naive equal weight (DeMiguel, Garlappi &
Uppal 2009). Most practitioner responses either ignore this arithmetic or bury it under
backtests whose robustness the reader cannot inspect.

This paper does the opposite. We field the canonical construction rules against each other
under one honesty protocol, we attach a p-value to every ranking sentence, and we publish the
apparatus: every number below regenerates from public data by running a named module. Our
contributions are:

1. **A fully-instrumented adjudication.** Beyond the standard walk-forward, we run — as
   standing diagnostics, not one-off appendices — sub-period splits, per-region exposure
   correlations, leave-one-region-out re-races, per-sleeve return attribution, Ledoit-Wolf
   (2008) bootstrap inference, deflated Sharpe ratios (Bailey & López de Prado 2014),
   CSCV backtest-overfitting probability (Bailey, Borwein, López de Prado & Zhu 2017), and
   sensitivity grids over costs, refit cadence, constraint levels and bootstrap block
   length.
2. **A transparent estimator for regime-conditioned inputs.** Regime-dependent allocation
   needs per-regime expected returns — the noisiest objects in finance (30–90 monthly
   observations per cell). We propose **era-agreement-gated long-history shrinkage**: pool
   each modern regime cell with its 66-year counterpart, weighted by months of evidence,
   *only where the two eras agree on the cell's sign*; translate academic long-short factors
   into long-only sleeve space with a single regression coefficient; exclude on principle
   cells whose long-run "behavior" is a policy level (cash). The estimator is two lines of
   arithmetic, ships with a 16-cell agreement table anyone can audit, and — critically — was
   frozen and then validated on a pre-registered universe it had never touched.
3. **An honest headline.** With inference attached, the correct summary of the horse race is
   that *nothing beats equal weight demonstrably*, several fashionable overlays lose to it
   demonstrably, and the practical edge available at this data scale comes from structure
   (risk-balanced weights), constraints (caps as shrinkage), and menu design (assets that
   win in different macro regimes) — not from estimation.

Section 2 places the paper in the literature. Section 3 describes the data, including the
virgin confirmatory universe. Section 4 specifies the classifier, the estimator, the
contestants and the protocol. Section 5 reports the races with inference. Section 6 runs the
referee's checklist. Section 7 states limitations; Section 8 concludes.

## 2. Related literature

**Estimation error and 1/N.** Markowitz (1952) optimality collides with sampling error
(Michaud 1989; Chopra & Ziemba 1993); DeMiguel et al. (2009) quantify the collision: across
14 models and 7 datasets, nothing consistently beats 1/N out of sample. We replicate this on
our menu and — unlike most of the literature — attach the p-values that make "nothing beats"
a statistical statement rather than a table read.

**Structure over estimation.** Risk-parity/ERC (Maillard, Roncalli & Teïletche 2010; Asness,
Frazzini & Pedersen 2012), hierarchical risk parity (López de Prado 2016), and
minimum-variance (Clarke, de Silva & Thorley 2006), whose empirical success the
low-volatility anomaly explains (Haugen & Baker 1991; Frazzini & Pedersen 2014). Our
attribution section makes that explanation concrete: minimum variance on our menu earns 82%
of its out-of-sample return in Quality sleeves.

**Constraints as shrinkage.** Jagannathan & Ma (2003) showed weight constraints act as
covariance shrinkage. We measure the effect prospectively: capped robust portfolios beat
their unconstrained twins out of sample in every cost/refit/cap grid cell and on a 54-year
proxy race.

**Regime-dependent allocation.** Ang & Bekaert (2002, 2004) established that regimes matter
for allocation; Guidolin & Timmermann (2007, 2008) extended the latent-state machinery. We
differ in kind: our states are observable (a deterministic macro classifier), our
conditional moments are pooled sample means, and our only estimation refinement is
cross-era shrinkage with a tenability gate — nothing is fitted to predict.

**Shrinkage of means.** Jorion (1986) and Frost & Savarino (1986) shrink unconditional means
toward within-sample grand means. Our estimator shrinks *conditional* means toward *another
era's* evidence — the target carries genuinely new information (the actual 1970s) — and adds
a pretest-style gate (Judge & Bock 1978 lineage) that keeps the pooling decision binary,
inspectable, and self-limiting.

**Backtest honesty.** Ledoit & Wolf (2008) for Sharpe inference under heavy tails and
autocorrelation; Bailey & López de Prado (2014) for multiplicity-deflated Sharpe; Bailey et
al. (2017) for the probability of backtest overfitting; Politis & Romano (1994) for the
stationary bootstrap our scenario validator uses. All four are implemented, not cited.

## 3. Data

**Modern menu.** 28 MSCI region×factor indices (ACWI, World, World ex-USA, USA, EM, Europe,
AC Asia ex-Japan, Japan × Reference / Momentum / Enhanced Value / Quality where available),
monthly net-USD total returns, common window 1999-01–2026-06 (330 months), with look-through
sector/country/top-10 weights from factsheets. The menu's measured redundancy disciplines
its interpretation: mean pairwise correlation 0.76, first principal component 77% of
variance, **≈2.8 effective bets** — equity region×factor selection is saturated, and the
marginal diversifier is an asset class, not another index (M18).

**Macro.** 16 FRED indicators feed a 4-quadrant growth×inflation classifier (composite
z-scored trends; empirical Markov transition counts). Descriptive statistics only — no
fitted latent-state model.

**Long history (free, public).** Ken French research factors (1926+) and six long-only
size×value portfolios; 10-year US Treasury total returns constructed from the FRED yield by
the Swinkels (2019) par-bond approximation (sanity: 2008 +21%, 2022 −16%); LBMA gold
(floating from 1971); T-bill returns. Research constructs, never investable sleeves. The
classifier labels months from 1960 (789 months — 2.4× the modern window, containing the
actual 1970s stagflation).

**The virgin confirmatory universe.** Nine Ken French international sleeves —
{Europe, Japan, Asia-Pacific ex-Japan} × {market, value, momentum}, USD, monthly, 1990-11
onward — never downloaded or inspected during development. The test protocol, thresholds
included, was committed to the repository *before* the single run; the data snapshot is
frozen in-repo (Section 6.3).

## 4. Method

### 4.1 The regime layer

Growth and inflation composites (z-scored, sign-adjusted trends of several indicators each)
define four quadrants — Goldilocks, Reflation, Deflationary bust, Stagflation — with soft
probabilities and an empirical monthly transition matrix. Two design facts matter downstream:
the classifier is deterministic and identical across eras; and its per-quadrant factor
patterns are *structural* — 15 of 16 factor×quadrant sign cells agree between 1960–2026 and
the modern window, the single flip being the market factor in stagflation (M4).

### 4.2 The estimator (the candidate contribution)

Full formal treatment in the repository's `estimator.md`; the two operative lines, for a
factor sleeve i in state s with modern conditional excess ê_is over its region Reference,
long counterpart j with 66-year state mean f̄_js, modern-window restriction f̄'_js, sample
sizes n_s (modern) and m_s (long), and mapping coefficient β_j:

    gate:   g_js = 1{ sign(f̄_js) = sign(f̄'_js) }
    blend:  ẽ_is = g_js · [n_s ê_is + m_s β_j f̄_js] / (n_s + m_s) + (1 − g_js) · ê_is

Asset-class sleeves blend toward their own 1962+ state means under the same gate; cash is
excluded on principle (its conditional "mean" is the era's policy-rate level, not
transferable behavior); sleeves without a long counterpart (Quality) stay modern. The blend
feeds (a) the Black-Litterman view vector — answering BL's classic silent question of where
views come from — and (b) the worst-quadrant (maximin) objective's per-regime means.
Reporting always shows raw modern means; blending is for decisions, never for the record.

Interpretation: empirical-Bayes pooling with prior strength equal to months of long
evidence, plus a pretest gate on the crudest sufficient statistic (the sign). Relative to
James-Stein-style optimal shrinkage this trades risk-optimality for a fixed, interpretable
intensity and a binary, auditable pooling decision.

### 4.3 Contestants

Equal weight (1/N); minimum variance; ERC; HRP (all on Ledoit-Wolf 2004 shrunk
covariances); a mean-variance-derived balanced blend around a Black-Litterman posterior;
cross-sectional momentum (Jegadeesh & Titman 1993, 12-1, top-6); unlevered volatility
targeting (Moreira & Muir 2017) overlaid on two bases; worst-quadrant maximin,
unconstrained and under the diversified caps (per-sleeve ≤25%, look-through geographic ≤40%,
factor ≤40%); and the all-weather diversified maximin on the menu extended with
Treasury/gold/cash proxies. Raw full-sample mean returns are forbidden as objective inputs
throughout.

### 4.4 Protocol

Expanding-window walk-forward: 120-month warmup, annual refits, every input re-estimated on
training data only, returns net of 10 bps one-way transaction costs on turnover. Companion
races: a 90-year re-race on the proxy universe (OOS 1936–2026) with shifted-start variants;
hand-dated episode replays; a regime-persistent stationary bootstrap as forward validator,
never objective.

### 4.5 Inference

Ledoit-Wolf (2008) HAC delta-method plus studentized circular block bootstrap (B=4999,
b≈T^⅓, sensitivity b∈{3,6,10}) for every contestant vs 1/N and vs the incumbent winner;
deflated Sharpe with the fielded-roster trial count; CSCV probability of backtest
overfitting (S=16, 12,870 half-splits). Sharpe conventions: rf=0 in internal tables,
excess-over-T-bill in this paper (rankings identical; the headline p-value moves 0.055→0.067
— all conclusions are convention-robust).

## 5. Results

### 5.1 The modern race, with p-values (M1, M14, M21)

Minimum variance tops the table (net OOS Sharpe 1.03 vs 1/N's 0.83, 2009–2026) — and no
contestant's edge over 1/N is significant at 5% (min-variance p_boot = 0.055; every other
p ≥ 0.14). The downside *is* detectable: 1/N + volatility targeting is significantly worse
than plain 1/N (p = 0.009), and four contestants lose significantly to the winner. Deflated
Sharpes ≥ 0.98 clear the multiplicity bar; the CSCV probability that the in-sample-selected
contestant is no better than the OOS median is 33% — real selection information, far from
certainty. Attribution completes the picture: minimum variance earns **82% of its
out-of-sample return in Quality sleeves** (USA 52%, World 30%) — the low-volatility-anomaly
mechanism made visible; it is a defensive factor bet wearing an optimizer's name.

### 5.2 Nine decades: structure generalizes, the modern winner does not (M2)

Re-raced over 1936–2026 on six long-only Fama-French portfolios, minimum variance falls to
last among structural rules (0.71) while HRP (0.76) and ERC (0.75) edge 1/N (0.74); across
shifted-start variants **HRP and ERC beat 1/N in 100% of windows, minimum variance in 25%**.
On the modern menu the same signature appears in rolling windows: ERC/HRP beat 1/N in
98–99% of rolling 3-year windows. Structure is the property that travels.

### 5.3 Constraints are implicit shrinkage, measured live (M3, M17)

The capped maximin beats its unconstrained twin out of sample in *every* sensitivity-grid
cell (+0.115 to +0.132 Sharpe across costs 0/10/25 bps, refits 6/12/24m, cap levels
20/35/35–30/45/45), replicating Jagannathan & Ma prospectively. No grid cell flips any
ranking conclusion; the single frontier is the headline p-value's block-length sensitivity
(0.042/0.055/0.066), which we report as such.

### 5.4 Regime structure pays only with a regime-diverse menu (M4, M6, M7, M10)

Within equities, the stagflation floor *was* the concentrated Value bet — forcing
diversification collapses it (+0.31→+0.02%/month). Extending the menu with Treasuries and
gold restores the floor almost free (+0.59%/month diversified) at half the volatility;
century-scale shape evidence: a static all-weather archetype returned +9.8% through OPEC
1973-74 while 60/40 lost 28.5%. As a walk-forward contestant, the all-weather diversified
maximin scores 0.94; anchoring its per-quadrant inputs with the estimator lifts every
maximin variant — the flagship reaches **0.95 at 8.7% volatility, maxDD −16.7%** — while
concrete corrections show the mechanism working (gold-in-bust tempered from the 2008-11
artifact +1.20 to +0.71%/month; Treasuries-in-bust raised toward six decades of
flight-to-quality). The flagship is statistically indistinguishable from the era-flagged
winner (p = 0.70) at two-thirds of its volatility — which is precisely its case.

## 6. The referee's checklist

### 6.1 Exposure cannot impersonate skill (M12, M13)

Sub-period splits and region correlations expose the equity-only maximin: 1/N-like before
2024, correlation 0.93 with EM, lifted by the 2024+ rally. The leave-one-region-out re-race
then *inverts* the naive story: dropping EM improves every maximin variant (all-weather
0.93→1.18, taking #1) — EM exposure was a net drag the objective was systematically
attracted into. Meanwhile the podium is method, not region: minimum variance is #1 in 8 of
9 menus, the all-weather never leaves the podium, and no overlay beats 1/N on any menu.
The estimator cannot fix the EM attraction — its binding cell (stagflation) is the market's
one era-flipped cell, so the gate correctly refuses the transfer (M15): where the eras
disagree there is nothing transferable, *and the estimator knows it*. The real mitigations
are the caps and these standing diagnostics.

### 6.2 Real time and the live era (M19, M20)

Lagging regime labels two months — the realistic macro-publication constraint — *improves*
every regime-dependent contestant (all-weather 0.93→1.11 at 6.6% volatility): the shipped
results carry no look-ahead subsidy and are, if anything, conservative. Restricting scoring
to the live-index era (2015+, after MSCI's factor indices existed) preserves the hierarchy —
the pre-launch-backfill critique is answered with measurement, alongside the structural
defense that every conclusion replicates on continuously-computed academic data.

### 6.3 The pre-registered virgin universe (M16)

With protocol and thresholds committed before the first run — CONFIRMS if every maximin
variant's anchored-minus-modern ΔSharpe ≥ 0 with at least one > +0.005; REFUTES if any
< −0.02 — the frozen estimator improves both variants on the nine international sleeves:
worst-quadrant +0.002, diversified **+0.016**, over 307 out-of-sample months (2000-11–
2026-05) containing the dot-com bust and the global financial crisis. Verdict: **CONFIRMS**.
Secondary readouts, reported ungated: nothing beats 1/N significantly there either (best
p = 0.246); the equity-only maximin family ranks last through the two bears — consistent
with Section 5.4's core claim that regime robustness must be bought with a regime-diverse
menu, not within equities.

## 7. Limitations

The modern OOS window contains no prolonged bear; the proxy race and the virgin universe
(two bears) are the complements, but proxies are frictionless constructs. The classifier
carries a mild full-sample z-normalization (scale, never direction; bounded by the
real-time lag test) and uses revised rather than vintage FRED values — an ALFRED-vintage
replay is future work. MSCI factor indices carry pre-launch backfill (mitigated in §6.2).
Costs are flat 10 bps on refit turnover; within-interval drift turnover, taxes, spreads and
tracking error are uncharged. The deflated-Sharpe trial count includes fielded contestants,
not every development-time variant — the pre-registered test is the stronger multiplicity
defense. All results are USD. Equal weight is menu-relative and the menu is a design layer:
our selection principle — span distinct risk sources, measured as effective bets — is
stated, not optimized. Nothing here is fitted or machine-learned; the flip side is that
nothing exploits information beyond counting, shrinking and constraining.

## 8. Conclusion

At retail data scale the enemy is estimation error, and everything above is a corollary.
What survives nine decades, three universes, pre-registration, real-time discipline, region
removal and sensitivity grids is not cleverness but discipline: risk-structure engines over
return estimation; hard caps as built-in shrinkage; a menu spanning assets that win in
different regimes; every regime-conditioned input shrunk toward the longest history whose
sign agrees; and a standing equal-weight benchmark. The flagship this selects is not the
highest-returning portfolio in any era — it is the construction that never needed to know
which era it was in. And the apparatus's last word is a p-value: even the best construction's
edge over equal weight is not statistically demonstrable at this data scale. That is not a
failure of the method; it is the central fact the method is built around — and, we argue,
the fact any honest adjudication at this data scale must lead with.

## References

Ang, A. & Bekaert, G. (2002). International Asset Allocation with Regime Shifts. *RFS* 15.
Ang, A. & Bekaert, G. (2004). How Do Regimes Affect Asset Allocation? *FAJ* 60(2).
Asness, C., Frazzini, A. & Pedersen, L. (2012). Leverage Aversion and Risk Parity. *FAJ* 68(1).
Bailey, D. & López de Prado, M. (2014). The Deflated Sharpe Ratio. *JPM* 40(5).
Bailey, D., Borwein, J., López de Prado, M. & Zhu, Q. (2017). The Probability of Backtest
Overfitting. *Journal of Computational Finance* 20(4).
Black, F. & Litterman, R. (1992). Global Portfolio Optimization. *FAJ* 48(5).
Chopra, V. & Ziemba, W. (1993). The Effect of Errors in Means, Variances, and Covariances
on Optimal Portfolio Choice. *JPM* 19(2).
Clarke, R., de Silva, H. & Thorley, S. (2006). Minimum-Variance Portfolios in the U.S.
Equity Market. *JPM* 33(1).
DeMiguel, V., Garlappi, L. & Uppal, R. (2009). Optimal Versus Naive Diversification. *RFS* 22(5).
Frazzini, A. & Pedersen, L. (2014). Betting Against Beta. *JFE* 111(1).
Frost, P. & Savarino, J. (1986). An Empirical Bayes Approach to Efficient Portfolio
Selection. *JFQA* 21(3).
Guidolin, M. & Timmermann, A. (2007). Asset Allocation under Multivariate Regime
Switching. *JEDC* 31(11).
Haugen, R. & Baker, N. (1991). The Efficient Market Inefficiency of Capitalization-Weighted
Stock Portfolios. *JPM* 17(3).
Jagannathan, R. & Ma, T. (2003). Risk Reduction in Large Portfolios: Why Imposing the Wrong
Constraints Helps. *JF* 58(4).
Jegadeesh, N. & Titman, S. (1993). Returns to Buying Winners and Selling Losers. *JF* 48(1).
Jorion, P. (1986). Bayes-Stein Estimation for Portfolio Analysis. *JFQA* 21(3).
Judge, G. & Bock, M. (1978). *The Statistical Implications of Pre-test and Stein-rule
Estimators in Econometrics.* North-Holland.
Ledoit, O. & Wolf, M. (2004). Honey, I Shrunk the Sample Covariance Matrix. *JPM* 30(4).
Ledoit, O. & Wolf, M. (2008). Robust Performance Hypothesis Testing with the Sharpe Ratio.
*Journal of Empirical Finance* 15(5).
López de Prado, M. (2016). Building Diversified Portfolios that Outperform Out-of-Sample.
*JPM* 42(4).
Maillard, S., Roncalli, T. & Teïletche, J. (2010). The Properties of Equally Weighted Risk
Contribution Portfolios. *JPM* 36(4).
Markowitz, H. (1952). Portfolio Selection. *JF* 7(1).
Michaud, R. (1989). The Markowitz Optimization Enigma: Is 'Optimized' Optimal? *FAJ* 45(1).
Moreira, A. & Muir, T. (2017). Volatility-Managed Portfolios. *JF* 72(4).
Politis, D. & Romano, J. (1994). The Stationary Bootstrap. *JASA* 89(428).
Swinkels, L. (2019). Treasury Bond Return Data Starting in 1962. *Data* 4(3).

## Appendix A — Reproducibility statement

Every table and figure regenerates from public data: MSCI end-of-day index levels, FRED,
the Ken French data library, and an LBMA gold mirror. The repository ships (i) the
critical-findings ledger (M1–M21), where each claim names its producing module, inputs and
validation status; (ii) a 16-stage pipeline (`python scripts/run_pipeline.py`) plus CLI
modules for the expensive probes (leave-one-region-out, sensitivity grids, the confirmatory
test); (iii) 63 unit/integrity tests; and (iv) the frozen snapshot of the confirmatory
dataset and the pre-registration commit that precedes its single run in the git history.

## Appendix B — Figure and table plan (to be exported from the cached CSVs)

F1 walk-forward cumulative race · F2 Sharpe-edge bars with bootstrap p labels · F3
leave-one-region-out rank paths · F4 virgin-universe A/B bars · F5 sensitivity grid lines +
block-length p panel · F6 attribution stacked bars · T1 modern race with inference columns ·
T2 90-year race and window dispersion · T3 grids · T4 confirmatory protocol and outcome.
