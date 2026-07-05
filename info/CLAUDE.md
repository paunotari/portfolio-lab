# CLAUDE.md — how this project works

Orientation doc for Claude (or any agent / the author) picking up this repo. Read this first.
For the *product vision and roadmap*, see [vision.md](vision.md). For the *conceptual diversification
thesis*, see [factor-diversification-thesis.md](factor-diversification-thesis.md).

---

## 1. What this is (today)

A reproducible pipeline + analytics toolkit + dashboard for studying **MSCI factor indices across
7 regions** (Reference, Momentum, Enhanced Value, Quality) over ~28 years of monthly data, with a
focus on: factor-vs-reference performance, macro-regime behaviour, cross-index correlations,
**index↔macro-indicator correlations** (12 FRED indicators, level + change bases, lead/lag), and
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
python tests/test_pipeline.py           # or: python -m pytest tests/ -q
open outputs/dashboard.html             # double-click; Plotly loads from CDN
```
Individual stages (from repo root, src is auto-added to path by scripts/tests):
```bash
python -m portfolio_lab.ingest.returns
python -m portfolio_lab.ingest.macro          # FRED fetch (uses FRED_API_KEY from .env if set)
python -m portfolio_lab.analytics.engine
python -m portfolio_lab.analytics.macro_link  # index<->macro correlations (needs macro_monthly.csv)
python -m portfolio_lab.portfolio.diversification
python -m portfolio_lab.dashboard.build
```
> To run a bare `python -m portfolio_lab.*` you must have `src/` on `PYTHONPATH`
> (`export PYTHONPATH=src`) or `pip install -e .`. The pipeline/test scripts handle this themselves.

## 4. Module map (where to find things)

| Module | Responsibility |
|---|---|
| `config.py` | **All paths and domain constants.** Regions, factor types, GICS sectors, country-name fixes, concentration thresholds, macro-link settings (`MACRO_MIN_OVERLAP_MONTHS`, `MACRO_LAGS`), `factor_type()`. Loads `.env` (e.g. `FRED_API_KEY`) at import. Import paths from here — never hard-code. |
| `ingest/returns.py` | `*Monthly.xlsx` → `returns_monthly_long.csv` (+`ret`) and `levels_wide.csv`. |
| `ingest/factsheets.py` | Factsheet `*.pdf` → `sector_weights / country_weights / top_constituents / index_meta`. Region from folder; handles 3 constituent-table layouts; `clean_name()` fixes pdfplumber row-merge. |
| `ingest/asia_images.py` | Appends the 2 AC Asia ex Japan factor indices with no PDF (transcribed from web screenshots, `source=msci_web_image`). **Run after factsheets.** |
| `ingest/macro.py` | Historical macro indicators from **FRED** → `macro_monthly.csv` (+`macro_meta.csv`), month-end aligned. Official JSON API when `FRED_API_KEY` is set, else keyless CSV endpoint. Uses `certifi` for SSL. |
| `analytics/regimes.py` | `REGIMES`: 10 macro regimes with dated boundaries + analyst annotations (macro/factors/regions/shift). Data only. |
| `analytics/engine.py` | Performance summary, factor-vs-reference, per-regime performance, correlation matrices (full + per regime), 36m rolling correlation, and `REPORT.md`. |
| `analytics/macro_link.py` | **Index↔macro correlation engine.** For each of the 21 return series × 12 indicators: contemporaneous + lagged (0/1/3/6/12m, macro leads) correlations on **two bases** — `chg` (Δ month-over-month, the sound basis) and `level` (regime context only) — plus univariate OLS betas. 36-month min-overlap guard flags short pairs as insufficient. Outputs to `outputs/analytics/macro/` (long CSV, two wide 21×12 matrices, betas, `REPORT_macro.md`). |
| `portfolio/diversification.py` | `analyze_portfolio({index: weight})` → look-through sector/country/stock exposure, HHI, threshold flags. Reusable API + CLI. |
| `dashboard/build.py` | Bakes all data as JSON into `outputs/dashboard.html`. Macro data is optional — the tab degrades gracefully when absent. |
| `dashboard/template.py` | The static HTML shell + browser JS (`__DATA__`/`__JS__` placeholders). Edit here for UI. **6 tabs**: Performance, Factor vs Reference, Regimes, Correlations, **Macro** (regime-shaded indicator chart, index↔macro heatmap with level/Δ toggle, per-series top-drivers bar), Diversification (live what-if). |

## 5. Data flow

```
data/raw/msci_indexes/<REGION>/*.xlsx ─ingest.returns──► returns_monthly_long.csv, levels_wide.csv
data/raw/msci_indexes/<REGION>/*.pdf  ─ingest.factsheets► sector/country/top_constituents/index_meta.csv
                                       ─ingest.asia_images (append 2 rows-sets)
FRED (network) ─ingest.macro──► macro_monthly.csv, macro_meta.csv
levels_wide.csv + regimes ─analytics.engine──► outputs/analytics/*  (+ REPORT.md)
levels_wide.csv + macro_monthly.csv ─analytics.macro_link──► outputs/analytics/macro/*  (+ REPORT_macro.md)
weights CSVs ─portfolio.diversification──► outputs/diversification/*
all of the above ─dashboard.build──► outputs/dashboard.html
```
Macro ingest needs network; skip it (and macro_link) offline with
`python scripts/run_pipeline.py --no-macro`. Pipeline is 8 steps; see `scripts/run_pipeline.py`.

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
   the standard full-history substitute if credit stress is needed — not yet added.
10. **Macro-link output is exploratory/descriptive**: many pairwise correlations, no significance
    testing. `chg` basis (Δ) is the statistically sound one; `level` basis is regime context —
    persistent series make level correlations prone to spuriousness.
11. **FRED terms of use prohibit using FRED data for AI/ML training.** Statistical/deterministic
    methods (correlations, optimization, regime rules) are fine; if vision.md Phase 4 (ML/RL)
    is ever built, its macro features must come from a different source than FRED.

## 8. Extending it (conventions to keep)

- New paths/constants → `config.py` only.
- New pipeline stage → expose a uniform `run()` entrypoint in the module and wire it into `run_pipeline.py`.
- Keep generated artifacts out of `data/raw/`; keep hand-authored facts in code, not in CSVs.
- After any change, `python scripts/run_pipeline.py && python tests/test_pipeline.py` must pass.
- The dashboard is self-contained by design (single HTML). Keep new tabs data-driven from the
  baked JSON so it stays serverless.
