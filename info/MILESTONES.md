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
