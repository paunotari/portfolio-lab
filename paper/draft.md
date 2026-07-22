# Dispersion, Not Method: When Portfolio Optimization Cannot Beat Equal Weight on an Investable Factor Menu

**Working paper — draft v0.2 (2026-07). Prepared for SSRN; target outlets: *Journal of
Portfolio Management* / *Journal of Asset Management*.**

*Author: [owner]. Full reproducibility: every number in this paper is an entry in the
project's critical-findings ledger (MILESTONES M1–M35), names the module that produces it,
and regenerates from public data with one command. Repository: [URL on publication].*

---

## Abstract

We study portfolio construction for the setting a real retail investor occupies: a
**long-only, index-based, factor-tilted equity menu** — 28 MSCI region×factor indices, about
330 monthly observations — and, as a mechanism-revealing contrast, its extension with
non-equity asset classes. We adjudicate the candidate rules with the full checklist a referee
would demand, applied in public: statistical significance for every Sharpe comparison
(Ledoit-Wolf 2008 bootstrap, not the classical Jobson-Korkie test), deflated Sharpe,
backtest-overfitting probability, a Friedman-Nemenyi joint test, leave-one-region-out
re-races, sensitivity grids, real-time label discipline, a pre-registered confirmatory test on
a never-touched universe, and — unusually — two placebo tests aimed at our own signature
feature. Three results survive. **First, the humility result, strengthened:** no rule beats
equal weight with statistical significance (minimum variance's +0.20 annualized Sharpe sits at
p = 0.055), several popular overlays are *significantly worse*, and the three most-cited
"beat-1/N" rules all fail under proper testing on this menu — the Yuan-Zhou (2023) combination
loses outright, Brodie et al.'s (2009) sparse portfolio reaches only p = 0.149, and HERC lands
below both its parents. This concurs with the most recent published replication of DeMiguel et
al. (Gelmini-Uberti, 2024). **Second, structure beats estimation:** equal-risk-contribution
and hierarchical risk parity beat equal weight in 98–100% of rolling windows and in 100% of
window variants of a 90-year proxy race, and hard diversification caps *improve*
out-of-sample results in every grid cell. **Third — the contribution — the reason is the
opportunity set, not the optimizer:** the investable factor menu holds only ~1.3 independent
risk bets (a diversification-ratio-squared of 1.31; long-only factor tilts within a region
correlate 0.885; the covariance is near-singular), so there is almost no dispersion to
exploit and no weighting scheme can manufacture any. The multi-asset contrast confirms the
mechanism: adding Treasuries and gold moves the menu's minimum pairwise correlation from 0.53
to −0.14 and transforms the worst-regime floor. This reconciles the twenty-year 1/N debate —
optimization wins where dispersion exists, as on the dispersed academic datasets of its
defenders, and an investable factor menu has almost none. Finally, we report two **null
results honestly**: a pre-registered regime-conditioned shrinkage estimator, and the macro
regime signal it depends on, each turn out to have no effect resolvable at this sample size
once tested against scrambled-label placebos — published with a power post-mortem rather than
buried. The flagship the apparatus selects, a capped worst-quadrant portfolio over equities,
Treasuries and gold (Sharpe 0.95, 8.7% volatility, −16.7% maximum drawdown, 2009–2026), owes
its record to holding regime-*diverse assets*, not to regime timing.

**Keywords:** portfolio choice, estimation error, naive diversification, diversification
ratio, backtest overfitting, replication, 1/N. **JEL:** G11, C58.

---

> **STRUCTURE NOTE (v0.2 re-framing, 2026-07-22 — delete before submission).** The spine moved
> from "our estimator is the contribution" (v0.1) to "the opportunity set, not the optimizer,
> is why 1/N is hard to beat here — measured, and it reconciles the debate." What each section
> now does:
> - **§2 Related literature** — add the reconciliation frame: the 1/N debate turns on five
>   levers (menu dispersion, estimation inputs/window, turnover, shorting, and the significance
>   bar). Engage the pro-optimization side we previously ignored — Kritzman-Page-Turkington
>   (2010) "the fallacy of 1/N" (blames short estimation windows) and Kirby-Ostdiek (2012)
>   (blames extreme turnover) — and place Gelmini-Uberti (2024) + Yuan-Zhou (2023) as the
>   modern empirical/theoretical trunk. [⚠ read KPT and Kirby-Ostdiek in full before submission
>   — cited at thesis altitude only for now.]
> - **§4.2** the estimator drops from "the contribution" to "a pre-registered construction",
>   pointing forward to its null result.
> - **§5 Results** — NEW central subsection: the dispersion mechanism (DR²=1.31; within-region
>   cross-factor corr 0.885; near-singular covariance; the asset-class contrast 0.53→−0.14).
>   This is now the paper's core, not an aside.
> - **§5.4 / §6** the regime layer and the estimator become the TWO placebo/null subsections
>   (M32 labels, M35 estimator) — reporting the tests that attack our own signature feature is
>   the credibility spine.
> - **§7 Limitations** — the factor menu is the liquid-MSCI-long-only set, not the full factor
>   zoo (no growth/size/low-vol as separate sleeves); DR² predicts more same-beta tilts would
>   not change the verdict, and growth is anti-value (no positive premium) so it is the weakest
>   such objection; size is tested in the 90-year proxy race and low-vol is what min-variance
>   harvests.

