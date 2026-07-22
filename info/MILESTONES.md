# MILESTONES — the critical-findings ledger

Every load-bearing claim this project makes, with its receipts. One entry per finding: what we
claim, the measured numbers, **where to see it**, **what code produces it**, **from what data**,
and its **validation status**. The point is trackable veracity: any entry can be re-derived by
running the named module — if a regeneration ever contradicts an entry, the entry (not the
memory of it) gets corrected. Keep this file current per the standing workflow (root CLAUDE.md):
when a finding is measured, it lands here in the same turn.

**Validation-status vocabulary** (weakest → strongest):
`in-sample` (fitted and judged on the same window) → `OOS modern` (walk-forward, 2009–2026,
net of 10 bps costs) → `OOS windows` (holds across shifted-start window variants, A2) →
`century-scale` (holds on the 1926+/1962+ proxy universe including the real 1970s).

---

## M1 — No optimizer beats 1/N on the modern MSCI menu; min-variance is the OOS winner
**Claim:** on 21 equity sleeves × 330 months, no construction rule reliably beats equal weight;
min-variance takes the best OOS Sharpe (1.06 vs 1/N 0.84); the balanced slider blend (0.70) and
the rule strategies (momentum 0.77, vol-target overlays) do not clear 1/N net of costs.
**See:** `outputs/analytics/optimizer/REPORT_optimizer.md` (walk-forward table) · viz chart 02.
**Code:** `portfolio/validation.py::walk_forward` (+ `portfolio/rules.py` for
momentum/vol-target). **Data:** `data/processed/levels_wide.csv` (MSCI, 1999–2026).
**Status:** OOS modern. Consistent with DeMiguel 2009 (break-even ≈ 3,000 months).

## M2 — Min-variance's win is era-specific; HRP/ERC are the rules that generalize
**Claim:** over ~90 years (OOS 1936–2026) min-variance drops to LAST among the structural rules
(0.71) while HRP (0.76) and ERC (0.75) match/edge 1/N (0.74); across shifted-window variants
**HRP and ERC beat 1/N in 100% of windows** (HRP top rule in 75%), min-variance in only 25%.
**See:** `outputs/analytics/proxy_backtest/REPORT_proxy_backtest.md` and
`REPORT_window_robustness.md` · viz "Evidence · the 90-year race / window robustness".
**Code:** `portfolio/proxy_backtest.py` (`run`, `run_dispersion`). **Data:**
`ff_portfolios_monthly.csv` (6 FF size×value long-only portfolios, Ken French, 1926+).
**Status:** century-scale + OOS windows. Explains M1's winner: the low-volatility/Quality
decade (see `literature/classics/low-volatility-anomaly.md`).

## M3 — Constraints are implicit shrinkage: capping IMPROVED out-of-sample results
**Claim:** the geo-capped maximin beat the unconstrained maximin OOS (Sharpe 0.84 vs 0.73);
the fully diversified preset (sleeve ≤25% / geo ≤40% / factor ≤40%) holds that edge (0.84,
maxDD −28%); in the 54-year multi-asset proxy race the capped maximin (0.59) again beats the
unconstrained (0.56). Unconstrained maximin is structurally a corner solution (LP vertices on
noisy per-quadrant means).
**See:** `REPORT_optimizer.md` walk-forward table · `REPORT_proxy_backtest.md` ·
`REPORT_window_robustness.md`. **Code:** `portfolio/optimizer.py` (`geo_cap`, `factor_cap`,
diversified preset), `portfolio/validation.py`, `portfolio/proxy_backtest.py`.
**Data:** MSCI levels + factsheet country weights; FF portfolios + asset proxies.
**Status:** OOS modern + century-scale. Matches Jagannathan-Ma 2003.

## M4 — Our per-quadrant regime patterns are structural, not a 28-year artifact
**Claim:** 15/16 factor×quadrant sign cells agree between the modern window and 1960–2026
(789 classified months): Value-in-Stagflation (+6.6%/yr over 66y) and Momentum's quadrant
pattern are real. The one flip: the MARKET factor in Stagflation (+0.5%/yr long vs −5.4%
modern) — "equities always crash in stagflation" is a 2021-22 artifact.
**See:** `outputs/analytics/long_history/REPORT_long_history.md` · viz appendix "the 66-year
reality check". **Code:** `analytics/long_history.py` (+ `classify_states(start=)`).
**Data:** `ff_factors_monthly.csv` (Ken French 1926+) × FRED macro (`macro_monthly.csv`).
**Status:** century-scale (sign agreement across eras).

## M5 — The BL regime views are now anchored on 66 years where the eras agree
**Claim:** blending each quadrant's modern excess toward β·f_long (β: Mom 0.28, HML 0.19)
tempered the Enhanced-Value view from +0.44% to +0.15%/month — the modern value-premium read
was window-inflated. Blend OOS Sharpe unchanged (0.70): the gain is input robustness, not
headline performance.
**See:** `REPORT_optimizer.md` "Active regime views" (per-view anchoring note) · viz chart 05.
**Code:** `analytics/long_history.py::msci_factor_prior` + `portfolio/views.py::regime_views`.
**Data:** FF factors × macro states × MSCI excess returns. **Status:** mechanism unit-tested;
effect measured in-sample; OOS-neutral by design (tilts are confidence-bounded).

## M6 — The all-weather menu transforms the maximin floor; equity-only cannot have both
**Claim:** adding bond/gold/cash proxies more than doubles the worst-quadrant floor
(+0.31→+0.73%/mo unconstrained; +0.59 diversified) at half the volatility (23.9→13.5%,
maxDD −61→−34%/−28%), for −1.5/−2.0pt CAGR. On equities alone, forcing full diversification
ERASES the stagflation floor (+0.31→+0.015%/mo) — it WAS the concentrated Value bet.
Century-scale support for the SHAPE: static all-weather archetype through OPEC stagflation
1973-74 = **+9.8% vs 60/40 −28.5% vs pure equity −44.6%**; 2022 replay: −16.9% vs −25/−27%.
**See:** `REPORT_optimizer.md` flagships · `REPORT_stress.md` · viz roster + "a century of
storms". **Code:** `ingest/asset_classes.py`, `portfolio/optimizer.py`
(`include_asset_classes`), `portfolio/stress.py`. **Data:** `asset_class_monthly.csv`
(bond TR constructed from FRED `ust_10y` per Swinkels 2019 — sanity: 2008 +21%, 2022 −16%;
gold LBMA mirror; FF rf).
**Status:** floor/vol numbers **in-sample**; shape century-scale (stress + proxy race).
~~The specific flagship weights lack an OOS verdict~~ → see M7.
**Reinforced by M32 (2026-07-21):** the placebo shows the labels are NOT what produces this —
which makes M6 the surviving explanation rather than a companion to it. The floor transformation
is a property of the MENU (holding assets that behave differently), not of knowing the regime.
Read together with M27's menu-level measurement (adding the proxies takes minimum pairwise
correlation 0.53 → −0.14), M6 is now the load-bearing claim it was always closest to being.

## M7 — The all-weather flagship SURVIVES out of sample
**Claim:** as a walk-forward contestant on its own extended universe (choosing
equities/bonds/gold/cash each year from TRAINING data only, diversified caps, net of 10 bps):
**OOS Sharpe 0.94, 2009–2026** — above every equity construction (HRP 0.88, ERC 0.86,
equity-diversified maximin 0.84, 1/N 0.84) — with the LOWEST volatility in the table (10.6%)
and maxDD −22.5%. Only min-variance (1.06 — era-flagged by M2) and its vol-target overlay rank
higher. M6's in-sample promise holds out of sample on the modern window.
**See:** `REPORT_optimizer.md` walk-forward table (row "Maximin (all-weather div)") · viz
charts 01–02 (new line/bar) · its `current_conditions` scenario cone now in chart 07.
**Code:** `portfolio/validation.py::walk_forward` (all-weather contestant on `rets_aw`),
`analytics/scenario.py::build_universe(include_asset_classes=True)` + `portfolio_cone`.
**Data:** `levels_wide.csv` + `asset_class_monthly.csv`. **Status:** OOS modern; the SHAPE is
additionally century-scale via M6's stress/proxy evidence. Caveat: 2009–2026 contains no
prolonged bear market; the proxy race (M2/M3) is the longer-track complement.
**Update (M10):** with the long-anchored objective the flagship improves further — OOS Sharpe
0.954, vol 8.7%, maxDD −16.7%.
**Attribution corrected by M32 (2026-07-21):** every number above stands — it was measured and
re-measured. What does NOT stand is the implied explanation. Under 40 scrambled-label replicates
the flagship's Sharpe null mean is **1.006** (real 0.933, p 0.659) and its realized worst-real-
quadrant floor null mean is **+0.005%/mo** (real −0.090%, p 0.756). The flagship survives out of
sample because of WHAT IT HOLDS (M6/M27), not because of what the classifier knew. Everywhere
this entry is cited, the sentence must be "a capped worst-case objective over a regime-diverse
MENU", never "a regime-aware portfolio".

