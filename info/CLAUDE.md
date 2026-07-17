# CLAUDE.md — how this project works

Orientation doc for Claude (or any agent / the author) picking up this repo. Read this first.
For the *product vision and roadmap*, see [vision.md](vision.md). For the *actionable task
backlog*, see [TODO.md](TODO.md). For the *conceptual diversification thesis*, see
[factor-diversification-thesis.md](factor-diversification-thesis.md). For the *Phase 3 portfolio
optimizer* (the unified method, v2 — engine + regime/maximin + walk-forward BUILT 2026-07;
dashboard tab 3c pending), see
[portfolio_optimization.md](portfolio_optimization.md). For the *literature canon* grounding the
optimizer and the regime forecasting (with adopt/adapt verdicts), see
[literature.md](literature.md) — index + verdicts — with implementation-grade deep dives
(formulas, algorithms, pitfalls; codeable without fetching the papers) in
[literature/](literature/).

---

## 1. What this is (today)

A reproducible pipeline + analytics toolkit + dashboard for studying **MSCI factor indices across
7 regions** (Reference, Momentum, Enhanced Value, Quality) over ~28 years of monthly data, with a
focus on: factor-vs-reference performance, macro-regime behaviour, cross-index correlations,
**index↔macro-indicator correlations** (16 FRED indicators, level + change bases, lead/lag), and
**look-through concentration** (real sector / country / single-stock exposure of a portfolio).

It is the empirical foundation for the larger product described in `vision.md`.

## 2. Directory layout

```
portfolio_lab/                     (repo root)
├── info/                          docs for humans & agents
│   ├── CLAUDE.md                  ← this file
│   ├── vision.md                  north-star product + roadmap
│   └── factor-diversification-thesis.md   conceptual rationale (no backtest numbers)
├── data/
│   ├── raw/msci_indexes/<REGION>/ source files: *Monthly.xlsx (returns) + *.pdf (factsheets)
│   └── processed/                 tidy CSVs (REGENERABLE — gitignored)
├── outputs/                       analytics CSVs, REPORT.md, diversification/, dashboard.html (REGENERABLE — gitignored)
├── src/portfolio_lab/             the Python package (see §4)
├── scripts/run_pipeline.py        one command to rebuild everything
├── tests/test_pipeline.py         data-integrity checks
├── requirements.txt, pyproject.toml
```

**Rule:** everything under `data/processed/` and `outputs/` is generated. Never hand-edit it —
change the code and re-run the pipeline. Only `data/raw/` is a source of truth (plus the
hard-coded Asia figures in `ingest/asia_images.py`).