## 1. Introduction

Whether portfolio optimization beats naive equal weight is one of the longest-running
unresolved questions in asset allocation, and the disagreement is unusually sharp. DeMiguel,
Garlappi & Uppal (2009) found that across fourteen models and seven datasets nothing
consistently beats 1/N out of sample, and the most recent replication, on the original
datasets extended twenty years through the global financial crisis and the pandemic, reaches
the same verdict (Gelmini-Uberti, 2024). Yet an equally serious literature insists the result
is an artifact: that 1/N wins only because the optimizers were fed short-window sample means
(Kritzman, Page & Turkington, 2010) or were tested in high-turnover forms that transaction
costs destroy (Kirby & Ostdiek, 2012), and that properly specified optimization does beat
equal weight. Both sides show real out-of-sample evidence. The debate has stayed open because
it has been argued as though it had a single answer.

We argue it does not, and we locate the answer. Whether optimization can beat 1/N turns on
five things: the dispersion of the asset menu, the length and quality of the estimation
inputs, how much turnover the strategy generates, whether short sales and leverage are
permitted, and how demanding a bar "beat" must clear. Fix those five at the position a real
retail investor occupies — a **long-only, index-based, factor-tilted equity menu**, realistic
data length, transaction costs charged, statistical significance required — and the question
has a clean and, we show, *inevitable* answer. On that menu no weighting rule beats 1/N, and
the reason is not any optimizer's weakness: the menu itself holds only about one independent
bet, so there is no dispersion for any scheme to exploit. The literature's optimization
defenders are right on their datasets, where dispersion is high; we are right on ours, where
it is not; and the two are not in conflict once the opportunity set is named. This is the
paper's spine, and it is a measurement, not an assertion (Figure F0).

We reach it by fielding the canonical construction rules — and the three most-cited rules
built specifically to beat 1/N — against each other under one honesty protocol, attaching a
p-value to every ranking sentence, and publishing the apparatus: every number below
regenerates from public data by running a named module. Our contributions are:

1. **The reconciling finding: dispersion, not method.** We measure why 1/N is unbeatable on
   an investable factor menu — a diversification ratio of 1.31 independent bets, long-only
   factor tilts co-moving at 0.885, a near-singular covariance — and confirm the mechanism
   with the contrast that adding three asset classes moves the menu's minimum pairwise
   correlation from 0.53 to −0.14. This places the twenty-year 1/N debate on a single axis:
   the opportunity set.
2. **A fully-instrumented adjudication.** As standing diagnostics, not one-off appendices,
   we run sub-period splits, per-region exposure correlations, leave-one-region-out re-races,
   per-sleeve attribution, Ledoit-Wolf (2008) bootstrap inference (the robust successor to
   the Jobson-Korkie test the prior replication uses), deflated Sharpe ratios (Bailey &
   López de Prado 2014), a Friedman-Nemenyi joint test, CSCV backtest-overfitting probability
   (Bailey et al. 2017), and sensitivity grids over costs, refit cadence, constraints,
   bootstrap block length and the covariance estimator. Under it, the three published
   "beat-1/N" rules we field all fail: Yuan-Zhou's (2023) combination loses outright,
   Brodie et al.'s (2009) sparse portfolio reaches only p = 0.149, and HERC lands below both
   its parents.
3. **Two null results, reported not buried.** We build, freeze and pre-register a
   regime-conditioned shrinkage estimator, and we attack it — and the macro regime signal it
   depends on — with two placebo tests aimed at our own signature feature. Both return
   nothing resolvable at this sample size. We report the negative result with a power
   post-mortem rather than a positive spin, because a paper whose thesis is *run the full
   checklist honestly* cannot hide the answers the checklist returns.

Section 2 places the paper in the five-lever debate. Section 3 describes the data, including
the virgin confirmatory universe. Section 4 specifies the classifier, the pre-registered
estimator, the contestants and the protocol. Section 5 reports the races, the dispersion
mechanism, and the two nulls. Section 6 runs the referee's checklist. Section 7 states
limitations; Section 8 concludes.

## 2. Related literature