## M10 — Anchoring the maximin OBJECTIVE on long history improves every variant OOS
**Claim:** blending the maximin's per-quadrant means toward long-history values (proxy sleeves:
their own 1962+ quadrant means, sign-agree rule, month-weighted; factor sleeves: β-scaled FF
excess as in the views; **cash excluded on principle** — its quadrant "mean" is the era's
policy-rate level, not transferable behavior) improved the OOS Sharpe of every maximin variant:
all-weather 0.942→**0.954** with vol 10.6→**8.7%** and maxDD −22.5→**−16.7%**; unconstrained
0.729→0.754. Concrete corrections that drove it: gold-in-bust tempered +1.20→+0.71%/mo (the
modern number was the 2008-11 artifact), Treasuries-in-bust raised +0.43→+0.66%/mo (six decades
of flight-to-quality).
**See:** `REPORT_optimizer.md` walk-forward table · MILESTONES M7 superseded numbers.
**Code:** `analytics/long_history.py::asset_class_prior` +
`portfolio/optimizer.py::_anchor_mu_q`/`_objective_mu_q` (objectives consume `mu_q_obj`;
reporting keeps the empirical `mu_q`). **Data:** `asset_class_monthly.csv` (1962+),
`ff_factors_monthly.csv`, macro states. **Status:** OOS modern (walk-forward, net of costs);
prior clipped to each training window (no look-ahead).
**SUPERSEDED BY M35 (2026-07-22): the A/B improvement is NOT resolvable at this sample size.**
Paired placebo test: every real-arm Δ is under half a null standard deviation, and the estimator
"helps" in 45-60% of replicates. The +0.012 claimed below was always smaller than this entry's
own acknowledged ±0.01-0.02 menu-shift band — read that caveat as the warning it was. Do not cite
this entry's deltas as evidence of anything without M35 next to them. The paragraph below is kept
verbatim as the record of what was claimed and when.
**Interpretation once revised by M32 (2026-07-21), now moot:** the A/B improvement is untouched — the estimator
still helps every variant on three universes including the pre-registered one. But since the
labels themselves are placebo-equivalent (M32), the mechanism cannot be "better regime
information": it is **shrinkage of noisy conditional means toward a long sample**, which reduces
estimation error regardless of whether the conditioning variable informs. The decisive
disambiguation — re-run this A/B under scrambled labels — is recorded in TODO. Note the concrete
corrections quoted above (gold-in-bust +1.20→+0.71) are exactly what a shrinkage reading
predicts: the modern cell was an artifact and the long sample tempered it.
**Re-measured 2026-07 after the B2 menu expansion (+USA Enhanced Value, Japan Momentum, EM
Quality via `msci_api`):** flagship OOS Sharpe 0.93 on the 24-sleeve menu — numbers shift by
~0.01-0.02 with the menu, every ranking and conclusion unchanged.
**SIGN CORRECTION 2026-07-21 (found while setting up the M35 estimator A/B): the claim
"improves EVERY maximin variant" no longer holds on the shipped 28-sleeve menu.** Re-measured
Δ (anchor ON − OFF) in net OOS Sharpe: worst-quadrant **+0.0050**, diversified **+0.0014**,
**all-weather −0.0036** (0.9362 → 0.9326). The magnitude sits inside the ±0.01–0.02 menu-shift
band this entry already acknowledged, but "improves every variant" is a claim about SIGNS, and
on the flagship the sign flipped. 1/N's Δ is exactly 0.0000 (invariance control). The honest
restatement pending M35: *the estimator's effect on the current menu is within noise of zero on
the flagship and mildly positive on the equity variants* — which, note, is itself more
consistent with a shrinkage reading (a variance-reduction device has no reason to help a
portfolio whose cells are already dominated by the proxy sleeves' long records) than with a
regime-information one. Do NOT quote M10's "+0.012 on the flagship" in the paper without this
correction.

## M8 — The price of preferences is measurable (profiles)
**Claim:** preference bundles cost measurable CAGR vs their unrestricted twins: the owner's
"Pure equity — diversified growth" −0.8pt for 7-sleeve factor/geo spread; "All-weather —
defensive" −2.0pt CAGR for −2.4pt vol. Preferences stay personal; their cost is a number.
**See:** `REPORT_optimizer.md` "price of preferences" · viz "Evidence · the price of
preferences". **Code:** `portfolio/optimizer.py::run_profiles` (+ `config.OPTIMIZER_PROFILES`).
**Data:** MSCI levels (+ proxies for the defensive profile). **Status:** in-sample by
construction (it prices constraint sets); the caps themselves are OOS-supported (M3).

## M9 — Recency is a trap, measured
**Claim:** EM Enhanced Value's trailing 3y return was −4.4%/yr seen from 2020-06, +39.7%/yr
seen from 2026-06 — ranking assets by recent returns points backwards at multi-year horizons
(momentum horizon is 3-12 months; 3-5y shows reversal). This motivates judging RULES
walk-forward, never assets by their current trailing numbers.
**See:** viz chart 03 foldable (window note) · this conversation's EM analysis (reproducible:
trailing 36m windows on `levels_wide.csv`). **Code:** one-liner on `levels_wide.csv`; the
protocol answer is `portfolio/validation.py`. **Status:** descriptive fact + literature
(Jegadeesh-Titman 1993; De Bondt-Thaler 1985).

## M11 — Japan is a full region; the mixed-window trap dodged by manual export
**Claim:** the 4 owner-exported xlsx (2026-07-19) complete the menu 24 → **28 sleeves** with
the 330-month common window INTACT: Japan Reference's manual web export starts 1998-12-31 —
exactly the window start — where the graph-service copy (rejected earlier) only had 2000-12+.
Japan is now a full 4-factor region and AC Asia ex Japan is complete. First measurement:
Japan factor excess over Reference 1998-12→2026-06 — **Enhanced Value +3.6%/yr** (the
deflation-decades Value market delivers), Quality +0.3, Momentum +0.03. Walk-forward
re-run on 28 sleeves: rankings unchanged (min-variance 1.03 net OOS Sharpe leads; all-weather
diversified maximin 0.93, lowest vol/maxDD in the table).
**See:** `outputs/analytics/factor_vs_reference.csv` (Japan rows) · `REPORT_optimizer.md`
walk-forward table. **Code:** `ingest/returns.py` (`msci_local`, empty `weights_file` =
returns-only) + registry rows 145817/145829/706026/939200. **Data:** owner MSCI web exports
in `data/raw/msci_indexes/Japan/` + `AC_Asia_ex_Japan/` (NETR USD monthly, verified in-file).
**Status:** full-sample descriptive (excesses); walk-forward net-of-costs OOS (rankings).
Look-through for all 7 factsheet-less sleeves stays approximated (caveat #18).

## M12 — The equity maximin's OOS record is largely an EM ride (owner suspicion, confirmed)
**Claim:** Maximin (diversified) holds ~48% EM at its caps (corner solution, flagged in the
report) and its walk-forward OOS monthly returns correlate **0.93 with EM Reference** — the
highest EM loading in the table after unconstrained maximin (0.96). Split at 2023-12: its
pre-2024 OOS Sharpe is **0.70 — indistinguishable from 1/N (0.68) / ERC (0.71) / HRP (0.73)**;
the 2024+ EM boom (EM sleeve Sharpe 0.43→1.40) lifts it to 1.68 along with everyone else.
Min-variance's edge, by contrast, exists in BOTH halves (0.94 / 1.71). Conclusion: the equity
maximin variant has no demonstrated skill beyond its structural EM tilt; the all-weather
variant (0.72 / 2.79, corr 0.88) remains the defensible flagship. Recommendation unchanged
but sharpened: never quote the equity maximin's full-period OOS Sharpe without this split.
**See:** this entry's numbers (reproducible: split-Sharpe + corr on
`optimizer_walkforward_returns.csv` × `levels_wide.csv` EM column). **Code:** ad-hoc
one-liner; promotion to a standing report section is a TODO (sub-period + leave-region-out).
**Data:** cached walk-forward OOS returns (2009-01..2026-06, net of costs).
**Status:** descriptive decomposition of OOS results; not yet a significance test (that is
paper-track item 1).

