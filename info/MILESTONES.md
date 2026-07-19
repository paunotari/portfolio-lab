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
decade (see `literature/low-volatility-anomaly.md`).

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
**Re-measured 2026-07 after the B2 menu expansion (+USA Enhanced Value, Japan Momentum, EM
Quality via `msci_api`):** flagship OOS Sharpe 0.93 on the 24-sleeve menu — numbers shift by
~0.01-0.02 with the menu, every ranking and conclusion unchanged.

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