**The debate, and its five levers.** The question of whether optimization beats equal weight
has two camps that rarely engage on the same terms. On one side, DeMiguel et al. (2009) and,
most recently, Gelmini-Uberti (2024) find 1/N is not systematically beaten out of sample; on
the other, Kritzman, Page & Turkington (2010) — titling their rebuttal "the fallacy of 1/N" —
and Kirby & Ostdiek (2012) show optimization *can* win. Read together, their disagreement is
not about optimization in the abstract but about experimental conditions, and it resolves into
five levers. (i) *Menu dispersion*: DeMiguel's own explanation, quoted approvingly by
Gelmini-Uberti, is that optimization improves relative to 1/N when idiosyncratic volatility is
high and the covariance is far from singular. (ii) *Estimation inputs*: Kritzman et al. locate
1/N's edge in short-window sample means and report that longer or more plausible inputs reverse
it — a lever Gelmini-Uberti test directly, finding that a growing estimation window helps the
optimizers but still does not produce a systematic win. (iii) *Turnover*: Kirby & Ostdiek
attribute the result to the extreme turnover of the strategies DeMiguel tested and propose
low-turnover "timing" rules that survive transaction costs. (iv) *Short sales and leverage*:
much of the optimization advantage in these studies requires positions a long-only investor
cannot take. (v) *The significance bar*: some pro-optimization evidence is point-estimate or
single-dataset, whereas the humility side demands significance across datasets. Pflug, Pichler
& Wozabal (2012) supply the theory the humility side otherwise lacks — 1/N is optimal under
sufficient model ambiguity — which is exactly the regime a retail investor with a few decades
of data inhabits. Our contribution is to fix all five levers at that retail position and report
the result, rather than to argue one lever in isolation.

**Estimation error and 1/N.** Markowitz (1952) optimality collides with sampling error
(Michaud 1989; Chopra & Ziemba 1993); DeMiguel et al. (2009) quantify the collision: across
14 models and 7 datasets, nothing consistently beats 1/N out of sample. We replicate this on
our menu and — unlike most of the literature — attach the p-values that make "nothing beats"
a statistical statement rather than a table read. Yuan & Zhou (2023) supply the missing
*theory* for that result — the plug-in Sharpe converges to τ·SR with τ = √((1−η)/(1+η/SR²)),
η = N/T, and under a one-factor structure 1/N is asymptotically optimal as N grows — and then
beat 1/N with a closed-form combination of the plug-in GMV and 1/N. We field their rule
(§5.1): on our menu it loses, which their own Proposition 3 and their T = 360 estimation-window
requirement predict in advance. Our humility result therefore survives its strongest published
challenger, adjudicated with that challenger's mathematics rather than against it.

**Selection, not just weighting.** A weighting study is only as interesting as its menu.
Ilmanen & Kizer (2012) give the selection-side result with the best evidence — average
correlation across *factor* constituents near zero against roughly 0.4 across asset classes —
which is why a factor-spanning menu diversifies more per slot than another regional equity
wrapper. We measure our own menu with the practitioner metric this literature standardized:
the Choueifaty & Coignard (2008) diversification ratio, whose square estimates the number of
independent risk bets. Our 28 equity sleeves are 1.31 such bets; the four-sleeve
minimum-variance portfolio is 1.28. Three non-equity proxy sleeves move the menu's minimum
pairwise correlation from 0.53 to −0.14. Hurst, Ooi & Pedersen's century of trend-following
evidence points at the diversifier we do not yet hold, strongest precisely in prolonged equity
bears; we test the *rule* form of it here (§5.1) and flag the *asset* form as the more
promising route.

**Selecting versus spreading.** Brodie et al. (2009) regularize Markowitz with an ℓ1 penalty
that both stabilizes the ill-conditioned problem and sparsifies the solution, reporting
portfolios that outperform 1/N on 48 industry portfolios. Their own analysis notes that under
a budget constraint the ℓ1 term is a short-position penalty and is therefore inert once
shorting is barred — so their long-only winner is minimum variance at a target return, the
same Jagannathan-Ma family as our caps. That makes them the *selecting* sibling of our
*spreading* constraints, and the natural contestant to field: we do so with the two things
their claim lacked, a Sharpe-difference test and transaction costs. DeMiguel, Garlappi,
Nogales & Uppal (2009) are the norm-constrained cousin of the same lineage.