## M13 — LORO verdict: the podium is method, not region — and EM was a net DRAG on maximin
**Claim:** the leave-one-region-out walk-forward (9 full re-runs, one per dropped region)
shows the top ranks survive every drop: min-variance is #1 in 8/9 menus (#2 only without EM,
at an unchanged 1.03), the all-weather flagship never leaves the podium, HRP/ERC stay
mid-table above 1/N in every menu, and no overlay/momentum contestant beats 1/N anywhere.
**The correction to M12's narrative:** dropping EM does not hurt the maximin family — it
IMPROVES every variant (all-weather 0.93→**1.18, taking #1**; equity maximin 0.84→0.94;
worst-quadrant 0.71→1.00). EM exposure was a net OOS drag 2009–2026 (2009-23 losses larger
than the 2024+ rally gains); the maximin objective's flaw is that modern per-quadrant means
systematically ATTRACT it into EM corners. M12 (period effect on the full-period Sharpe)
stands; "it rode EM to a good number" does not — it paid for EM, then the rally repaid part.
**Estimator gap exposed (paper-relevant):** the M10 long-history anchor disciplines FACTOR
cells via Fama-French β-mapping, but REGIONAL means (EM's premium) have no anchor — the
undisciplined cell is exactly where the objective got hurt. Candidate refinement recorded in
TODO (paper track).
**See:** `REPORT_exposure_robustness.md` (full 11×9 Sharpe/rank matrix) · `optimizer_loro.csv`.
**Code:** `portfolio/validation.py::leave_one_region_out` (CLI `--loro`), `_drop_region`,
`exposure_diagnostics` (standing report section + `optimizer_exposure.csv`).
**Data:** MSCI 28-sleeve menu + proxies, net of 10 bps. **Status:** OOS modern (walk-forward
protocol, training-only estimation, same warmup/refit/costs as the honesty table).

## M14 — The honesty table now has p-values: NOTHING beats 1/N significantly
**Claim:** with the Ledoit-Wolf (2008) studentized circular-block-bootstrap test on the
walk-forward net OOS returns (B=4999, b≈T^⅓), **no contestant's Sharpe edge over 1/N is
significant at 5%** — min-variance, the OOS winner with +0.20 annualized Sharpe over 1/N,
lands at p_boot **0.055** (HAC z-test 0.034 — the bootstrap is the honest one under heavy
tails). Downside significance IS detectable: vs 1/N, the 1/N+vol-target overlay is
significantly worse (p=0.009); vs Min-variance, four contestants lose significantly
(1/N+vol-target 0.003, balanced sliders 0.025, min-var+vol-target 0.027, momentum 0.032).
The all-weather flagship is statistically indistinguishable from min-variance (p=0.70)
while running at ~⅔ of its volatility — which is precisely its case. Deflated Sharpes (N=11 contestants) are
all ≥0.98 — every fielded record survives multiplicity vs zero skill (a low bar in a
2009-2026 OOS window with no prolonged bear). DeMiguel's verdict, replicated on our menu
with our own inference: the estimation advantage the optimizers claim is not statistically
demonstrable in 210 OOS months — which is WHY the product's preferences tilt a structural
anchor instead of trusting estimated edges.
**See:** `REPORT_optimizer.md` "Are the Sharpe differences real?" · `optimizer_inference.csv`.
**Code:** `portfolio/inference.py` (LW test + DSR; unit-tested against synthetic
same-Sharpe/different-Sharpe cases, scale-invariance and antisymmetry). **Data:** walk-forward
net OOS monthly returns (2009-01..2026-06). **Status:** the test itself is the validation
layer; remaining paper items: PBO (CSCV) and block-size sensitivity.

## M15 — The regional anchor CANNOT bite, by the estimator's own rule (measured no-op)
**Claim:** extending the M10 long-history anchor to REGIONAL per-quadrant means (each region
Reference blended toward β_region · the FF market's 66y quadrant mean, same agree gate,
month-weighted, factor excesses riding the anchored base) is a measured NO-OP for the equity
maximin and slightly NEGATIVE for the all-weather: equity walk-forward results are IDENTICAL
to 4 decimals (weights unchanged, floor quadrant unchanged), all-weather OOS Sharpe
0.933→0.898 (vol 8.7→8.3%, maxDD −17.9→−19.8%). The mechanism works (cells move by up to
0.8%/mo where the gate opens) — but the equity maximin's binding quadrant is Stagflation,
**the market's one era-flipped cell (M4), so the agree gate correctly refuses the transfer
exactly where discipline was wanted.** The estimator is self-limiting by design: where the
eras disagree there is nothing transferable, and no anchoring variant can fix EM's corner
attraction without breaking the gate principle. The EM problem's real mitigations remain the
caps + the M12/M13 standing diagnostics. Default `OPTIMIZER_ANCHOR_REGIONAL = False`; the
mechanism stays in the codebase behind the flag for reproducibility.
**See:** A/B table in the 2026-07-19 session (reproducible: toggle the flag, re-run
`walk_forward()`); scratch CSV regenerable in one command. **Code:**
`analytics/long_history.py::market_prior` + `portfolio/optimizer.py::_anchor_mu_q` (two-pass)
+ `config.OPTIMIZER_ANCHOR_REGIONAL`; unit test `test_regional_anchor_mechanics`.
**Data:** FF market total return 1960+ × macro states × MSCI menu. **Status:** OOS modern
(walk-forward A/B, net of costs); negative result recorded per the honesty principle — for
the paper this is the "we tried the obvious refinement and show why it cannot work" section.

## M16 — The confirmatory test: the frozen estimator CONFIRMS on a virgin universe
**Claim:** with the protocol declared and committed BEFORE the first run (fixed thresholds,
one A/B, no re-tuning), the frozen long-history estimator improves both maximin variants on
9 Ken French international sleeves (Europe/Japan/Asia-Pacific × Reference/Value/Momentum,
1990-11→2026-05) that were NEVER touched during development: worst-quadrant 0.582→0.584
(Δ+0.002), diversified 0.597→0.614 (**Δ+0.016**) — net OOS Sharpe over 307 OOS months
(2000-11→2026-05) containing the dot-com bust AND the GFC. Declared verdict: **CONFIRMS**
(every Δ≥0, one >+0.005). The estimator's record now: improves or leaves unchanged on three
universes, one of them virgin, never degrades.
**The secondary readouts are just as load-bearing (reported ungated):** (a) on this
two-bear window the maximin FAMILY ranks last (0.58-0.61 vs 1/N 0.68, maxDD −63/−65%) —
equity-only regime-maximin through real bears is bad, consistent with M6's "equity-only
cannot have both" and M2's era-specificity; the estimator improves it, but cannot rescue it.
(b) The hierarchy compresses: min-var +0.019, HRP +0.022, ERC +0.001 over 1/N — signs
consistent with M2, magnitudes ~noise. (c) Ledoit-Wolf on the third universe: **nothing
beats 1/N significantly (best p=0.246)** — the DeMiguel verdict now holds with p-values on
all three universes. The paper's humility thesis is now triple-confirmed.
**See:** `outputs/analytics/ff_intl/REPORT_ff_intl.md` (+ `ff_intl_ab.csv`,
`ff_intl_inference.csv`). **Code:** `portfolio/ff_intl_test.py` (protocol in docstring,
pre-registration commit precedes the results commit in git history),
`ingest/ff_international.py`. **Data:** Ken French international library, fetched
2026-07-19; frozen snapshot committed at
`data/raw/ff_intl/ff_intl_monthly_snapshot_2026-07-19.csv` (the library restates history —
the snapshot is what this verdict was computed on). **Status:** OOS on a pre-registered
virgin universe, net of costs — the strongest validation level in this ledger.
**POWER POST-MORTEM, added 2026-07-22 (M35).** This test is not falsified — its declared
thresholds were met on the virgin universe exactly as measured, and the pre-registration
discipline stands as an example. But M35 now shows that a Δ of +0.002/+0.016 sits INSIDE the
noise band of menu composition (paired placebo null sd 0.03-0.10 on the MSCI menu). **The
thresholds were set below the noise floor**, so clearing them was not evidence of much. The
honest description is: a correctly-run pre-registered test of a question it did not have the
power to answer. Any future confirmatory test in this project must declare its thresholds
against a MEASURED null, not against a hoped-for effect size — recorded as the methodological
lesson.

## M17 — The sensitivity grids: a plateau, with one honestly-reported frontier
**Claim:** varying one dimension at a time around the shipped configuration (MSCI menu),
NO ledger conclusion flips in any of the 9 walk-forward grid cells: min-variance stays #1
at costs 0/10/25 bps, refits 6/12/24m and caps 20/35/35–30/45/45 (C1); the capped maximin
beats the unconstrained in every cell, +0.115 to +0.132 (C3 — constraints-as-shrinkage is a
plateau, not a tuned point); the all-weather flagship stays on the podium (#2–#3) in every
cell (C4). The one frontier, reported not hidden (C2): the headline p-value (min-variance
vs 1/N) crosses 5% with the bootstrap block length — p=0.042 (b=3) / 0.055 (b=6, shipped) /
0.066 (b=10). Smaller blocks under-respect autocorrelation, so the CONSERVATIVE reading
stands: **borderline, not significant** — the claim is specification-sensitive at the 5%
line and is stated as such wherever it appears.
**See:** `REPORT_sensitivity.md` (+ `optimizer_sensitivity.csv`) · viz "Referee's checklist ·
sensitivity grids". **Code:** `portfolio/sensitivity.py` (CLI, like `--loro`; cost grid
re-netted from the walk-forward's own gross/turnover — no re-optimization, weights are
cost-independent). **Data:** MSCI menu walk-forward (5 full runs + re-netting).
**Status:** OOS modern across the declared grid. Out of scope by design: the agreement-rule
variant grid (estimator specification, not result robustness — post-M16 it would need a
fresh confirmatory universe).
**CORRECTION 2026-07-21 (M33 re-run): C4 as originally worded no longer holds, and not because
of any grid dimension.** The contestant field grew 12 → 17 (M26/M28/M29/M30) and Brodie 2009
landed at 0.9335 against the all-weather's 0.9326 — **a 0.0009 Sharpe margin** — so the flagship
is rank #4 in the SHIPPED cell itself. C4 is restated, not re-thresholded: *"the all-weather
flagship stays within 0.001 Sharpe of the podium in every grid cell, at two-thirds of the
volatility of everything above it."* C1, C2 and C3 are unchanged, and `sensitivity.py` now
separates "false in the shipped cell" (a stale conclusion) from "flips in a grid cell" (a
robustness failure) so this cannot be misattributed again.

## M18 — The 28-sleeve equity menu contains ~3 real bets (the KISS verdict, measured)
**Claim:** the full MSCI menu's monthly returns have mean pairwise correlation 0.76 (min
0.49); the first principal component explains 77% of variance, 4 components reach 90%, and
the eigenvalue-entropy effective number of bets is **2.8**. Equity region×factor sleeves are
one big bet with small tilts: adding equity index #29 adds paperwork, not diversification —
consistent with LORO (M13: dropping entire regions barely moves the structural rules) and
with M6 (one new ASSET CLASS — bonds/gold — was worth more than any number of equity sleeves:
it doubled the stagflation floor). Menu-design principle for product and paper: selection =
spanning distinct RISK SOURCES; within a source, redundancy is harmless for ERC/HRP (shared
risk budgets) and harmful for 1/N (silent double-counting).
**See:** this entry (reproducible one-liner: PCA/entropy on `levels_wide.csv` returns).
**Code:** ad-hoc on cached CSV. **Data:** 28-sleeve common window. **Status:** descriptive,
full-sample; the actionable consequences (B1b commodities as the next distinct source) were
already OOS/century-tested where they land (M6/M7).

