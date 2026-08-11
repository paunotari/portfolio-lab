# Robust Portfolio Construction at Retail Data Scale: Structure, Constraints, and Regime-Diverse Assets

*A working paper of the portfolio_lab project. Every number below is traceable: the
[MILESTONES.md](MILESTONES.md) ledger entry (M1–M36) names the producing module, the input
data, and the validation status. Regenerate any figure by running the named module.*

> ## ⚠ THIS DOCUMENT IS STALE (as of 2026-07-22) — read `paper/draft.md` v0.2 instead
>
> It reflects the **v0.1 framing**, in which the era-agreement-gated estimator was the
> candidate contribution. Three later results overturned that framing. Until this file is
> rewritten, treat the following as corrections that override anything below:
>
> 1. **The estimator is NOT a contribution — it is a reported null result (M35).** A paired
>    placebo A/B finds every real-arm effect under half a null standard deviation and the
>    estimator "helping" in 45–60% of replicates (a coin flip). M10's claimed +0.012 was
>    always smaller than its own acknowledged ±0.01–0.02 menu-composition noise band. M16's
>    pre-registered thresholds sat below the measured noise floor — a correctly-run test of a
>    question it lacked the power to answer.
> 2. **The macro regime labels add nothing to allocation (M32).** Eighty scrambled-label
>    walk-forwards: best permutation p = 0.195 across twelve cells, and the real labels sit
>    BELOW the scrambled mean in seven of them. The flagship's record comes from the
>    regime-DIVERSE MENU (M6), not from knowing the regime. Every "regime-aware portfolio"
>    phrasing below should read "a capped worst-case objective over a regime-diverse menu".
> 3. **The spine is now dispersion, not method (M36).** The 1/N debate has two answers and
>    menu dispersion decides which applies; the investable factor menu holds DR² = 1.31
>    independent bets (M27), so no weighting rule can help there. That — plus the defeat of
>    three published "beat-1/N" rules (M26/M28/M29) and the two placebos above — is what the
>    paper now argues.
>
> The measured NUMBERS below stand; the framing and the attribution do not.

---

## Abstract

We ask which portfolio-construction rules an individual investor with realistic data (≈27
years of monthly index returns) should actually trust. Racing the canonical rules — equal
weight, minimum variance, equal risk contribution (ERC), hierarchical risk parity (HRP),
mean-variance-derived blends, momentum, and volatility targeting — under a strict walk-forward
protocol (expanding window, training-only estimation, net of transaction costs), and then
re-racing them over 90 years of proxy data, we find: (1) no estimation-based rule reliably
beats equal weight on the modern window, replicating DeMiguel et al. (2009); (2) the modern
window's apparent winner, minimum variance, is era-specific — over nine decades it falls to
last among structural rules, while HRP and ERC beat equal weight in 100% of window variants;
(3) diversification constraints (per-sleeve, look-through geographic, and factor caps)
*improve* out-of-sample performance — constraints act as implicit shrinkage (Jagannathan & Ma
2003), measured live; (4) regime-conditioned per-quadrant behavior is structural, not sample
noise — 15 of 16 factor×quadrant patterns hold from 1960 to today; and (5) a
worst-macro-quadrant maximin portfolio over a menu extended with bonds, gold and cash — with
its noisy per-quadrant inputs shrunk toward six decades of evidence — achieves the best
risk-adjusted out-of-sample result of any construction we field that is not itself
era-flagged: Sharpe 0.95 at 8.7% volatility and −16.7% maximum drawdown (2009–2026). We then
subject every claim to the referee's checklist: (6) **no Sharpe edge over equal weight is
statistically significant at 5%** (Ledoit-Wolf 2008 block bootstrap; the winner's edge is
p≈0.055, and crosses 5% only under the least conservative block length) while several
overlays are significantly *worse*; the probability of backtest overfitting in our contestant
selection is 33% (CSCV); (7) the input-shrinkage estimator — pre-registered and frozen —
**confirms on a virgin Ken French international universe** whose out-of-sample window
contains two prolonged bears; and (8) results survive real-time label lags, the live-index
era, leave-one-region-out menus, and cost/refit/cap grids. The practical thesis: **at retail
data scale, allocate by structure, diversify by constraint, extend the menu across
regime-diverse asset classes, shrink every estimated input toward the longest history whose
sign agrees — and keep the equal-weight benchmark on screen, because your edge over it is
probably not provable.**