**Structure over estimation.** Risk-parity/ERC (Maillard, Roncalli & Teïletche 2010; Asness,
Frazzini & Pedersen 2012), hierarchical risk parity (López de Prado 2016), and
minimum-variance (Clarke, de Silva & Thorley 2006), whose empirical success the
low-volatility anomaly explains (Haugen & Baker 1991; Frazzini & Pedersen 2014). Our
attribution section makes that explanation concrete: minimum variance on our menu earns 82%
of its out-of-sample return in Quality sleeves. Antonov, Lipton & López de Prado (2024) supply
the theory the 2016 proposal lacked — analytical expressions showing HRP's weights carry less
estimation-induced noise than plug-in Markowitz's — which is the mechanism our nine-decade
race measures. Raffinot (2018) hybridizes the two structural families as HERC: Ward linkage,
a gap-index cluster count, and equal-risk-contribution splits down the hierarchy. We field it
in both linkages, since linkage is a hyperparameter and reporting only the flattering one is
how hyperparameters get hidden.

**The institutional foil.** Boyd, Johansson, Kahn, Schiele & Schmelzer (2024) show what
Markowitz looks like when the inputs are there: one convex program carrying holding and
transaction costs, factor risk models, and explicit robustness terms against forecast
uncertainty. Their position — that the failures blamed on Markowitz are failures of inputs
and naive implementations — is compatible with ours and sharpens it. This paper is about the
opposite regime: T ≈ 330 months, no live forecasts, no engineering budget. At that data scale
the correct robustness term degenerates into exactly what we test — structure, constraints,
and cross-era shrinkage.

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
al. (2017) for the probability of backtest overfitting; Demšar (2006) for the Friedman /
Nemenyi protocol that tests a dozen contestants *simultaneously* rather than as a stack of
pairwise comparisons; Politis & Romano (1994) for the stationary bootstrap our scenario
validator uses. All five are implemented, not cited. Ledoit & Wolf's (2020) analytical
nonlinear shrinkage enters as a sensitivity dimension on the covariance estimator that every
risk number in the study rides on.

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

### 4.2 A pre-registered regime-conditioned estimator