## M19 — Real-time discipline test: no look-ahead subsidy — lagged labels do BETTER
**Claim:** re-running the walk-forward with state labels lagged 2 months (at month t you
only know t−2's label — the realistic macro-publication constraint; instrument
`config.OPTIMIZER_STATE_LAG_MONTHS`), every regime-dependent contestant improves or holds:
all-weather 0.933→**1.114** (vol 8.7→6.6%, maxDD −17.9→−14.7%), worst-quadrant maximin
0.713→0.885, diversified 0.837→0.849, balanced/BL 0.700→0.699; all non-regime contestants
are bit-identical (the instrument touches only the regime layer — sanity check passed).
Conclusion: the maximin/all-weather results carry NO look-ahead subsidy from knowing macro
prints early — the shipped as-published labels are, if anything, the CONSERVATIVE
specification, plausibly because boundary months (freshest, still-revising data) are the
classifier's noisiest and lagging avoids trading on them (mechanism = hypothesis, not
claim). Defaults deliberately stay lag-0: switching to the better post-hoc number would be
tuning on the test; the paper states both. Remaining real-time gap (stated): FRED serves
revised values — a full ALFRED-vintage replay is future appendix work.
**See:** A/B table (reproducible: set the flag, re-run `walk_forward()`).
**Code:** `optimizer._load_states` (shift) + `config.OPTIMIZER_STATE_LAG_MONTHS`.
**Data:** MSCI walk-forward, net of costs. **Status:** OOS modern; closes pre-draft check 1.

## M20 — The hierarchy survives the live-index era (backfill-bias check)
**Claim:** MSCI's factor indices were launched ~2013-15 with backfilled history (providers
launch what backtested well). Restricting the walk-forward OOS record to 2015+ months only
(138 live-era months, every index computed in real time by then): the hierarchy holds —
min-variance #1 (0.963), all-weather #2 (0.916), HRP 0.857 > ERC 0.831 > 1/N 0.812; capped
maximin still beats unconstrained (0.804 vs 0.694). No ledger conclusion flips; the only
movement is the equity maximin sliding a hair below 1/N (0.804 vs 0.812), consistent with
M12. Together with the FF replications (M2, M16 — academic data computed continuously, no
launch-selection bias), the backfill critique is answered with measurements, not words.
**See:** split table (reproducible one-liner on `optimizer_walkforward_returns.csv`).
**Code:** ad-hoc on cached CSV. **Data:** walk-forward net OOS returns. **Status:**
descriptive sub-period read; closes pre-draft check 2.

## M21 — PBO 33%, and min-variance is measured to be a Quality bet in disguise
**Claim:** (a) the probability of backtest overfitting for our contestant selection (CSCV,
Bailey et al. 2017; S=16, 12,870 half-splits, 11 trials on the walk-forward net OOS matrix)
is **33.2%** — the in-sample winner carries real OOS information (well below the 50%
coin-flip), but one split in three would have crowned a below-median contestant: moderate
selection risk, coherent with M14's borderline significance. (b) Per-sleeve attribution
(arithmetic Brinson shares, weights per refit × sleeve returns): **min-variance earns 82%
of its OOS return from the Quality sleeves** (USA Quality 52%, World Quality 30%) — the
M2/low-vol hypothesis is now a measurement: min-variance is a defensive-Quality factor bet
wearing an optimizer's name, and the paper/product must describe it as such. The
all-weather flagship's gold sleeve is structural, not decorative (33% of its OOS return,
plus EM Enhanced Value 32%, bonds 6%); HRP is the only rule that actually spreads (top
sleeve 9%).
**See:** `REPORT_optimizer.md` PBO line + attribution section · `optimizer_attribution.csv`.
**Code:** `inference.pbo_cscv` (unit-tested null≈0.5 / dominant-trial→low),
`validation.sleeve_attribution` (+ per-refit weights in walk-forward meta).
**Data:** walk-forward net OOS returns + per-refit weights. **Status:** OOS decomposition;
closes the last two paper-track appendix items.

