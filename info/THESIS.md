# Robust Portfolio Construction at Retail Data Scale: Structure, Constraints, and Regime-Diverse Assets

*A working paper of the portfolio_lab project. Every number below is traceable: the
[MILESTONES.md](MILESTONES.md) ledger entry (M1–M10) names the producing module, the input
data, and the validation status. Regenerate any figure by running the named module.*

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
era-flagged: Sharpe 0.95 at 8.7% volatility and −16.7% maximum drawdown (2009–2026). The
practical thesis: **at retail data scale, allocate by structure, diversify by constraint,
extend the menu across regime-diverse asset classes, shrink every estimated input toward the
longest defensible history — and keep the equal-weight benchmark on screen.**

## 1. The question

Given ~330 monthly observations of 21 equity region/factor indices — the data a serious
individual investor can actually assemble — which portfolio-distribution rules deserve trust?
The literature warns that this is an estimation-error regime: errors in expected returns cost
~11× errors in risk estimates (Chopra & Ziemba 1993), optimizers amplify exactly those errors
(Michaud 1989), and sample-based mean-variance needs on the order of 3,000 months to reliably
beat equal weight (DeMiguel, Garlappi & Uppal 2009). Our contribution is not a new estimator;
it is a disciplined, fully reproducible adjudication — plus two menu/input extensions that
measurably move the frontier at this data scale.

## 2. Data

- **Modern menu:** 21 MSCI region×factor indices (7 regions × Reference/Momentum/Enhanced
  Value/Quality where available), monthly net-USD total returns, common window 1999-01–2026-06
  (330 months); look-through sector/country/top-10 weights from factsheets.
- **Macro:** 16 FRED indicators feeding a 4-quadrant growth×inflation regime classifier
  (composite z-scored trends; counted Markov transitions — descriptive statistics, no fitting).
- **Long-history proxies (free):** Ken French research factors (1926+) and 6 long-only
  size×value portfolios (1926+); constructed 10y US Treasury total returns from the FRED yield
  (Swinkels-2019 approximation, verified against known years: 2008 +21%, 2022 −16%); LBMA gold
  (1833+, floating from 1971); T-bill returns (1926+). Proxies are research constructs, never
  investable sleeves.

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

## 5. Limitations

The modern OOS window (2009–2026) contains no prolonged bear market — the proxy race is the
longer-track complement, but proxies are frictionless research constructs. The regime
classifier carries a mild full-sample z-normalization (scale only, direction never). Costs are
modeled at a flat 10 bps; taxes, spreads and tracking error are not. The bond series is an
approximation (validated against known years). All results are USD. Nothing here is fitted or
machine-learned; the flip side is that nothing here exploits information beyond counting,
shrinking and constraining.

## 6. Conclusion

At retail data scale the enemy is estimation error, and every result above is a corollary of
that fact. What survives nine decades of out-of-sample examination is not cleverness but
discipline: **risk-structure engines (ERC/HRP) over return estimation; hard diversification
caps as built-in shrinkage; a menu spanning assets that win in different macro regimes; every
estimated input shrunk toward the longest history whose sign agrees; and a standing
equal-weight benchmark that keeps the whole apparatus honest.** The resulting flagship — a
capped worst-quadrant maximin over equities, Treasuries and gold with history-anchored inputs —
is not the highest-returning portfolio in any single era; it is the construction that never
needed to know which era it was in.

## References

Black & Litterman (1992) · Chopra & Ziemba (1993) · DeMiguel, Garlappi & Uppal (2009) ·
Fama & French (1993) · Frazzini & Pedersen (2014) · Jagannathan & Ma (2003) · Jegadeesh &
Titman (1993) · Ledoit & Wolf (2004) · López de Prado (2016) · Maillard, Roncalli & Teïletche
(2010) · Markowitz (1952) · Michaud (1989) · Politis & Romano (1994) · Swinkels (2019) —
full canon with verdicts and implementation-grade deep dives in [literature.md](literature.md).