We build, freeze and pre-register a transparent estimator for the noisiest objects in the
whole exercise — per-regime conditional means (30–90 monthly observations per cell). We
describe it here because §5.6 reports, honestly, that it has **no effect resolvable at this
sample size**; the construction and its null result are inseparable and both belong in the
record. Full formal treatment in the repository's `estimator.md`; the two operative lines, for a
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
targeting (Moreira & Muir 2017) and binary trend overlays (Faber 2007 10-month SMA;
Antonacci dual momentum); worst-quadrant maximin, unconstrained and under the diversified
caps (per-sleeve ≤25%, look-through geographic ≤40%, factor ≤40%); and the all-weather
diversified maximin on the menu extended with Treasury/gold/cash proxies. We also field the
three most-cited "beat-1/N" rules as contestants, to test them rather than cite them: the
**Yuan-Zhou (2023) GMV combination** (their closed-form shrinkage of the plug-in
global-minimum-variance portfolio toward 1/N), the **Brodie et al. (2009) sparse portfolio**
(which in its long-only form reduces exactly to minimum variance at a target return, the L1
penalty being inert), and **HERC** (Raffinot 2018, ERC on HRP's topology, both linkages).
Raw full-sample mean returns are forbidden as objective inputs throughout.

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
than plain 1/N (p = 0.009), and four contestants lose significantly to the winner. This
holds under a joint test as well as the pairwise ones: a Friedman test on 12-month block
ranks rejects the null that the ordering is noise (χ² = 46.6, p = 0.0001), yet the Nemenyi
critical difference clears no contestant past 1/N — the ranking is real, the gap to equal
weight is not. Deflated Sharpes ≥ 0.98 clear the multiplicity bar; the CSCV probability that
the in-sample-selected contestant is no better than the OOS median is 33% — real selection
information, far from certainty.

The three most-cited rules designed to beat 1/N do not, on this menu. The **Yuan-Zhou (2023)
combination loses outright** (0.74 vs 0.83, p = 0.45) — its own theory predicts this where
the estimation window is short and the menu one-factor-dominated, and we declared the
prediction before running. **Brodie et al.'s (2009) sparse portfolio** reaches third place
(0.93) but only p = 0.149 — their "significantly and consistently" does not survive the
Sharpe-difference test and transaction charge they never applied. **HERC** lands below both
its parents. Two mechanical facts explain why nothing separates: the contestants' out-of-
sample returns are 0.93–0.998 correlated with one another (HRP and ERC at 0.998 are one
portfolio under two names; Brodie and minimum variance at 0.975 earn from the same USA
Quality sleeve), so the 17-row table is roughly four distinct strategies — a Sharpe test
cannot pull apart series that move together this closely. Attribution completes the picture:
minimum variance earns **82% of its out-of-sample return in Quality sleeves** (USA 52%,
World 30%) — the low-volatility-anomaly mechanism made visible; it is a defensive factor bet
wearing an optimizer's name. This concurs with the most recent published replication of
DeMiguel et al.: Gelmini-Uberti (2024), on the original datasets extended twenty years, also
find no strategy that beats 1/N across datasets and metrics, and note that the strategies
that do win individual cells owe it to higher idiosyncratic dispersion — the mechanism
Section 5.4 makes central.

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

### 5.4 The reason is the opportunity set, not the optimizer (M18, M27, M34)

Why does no weighting rule beat 1/N here, when the literature's optimization defenders show
that it can? Because on an investable long-only factor menu there is almost nothing to
optimize. We measure it three ways (Figure F0). **First, correlation structure:** the
highest-correlated cut of the entire menu is *same region, different factors* — value,
momentum and quality within one country co-move at 0.885, higher than the same factor across
regions (0.786) or pure market beta across regions (0.821). Long-only factor tilts do not
decorrelate, because each index is roughly its parent market plus a small tilt; the market
beta dominates. The three non-equity proxies are the only genuinely different bets on the
menu: Treasuries correlate −0.115 with the 28 equity sleeves, gold −0.007. **Second,
independent bets:** the Choueifaty-Coignard diversification ratio squared — the effective
number of independent risk bets — is **1.31** for the equal-weighted equity menu, and **1.28**
for the four-sleeve minimum-variance portfolio. The engine whose entire job is to exploit
correlations to cancel risk, holding a quarter as many sleeves, finds no more independent
bets than naive diversification does. Twenty-four extra equity sleeves buy 0.03 of a bet;
the first principal component alone explains 77% of variance and the covariance matrix is
near-singular (smallest eigenvalue 3×10⁻⁷). **Third, the contrast that proves the
mechanism:** adding the three asset-class proxies moves the menu's minimum pairwise
correlation from 0.53 to −0.14 and its diversification ratio to 1.43 — three sleeves buying
more independent-bet content than twenty-eight equity sleeves did.

This is the paper's central claim, and it reconciles the twenty-year debate. Optimization
beats 1/N exactly where there is dispersion to exploit — on the industry and factor-portfolio
datasets of its defenders, where idiosyncratic volatility is high and the covariance is
well-conditioned (Gelmini-Uberti's own explanation, §2). An investable factor menu is the
opposite regime: one dominant bet, near-singular covariance, no dispersion for any weighting
scheme to convert into an edge. The disagreement in the literature is not about method; it is
about the opportunity set, and the retail factor investor sits squarely in the region where
1/N cannot be beaten.

### 5.5 A worst-case objective over a regime-diverse menu (M6, M7, M32, M35)

The one construction that measurably changes the risk profile does so through the *menu*, not
through regime information. Within equities alone, the stagflation floor *was* a concentrated
Value bet — forcing diversification collapses it (+0.31→+0.02%/month). Extending the menu with
Treasuries and gold restores the floor at half the volatility (century-scale shape evidence: a
static all-weather archetype returned +9.8% through OPEC 1973-74 while 60/40 lost 28.5%). As a
walk-forward contestant the resulting flagship — a capped worst-quadrant portfolio over
equities, Treasuries and gold — delivers **Sharpe 0.95 at 8.7% volatility, maxDD −16.7%**, is
statistically indistinguishable from the era-flagged winner (p = 0.70) at two-thirds of its
volatility, and holds the lowest drawdown in the table.

Those numbers stand; their *explanation* is where we correct ourselves, using two placebo
tests on our own signature feature (§5.6). The worst-quadrant objective maximizes the mean of
the worst of four macro partitions of history — but that objective is a robustness device even
when the partitions are meaningless. A capped worst-case allocation over a menu that contains
genuinely negatively-correlated assets is pushed toward those assets under *any* four-way
partition, because they are what a worst-case floor rewards. The flagship's record is the
regime-*diverse menu* (M6, and the dispersion of §5.4), not knowledge of the regime. The
practical statement survives fully: to buy a shallow-drawdown floor at this data scale, change
what you hold, not how you time it.

### 5.6 Two null results, reported not buried (M32, M35)

The regime layer is this paper's most attackable feature, so we attack it ourselves with
permutation tests and report what they return. **The labels (M32):** re-running the entire
walk-forward 80 times with the macro-state labels scrambled — a circular rotation that
preserves marginal frequencies, run lengths and the transition matrix exactly, destroying only
the alignment between a month's label and its returns — the maximin family performs no better
with real labels than with random ones. On both metrics (net Sharpe and the realized
worst-real-quadrant floor the objective actually optimizes), across twelve cells, the best
permutation p is 0.195 and the real labels sit *below* the scrambled mean in seven of twelve;
the average randomly-labelled flagship achieved a *better* worst-quadrant floor than the real
one. Equal weight, which consumes no labels, is bit-identical across all 81 runs (a leak
check). **The estimator (M35):** a paired difference-of-differences — the anchor switched off
and on within each replicate on the same labels — finds every real-arm effect under half a
null standard deviation and the estimator "helping" in 45–60% of replicates, a coin flip. The
pre-registered improvement of §6.3 turns out to sit inside the noise band of menu composition
that the same ledger entry had always acknowledged (±0.01–0.02 Sharpe).

We report these because a checklist paper that ran the tests and hid the answers would refute
its own thesis. The regime classifier's *descriptive* value — which quadrant we occupy, how
factors have behaved per state — is a different claim, not tested here. What the placebos
settle is narrow and clean: the macro signal does not earn its place in the *allocation*, and
the honest contribution is the negative result plus the apparatus that produced it.

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
2026-05) containing the dot-com bust and the global financial crisis. Verdict on its own
terms: **CONFIRMS**. But we owe the reader the power post-mortem that §5.6 forces: those
declared thresholds (+0.002, +0.016) sit *inside* the ±0.01–0.02 noise band that menu
composition alone produces, as the scrambled-label distribution later measured (null standard
deviation 0.03–0.10). The pre-registration discipline was sound and we keep it as an example;
the lesson we draw against ourselves is that its thresholds were set below the noise floor, so
clearing them was a correctly-run test of a question it did not have the power to answer. Any
future confirmatory test in this program must declare thresholds against a *measured* null,
not a hoped-for effect size. Secondary readouts, reported ungated: nothing beats 1/N
significantly there either (best p = 0.246); the equity-only maximin family ranks last through
the two bears — consistent with Section 5.4.

## 7. Limitations

The modern OOS window contains no prolonged bear; the proxy race and the virgin universe
(two bears) are the complements, but proxies are frictionless constructs. The classifier
carries a mild full-sample z-normalization (scale, never direction; bounded by the
real-time lag test) and uses revised rather than vintage FRED values — an ALFRED-vintage
replay is future work. **MSCI factor indices carry pre-launch backfill**, and the concern is real: an index provider
launching a factor index in the mid-2010s computes its earlier history with the benefit of
knowing which factor definitions had worked. Two defenses, one measured and one structural.
Measured: restricting the walk-forward's scoring to the live-index era (2015 onward, 138
months) leaves the hierarchy intact — minimum variance still first, the all-weather flagship
still second, HRP still above ERC still above 1/N — so no conclusion in this paper depends on
backfilled months. Structural: every headline result replicates on Ken French portfolios, which
are continuously computed from the underlying stock data and have no launch date to backfill
from — the 90-year race, the nine-sleeve international confirmatory test, and the 66-year
regime evidence the estimator draws on. What backfill can still do is inflate the *level* of
factor-sleeve returns before 2015; it cannot manufacture the relative ordering of construction
rules applied to the same sleeves, which is the object of study.
Costs are flat 10 bps on refit turnover; within-interval drift turnover is uncharged but
measured immaterial (largest Sharpe overstatement 0.002; a buy-and-hold implementation of the
same weight schedules preserves the ranking exactly); taxes, spreads and tracking error are
not modeled. The deflated-Sharpe trial count includes fielded contestants,
not every development-time variant — the pre-registered test is the stronger multiplicity
defense. All results are USD. Equal weight is menu-relative and the menu is a design layer:
our selection principle — span distinct risk sources, measured as effective bets — is
stated, not optimized. That layer is where the largest unexploited gain sits, and we say so
with a number rather than a hope: our 28 equity sleeves carry a diversification ratio squared
of 1.31 independent risk bets, and the four-sleeve minimum-variance portfolio carries 1.28.
Adding three non-equity proxy sleeves moves the menu's minimum pairwise correlation from 0.53
to −0.14 and its first principal component from 77% to 69% — three slots buying more than
twenty-eight. A study of weighting rules on a menu of roughly one bet is, by construction,
a study of small differences, and readers should discount our effect sizes accordingly.