## M22 — The constant-mix assumption is not load-bearing (rebalancing schemes measured)
**Claim:** re-implementing every contestant's SAME per-refit weight schedule three ways —
shipped constant-mix (drift trades free), constant-mix with all drift turnover costed at
10 bps, and within-interval buy-and-hold (no monthly trades) — the free-drift Sharpe
overstatement is **≤0.002** (mean drift turnover 0.55–1.21%/month ⇒ ~0.6–1.4 bps/month of
uncharged cost) and the buy-and-hold ranking is IDENTICAL to the shipped one; the
all-weather is actually slightly better under drift (0.933→0.957 — the buy-and-hold
momentum tilt meeting the 2024+ trend). The "within-interval drift turnover is uncosted"
limitation is quantified and immaterial; annual-refit buy-and-hold is the cheapest
implementable scheme and loses nothing.
**See:** `REPORT_rebalancing.md` + `optimizer_rebalancing.csv` · deep dive
`info/literature/classics/rebalancing.md` (C1). **Code:** `portfolio/rebalancing.py` (CLI; reuses
the walk-forward's per-refit weights, no re-optimization). **Data:** walk-forward weights ×
sleeve returns. **Status:** OOS re-implementation of identical decisions; closes C1's
empirical half and the drift-turnover limitation.

## M23 — Horizon is now a measured input: the equity/all-weather loss-probability gap is 10×
**Claim:** per-profile scenario cones at 5/10/20 years (current_conditions, re-sequenced
history — stated assumption, not a forecast): the equity profiles carry **~14% probability
of cumulative loss at 5 years** (7.2-7.5% at 10y, ~1.2% at 20y) while the all-weather
defensive profile carries **1.4% / 0.1% / 0.0%** — a 10× gap at short horizons that
converges with time. Investment horizon therefore selects between the profiles as strongly
as risk appetite does: below ~10 years the all-weather's floor is the dominant argument;
at 20 years the equity profiles' higher median CAGR (~9.6-9.8% vs 7.3%) comes with nearly
the same loss probability. The applied thesis gains its horizon axis with numbers.
**See:** `REPORT_optimizer.md` "User profiles" horizon tables. **Code:**
`portfolio/optimizer.py::_profile_cones` (+ `_profiles_section`), reusing
`scenario.portfolio_cone(years=…)`. **Data:** scenario universes (equity + extended).
**Status:** simulation under the stated re-sequenced-history assumption (validator layer,
same caveat as every cone).

## M24 — The verdicts survive the currency seat: unhedged EUR re-statement (B3, half 1)
**Claim:** re-stating every contestant's walk-forward net OOS returns in unhedged EUR
(FRED DEXUSEU month-end, EUR return = (1+r_USD)(1+r_FX)−1): the podium is unchanged —
min-variance #1 (1.21), HRP #2 (1.12), all-weather #3 (1.11) — and every construction
conclusion holds. All Sharpes RISE (USD appreciation 2009-2026 paid the EUR seat; FX vol
8.5%/yr partially diversifies). The one real movement: **vol-target overlays lose their
edge** (min-var+VT #2→#5) — their volatility control is diluted by unhedged FX noise, so
for a EUR investor the overlay's USD result was partly a currency artifact. Hedged
re-statement (needs EUR short-rate data, pairs with the C2 deep dive) remains open.
**See:** this entry's table (reproducible: DEXUSEU × `optimizer_walkforward_returns.csv`).
**Code:** ad-hoc on cached CSV + keyless FRED fetch. **Data:** walk-forward OOS returns,
DEXUSEU 1999+. **Status:** descriptive currency re-statement of OOS results; closes the
unhedged half of B3.
**Update (same day, hedged half — B3 CLOSED):** hedged EUR ≈ USD return + (rf_EUR − rf_US)
(covered interest parity; euro-area 3m interbank from FRED, mean carry −0.56%/yr over the
OOS window): rankings are virtually the USD table (top-5 identical; 1/N and equity maximin
swap #6/#7). Across all three seats — USD, EUR unhedged, EUR hedged — every construction
conclusion holds; the seat moves levels, never decisions. Caveats stated: CIP basis
post-2008, frictionless monthly hedge, 3m rate as the 1m proxy.

## M25 — Anchor decision closed: ERC stays the prior, HRP is the (insignificantly) better construction
**Claim:** with all accumulated evidence, HRP edges ERC in every table by a hair — modern
0.87 vs 0.85, 90y race 0.76 vs 0.75, virgin universe 0.70 vs 0.68, above it in every LORO
menu and in the EUR seat — but the edge is NOT significant (LW p_boot 0.119 on the modern
OOS pair) and costs 12× the turnover (5.0% vs 0.4% per refit). Decision, recorded: **ERC
remains the BL anchor** (the prior's job is neutrality and stability, where ERC's near-zero
turnover and clean risk-balance interpretation win); **HRP remains the marginally better
standalone construction** and is described as such wherever rules are ranked. Revisit only
if a future universe makes the HRP-ERC gap significant.
**See:** the tables cited (M1/M2/M13/M16/M24) + this entry's LW test (reproducible
one-liner on the cached walk-forward returns). **Code:** decision — no code change.
**Data:** all accumulated walk-forward evidence. **Status:** design decision grounded in
OOS measurements + significance test; closes the standing TODO item.

## M26 — The strongest published challenger to the humility claim, fielded: it loses, as its own theory predicted
**Claim:** Yuan & Zhou (2023, *JFQA*) is the direct attack on "nothing beats 1/N" — they give
the humility result a THEORY (the plug-in Sharpe haircut τ = √((1−η)/(1+η/SR²)), η = N/T) and
then beat 1/N with a closed-form combination rule ŵ_λ = λ·Σ̂⁻¹1/(1'Σ̂⁻¹1) + (1−λ)·1_N/N. We
fielded it. **Pre-registered prediction, declared in `literature/frontier/beating-1N-yuan-zhou.md`
and TODO before the run: no significant win on our menu**, because their own Proposition 3 makes
1/N asymptotically optimal on a one-factor-dominated menu (ours: first PC 77%, M18) and their
empirics require T = 360 ("smaller is not sufficient") against our T = 120 warmup.
**Measured (walk-forward, 210 OOS months, net of 10 bps):** GMV combo **net Sharpe 0.735 vs
1/N's 0.830** — Δ = **−0.095** annualized, LW p_boot **0.449** (p_hac 0.442): it does not beat
1/N, and it is significantly WORSE than min-variance (Δ −0.296, p_boot 0.016). Gross Sharpe
0.749, so **the loss is the rule, not the cost charge**.
**The mechanism, visible in λ\*:** λ\* = 0.000 at the first three refits (η = 0.23→0.19 — their
formula itself refuses the GMV and returns pure 1/N), then rises to a 0.61 mean as T grows.
Where it does trust the GMV, the unconstrained plug-in produces a **13.4× mean gross exposure**
(up to 23.3×, 9–14 short sleeves) — what an unconstrained GMV does to 28 correlated equity
sleeves. **Sensitivity (reported, not fielded — one contestant, one specification):** re-run with
our Ledoit-Wolf Σ instead of their plug-in S, i.e. the version a practitioner would actually
trade, λ\* drops to a 0.296 mean, gross exposure to 1.6×, and net Sharpe rises to **0.825 — a
dead heat with 1/N (0.830), still not a win.** So the verdict is not an artifact of handicapping
them with the raw sample covariance.
**⇒ the humility claim survives its strongest published challenger, adjudicated with the
challenger's own mathematics** — and C2 ("nothing beats 1/N significantly") is now a statement
about a table that CONTAINS the rule designed to break it.
**See:** `outputs/analytics/optimizer/optimizer_walkforward.csv` + `optimizer_inference.csv`
(row "GMV combo (Yuan-Zhou)"), `REPORT_optimizer.md`. **Code:** `portfolio/rules.py::
gmv_combo_weights` (λ\* re-derived from their five stated scalars — the derivation is in the
docstring, their eq. 29 was not transcribable from the deep dive), fielded in
`portfolio/validation.py::_contestants`. **Data:** the 28-sleeve MSCI menu, 1998-12→2026-06.
**Status:** `OOS modern`, with the outcome PRE-DICTED by the challenger's theory before the run.

## M27 — DR² lands: the 28-sleeve equity menu is 1.3 independent risk bets, and min-variance's 4 sleeves are the same 1.3
**Claim:** the Choueifaty-Coignard Diversification Ratio (DR = Σwᵢσᵢ/σ_p; **DR² = the effective
number of independent RISK bets**) is now a standing number next to the look-through
effective-bets counts, because the two answer different questions and only one of them is about
diversification. Look-through counts EXPOSURE spread (how many sectors/countries/stocks the
money touches); DR² counts RISK spread. **Measured on the shipped menu:** the 28-sleeve equity
menu at 1/N has **DR² = 1.31** — against look-through bets in the dozens. **Min-variance, which
holds FOUR sleeves, has DR² = 1.28.** Holding 28 equity sleeves instead of 4 buys **0.03 of an
independent bet.** ERC 1.32, HRP 1.31 — the whole podium is the same single bet, differently
sliced. This is M18's KISS verdict in the practitioner's own metric, and it is harsher than the
eigenvalue-entropy number (3.0 on the shrunk correlation; M18's 2.8 was on the raw one — both
promoted from an ad-hoc one-liner to `optimizer.menu_diagnostics`, a standing report section).
**The asset-class contrast, at menu level:** adding the three non-equity proxy sleeves moves
mean pairwise correlation 0.76→0.61, **minimum pairwise correlation 0.53→−0.14** (the first
genuinely negative pair the project has ever had on its menu), PC1 77%→69%, components-for-90%
4→7, entropy bets 3.0→4.1 and **DR² 1.31→1.43** — three sleeves buying more than twenty-eight
did. That is M6's "one new asset class beat any number of equity sleeves" measured on the MENU,
before any optimizer touches it, which makes it a statement about the opportunity set rather
than about our weighting scheme. **⇒ the B1/B1b sourcing items are the highest-value open work
in the backlog, and the paper's menu-design paragraph now has its number.**
**See:** `REPORT_optimizer.md` §"The menu itself" + the DR² column in the benchmark table and a
DR² clause on every flagship. **Code:** `portfolio/optimizer.py::diversification_ratio` /
`::menu_diagnostics`; unit-tested against both known endpoints (DR² = N for N uncorrelated
equal-vol sleeves, DR² = 1 for perfectly correlated). **Data:** shrunk Σ on the 28-sleeve MSCI
common window (and the 31-sleeve extended menu). **Status:** descriptive, full-sample — a
property of the opportunity set, not a backtested claim.

## M28 — Brodie 2009's "significantly outperforms 1/N" does not replicate once you test it
**Claim:** the owner spotted the claim in Brodie-Daubechies-De Mol-Giannone-Loris (2009, *PNAS*)
that their sparse-and-stable Markowitz portfolios "outperform 1/N significantly and
consistently" (FF48 Sharpe 0.41 vs 0.27, 1976-2006). Reading the paper closed two gaps: (a) under
the budget constraint their ℓ1 penalty is a short-position penalty and is **inert long-only**
(‖w‖₁ ≡ 1), so their FF48 winner IS long-only minimum variance at the trailing-1/N target
return; (b) "significantly" is used colloquially — there is **no Sharpe-difference test and no
transaction-cost charge** anywhere in the paper. Fielded here with both.
**Measured (210 OOS months, net of 10 bps):** **net Sharpe 0.933 — third in the table, ahead of
HRP, ERC and 1/N**, Δ vs 1/N = **+0.104 annualized, LW p_boot 0.149** (p_hac 0.132). So: a real
point estimate, and **not statistically significant** — the same verdict our own min-variance
gets (+0.201, p 0.055) on a menu with far less variance-reduction room than their 48 dispersed
industry portfolios. It is also NOT significantly worse than min-variance (p 0.111), and it is
cheap (0.086 turnover per refit vs min-var's 0.041). Sparsity: 4-6 of 28 sleeves, the constraint
set's doing, exactly as they observe.
**⇒ they are an ALLY, not a challenge, and the adjudication is symmetric**: the family that wins
their experiment (positivity-constrained variance minimization) is the family that wins ours;
what does not survive is the word "significantly", in their table and in ours alike. Brodie is
the SELECTING sibling of our SPREADING caps — both are Jagannathan-Ma regularization — and that
is the paper's related-work paragraph.
**See:** `optimizer_walkforward.csv` / `optimizer_inference.csv`, row "Sparse Markowitz (Brodie
2009)". **Code:** `portfolio/rules.py::brodie_weights` (sample covariance and the raw mean
vector — their specification, faithfully; caveat #19 governs OUR optimizer, not a replicated
challenger), fielded in `validation._contestants`. **Data:** 28-sleeve MSCI menu.
**Status:** `OOS modern`.

## M29 — HERC measured: the hybrid lands BELOW both its parents, and the linkage does not matter
**Claim:** HERC (Raffinot 2018) is literally "ERC on HRP's topology" — both sides of the M25
anchor decision in one rule — so it was the natural frontier contestant. Declared prior,
recorded in TODO before the run: *statistically indistinguishable from HRP/ERC*.
**Measured:** **HERC (Ward) 0.800, HERC (single) 0.797** net OOS Sharpe — **below 1/N (0.830),
below ERC (0.848) and below HRP (0.870)**. Versus 1/N: Δ −0.030 (p_boot 0.573) and −0.033
(p 0.576) — indistinguishable, as predicted. Versus min-variance both are significantly worse
(p 0.033 / 0.012). **The prior was right about the statistics and wrong about the direction:
combining the two structural rules is not better than either.** Linkage — the hyperparameter the
CBS thesis insists on reporting — moves the answer by **0.003 Sharpe**, so the Ward-vs-single
question that the HERC literature makes much of is, on this menu, not a question.
**The third finding, and the most useful one: Raffinot's early stopping is INOPERATIVE here.**
The gap index rises monotonically to its ceiling (Gap = 1.41 at k=1 → 3.69 at k=21, s ≈ 0.01
throughout), so the 1-standard-error rule never fires and the rule descends the full hierarchy.
The reason is mechanical and worth stating rather than hiding: the permutation null has
near-zero correlation everywhere, so its dispersion falls only through the arithmetic
0.25·(n−k) term while the real menu's falls faster at every k. **There is no scale at which our
sleeves stop looking more clustered than nothing at all** — M18/M27 from a third angle, and a
caution for anyone reporting a gap-index cluster count on a one-factor-dominated menu.
**See:** `optimizer_walkforward.csv` / `optimizer_inference.csv`, rows "HERC (…)".
**Code:** `portfolio/anchors.py::herc_weights` + `::gap_index` (exact ERC solves at every split
and inside every terminal cluster — the recursion never leaves the ERC family). **Data:**
28-sleeve MSCI menu. **Status:** `OOS modern`. **Decision:** HERC is NOT promoted; ERC stays the
anchor and HRP the better standalone construction (M25 unchanged).

## M30 — the trend family joins the losing overlays: Faber buys drawdown, not Sharpe; dual momentum is significantly worse
**Claim:** trend-following was the one overlay family the table lacked (vol-targeting scales
exposure by turbulence; trend switches it by direction). Declared prior, recorded before the
run: *helps drawdowns, struggles net of costs.* Both halves measured.
**Measured:** **1/N + Faber 10-month SMA: net Sharpe 0.656 vs 1/N's 0.830** (Δ −0.174,
p_boot 0.326 — worse, not significantly so) — but **max drawdown −19.9% against 1/N's −26.9%,
the shallowest of any equity rule in the table**, at 12% volatility instead of 15%. So the prior
is confirmed on both counts and the honest summary is that Faber trades Sharpe for drawdown, at
1.67 turnover per refit. **Antonacci dual momentum** (the cross-sectional momentum contestant
gated by absolute momentum — the rule as defined, both legs): **0.460, Δ −0.371, p_boot 0.034 —
SIGNIFICANTLY WORSE than 1/N**, the third overlay to earn that label alongside 1/N+vol-target
(p 0.009) and, at 7%, the balanced sliders.
**⇒ the overlay family verdict is now complete and one-directional: on this menu, over this
window, every timing overlay tested — volatility targeting, cross-sectional momentum, trend
switching, dual momentum — fails to beat the thing it overlays, and three of them lose
significantly to doing nothing.** The window is stated honestly: 2009-2026 is a 17-year bull
with two short crashes, the least hospitable arena imaginable for rules whose payoff is
sidestepping prolonged bears — which is exactly why the FF-international universe (two bears)
is the fair arena and the next place to read these rows.
**See:** `optimizer_walkforward.csv` / `optimizer_inference.csv`, rows "1/N + trend (Faber 10m
SMA)" and "Dual momentum (Antonacci)". **Code:** `portfolio/rules.py::trend_overlay`, wired via
`validation.TREND_OVERLAYS`. **Data:** 28-sleeve MSCI menu. **Status:** `OOS modern`.