## 1. The question

Given ~330 monthly observations of 28 equity region/factor indices — the data a serious
individual investor can actually assemble — which portfolio-distribution rules deserve trust?
The literature warns that this is an estimation-error regime: errors in expected returns cost
~11× errors in risk estimates (Chopra & Ziemba 1993), optimizers amplify exactly those errors
(Michaud 1989), and sample-based mean-variance needs on the order of 3,000 months to reliably
beat equal weight (DeMiguel, Garlappi & Uppal 2009). Our contributions are (i) a disciplined,
fully reproducible adjudication with the referee's full checklist applied — significance,
overfitting probability, exposure decomposition, sensitivity grids; and (ii) a simple,
transparent estimator for regime-conditioned inputs — **era-agreement-gated long-history
shrinkage** ([estimator.md](estimator.md)) — validated on a pre-registered universe it never
touched during development.

## 2. Data

- **Modern menu:** 28 MSCI region×factor indices (8 regions × Reference/Momentum/Enhanced
  Value/Quality where available; Japan completed 2026-07 from owner exports with the window
  intact), monthly net-USD total returns, common window 1999-01–2026-06 (330 months);
  look-through sector/country/top-10 weights from factsheets. Measured redundancy: the menu
  contains ≈2.8 effective bets (first PC 77% of variance) — equity selection is saturated,
  and the marginal diversifier is an asset class, not another index (M18).
- **Macro:** 16 FRED indicators feeding a 4-quadrant growth×inflation regime classifier
  (composite z-scored trends; counted Markov transitions — descriptive statistics, no fitting).
- **Long-history proxies (free):** Ken French research factors (1926+) and 6 long-only
  size×value portfolios (1926+); constructed 10y US Treasury total returns from the FRED yield
  (Swinkels-2019 approximation, verified against known years: 2008 +21%, 2022 −16%); LBMA gold
  (1833+, floating from 1971); T-bill returns (1926+). Proxies are research constructs, never
  investable sleeves.
- **The virgin confirmatory universe:** 9 Ken French international sleeves
  (Europe/Japan/Asia-Pacific × market/value/momentum, USD, 1990-11+), never downloaded or
  inspected during estimator development; protocol and thresholds committed to the repository
  before the single run (M16); the data snapshot is frozen in-repo.

## 3. Protocol

All claims pass one honesty pipeline: **expanding-window walk-forward** (120-month warmup,
annual refits), every input re-estimated on training data only, returns **net of 10 bps
one-way transaction costs**, equal weight always in the table. Robustness: shifted-start
window variants (A2); a 90-year re-race on the proxy universe (A1); hand-dated episode replays
(A3); a regime-persistent stationary bootstrap (Politis-Romano 1994) as forward validator —
never as objective. Covariance is always Ledoit-Wolf shrunk; expected returns enter only as a
Black-Litterman posterior around an ERC-implied prior with confidence-bounded views.

## 4. Results

**R1 (M1). The modern window replicates the humiliation result.** No estimation-based
construction beats 1/N net of costs on 2009–2026: balanced mean-variance blend 0.70, momentum
0.77, vol-target overlays ≤0.99, vs 1/N 0.84. Minimum variance tops the table (1.06).