Our factor menu is also the set with liquid, long-only MSCI indices — market, value,
momentum and quality — not the full factor zoo; a referee will ask about growth, size or low
volatility. The diversification-ratio result answers the class of objection directly: more
long-only tilts on the same market beta would land at the same ~0.88 correlation as the ones
we hold and add no independent bets, so the verdict is coverage-robust. Growth is the weakest
such case, being the low-premium short leg of value rather than a separate premium; size *is*
tested, in the 90-year proxy race on Fama-French size×value portfolios; and low volatility is
precisely what the minimum-variance contestant harvests. What changes the menu's character is
not another equity factor but another asset class — which is the finding, and the bridge to a
sequel on selection rather than weighting. Nothing here is fitted or machine-learned; the flip
side is that nothing exploits information beyond counting, shrinking and constraining.

## 8. Conclusion

Two decades of argument over whether optimization beats equal weight have a resolution this
paper can state precisely: it depends on the opportunity set, and on an investable long-only
factor menu — where a real retail investor lives — the set holds one dominant bet, so no
weighting rule can beat 1/N and, tested properly, none does. That is not a limitation of any
optimizer; it is a property of the menu, which we measure (a diversification ratio of 1.31,
factor tilts co-moving at 0.885, a near-singular covariance) rather than assert. The
optimization defenders are right on their own datasets, where dispersion is high; both can be
true because they are describing different opportunity sets, and we say which one the retail
factor investor occupies.