## M31 — the joint test agrees with the pairwise one: Friedman rejects, Nemenyi names nobody above 1/N
**Claim:** the honesty table is a stack of pairwise Ledoit-Wolf tests, which is a multiplicity
problem the deflated Sharpe only partly covers. The Demšar (2006) protocol answers the joint
question directly: rank all 17 contestants inside each of 17 non-overlapping 12-month OOS
blocks, then test the average ranks.
**Measured:** **Friedman χ² = 46.6 (p = 0.0001)**, Iman-Davenport F = 3.31 (p < 0.0001) — **the
ordering is NOT noise**; something in this table is genuinely better than something else.
**Nemenyi critical difference at 5% = 5.99 rank units**, and against it: **no contestant differs
from 1/N** (best gap: min-variance at −2.97, half the threshold), while the two worst — the
unconstrained equity maximin (+3.18) and dual momentum (+4.41) — do differ from the top.
**⇒ two claims that are easy to conflate, now separated with evidence: the ranking is real, and
the gap to 1/N is not.** C2 survives the simultaneous-comparison test as well as the pairwise
one, which is the stronger statement.
**See:** `REPORT_optimizer.md` §"All contestants at once" + `optimizer_nemenyi.csv`.
**Code:** `portfolio/inference.py::friedman_nemenyi` / `::block_ranks`. **Data:** the walk-forward
net OOS returns (common panel — rows with any NaN dropped, so all contestants face the same
months). **Status:** `OOS modern`.