**R2 (M2). The modern winner is an era artifact.** Re-raced over 1936–2026 (1,079 OOS months),
minimum variance falls to last among structural rules (0.71) while HRP (0.76) and ERC (0.75)
edge 1/N (0.74). Across shifted-window variants, **HRP and ERC beat 1/N in 100% of windows;
minimum variance in only 25%.** Its modern win is the low-volatility/Quality decade speaking
(consistent with Frazzini-Pedersen's leverage-aversion mechanism), not a structural property.

**R3 (M3). Constraints are alpha-preserving, not alpha-costing.** Adding look-through
geographic caps to the maximin *raised* its OOS Sharpe (0.73→0.84); the full diversified cap
family (sleeve ≤25%, geo ≤40%, factor ≤40%) holds that edge while eliminating the corner
solutions a linear robust objective structurally produces. The same pattern repeats on the
54-year proxy race (capped 0.59 > uncapped 0.56).

**R4 (M4). Regime structure is real.** Extending the quadrant classification to 1960 (789
months, the actual 1970s), 15/16 factor×quadrant sign patterns hold across eras — Value's
stagflation strength (+6.6%/yr over 66 years) and momentum's quadrant profile are structural.
The single flip is the market factor in stagflation: the modern "equities always crash in
stagflation" reading is a 2021-22 artifact (long sample: ≈flat).

**R5 (M6, A3). Equity-only portfolios cannot buy a stagflation floor with diversification.**
Within equities, the robust floor *was* the concentrated Value bet: forcing full
diversification collapses the worst-quadrant floor from +0.31 to +0.02%/month. Extending the
menu with bonds and gold restores it almost free (+0.59 diversified) at half the volatility.
Century-scale shape evidence: through OPEC stagflation 1973-74, a static all-weather archetype
returned **+9.8%** while 60/40 lost 28.5% and pure equity 44.6%.

**R6 (M7, M10). The flagship survives — and improves when its inputs respect history.** As a
walk-forward contestant on its own extended universe, the all-weather diversified maximin
scores OOS Sharpe 0.94; shrinking its per-quadrant means toward six decades of evidence
(sign-agree, month-weighted; cash excluded on principle — rate levels are policy, not
behavior) lifts every maximin variant: the flagship reaches **Sharpe 0.95 at 8.7% volatility,
maxDD −16.7%**, with a 10-year simulated loss probability of 0.4% — the best non-era-flagged
result we field, at the lowest risk in the table.

**R7 (M8, M9). Preferences are priceable; recency is quantifiably toxic.** Formalizing user
profiles as constraint presets prices each preference (the owner's pure-equity growth profile:
−0.8pt CAGR for 7-sleeve factor/geo spread; defensive all-weather: −2.0pt for −2.4pt vol).
And ranking assets by trailing returns points backwards at multi-year horizons (EM Value's 3y
trailing: −4.4%/yr seen from 2020, +39.7%/yr seen from 2026) — which is *why* rules are judged
walk-forward and assets are never judged by their recent tape.

**R8 (M12, M13, M21). Records decompose — and exposures must not impersonate skill.** A
full-period OOS Sharpe can hide a period effect: the equity maximin was 1/N-like before 2024
and its record correlates 0.93 with EM. The leave-one-region-out re-race then *inverts* the
naive reading: dropping EM improves every maximin variant (all-weather 0.93→1.18) — EM
exposure was a net drag the objective was systematically attracted into, not a lucky ride.
Attribution closes the loop on the modern winner: **minimum variance earns 82% of its OOS
return in the Quality sleeves** — it is a defensive-Quality factor bet wearing an optimizer's
name, and we describe it as such. These three diagnostics (sub-period split, region
correlation/LORO, per-sleeve attribution) now run as standing sections of every build.

**R9 (M14, M17, M21). With p-values attached, the honest headline is humility.** Under the
Ledoit-Wolf (2008) studentized block bootstrap, **no contestant beats 1/N significantly at
5%** — the winner's +0.20 annualized edge is p=0.055, crossing 5% only at the least
conservative block length (0.042/0.055/0.066 for b=3/6/10) — while the downside *is*
detectable (1/N+vol-target significantly worse, p=0.009; four contestants lose significantly
to the winner). Deflated Sharpes ≥0.98 clear the multiplicity bar; the probability of
backtest overfitting in selecting among our 11 contestants is 33% (CSCV) — real but moderate
selection information. Across cost (0/10/25 bps), refit (6/12/24m) and cap grids, no ranking
conclusion flips.

**R10 (M16, M19, M20). The estimator survives pre-registration, real time, and the live
era.** With protocol and thresholds committed before a single run, the frozen estimator
improves both maximin variants on the virgin international universe (Δ+0.002/+0.016 over 307
OOS months containing the dot-com bust and the GFC) — and there, too, nothing beats 1/N
significantly. Lagging regime labels two months (the realistic publication constraint) does
not degrade but *improves* every regime-dependent contestant (all-weather 0.93→1.11) — the
shipped results carry no look-ahead subsidy and are, if anything, conservative. Restricting
to the live-index era (2015+) preserves the hierarchy, answering the index-backfill critique
with measurement.

## 5. Limitations

The modern OOS window (2009–2026) contains no prolonged bear market — the proxy race and the
virgin universe (whose OOS spans the dot-com bust and the GFC) are the complements, but
proxies are frictionless research constructs. The regime classifier carries a mild
full-sample z-normalization (scale only, direction never; the real-time lag test bounds its
effect — M19) and uses revised rather than vintage FRED values (an ALFRED-vintage replay is
future work). MSCI factor indices carry pre-launch backfill (mitigated by the live-era split
and the FF replications, M20/M2/M16). Costs are modeled at a flat 10 bps on refit turnover;
within-interval drift turnover is uncharged but measured immaterial (≤0.002 Sharpe;
buy-and-hold ranking identical — M22); taxes, spreads and tracking error are not modeled. The deflated-Sharpe trial count includes fielded contestants, not every variant
examined during development — the pre-registered confirmatory test is the stronger
multiplicity defense. The bond series is an approximation (validated against known years).
All results are USD. Equal weight is menu-relative, and the menu is a design layer: our
selection principle (span distinct risk sources; measured effective bets) is stated, not
optimized. Nothing here is fitted or machine-learned; the flip side is that nothing here
exploits information beyond counting, shrinking and constraining.

## 6. Conclusion

At retail data scale the enemy is estimation error, and every result above is a corollary of
that fact. What survives nine decades of out-of-sample examination is not cleverness but
discipline: **risk-structure engines (ERC/HRP) over return estimation; hard diversification
caps as built-in shrinkage; a menu spanning assets that win in different macro regimes; every
estimated input shrunk toward the longest history whose sign agrees; and a standing
equal-weight benchmark that keeps the whole apparatus honest.** The resulting flagship — a
capped worst-quadrant maximin over equities, Treasuries and gold with history-anchored inputs —
is not the highest-returning portfolio in any single era; it is the construction that never
needed to know which era it was in. And the apparatus's last word is a p-value: the edge of
even the best construction over equal weight is not statistically demonstrable at this data
scale — which is not a failure of the method but the central fact the method is built
around.

## References

Ang & Bekaert (2002, 2004) · Bailey & López de Prado (2014) · Bailey, Borwein, López de
Prado & Zhu (2017) · Black & Litterman (1992) · Chopra & Ziemba (1993) · DeMiguel, Garlappi
& Uppal (2009) · Fama & French (1993) · Frazzini & Pedersen (2014) · Jagannathan & Ma (2003)
· Jegadeesh & Titman (1993) · Jorion (1986) · Ledoit & Wolf (2004, 2008) · López de Prado
(2016) · Maillard, Roncalli & Teïletche (2010) · Markowitz (1952) · Michaud (1989) · Politis
& Romano (1994) · Swinkels (2019) — full canon with verdicts and implementation-grade deep
dives in [literature.md](literature.md); the estimator's formal treatment in
[estimator.md](estimator.md).