What survives our full checklist — nine decades, three universes, pre-registration, real-time
discipline, region removal, sensitivity grids, and two placebos aimed at our own signature
feature — is disciplined and modest: risk-structure engines edge return-estimation ones but
not significantly; hard caps help; and a menu holding genuinely different asset classes, not
another equity factor, is what buys a shallow-drawdown floor. What does *not* survive is
equally part of the record: neither the macro-regime signal nor the pre-registered estimator
built on it has an effect resolvable at this sample size, and we report that with a power
post-mortem rather than a positive spin. The apparatus's last word is a p-value on our own
best idea as much as on the literature's. At retail data scale, the honest contribution is
not a better portfolio — it is knowing, and being able to prove, that the menu is where the
question actually lives.

## References

Ang, A. & Bekaert, G. (2002). International Asset Allocation with Regime Shifts. *RFS* 15.
Ang, A. & Bekaert, G. (2004). How Do Regimes Affect Asset Allocation? *FAJ* 60(2).
Antonacci, G. (2014). *Dual Momentum Investing.* McGraw-Hill.
Antonov, A., Lipton, A. & López de Prado, M. (2024). Overcoming Markowitz's Instability with
the Help of the Hierarchical Risk Parity. *Transactions of ADIA Lab* 1.
Asness, C., Frazzini, A. & Pedersen, L. (2012). Leverage Aversion and Risk Parity. *FAJ* 68(1).
Bailey, D. & López de Prado, M. (2014). The Deflated Sharpe Ratio. *JPM* 40(5).
Bailey, D., Borwein, J., López de Prado, M. & Zhu, Q. (2017). The Probability of Backtest
Overfitting. *Journal of Computational Finance* 20(4).
Black, F. & Litterman, R. (1992). Global Portfolio Optimization. *FAJ* 48(5).
Boyd, S., Johansson, K., Kahn, R., Schiele, P. & Schmelzer, T. (2024). Markowitz Portfolio
Construction at Seventy. arXiv:2401.05080.
Brodie, J., Daubechies, I., De Mol, C., Giannone, D. & Loris, I. (2009). Sparse and Stable
Markowitz Portfolios. *PNAS* 106(30).
Choueifaty, Y. & Coignard, Y. (2008). Toward Maximum Diversification. *JPM* 35(1).
Chopra, V. & Ziemba, W. (1993). The Effect of Errors in Means, Variances, and Covariances
on Optimal Portfolio Choice. *JPM* 19(2).
Clarke, R., de Silva, H. & Thorley, S. (2006). Minimum-Variance Portfolios in the U.S.
Equity Market. *JPM* 33(1).
DeMiguel, V., Garlappi, L., Nogales, F. & Uppal, R. (2009). A Generalized Approach to
Portfolio Optimization: Improving Performance by Constraining Portfolio Norms.
*Management Science* 55(5).
DeMiguel, V., Garlappi, L. & Uppal, R. (2009). Optimal Versus Naive Diversification. *RFS* 22(5).
Demšar, J. (2006). Statistical Comparisons of Classifiers over Multiple Data Sets. *JMLR* 7.
Faber, M. (2007). A Quantitative Approach to Tactical Asset Allocation. *Journal of Wealth
Management* 9(4).
Frazzini, A. & Pedersen, L. (2014). Betting Against Beta. *JFE* 111(1).
Frost, P. & Savarino, J. (1986). An Empirical Bayes Approach to Efficient Portfolio
Selection. *JFQA* 21(3).
Gelmini, M. & Uberti, P. (2024). The Equally Weighted Portfolio Still Remains a Challenging
Benchmark. *International Economics* 179, 100525.
Guidolin, M. & Timmermann, A. (2007). Asset Allocation under Multivariate Regime
Switching. *JEDC* 31(11).
Hurst, B., Ooi, Y. H. & Pedersen, L. (2017). A Century of Evidence on Trend-Following
Investing. *JPM* 44(1).
Ilmanen, A. & Kizer, J. (2012). The Death of Diversification Has Been Greatly Exaggerated.
*JPM* 38(3).
Haugen, R. & Baker, N. (1991). The Efficient Market Inefficiency of Capitalization-Weighted
Stock Portfolios. *JPM* 17(3).
Jagannathan, R. & Ma, T. (2003). Risk Reduction in Large Portfolios: Why Imposing the Wrong
Constraints Helps. *JF* 58(4).
Jegadeesh, N. & Titman, S. (1993). Returns to Buying Winners and Selling Losers. *JF* 48(1).
Jobson, J. & Korkie, B. (1981). Performance Hypothesis Testing with the Sharpe and Treynor
Measures. *JF* 36(4).
Jorion, P. (1986). Bayes-Stein Estimation for Portfolio Analysis. *JFQA* 21(3).
Judge, G. & Bock, M. (1978). *The Statistical Implications of Pre-test and Stein-rule
Estimators in Econometrics.* North-Holland.
Kirby, C. & Ostdiek, B. (2012). It's All in the Timing: Simple Active Portfolio Strategies
that Outperform Naïve Diversification. *JFQA* 47(2).
Kritzman, M., Page, S. & Turkington, D. (2010). In Defense of Optimization: The Fallacy of
1/N. *FAJ* 66(2).
Ledoit, O. & Wolf, M. (2004). Honey, I Shrunk the Sample Covariance Matrix. *JPM* 30(4).
Ledoit, O. & Wolf, M. (2008). Robust Performance Hypothesis Testing with the Sharpe Ratio.
*Journal of Empirical Finance* 15(5).
Ledoit, O. & Wolf, M. (2020). Analytical Nonlinear Shrinkage of Large-Dimensional Covariance
Matrices. *Annals of Statistics* 48(5).
López de Prado, M. (2016). Building Diversified Portfolios that Outperform Out-of-Sample.
*JPM* 42(4).
Maillard, S., Roncalli, T. & Teïletche, J. (2010). The Properties of Equally Weighted Risk
Contribution Portfolios. *JPM* 36(4).
Markowitz, H. (1952). Portfolio Selection. *JF* 7(1).
Michaud, R. (1989). The Markowitz Optimization Enigma: Is 'Optimized' Optimal? *FAJ* 45(1).
Moreira, A. & Muir, T. (2017). Volatility-Managed Portfolios. *JF* 72(4).
Pflug, G., Pichler, A. & Wozabal, D. (2012). The 1/N Investment Strategy Is Optimal under
High Model Ambiguity. *Journal of Banking & Finance* 36(2).
Politis, D. & Romano, J. (1994). The Stationary Bootstrap. *JASA* 89(428).
Raffinot, T. (2018). The Hierarchical Equal Risk Contribution Portfolio. SSRN 3237540.
Swinkels, L. (2019). Treasury Bond Return Data Starting in 1962. *Data* 4(3).
Tibshirani, R., Walther, G. & Hastie, T. (2001). Estimating the Number of Clusters in a Data
Set via the Gap Statistic. *JRSS-B* 63(2).
Yuan, M. & Zhou, G. (2023). Why Naive Diversification Is Not So Naive, and How to Beat It?
*JFQA* 58(7).