## M33 — The covariance estimator IS load-bearing, for exactly one contestant: nonlinear shrinkage costs min-variance 0.084 Sharpe
**Claim:** every risk number in the engine rides on one matrix, so the covariance estimator is
now a sensitivity dimension rather than a hard-coded assumption (`config.OPTIMIZER_SIGMA_ESTIMATOR`
→ `shrinkage.estimate_covariance`). **Declared expectation, recorded in TODO before the run: "no
material change at N≪T". That expectation was WRONG, and the way it is wrong is the finding.**
**Measured (full walk-forward per estimator, 17 contestants):** swapping our constant-correlation
Ledoit-Wolf for **Ledoit-Wolf 2020 analytical NONLINEAR shrinkage costs min-variance
1.031 → 0.947 (−0.084)** — the largest single move any sensitivity cell has ever produced here,
five times the next largest — and its vol-target overlay −0.085, HRP −0.019, ERC −0.001. The
scaled-identity LW variant moves min-variance only −0.008. HERC *improves* (+0.008 Ward,
+0.018 single). Every μ_q-driven and rule-based contestant is bit-identical, as it must be
(they never touch Σ except through the caps) — a free correctness check on the harness.
**The mechanism, and why it is not a defect in either estimator:** at p/n = 0.085 nonlinear
shrinkage correctly does almost nothing (measured directly: smallest eigenvalue 3.4e-7 against
the sample matrix's 2.8e-7 — on 28 sleeves at 0.76 mean correlation the near-null direction is
real structure, not noise). Nonlinear shrinkage is built for p/n near 1 and, out of that regime,
it faithfully declines to shrink. **Min-variance is the contestant that wanted the shrinking**:
it is the only Σ⁻¹-driven rule in the table, so it is the only one that notices. So the correct
statement is not "nonlinear shrinkage is worse" but **"our headline winner's edge is partly the
crude estimator's doing, and the more sophisticated estimator withholds the help"** — which is
Jagannathan-Ma's constraints-as-shrinkage lesson (M3) arriving through a third door.
**C1 does NOT flip:** min-variance is still rank #1 under all three estimators — but its margin
over the next contestant collapses from 0.098 to **0.014**, one more reason the humility verdict
(M14/M31) is the right headline.
**See:** `REPORT_sensitivity.md` §"sigma_estimator" + `optimizer_sensitivity.csv`.
**Code:** `portfolio/shrinkage.py::shrink_nonlinear` (closed-form Epanechnikov kernel + Hilbert
transform, p ≤ n enforced; unit-tested to cut Frobenius loss to the true identity by 4× against
the sample matrix) + `::estimate_covariance` dispatcher; grid in `portfolio/sensitivity.py`.
**Data:** MSCI menu walk-forward, 3 full runs. **Status:** `OOS modern`.
**Second finding, from the same run — a reporting bug this grid exposed:** `sensitivity.py` was
attributing to grid dimensions a conclusion (C4) that had become false in the SHIPPED cell,
purely because the contestant field grew. Fixed: the report now separates *stale conclusions*
from *sensitivity flips*, and says explicitly that a stale conclusion must be restated or
retired, never re-thresholded to make it pass. M17 corrected accordingly.

## M32 — THE PLACEBO KILLS THE REGIME SIGNAL'S ALLOCATION CLAIM: scrambled labels do as well, on both metrics, under both nulls
**Claim (a negative result, and the most consequential entry in this ledger):** the macro-state
labels contribute **nothing measurable** to what the maximin family achieves out of sample. The
mechanism — "maximize the worst of four partitions of history" — works. The macro information
that was supposed to define those four partitions does not.
**Protocol:** the identical walk-forward re-run **80 times** with the state labels scrambled,
40 replicates under each of two nulls. **circular** (primary) rotates the whole label frame by a
random offset: marginal frequencies, run lengths and the transition matrix are preserved
EXACTLY, so the ONLY thing destroyed is the correspondence between a month's label and that
month's returns. **iid** permutes the rows, destroying persistence too. Two scores, because
grading on Sharpe alone would test the maximin on a target it never claimed: `sharpe` (net OOS)
and **`floor`** — the realized worst mean monthly return across the four **REAL** quadrants for
whatever weights each arm chose, i.e. the quantity `max_w min_q w'μ_q` actually optimizes.
Always real labels for scoring: grading a scrambled-label portfolio against its own scrambled
quadrants would be circular and would hand the placebo the result by construction.

| contestant | metric | real | placebo mean ± sd (circular) | p | placebo mean (iid) | p |
|---|---|---|---|---|---|---|
| Maximin (worst quadrant) | Sharpe | 0.713 | 0.784 ± 0.127 | 0.610 | 0.711 | 0.488 |
| Maximin (diversified) | Sharpe | 0.837 | 0.856 ± 0.041 | 0.659 | 0.840 | 0.463 |
| Maximin (all-weather div) | Sharpe | 0.933 | **1.006** ± 0.140 | 0.659 | 0.930 | 0.512 |
| Maximin (worst quadrant) | floor | −0.813% | −0.615% ± 0.377% | 0.659 | −0.812% | 0.537 |
| Maximin (diversified) | floor | −0.455% | −0.528% ± 0.156% | 0.341 | −0.595% | **0.195** |
| Maximin (all-weather div) | floor | −0.090% | **+0.005%** ± 0.194% | 0.756 | −0.121% | 0.488 |

**Nothing comes close to significance. The best p in twelve cells is 0.195**, and with twelve
comparisons one p at 0.195 is exactly what noise produces. The real labels sit BELOW the
scrambled mean in **7 of the 12 cells**, including the flagship's own objective: the average
RANDOMLY-labelled all-weather portfolio achieved a **positive** worst-real-quadrant floor
(+0.005%/mo) against the real-labelled one's −0.090%.
**Harness verified:** 1/N consumes no labels, so its score must be bit-identical across all 81
arms — placebo sd **1.1e-16**. And the Sharpe column reproduced EXACTLY when the whole study was
re-run with the floor metric added (same seed), so the experiment is deterministic.
**Why "worse than the placebo" is mechanically sensible, not a paradox:** real labels correlate
with returns, so "maximize the worst quadrant" becomes "maximize performance in this particular
set of historically bad months" — a specific bet on the past. Rotated labels give four
persistent-but-arbitrary slices of time, and "do least badly across four arbitrary slices" is a
PURER robustness device — closer to diversifying across time, less prone to fitting what
happened to be bad. A second reading points the same way: the diversified variants' null
distributions are half as wide as the unconstrained one's (sd 0.13–0.16pp vs 0.25–0.38pp) —
**the caps, not the labels, are what stabilize the floor.**

### What this does and does not overturn
- **UNTOUCHED — M1, M2, M3, M13, M14, M25, M31 and everything about 1/N, min-variance, ERC, HRP
  and the caps.** None of those consume labels. The humility result and the
  structure-beats-estimation result stand exactly as measured.
- **UNTOUCHED — every NUMBER in M6/M7/M10.** The flagship really did deliver Sharpe 0.95 at 8.7%
  vol and −16.7% maxDD; its floor really is −0.09%/mo against 1/N's −0.61%. What changes is the
  EXPLANATION, not the measurement.