## 3. How to run

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py          # raw -> processed -> analytics -> dashboard
python tests/test_pipeline.py           # data-integrity checks
python tests/test_optimizer.py          # optimizer-stack unit tests (or: python -m pytest tests/ -q)
open outputs/dashboard.html             # double-click; Plotly loads from CDN
```
Individual stages (from repo root, src is auto-added to path by scripts/tests):
```bash
python -m portfolio_lab.ingest.returns
python -m portfolio_lab.ingest.macro          # FRED fetch (uses FRED_API_KEY from .env if set)
python -m portfolio_lab.analytics.engine
python -m portfolio_lab.analytics.macro_link  # index<->macro correlations (needs macro_monthly.csv)
python -m portfolio_lab.portfolio.diversification
python -m portfolio_lab.portfolio.optimizer --return 5 --risk 5 --div 5   # or --maximin
python -m portfolio_lab.portfolio.validation  # walk-forward OOS backtest only
python -m portfolio_lab.portfolio.visualize   # comparison charts -> outputs/analytics/optimizer/optimizer_viz.html
python -m portfolio_lab.dashboard.build
```
> To run a bare `python -m portfolio_lab.*` you must have `src/` on `PYTHONPATH`
> (`export PYTHONPATH=src`) or `pip install -e .`. The pipeline/test scripts handle this themselves.

## 4. Module map (where to find things)

| Module | Responsibility |
|---|---|
| `config.py` | **All paths and domain constants.** Regions, factor types, GICS sectors, country-name fixes, concentration thresholds, macro-link settings (`MACRO_MIN_OVERLAP_MONTHS`, `MACRO_LAGS`), `factor_type()`, and **`load_registry()`** (reads the index manifest). Loads `.env` (e.g. `FRED_API_KEY`) at import. Import paths from here — never hard-code. |
| `ingest/returns.py` | Iterates the **registry**; reads each index's `*Monthly.xlsx` → `returns_monthly_long.csv` (+`ret`) and `levels_wide.csv`. |
| `ingest/factsheets.py` | Iterates registry rows with a PDF; parses each factsheet `*.pdf` → `sector_weights / country_weights / top_constituents / index_meta`. Handles 3 constituent-table layouts; `clean_name()` fixes pdfplumber row-merge. |
| `ingest/asia_images.py` | Appends the 2 AC Asia ex Japan factor indices with no PDF (transcribed from web screenshots, `source=msci_web_image`). **Run after factsheets.** |
| `ingest/macro.py` | Historical macro indicators from **FRED** → `macro_monthly.csv` (+`macro_meta.csv`), month-end aligned. **16 indicators** (added `breakeven_10y`/`breakeven_5y` = T10YIE/T5YIE market inflation expectations, `us_recession` = NBER USREC, and `baa10y_spread` = BAA10Y full-history credit stress — all for the 4-quadrant classifier below). Official JSON API when `FRED_API_KEY` is set, else keyless CSV endpoint. Uses `certifi` for SSL. |
| `ingest/ff_factors.py` | **Fama-French research factors** (Ken French data library, free, not FRED) → `ff_factors_monthly.csv`: Mkt-RF/SMB/HML/RF from 1926-07, Mom from 1927 — ~100 years, monthly, fractions. Research proxies for the regime layer, **not investable sleeves** (deliberately outside the index registry). Network-dependent; WARNs and keeps the previous file on failure, like `ingest/macro.py`. |
| `ingest/asset_classes.py` | **Non-equity PROXY sleeves** (data roadmap P1, free slice) → `asset_class_monthly.csv`: `Asset \| US Treasury 10y` (total return CONSTRUCTED from `ust_10y` via the Swinkels-2019 carry+duration+convexity par-bond approximation — sanity-tested vs known years: 2008 +21%, 2022 −16%), `Asset \| Gold` (datasets/gold-prices LBMA mirror, 1833+, floats post-1971), `Asset \| Cash (T-bill)` (FF `rf`). Proxies, not investable sleeves — no registry row, no factsheets. Only gold needs network (WARNs on failure). |
| `analytics/long_history.py` | **Long-history regime proxy** (data roadmap P2): joins the FF factors with `classify_states(start="1926-01-01")` — classifiable from 1960 (core PCE start), ~789 months ≈ 2.2× the modern window, including the real 1970s Stagflation. Per-quadrant factor stats long-vs-modern + a **sign-agreement verdict** (first run 2026-07: 15/16 cells agree; Value-in-Stagflation and Momentum patterns are structural; the market factor's Stagflation direction is the one era-specific flip). Outputs `outputs/analytics/long_history/` (`long_history_factor_states.csv`, `REPORT_long_history.md`). Research layer only — wiring agreed patterns into the regime views' Q is a recorded TODO follow-up. |
| `portfolio/proxy_backtest.py` | **The 60-year construction-rule race** (roadmap A1): same rules/engines/honesty protocol as the MSCI walk-forward, on the proxy universe. Equity race (6 FF size×value portfolios, OOS **1936→2026**, ~90y): HRP 0.76 > ERC 0.75 ≈ 1/N 0.74 > **min-variance 0.71 — its modern-era win does NOT generalize** (era-specific, consistent with the low-vol-anomaly caveat). Multi-asset race (+bond/gold/cash, OOS **1972→2026** incl. the real 1970s; Sharpe = excess over the cash sleeve, else hiding in T-bills scores absurdly): **ERC 0.64 wins; maximin sleeve≤25% 0.59 beats 1/N 0.58 and unconstrained maximin 0.56**; min-var/HRP degenerate into cash (excess ≈0.07) — design lesson: cap or exclude cash for those engines. Outputs `outputs/analytics/proxy_backtest/`. **A2 window-robustness** (`--dispersion` CLI, not a pipeline stage): each race re-run dropping 0/36/72/108 early months → dispersion table (`REPORT_window_robustness.md`). Verdict: **HRP and ERC beat 1/N in 100% of equity-race windows** (HRP top rule in 75%); min-var only 25%; multi-asset ERC most robust (beats 1/N 75%). |
| `portfolio/stress.py` | **Named-episode stress library** (roadmap A3, pipeline stage 13): constant-mix replay of hand-dated episodes (`config.STRESS_EPISODES_*`). Modern table = today's flagships+anchors through dot-com/GFC/COVID/2022 (e.g. 2022: all-weather −17% vs −27% equity portfolios). Historic table = static archetypes (pure equity / 60-40 / all-weather static) through a century of storms on the proxy universe — OPEC stagflation: **all-weather +9.8% vs pure equity −44.6%**. Outputs `outputs/analytics/stress/`. |
| `analytics/regimes.py` | `REGIMES`: 10 hand-dated historical eras with analyst annotations (macro/factors/regions/shift) — event-driven narrative labels ("GFC," "dot-com bust"). Data only. Distinct from the systematic classifier below. |
| `analytics/engine.py` | Performance summary (CAGR/vol/Sharpe/maxDD, one number per series over the common window — no more "cw_"/"full_" split), factor-vs-reference, per-regime performance, correlation matrices (full + per regime), 36m rolling correlation, and `REPORT.md`. |
| `analytics/macro_link.py` | **Index↔macro correlation engine.** For each of the 21 return series × 16 indicators: contemporaneous + lagged (0/1/3/6/12m, macro leads) correlations on **two bases** — `chg` (Δ month-over-month, the sound basis) and `level` (regime context only) — plus univariate OLS betas. 36-month min-overlap guard flags short pairs as insufficient. Also computes **per-(named)-regime** correlation matrices (chg basis, lag 0; lower 6-month overlap floor since regimes run as short as ~15 months — `regime_correlations()`). Outputs to `outputs/analytics/macro/` (long CSV, two wide 21×16 matrices, betas, `correlation_by_regime/*.csv`, `REPORT_macro.md`). |
| `analytics/macro_state.py` | **4-quadrant macro-state classifier (v2, composite)** — systematic, month-by-month (growth trend × inflation trend → Goldilocks/Reflation/Deflationary-bust/Stagflation). Growth and inflation are each a **composite of several indicators' z-scored, sign-adjusted trends** (`config.MACRO_STATE_GROWTH_COMPONENTS` / `_INFLATION_COMPONENTS`; primaries `indpro_yoy` / `core_pce_yoy` required, short-history components join when available). Produces **continuous scores + soft quadrant probabilities** (Φ of the scores, product across the two axes) alongside the hard label (= most probable quadrant = sign of the scores), plus an **empirical monthly Markov transition matrix** (`transition_matrix()`, persistence + expected durations) and a **short-horizon probabilistic outlook** (`quadrant_outlook()`: soft vector × P^3 — the best-calibrated method in the 2026-07 walk-forward backtest recorded in TODO.md). `classify_states()`/`transition_matrix()` are reused by `analytics/scenario.py`. Also computes per-state performance for all 21 series, **factor-level attribution**, and an NBER-recession overlap sanity check in the report. Outputs to `outputs/analytics/macro_state/` (`macro_state_monthly.csv`, `macro_state_transitions.csv`, `macro_state_performance.csv`, `macro_state_factor_attribution.csv`, `REPORT_macro_state.md`). See caveats §7 (#14 NaN pitfall, #17 v2 simplifications). |
| `analytics/scenario.py` | **Regime-persistent bootstrap scenario simulation (v2)**. Monte Carlo in **regime spells**, not i.i.d. months: spell durations are geometric from the transition matrix's continuation probabilities (realistic regime persistence), and months within a spell are **contiguous blocks** of real history (partial within-regime serial correlation), always whole cross-sections (preserving cross-series correlation). Three built-in scenarios: `current_conditions` (**starts from today's actual quadrant**, spells then follow historical transition probabilities — `simulate_from_current()`), `historical_frequency`, `even_25_25_25_25` (weights mode: long-run month shares converge to the target weights via q ∝ w·(1−p_stay); `simulate_scenario(weights, ...)` keeps the custom-weights API). **`portfolio_cone(weights_by_series)`** runs a weighted blend through the `current_conditions` simulation and returns the portfolio-level CAGR cone + P(loss) — the optimizer's validator. Outputs simulated CAGR/maxDD percentiles + probability of cumulative loss per series, to `outputs/analytics/scenario/` (`scenario_summary.csv`, `REPORT_scenario.md`). Explicitly non-ML (resampling + empirical transition counts) — see caveat §11; the method is a state-conditioned **stationary bootstrap (Politis-Romano 1994)**, cited in the docstring. |
| `portfolio/diversification.py` | `analyze_portfolio({index: weight})` → look-through sector/country/stock exposure, HHI, threshold flags, **plus blended portfolio performance** (`portfolio_performance()`: constant-mix CAGR/vol/Sharpe/maxDD over the sleeves' overlapping history, via `analytics.engine._perf_stats`). **Weights must sum to 100%** (`config.PORTFOLIO_WEIGHT_TOLERANCE_PCT`) — raises `ValueError` rather than silently rescaling (e.g. a 340%-summing input is rejected, not renormalized). Reusable API + CLI. |
| `portfolio/shrinkage.py` | **Ledoit-Wolf covariance shrinkage** — constant-correlation target (default, "Honey, I Shrunk…") + scaled-identity variant (sklearn-equivalent test oracle). Closed-form, returns `(Sigma, delta*)`; δ* is reported in optimizer output as an input-quality number. |
| `portfolio/anchors.py` | **μ-free structural engines**: `equal_weight` (1/N), `erc_weights` (equal risk contribution, Spinu convex form — the optimizer's neutral anchor), `hrp_weights` (López de Prado's 3-stage HRP), `min_var_weights`, `risk_contributions` (Euler RC vector, reused in reporting). All long-only, sum to 1, consume the shrunk Σ. |
| `portfolio/views.py` | **Black-Litterman layer — the only place expected returns are produced.** `implied_returns` (Π = δΣw₀, δ calibrated to the anchor's own history), `posterior` (master formula; τ=1/T, He-Litterman Ω, confidence capped at 0.95), `regime_views` (relative factor-vs-Reference views with Q outlook-weighted and confidence = the Markov outlook's probability mass; optionally **anchored on 66y of Fama-French history** via `long_history.msci_factor_prior` — where both eras agree on a cell's sign, Q shrinks toward β·f_long weighted by months of evidence; disagreeing cells and Quality stay modern-only). No views ⇒ μ_BL = Π ⇒ optimizer returns the anchor (unit-tested). |
| `portfolio/optimizer.py` | **The multi-objective optimizer (unified method — see [portfolio_optimization.md](portfolio_optimization.md)).** Objectives: return (w·μ_BL only), risk (shrunk-Σ vol \| empirical blended maxDD), diversification (geometric mean of look-through effective bets, exact quadratic forms), regime row (per-quadrant scores), maximin mode (epigraph). Utopia/nadir 0–100 normalization → scorecard; multi-start SLSQP; caps as implicit shrinkage (40%/sleeve default; ≥m sleeves = cap just under 1/(m−1)); **geographic look-through caps** (`geo_cap` + `config.OPTIMIZER_GEO_ZONES` — zone exposure w·Z from factsheet country weights, so "EM" counts as the Asia it holds; linear constraints); **factor caps** (`factor_cap`, w·F per sleeve-label bucket — closes the third concentration axis; the **"Maximin (diversified)" preset** = sleeve ≤25% + geo ≤40% + factor ≤40%, `OPTIMIZER_DIVERSIFIED_*`/`OPTIMIZER_FACTOR_CAP_PCT`, is the recommended robust mode: unconstrained maximin is structurally a corner solution, and the measured trade-off is that on equities alone forcing spread erases the stagflation floor (+0.31→+0.015%/mo — it WAS the concentrated Value bet) while with bonds/gold it's nearly free (+0.59 vs +0.73); OOS Sharpe 0.84 vs 0.73 unconstrained); hard targets as constraints with explicit "NOT ACHIEVABLE" reporting; corner-solution warnings. **`include_asset_classes=True` opt-in** appends the bond/gold/cash proxy sleeves (period-aligned — business vs calendar month-ends differ; exempt from geo caps; own category in the diversification HHIs). **Equity-only stays the product default** (house thesis; profiles opt in). `run()` = pipeline stage 13: benchmark table (1/N/ERC/HRP/min-var always), flagship portfolios (balanced 5/5/5, maximin, geo-capped maximin, **all-weather maximin** — measured 2026-07: worst-quadrant floor +0.31%→+0.73%/mo, vol 23.9%→13.5%, maxDD −61%→−34%, CAGR −1.5pt, buying 40% gold + 13% bonds), scenario cones (skipped for portfolios holding proxy sleeves — not in the scenario universe yet), walk-forward table → `outputs/analytics/optimizer/` (`REPORT_optimizer.md`, `optimizer_portfolios.csv`). Degrades gracefully without macro. CLI for custom runs. |
| `portfolio/visualize.py` | **Optimizer comparison visualization** — self-contained `outputs/analytics/optimizer/optimizer_viz.html` (Plotly CDN, same pattern/theme as the dashboard; no new dependency). 7 captioned charts: walk-forward cumulative race, OOS scoreboard, sleeve-vs-portfolio risk/return map, per-quadrant bars (the maximin story), Π-vs-μ_BL dumbbells (the BL tilt made visible), weights-vs-risk-contribution pairs, scenario cones, **plus an appendix "66-year reality check"** (the Fama-French long-history study rendered: Value/Momentum per-quadrant modern-vs-66y bars + the 15/16 era-agreement verdict — reads `analytics/long_history.build()`). Each section is Tier-1/Tier-2 layered: plain-language caption on top + a collapsible "Method, math &amp; sources" block (formulas, primary papers with links, pointer to the repo deep dive + code). Reuses the walk-forward CSVs cached by the optimizer stage when present (recomputes otherwise, ~1 min). CLI only, not a pipeline stage. |
| `portfolio/rules.py` | **Rule-based strategies tested as walk-forward contestants** (not optimizer portfolios): `momentum_weights` (Jegadeesh-Titman cross-sectional 12-1, top-K equal weight) and `vol_managed` (unlevered Moreira-Muir volatility targeting — scale a base portfolio's exposure down toward a vol target, hold cash, never lever up; causal). `OPTIMIZER_MOMENTUM_*` / `OPTIMIZER_VOLTARGET_*` config. 2026-07 verdict: neither beat min-variance OOS. |
| `portfolio/validation.py` | **Walk-forward OOS backtest** (literature directive 7): expanding window (120m warmup, annual refits, `OPTIMIZER_WF_*` config), everything re-estimated on train only; contestants 1/N, min-var, ERC, HRP, balanced sliders, maximin (±geo-cap), **plus the `rules.py` challengers (momentum, vol-target overlays)**; returns **net of `OPTIMIZER_TC_BPS` transaction cost** on one-way turnover (`oos_sharpe_gross` = pre-cost) → `optimizer_walkforward.csv`/`_returns.csv` + report section. First result (2026-07): min-var best OOS Sharpe (net); balanced blend, momentum and vol-targeting all did NOT beat it — stated in the report, per the honesty principle. |
| `dashboard/build.py` | Bakes all data as JSON into `outputs/dashboard.html`. Macro, macro-state and scenario data are each optional — their tabs degrade gracefully when the files are absent (e.g. after `--no-macro`). |
| `dashboard/template.py` | The static HTML shell + browser JS (`__DATA__`/`__JS__` placeholders). Edit here for UI. **Visual identity (v1, 2026-07): light "research note" theme** — paper `#FBFBFD`/ink `#1D1D1F`, governing rule *chrome is monochrome, color only means data* (regime + factor hues are the only saturated pixels); type trio Newsreader italic (wordmark only) / Instrument Sans (UI) / IBM Plex Mono (all numbers, dates, pills — Google Fonts CDN, falls back to system offline); signature element = the 3px **regime ribbon** under the nav (the full monthly quadrant timeline as real-data brand mark) + current-regime chip in the header. `SCOLOR`/`FCOLOR`/`P` at the top of the JS are the palette single-source — keep new charts on them. **7 tabs**: **Performance** (single CAGR/vol/Sharpe/maxDD driven by a live date-range picker, defaulting to the common window; the cumulative-growth chart **rebases every series to 100 at the start of whatever range is selected** — `rebasedTraces()` — so the comparison is fair regardless of each index's own inception date; recomputed client-side in JS from the baked level series, so the formula must stay in sync with `analytics/engine.py`'s `_perf_stats`), Factor vs Reference, Regimes, Correlations, Macro (regime-shaded indicator chart, index↔macro heatmap with level/Δ toggle, per-series top-drivers bar), **Macro State** (Tier-1 current-quadrant verdict card with the soft probability read, persistence AND the 3-month Markov outlook pills; the **4-quadrant position chart** — current dot on continuous composite scores so it can straddle borders, trail of past months, month picker showing the actual forward path from any past date, direction-only momentum arrow, **empirical 3-month cone** (percentile boxes + re-anchored historical outcome dots conditioned on the current state), per-selected-month Markov outlook line, and a collapsible full-methodology block, all computed client-side from the baked scores/probs/transitions/`method` params; a Tier-2 **"Similar past months" analog panel** — k-nearest past months by scores+velocities with their 3-month outcomes and an optional top-5 path overlay on the chart; colored 4-quadrant month-by-month timeline; per-state index performance bars with state selector; factor-edge-by-state grouped bars; and the Monte Carlo scenario chart — median dot + p5–p95 range per series with a scenario selector incl. `current_conditions`), Diversification (live what-if — sleeve weights must sum to 100%, shown as a red/green total pill; blended portfolio CAGR/vol/Sharpe/maxDD computed live via the shared `computeSeriesStats()` helper, same one the Performance tab uses). |

## 5. Data flow

```
data/index_registry.csv ──drives which indexes exist & where their data comes from──┐
                                                                                     ▼
data/raw/msci_indexes/<REGION>/<returns_file>.xlsx ─ingest.returns──► returns_monthly_long.csv, levels_wide.csv
data/raw/msci_indexes/<REGION>/<weights_file>.pdf  ─ingest.factsheets► sector/country/top_constituents/index_meta.csv
                                                    ─ingest.asia_images (webweights rows: append 2 index sets)
FRED (network) ─ingest.macro──► macro_monthly.csv, macro_meta.csv
levels_wide.csv + regimes ─analytics.engine──► outputs/analytics/*  (+ REPORT.md)
levels_wide.csv + macro_monthly.csv ─analytics.macro_link──► outputs/analytics/macro/*  (+ REPORT_macro.md)
macro_monthly.csv ─analytics.macro_state──► outputs/analytics/macro_state/*  (+ REPORT_macro_state.md)
macro_state's classify_states() + levels_wide.csv ─analytics.scenario──► outputs/analytics/scenario/*
Ken French library (network) ─ingest.ff_factors──► ff_factors_monthly.csv
macro_monthly.csv (ust_10y) + gold mirror (network) + ff rf ─ingest.asset_classes──► asset_class_monthly.csv
ff_factors_monthly.csv + classify_states(start=1926) ─analytics.long_history──► outputs/analytics/long_history/*
weights CSVs ─portfolio.diversification──► outputs/diversification/*
levels_wide.csv + weights CSVs + macro_state outputs ─portfolio.optimizer (+validation, scenario.portfolio_cone)──► outputs/analytics/optimizer/*
all of the above ─dashboard.build──► outputs/dashboard.html
```

### The index registry — single source of truth for tracked indexes
`data/index_registry.csv` lists every tracked index (one row each) so "what indexes exist" is
explicit, not implied by which folders happen to exist. Columns:

| column | meaning |
|---|---|
| `index_id` | MSCI numeric code (also prefixes the returns filename) |
| `display_name` | full index name (as it appears in the returns xlsx) |
| `region`, `factor_type` | the series key — **unique together** |
| `source` | how ingest loads it: `msci_local` (xlsx + factsheet pdf) · `msci_local_webweights` (xlsx local, weights via `ingest/asia_images.py`) · *(future: `api`)* |
| `returns_file` | xlsx basename inside `data/raw/msci_indexes/<region>/` |
| `weights_file` | factsheet pdf basename, or empty (webweights / none) |

**To add a new MSCI index (manual):** drop its xlsx (and factsheet pdf) into
`data/raw/msci_indexes/<region>/`, append one row to `index_registry.csv`, and rerun
`python scripts/run_pipeline.py`. No code edit. (A genuinely new *region* also needs one line in
`config.REGIONS` for display ordering.)

**To add an API-sourced index (future):** add a row with `source=api` (using `returns_file` /
`weights_file` to hold a ticker or endpoint) and implement one new branch in `ingest/returns.py`
keyed on `source`. The registry contract stays the same — see TODO.md.
Macro ingest needs network; skip it (and macro_link/macro_state/scenario, which all depend on
macro data) offline with `python scripts/run_pipeline.py --no-macro` (this also skips the
FF-factor fetch, asset-class proxies and long-history study, which need network/macro). Pipeline
is 14 steps; see
`scripts/run_pipeline.py`.

## 6. Data model / conventions

- **Series key:** a series is identified by `region` + `factor_type` (7 × up to 4). In
  `levels_wide.csv` the column label is `"<region> | <factor_type>"`.
- **Regions (7):** `ACWI, World, World_ex_USA, USA, EM, Europe, AC_Asia_ex_Japan`.
- **Factor types (4):** `Reference, Momentum, Enhanced Value, Quality` (coverage is uneven — see §7).
- **Levels** are month-end, net return, USD, rebased to 100. **Returns** are simple monthly % change.
- **Weights** (`weight_pct`) are percentages 0–100; `source` ∈ {`factsheet_pdf`, `msci_web_image`}.
- All factsheet weights are as of `config.FACTSHEET_ASOF` (2026-06-30).

## 7. Known caveats (read before trusting a join or a comparison)

1. **EM naming mismatch — IMPORTANT.** Returns use `MSCI EM (Emerging Markets) …` (from XLSX);
   weight tables use `MSCI Emerging Markets …` (from PDF). **Join on `region`+`factor_type`, not
   on `index_name`.**
2. **USA has no country chart.** USA indices are single-country → no `country_weights` rows.
   The diversification tool injects 100% United States for them.
3. **Uneven factor coverage.** Not every region has all 3 factors (e.g. World_ex_USA has only
   Enhanced Value; USA has Momentum + Quality but no Enhanced Value). Cross-region factor
   comparisons are not always apples-to-apples.
4. **Stock look-through is a lower bound** — only each index's top-10 holdings are known.
5. **Asia factor weights are 1-decimal** (from screenshots) → sector sums round to ~99.5%.
6. **Common analysis window is 1998-12-31 → 2026-06-30** (330 months) because Reference indices
   start later than the factor indices (which go back to 1997).
7. **Regime annotations are analyst priors.** The engine computes realized numbers alongside them
   so they can be confirmed/challenged — don't treat the narrative as the result.
8. **Macro series have uneven start dates** (e.g. broad USD index from 2006). The macro_link
   engine aligns per-pair on overlapping months and flags pairs under 36 months as insufficient
   rather than reporting noise.
9. **`hy_credit_spread` (BAMLH0A0HYM2) only has history from 2023** — ICE Data Indices restricts
   historical redistribution through FRED (verified against real API + key; not a code issue).
   All its macro-link pairs are flagged insufficient. `BAA10Y` (Moody's Baa − 10Y, from 1986) is
   the standard full-history substitute — **now ingested as `baa10y_spread` (2026-07)** and used
   in the macro-state classifier's composite growth signal.
10. **Macro-link output is exploratory/descriptive**: many pairwise correlations, no significance
    testing. `chg` basis (Δ) is the statistically sound one; `level` basis is regime context —
    persistent series make level correlations prone to spuriousness.
11. **FRED terms of use prohibit using FRED data for AI/ML training.** Statistical/deterministic
    methods (correlations, optimization, regime rules) are fine; if vision.md Phase 4 (ML/RL)
    is ever built, its macro features must come from a different source than FRED.
    **The line, decided 2026-07 while scoping the classifier/scenario v2 redesign:** anything
    that *counts, normalizes or resamples* history (rolling means, z-scores, empirical Markov
    transition counts, bootstrap, linear momentum extrapolation) stays on the allowed side;
    anything *fitted/trained to predict* (regression forecasts, EM-fitted HMMs, any ML) is
    Phase 4 and needs non-FRED macro data. The v2 classifier + scenario simulation were built
    entirely on the allowed side.
12. **The stats formula (CAGR/vol/Sharpe/maxDD) is implemented twice, independently** — once in
    Python (`analytics/engine.py::_perf_stats`, used by the CSV/report and by
    `portfolio/diversification.py`'s blended portfolio stats) and once in JS
    (`dashboard/template.py::computeSeriesStats`, shared by both the Performance tab's date-range
    recompute and the Diversification tab's blended-portfolio recompute — one JS implementation,
    not three). Verified to match Python (~5-6 significant figures). **If you change the formula
    in one, update the other** — nothing enforces they stay in sync.
13. **`breakeven_10y`/`breakeven_5y` only start 2003** (TIPS breakeven inflation didn't exist as a
    published series before then). **`us_recession`, unusually, has genuine data back to 1854**
    (NBER's full business-cycle dating). `macro_state.py` clips its classification to the return
    series' own start (1997+) precisely so "historical frequency of each state" isn't distorted by
    depression-era history.
14. **pandas' `>`/`<` comparison silently returns `False` (not `NaN`) when either side is `NaN`.**
    `macro_state.py`'s trend classification hit this directly: months with not-yet-released
    macro prints (industrial production / core PCE lag ~1-2 months behind e.g. VIX) were being
    silently classified as "decelerating" instead of excluded, because the raw boolean comparison
    doesn't propagate NaN like arithmetic does. Fixed via an explicit `.where(...notna() & ...notna())`
    mask — **any new trend/threshold comparison on a possibly-NaN macro series needs the same
    guard**, the bug is easy to reintroduce.
15. **Scenario simulation assumes history repeats, and says so.** `analytics/scenario.py`
    bootstraps future paths by reshuffling *actual* 1997-2026 monthly returns, weighted by macro
    quadrant. This is explicitly not a forecast — it's "what would a similar macro mix have
    historically produced," a stated assumption, not a hidden one. It samples whole historical
    months (not each series independently) specifically to preserve real cross-series correlation
    within each simulated month.
16. **`ingest/macro.py` silently skips a series if its FRED fetch fails** (broad `except
    Exception`, prints a `[macro] WARN ... failed` line and continues without that column). This
    was hit once during development — a transient fetch blip dropped `cpi_yoy` for one run, fixed
    on retry, no code bug. It means: if a downstream module using a specific column (e.g.
    `macro_state.py` hardcodes `indpro_yoy`/`core_pce_yoy`) runs right after a partial fetch
    failure, it will `KeyError` rather than degrade gracefully. Re-run `ingest.macro` (or the
    pipeline) if you see a `WARN` line before trusting the rest of the macro-dependent steps.
    (The v2 classifier tolerates missing *secondary* composite components — only the two
    primaries hard-fail.)
17. **Macro-state v2's stated simplifications** (documented in the module + the dashboard's
    "how is this computed" block): component z-scores are normalized by each trend's
    *full-sample* std — a mild look-ahead that only affects scale/component weighting, never
    the primary trend's direction; the growth and inflation axes are treated as independent
    when multiplying into quadrant probabilities; the dashboard's forecast arrow is a pure
    linear momentum extrapolation (avg monthly score change over the last 6 months × 6-month
    horizon), deliberately not a fitted model — and the 2026-07 walk-forward backtest (results
    in TODO.md) showed it must be read as DIRECTION-ONLY: its direction gives the best hard
    quadrant call, but any extrapolated length predicts the dot's position worse than assuming
    no movement, which is why the dashboard pairs it with the empirical cone and Markov outlook.
    When exploring a past date in the dashboard, the transition matrix, cone pool and analog
    search all use the full sample (exploration convenience, not an out-of-sample replay).
    Changing any classifier constant reshuffles the
    hard labels and therefore per-state performance, attribution AND scenario outputs — they
    all share `classify_states()`.
18. **The optimizer never sees raw historical mean returns.** The only expected-return vector any
    objective consumes is the Black-Litterman posterior μ_BL (`portfolio/views.py`) — anchored on
    ERC-implied returns and tilted only by confidence-weighted regime views. Per-quadrant means
    μ̂_q do enter the regime/maximin objectives directly (that's the signature feature, licensed
    by Ang-Bekaert), guarded by the caps + corner warnings + scenario/walk-forward validation.
    If you add a new objective, keep this line: raw full-sample μ̂ is forbidden by the evidence
    (info/literature.md §4, directive 2). Also note: the walk-forward in
    `portfolio/validation.py` re-estimates everything on the training window, but the
    macro-state labels retain the classifier's mild full-sample z-normalization (caveat #17) —
    stated in the report.

## 8. Extending it (conventions to keep)

- New paths/constants → `config.py` only.
- New pipeline stage → expose a uniform `run()` entrypoint in the module and wire it into `run_pipeline.py`.
- Keep generated artifacts out of `data/raw/`; keep hand-authored facts in code, not in CSVs.
- After any change, `python scripts/run_pipeline.py && python tests/test_pipeline.py` must pass.
- The dashboard is self-contained by design (single HTML). Keep new tabs data-driven from the
  baked JSON so it stays serverless.