## Appendix A — Reproducibility statement

Every table and figure regenerates from public data: MSCI end-of-day index levels, FRED,
the Ken French data library, and an LBMA gold mirror. The repository ships (i) the
critical-findings ledger (M1–M28), where each claim names its producing module, inputs and
validation status; (ii) a 16-stage pipeline (`python scripts/run_pipeline.py`) plus CLI
modules for the expensive probes (leave-one-region-out, sensitivity grids, the confirmatory
test); (iii) 71 unit/integrity tests; and (iv) the frozen snapshot of the confirmatory
dataset and the pre-registration commit that precedes its single run in the git history.

## Appendix B — Figure and table plan (to be exported from the cached CSVs)

**F0 (the pillar) — the dispersion figure**: Panel A, mean pairwise correlation by menu cut
(same-region/different-factors 0.885 the highest, vs Treasuries −0.115 and gold −0.007);
Panel B, independent risk bets (DR²) across the equity menu (1.31), minimum variance's four
sleeves (1.28) and the asset-class-extended menu (1.43). This is Section 5.4 in one image and
opens the results. F1 walk-forward cumulative race · F2 Sharpe-edge bars with bootstrap p
labels (now including the three defeated challengers) · F3 leave-one-region-out rank paths ·
F4 virgin-universe A/B bars · F5 sensitivity grid lines + block-length p panel · F6
attribution stacked bars · **F7 (to build) the two placebo null distributions** (real value
inside the scrambled-label histogram, both metrics) · T1 modern race with inference columns ·
T2 90-year race and window dispersion · T3 grids · T4 confirmatory protocol and outcome.