- **OVERTURNED — the attribution.** We can no longer say the flagship's record comes from knowing
  which regime we were in. The explanation that survives is the one M6 and M27 already measured
  independently: **it comes from HOLDING assets that behave differently** (bonds and gold take
  the menu's minimum pairwise correlation from 0.53 to −0.14, M27), and any four-way partition
  pushes a worst-case objective toward them. The labels do not select; the menu offers.
- **RE-INTERPRETED — the candidate contribution (M5/M10/M16).** The estimator's measured A/B
  improvement is untouched: it still improves every regime-dependent construction on three
  universes including the pre-registered virgin one. But its INTERPRETATION shifts from "better
  regime information transfers across eras" to "**shrinking noisy conditional means toward a
  long sample reduces estimation error**" — which is true whether or not the conditioning
  variable carries information. That is a more modest but still real and still measured claim.
  **The decisive test is recorded in TODO: re-run the estimator's on/off A/B under scrambled
  labels.** If the estimator still improves things there, it is a shrinkage device and the paper
  should say so; if it only improves under real labels, the conditioning matters after all and
  this entry needs revisiting.
- **NOT TESTED HERE — the classifier's DESCRIPTIVE value.** Which quadrant we are in now,
  per-state performance, the dashboard's regime tab: different claims, not in scope. The placebo
  asks only whether the labels should move WEIGHTS.

**Power, stated:** 40 replicates put the smallest attainable p at 0.024, so only a large effect
was detectable. But there is no effect to detect in the point estimates either — the real arm is
not consistently on one side of the null, which is a stronger reading than a null result at low
power.
**See:** `REPORT_placebo.md` + `optimizer_placebo.csv`. **Code:** `portfolio/placebo.py`
(`scramble_states`, `_regime_walk_forward`, `_realized_floor`); `optimizer.build_inputs(states=)`
exists solely to feed it. **Data:** 28-sleeve MSCI menu + the extended 31-sleeve universe, 81
full walk-forwards. **Status:** `OOS modern`, permutation-tested, harness-verified.

## M34 — Why nothing is significant, measured two ways: the sleeves are one bet, and so are the portfolios
**Claim:** the humility result (M14/M31) is usually reported as a fact about statistical power.
On this menu it is better described as a fact about the OBJECTS being compared. Two measurements,
both cheap, both new:

**(a) Long-only factor tilts do NOT decorrelate — they are the most correlated cut of the menu.**
Mean pairwise correlation of monthly returns, 1998-2026:

| cut | mean corr | min |
|---|---|---|
| **same country, different factors** (Ref/Value/Momentum/Quality) | **0.885** | 0.766 |
| same factor, different countries | 0.786 | 0.555 |
| Reference across countries (pure market beta) | 0.821 | 0.629 |

Diversifying by FACTOR inside a country diversifies **less** than diversifying by COUNTRY.
Against the three non-equity proxies: Treasuries **−0.115**, gold **−0.007**, cash +0.018 vs the
28 equity sleeves. **⇒ this qualifies Ilmanen-Kizer (2012) for our case rather than contradicting
them.** Their near-zero cross-factor correlations are for LONG-SHORT factor portfolios, where the
market beta has been sold off; a long-only factor index is ~95% its parent market and ~5% tilt,
so the beta dominates and the correlations go to 0.885. They say the benefit is largest
long-short and "meaningful" long-only; on our menu the long-only version is not meaningful. This
is the practitioner-facing sentence the paper's menu-design section needed: **for an investor who
cannot short, the asset-class route delivers the decorrelation the factor route promises.**

**(b) The contestants themselves are 93–99.8% correlated.** OOS net monthly return correlations:
Brodie vs Min-variance **0.975**, Brodie vs 1/N 0.955, Min-variance vs 1/N 0.929, HRP vs ERC
**0.998**. **A Sharpe-difference test cannot separate series that move together this closely —
which is the mechanical reason the p-values sit at 0.05-0.2 and not lower**, and it is DR² = 1.31
(M27) showing up a third time. HRP and ERC at 0.998 are, for practical purposes, the same
portfolio wearing two names (consistent with M25's decision to stop arguing about them).
**Corollary for the paper's multiplicity accounting:** Brodie (M28) is not independent evidence —
it is minimum variance with a return floor, it earns from the same place (USA Quality 47% vs
min-var's 52%, M21 attribution), and it inflates the deflated-Sharpe trial count without adding
an independent test. The honesty table should be read as **~4 distinct strategies wearing 17
labels**, and the paper must say so rather than let the row count imply breadth.
**See:** reproducible one-liners on `levels_wide.csv` / `optimizer_walkforward_returns.csv` /
`optimizer_attribution.csv`. **Code:** ad-hoc on cached CSVs (the correlation cuts) +
`validation.sleeve_attribution`. **Data:** 28-sleeve common window; 210 OOS months.
**Status:** descriptive, full-sample — a property of the opportunity set and of the contestant
field, not a backtested claim.

## M35 — The candidate contribution has no measurable effect on the shipped menu — in EITHER arm
**Claim (the hardest entry in this ledger to write, and the one it exists for):** the
era-agreement-gated estimator's benefit on the 28-sleeve MSCI menu is **indistinguishable from
zero**, and so is the placebo's. M32 asked whether the LABELS matter; this asked what the
ESTIMATOR is. The answer is neither of the two outcomes declared in advance — **there is no
effect to attribute.**
**Protocol:** paired difference of differences. Within each replicate the `OPTIMIZER_ANCHOR_LONG`
switch is run OFF and ON on the SAME labels, so that replicate's noise cancels in the Δ.
20 replicates, circular null, both metrics (net OOS Sharpe and the realized worst-REAL-quadrant
floor). Pairing is what makes it readable at all: an unpaired design would drown a ±0.01 Δ in a
null with sd 0.09.

| contestant | metric | Δ_real | Δ_placebo mean ± sd | \|Δ_real\| in null sd | placebo mean in SE |
|---|---|---|---|---|---|
| Maximin (worst quadrant) | Sharpe | +0.0050 | +0.0156 ± 0.0866 | 0.06 | 0.8 |
| Maximin (diversified) | Sharpe | +0.0014 | −0.0028 ± 0.0276 | 0.05 | 0.5 |
| Maximin (all-weather div) | Sharpe | −0.0036 | +0.0053 ± 0.0991 | 0.04 | 0.2 |
| Maximin (worst quadrant) | floor | −0.154% | +0.095% ± 0.318% | 0.48 | 1.3 |
| Maximin (diversified) | floor | +0.060% | +0.015% ± 0.129% | 0.46 | 0.5 |
| Maximin (all-weather div) | floor | −0.027% | +0.078% ± 0.195% | 0.14 | 1.8 |

**Every real-arm Δ is under half a null standard deviation; no placebo mean clears two standard
errors of zero. The estimator "helps" in 45–60% of replicates, and with B = 20 that share carries
a ±22-point interval — a coin flip in every cell.** 1/N's Δ is exactly 0.0000 (invariance
control).

### The reading that matters, and it was always visible in this ledger
M10 claimed +0.012 on the flagship and simultaneously carried the note that *"numbers shift by
~0.01–0.02 with the menu"*. **The claimed effect was never larger than the acknowledged
menu-composition noise.** The 24→28 sleeve expansion then flipped the flagship's sign (−0.0036,
corrected in M10 on 2026-07-21), and this test shows the whole thing sits inside a null with
sd 0.03–0.10. So the honest statement is not "the estimator stopped working" — it is **"the
estimator's measured benefit was never resolvable at this sample size, and we should have read
our own caveat as the warning it was."**
### Consequences, stated without softening
- **The paper's candidate headline contribution does not survive.** It cannot be presented as an
  estimator that improves regime-conditioned allocation, because on the shipped menu it does not
  measurably do anything. Nor can M32's "it is really a shrinkage device" re-interpretation be
  asserted — that also requires an effect.
- **M16 (the pre-registered confirmatory test) is not falsified, but its POWER is now known to
  have been inadequate.** Its declared thresholds (every Δ ≥ 0, at least one > +0.005) were met on
  the FF-international universe as measured. We now know Δ of that size is inside the noise band
  of menu composition, so passing them was not evidence of much. **This is the correct
  post-mortem: a pre-registered test with thresholds below the noise floor is a well-run test of
  a question it could not answer.** Recorded here rather than quietly dropped.
- **What survives is unaffected:** M1/M2/M3/M13/M14/M25/M27/M31/M34 and everything about 1/N,
  min-variance, ERC, HRP, caps, and the menu measurements. None involve the estimator.
- **The paper's spine becomes the negative results + the adjudication apparatus + the menu
  measurement** (see the re-framing item in TODO). Four published or in-house claims that do not
  survive proper testing — Yuan-Zhou (M26), Brodie (M28), HERC (M29), and our own regime layer
  (M32) and estimator (M35) — is a contribution, and a rarer one than another positive result.
**See:** `REPORT_estimator_ab.md` + `optimizer_estimator_ab.csv`. **Code:**
`portfolio/placebo.py::estimator_ab` / `::estimator_verdicts`. Note the report's verdict logic was
FIXED in the same session: it was assigning directional labels ("shrinkage" / "conditioning
matters") to differences well inside the null, the same failure mode caught in `sensitivity.py`
the day before; it now tests both Δs against the null's dispersion first and says "no measurable
effect" when neither clears. **Data:** 42 full walk-forwards on the 28-sleeve menu + the extended
universe. **Status:** `OOS modern`, paired permutation design, harness-verified.
