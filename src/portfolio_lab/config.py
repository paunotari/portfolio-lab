"""Central configuration: filesystem paths and shared domain constants.

Every module imports paths from here — nothing hard-codes a relative path or assumes a
current working directory. Paths are derived from this file's location, so the pipeline runs
the same regardless of where it is invoked from.
"""
from __future__ import annotations
import csv
from pathlib import Path

# --- paths ---------------------------------------------------------------
PACKAGE_DIR = Path(__file__).resolve().parent          # src/portfolio_lab
PROJECT_ROOT = PACKAGE_DIR.parents[1]                   # repo root

# Load secrets (e.g. FRED_API_KEY) from a local, gitignored .env file at the repo root, if
# present. Copy .env.example -> .env and fill it in. Never hardcode secrets in the codebase.
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # python-dotenv not installed: env vars must be exported in the shell instead

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "msci_indexes"             # region subfolders: xlsx + pdf
MSCI_API_CACHE_DIR = DATA_DIR / "raw" / "msci_api"      # committed JSON cache for source=msci_api
PROCESSED_DIR = DATA_DIR / "processed"                  # tidy CSVs (regenerable)
INDEX_REGISTRY = DATA_DIR / "index_registry.csv"        # the manifest of tracked indexes

OUTPUT_DIR = PROJECT_ROOT / "outputs"
ANALYTICS_DIR = OUTPUT_DIR / "analytics"
CORR_REGIME_DIR = ANALYTICS_DIR / "correlation_by_regime"
DIVERSIFICATION_DIR = OUTPUT_DIR / "diversification"
DASHBOARD_HTML = OUTPUT_DIR / "dashboard.html"

# processed CSV file handles (single source of truth for filenames)
RETURNS_LONG = PROCESSED_DIR / "returns_monthly_long.csv"
LEVELS_WIDE = PROCESSED_DIR / "levels_wide.csv"
SECTOR_WEIGHTS = PROCESSED_DIR / "sector_weights.csv"
COUNTRY_WEIGHTS = PROCESSED_DIR / "country_weights.csv"
TOP_CONSTITUENTS = PROCESSED_DIR / "top_constituents.csv"
INDEX_META = PROCESSED_DIR / "index_meta.csv"
MACRO_MONTHLY = PROCESSED_DIR / "macro_monthly.csv"      # date x indicators (transformed)
MACRO_META = PROCESSED_DIR / "macro_meta.csv"            # one row per indicator
FF_FACTORS_MONTHLY = PROCESSED_DIR / "ff_factors_monthly.csv"  # Fama-French factors, 1926+
ASSET_CLASS_MONTHLY = PROCESSED_DIR / "asset_class_monthly.csv"  # bond/gold/cash proxy returns
# free LBMA gold price history (datasets/gold-prices mirror, monthly, 1833+; floats post-1971)
GOLD_PRICES_URL = "https://raw.githubusercontent.com/datasets/gold-prices/master/data/monthly.csv"
# EQUITY-ONLY IS THE PRODUCT DEFAULT (house thesis: equity indices are the productive asset).
# Non-equity sleeves are an OPT-IN (optimizer include_asset_classes=True) so other user
# profiles can complete the all-weather picture without imposing it on anyone.

# analytics output file handles
PERFORMANCE_SUMMARY = ANALYTICS_DIR / "performance_summary.csv"
FACTOR_VS_REFERENCE = ANALYTICS_DIR / "factor_vs_reference.csv"
REGIME_PERFORMANCE = ANALYTICS_DIR / "regime_performance.csv"
CORRELATION_FULL = ANALYTICS_DIR / "correlation_full.csv"
ROLLING_CORRELATION = ANALYTICS_DIR / "rolling_avg_correlation.csv"
ANALYTICS_REPORT = ANALYTICS_DIR / "REPORT.md"

# macro-link (index/factor returns <-> macro indicators) output file handles
MACRO_ANALYTICS_DIR = ANALYTICS_DIR / "macro"
MACRO_CORRELATIONS = MACRO_ANALYTICS_DIR / "macro_correlations.csv"
MACRO_CORR_CONTEMP_LEVEL = MACRO_ANALYTICS_DIR / "macro_corr_contemp_level.csv"
MACRO_CORR_CONTEMP_CHG = MACRO_ANALYTICS_DIR / "macro_corr_contemp_chg.csv"
MACRO_BETA = MACRO_ANALYTICS_DIR / "macro_sensitivity_beta.csv"
MACRO_REPORT = MACRO_ANALYTICS_DIR / "REPORT_macro.md"
MACRO_CORR_BY_REGIME_DIR = MACRO_ANALYTICS_DIR / "correlation_by_regime"

# 4-quadrant macro-state classifier (analytics/macro_state.py) output file handles
MACRO_STATE_DIR = ANALYTICS_DIR / "macro_state"
MACRO_STATE_MONTHLY = MACRO_STATE_DIR / "macro_state_monthly.csv"
MACRO_STATE_PERFORMANCE = MACRO_STATE_DIR / "macro_state_performance.csv"
MACRO_STATE_FACTOR_ATTRIBUTION = MACRO_STATE_DIR / "macro_state_factor_attribution.csv"
MACRO_STATE_TRANSITIONS = MACRO_STATE_DIR / "macro_state_transitions.csv"
MACRO_STATE_REPORT = MACRO_STATE_DIR / "REPORT_macro_state.md"

# 4-quadrant classifier settings. Growth and inflation are each a COMPOSITE of several
# indicators' trends (smoothed value now vs N months ago, z-scored per indicator, sign-adjusted,
# averaged) -- not a single hard-thresholded series. The map value is the SIGN: +1 means "this
# indicator rising = growth (or inflation) accelerating," -1 the opposite (e.g. unemployment
# rising = growth decelerating). The *_PRIMARY indicator must be present for a month to be
# classified at all; the other components are optional extras (they have shorter histories).
MACRO_STATE_GROWTH_PRIMARY = "indpro_yoy"
MACRO_STATE_GROWTH_COMPONENTS = {
    "indpro_yoy": +1,       # industrial production growth (primary real-activity proxy)
    "unemployment": -1,     # labor market (rising unemployment = slowing growth)
    "yc_10y_2y": +1,        # yield-curve slope (steepening = improving growth expectations)
    "vix": -1,              # equity risk stress (rising VIX = deteriorating environment)
    "baa10y_spread": -1,    # credit stress (widening spreads = deteriorating growth), 1986+
}
MACRO_STATE_INFLATION_PRIMARY = "core_pce_yoy"
MACRO_STATE_INFLATION_COMPONENTS = {
    "core_pce_yoy": +1,     # Fed's preferred gauge (primary)
    "cpi_yoy": +1,          # headline CPI
    "ppi_commodities_yoy": +1,  # pipeline/commodity pressure
    "breakeven_10y": +1,    # market-implied inflation expectations, 2003+
}
MACRO_STATE_SMOOTH_MONTHS = 3
MACRO_STATE_TREND_LAG_MONTHS = 6
# dashboard forecast arrow: linear momentum extrapolation of the composite scores' average
# monthly change over the last MOMENTUM months, projected HORIZON months ahead (a trend read
# computed live in the browser, not a fitted model -- see dashboard/template.py).
# Walk-forward backtest (2026-07, see info/TODO.md): the FULL-length arrow gives the best hard
# quadrant call (57.4% at 3m vs 51.7% persistence) but ANY extrapolated length worsens the
# position estimate vs no-change -- so the arrow is displayed as DIRECTION-ONLY guidance and the
# honest position range comes from the empirical cone + Markov outlook below.
MACRO_STATE_FORECAST_MOMENTUM_MONTHS = 6
MACRO_STATE_FORECAST_HORIZON_MONTHS = 6

# short-horizon probabilistic outlook + analogs (backtest-selected methods, 2026-07):
# outlook = transition matrix ^ OUTLOOK_MONTHS applied to the soft probability vector (best
# Brier score of all tested methods); analogs = the K nearest past months by (scores + 6m
# velocities, z-scored), excluding +/- ANALOG_EXCLUDE months around the anchor so "last month"
# doesn't trivially count as an analog.
MACRO_STATE_OUTLOOK_MONTHS = 3
MACRO_STATE_ANALOG_K = 20
MACRO_STATE_ANALOG_EXCLUDE_MONTHS = 6

# scenario simulation (analytics/scenario.py) output file handles
SCENARIO_DIR = ANALYTICS_DIR / "scenario"
SCENARIO_SUMMARY = SCENARIO_DIR / "scenario_summary.csv"
SCENARIO_REPORT = SCENARIO_DIR / "REPORT_scenario.md"
SCENARIO_YEARS = 10
SCENARIO_TRIALS = 2000
SCENARIO_SEED = 42

# portfolio optimizer (portfolio/optimizer.py) settings + output file handles.
# Defaults follow the unified method (info/portfolio_optimization.md): the 40% sleeve cap and
# min-sleeves guardrails are implicit shrinkage (Jagannathan-Ma 2003), not just prudence.
# min_sleeves is enforced through the cap: a cap of c forces at least ceil(1/c) sleeves, so
# forcing >= m sleeves means capping just under 1/(m-1). The 40% default already forces >= 3.
OPTIMIZER_DIR = ANALYTICS_DIR / "optimizer"
OPTIMIZER_REPORT = OPTIMIZER_DIR / "REPORT_optimizer.md"
OPTIMIZER_PORTFOLIOS = OPTIMIZER_DIR / "optimizer_portfolios.csv"
OPTIMIZER_WALKFORWARD = OPTIMIZER_DIR / "optimizer_walkforward.csv"
OPTIMIZER_WALKFORWARD_RETURNS = OPTIMIZER_DIR / "optimizer_walkforward_returns.csv"
OPTIMIZER_EXPOSURE = OPTIMIZER_DIR / "optimizer_exposure.csv"          # M12 diagnostics
OPTIMIZER_LORO = OPTIMIZER_DIR / "optimizer_loro.csv"                  # leave-one-region-out
OPTIMIZER_LORO_REPORT = OPTIMIZER_DIR / "REPORT_exposure_robustness.md"
OPTIMIZER_INFERENCE = OPTIMIZER_DIR / "optimizer_inference.csv"        # Sharpe inference

# Sharpe inference (Ledoit-Wolf 2008 studentized circular block bootstrap — see
# info/literature/sharpe-inference.md). Block=None -> auto T^(1/3).
OPTIMIZER_INFER_B = 4999
OPTIMIZER_INFER_BLOCK = None

# M13 follow-up: anchor the REGIONAL per-quadrant means (each region Reference blended
# toward beta_region * the FF market's 66y quadrant mean, agree-gated). MEASURED 2026-07
# (MILESTONES M15): a NO-OP for the equity maximin — its binding quadrant (Stagflation) is
# the market's one era-flipped cell, so the agree gate correctly blocks the transfer; on the
# all-weather universe it slightly HURT OOS (Sharpe 0.933->0.898). Default OFF; the
# mechanism stays for reproducibility (long_history.market_prior + _anchor_mu_q pass 1).
OPTIMIZER_ANCHOR_REGIONAL = False
OPTIMIZER_VIZ = OPTIMIZER_DIR / "optimizer_viz.html"
OPTIMIZER_MAX_SLEEVE_PCT = 40.0     # default per-sleeve cap (Tier-2 overridable)
OPTIMIZER_MIN_SLEEVES = 3           # implied by the 40% cap; kept explicit for overrides
OPTIMIZER_N_STARTS = 50             # multi-start SLSQP random starts (+ anchor + equal-weight)
OPTIMIZER_SEED = 7
# walk-forward validation (portfolio/validation.py): expanding window, annual refits, fewer
# starts per refit (each refit re-solves the whole normalization; 8 starts keeps it honest+fast)
OPTIMIZER_WF_WARMUP_MONTHS = 120
OPTIMIZER_WF_REFIT_MONTHS = 12
OPTIMIZER_WF_N_STARTS = 8
# transaction cost charged in the walk-forward: one-way turnover x this rate, applied on the
# month a rebalance happens. 10 bps is a realistic round-trip-ish cost for liquid index funds;
# it exists so high-turnover rules (momentum, vol-target) can't look good for free.
OPTIMIZER_TC_BPS = 10.0
# rule-based contestants (portfolio/rules.py), tested through the same walk-forward as the
# optimizer portfolios -- rules are validated over many decision dates, never on a return snapshot.
OPTIMIZER_MOMENTUM_K = 6            # cross-sectional momentum: hold the top-K sleeves, equal weight
OPTIMIZER_MOMENTUM_LOOKBACK = 12    # formation window (months)
OPTIMIZER_MOMENTUM_SKIP = 1         # skip the most recent month (avoids short-term reversal) -> "12-1"
# volatility targeting (Moreira-Muir 2017), UNLEVERED version for a long-only investor: scale a
# base portfolio's exposure DOWN toward the target when its trailing vol runs hot, hold cash for
# the rest; never lever up (max leverage 1.0). A defensive overlay, tested as its own contestant.
OPTIMIZER_VOLTARGET_ANN = 0.12      # annual volatility target
OPTIMIZER_VOLTARGET_WINDOW = 12     # trailing months used to estimate current vol
OPTIMIZER_VOLTARGET_MAXLEV = 1.0    # 1.0 = unlevered (can only de-risk into cash)

# geographic look-through caps (optimizer `geo_cap`): zones are defined on the LOOK-THROUGH
# country exposures (factsheet country_weights), not on the sleeve's region label — an "EM"
# sleeve is mostly Asia in look-through terms and is constrained as such. Countries not listed
# below (incl. the factsheets' own "Other" residual bucket) fall into "Rest of world".
# The cap is a linear constraint (zone exposure = w'Z, Z from the weights tables), so within
# each zone the optimizer still picks by its objective — the cap forces geographic spread, it
# never forces "investing somewhere just because".
OPTIMIZER_GEO_ZONES = {
    "North America": ["United States", "Canada"],
    "Europe": ["France", "Germany", "Italy", "Netherlands", "Spain", "Switzerland",
               "United Kingdom"],
    "Asia-Pacific": ["China", "Hong Kong", "India", "Japan", "Korea", "Singapore", "Taiwan",
                     "Thailand"],
}
OPTIMIZER_GEO_CAP_PCT = 40.0        # default zone cap for the geo-capped flagship portfolio

# "diversified maximin" preset: the answer to maximin's structural corner problem. Its linear
# objective lands on vertices (few sleeves, weights at the caps) and per-quadrant means are
# noisy (~90 months/state), so unconstrained maximin is a concentrated bet on the sleeves whose
# quadrant history LOOKS best (Michaud, per quadrant). The literature's fix, measured on our own
# data (geo-capped beat unconstrained OOS, Sharpe 0.84 vs 0.73): constraints as implicit
# shrinkage (Jagannathan-Ma) across all three concentration axes — sleeve, geography, factor.
OPTIMIZER_FACTOR_CAP_PCT = 40.0             # max exposure per factor bucket (label-based)
OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT = 25.0  # forces >= 4 sleeves before geo/factor caps bite

# long-history regime proxy (ingest/ff_factors.py + analytics/long_history.py): Fama-French
# research factors from Ken French's data library (free, NOT FRED — no ToS constraint). These
# are RESEARCH PROXIES for the regime layer, not investable sleeves — deliberately kept out of
# the index registry. The macro-state classification extends back as far as both primary
# indicators exist (core PCE YoY starts 1960), which triples the regime sample and finally
# includes the real 1970s stagflation.
FF_SOURCES = {
    "factors": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip",
    "momentum": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip",
}
# 6 value-weighted size x book-to-market portfolios (1926+): LONG-ONLY total-return proxies for
# the 60-year construction-rule race (portfolio/proxy_backtest.py). Column renames applied on
# ingest (LoBM = growth, HiBM = value).
FF_PORTFOLIOS_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/6_Portfolios_2x3_CSV.zip"
FF_PORTFOLIOS_MONTHLY = PROCESSED_DIR / "ff_portfolios_monthly.csv"
FF_PORTFOLIO_RENAME = {
    "SMALL LoBM": "Proxy | Small Growth", "ME1 BM2": "Proxy | Small Neutral",
    "SMALL HiBM": "Proxy | Small Value", "BIG LoBM": "Proxy | Big Growth",
    "ME2 BM2": "Proxy | Big Neutral", "BIG HiBM": "Proxy | Big Value",
}
LONG_HISTORY_DIR = ANALYTICS_DIR / "long_history"
LONG_HISTORY_CSV = LONG_HISTORY_DIR / "long_history_factor_states.csv"
LONG_HISTORY_REPORT = LONG_HISTORY_DIR / "REPORT_long_history.md"

# 60-year construction-rule race on the proxy universe (portfolio/proxy_backtest.py, roadmap A1)
PROXY_BACKTEST_DIR = ANALYTICS_DIR / "proxy_backtest"
PROXY_BACKTEST_SUMMARY = PROXY_BACKTEST_DIR / "proxy_backtest_summary.csv"
PROXY_BACKTEST_REPORT = PROXY_BACKTEST_DIR / "REPORT_proxy_backtest.md"
# window-robustness (roadmap A2): re-run each race dropping the first k months, report the
# DISPERSION of each rule's OOS Sharpe across window variants. CLI-only (not a pipeline stage —
# it is several full races); python -m portfolio_lab.portfolio.proxy_backtest --dispersion
PROXY_BACKTEST_DISPERSION = PROXY_BACKTEST_DIR / "proxy_backtest_dispersion.csv"
PROXY_BACKTEST_DISPERSION_REPORT = PROXY_BACKTEST_DIR / "REPORT_window_robustness.md"
PROXY_BACKTEST_OFFSETS = (0, 36, 72, 108)   # months of early history dropped per variant

# named-episode stress library (portfolio/stress.py, roadmap A3): replay hand-dated historical
# episodes on (a) the optimizer's flagship portfolios over the MSCI window and (b) four static
# ARCHETYPE allocations over the century-scale proxy universe. Dates are month-ends, inclusive.
STRESS_DIR = ANALYTICS_DIR / "stress"
STRESS_SUMMARY = STRESS_DIR / "stress_summary.csv"
STRESS_REPORT = STRESS_DIR / "REPORT_stress.md"
STRESS_EPISODES_MODERN = {          # within the MSCI common window (1999+)
    "Dot-com bust": ("2000-09-30", "2002-09-30"),
    "Global Financial Crisis": ("2007-11-30", "2009-02-28"),
    "COVID crash": ("2020-01-31", "2020-03-31"),
    "2022 rate shock": ("2022-01-31", "2022-09-30"),
}
STRESS_EPISODES_HISTORIC = {        # proxy universe only (multi-asset from 1962)
    "OPEC stagflation": ("1973-01-31", "1974-09-30"),
    "Volcker squeeze": ("1981-01-31", "1982-07-31"),
    "Black Monday era": ("1987-09-30", "1987-11-30"),
    "Dot-com bust": ("2000-09-30", "2002-09-30"),
    "Global Financial Crisis": ("2007-11-30", "2009-02-28"),
    "2022 rate shock": ("2022-01-31", "2022-09-30"),
}
# user profiles (roadmap A4): preference bundles as constraint presets. The empirical/personal
# split made concrete — the engine finds the best portfolio WITHIN each profile and the report
# quantifies what each preference costs vs its unrestricted twin ("the price of preferences").
# All profiles use the diversified cap family (sleeve 25 / geo 40 / factor 40); they differ in
# objective and menu. "Pure equity — diversified growth" is the owner's own stated profile.
OPTIMIZER_PROFILES = {
    "Pure equity — diversified growth": dict(
        include_asset_classes=False,
        kwargs=dict(prefs={"return": 6, "risk": 2, "diversification": 4}),
        twin="same sliders, no caps"),
    "Equity — balanced": dict(
        include_asset_classes=False,
        kwargs=dict(prefs={"return": 4, "risk": 4, "diversification": 4}),
        twin="same sliders, no caps"),
    "All-weather — defensive": dict(
        include_asset_classes=True,
        kwargs=dict(maximin=True),
        twin="same objective, no caps"),
}

# archetype allocations for the historic table (fractions; proxy sleeves)
STRESS_ARCHETYPES = {
    "Pure equity (1/N of 6)": {"equity_equal": 1.0},
    "60/40 stocks/bonds": {"equity_equal": 0.60, "Asset | US Treasury 10y": 0.40},
    "All-weather static": {"equity_equal": 0.30, "Asset | US Treasury 10y": 0.30,
                           "Asset | Gold": 0.25, "Asset | Cash (T-bill)": 0.15},
}


def ensure_dirs() -> None:
    """Create all writable output directories if missing (idempotent)."""
    for d in (PROCESSED_DIR, ANALYTICS_DIR, CORR_REGIME_DIR, DIVERSIFICATION_DIR,
              MACRO_ANALYTICS_DIR, MACRO_CORR_BY_REGIME_DIR, MACRO_STATE_DIR, SCENARIO_DIR,
              OPTIMIZER_DIR, LONG_HISTORY_DIR, PROXY_BACKTEST_DIR, STRESS_DIR):
        d.mkdir(parents=True, exist_ok=True)


# --- domain constants ----------------------------------------------------
REGIONS = ["ACWI", "World", "World_ex_USA", "USA", "EM", "Europe", "AC_Asia_ex_Japan", "Japan"]

FACTOR_TYPES = ["Reference", "Momentum", "Enhanced Value", "Quality"]

# 11 GICS sectors — used to separate sector vs country legend entries in factsheets
GICS_SECTORS = {
    "Information Technology", "Financials", "Industrials", "Consumer Discretionary",
    "Health Care", "Communication Services", "Consumer Staples", "Materials",
    "Energy", "Utilities", "Real Estate",
}

# short sector names as they appear in the TOP-10 constituents tables
GICS_SECTORS_SHORT = ["Info Tech", "Industrials", "Health Care", "Financials", "Cons Discr",
                      "Comm Srvcs", "Cons Staples", "Materials", "Energy", "Utilities", "Real Estate"]

# normalise country-name variants so roll-ups aggregate cleanly
COUNTRY_FIX = {"South Korea": "Korea", "Hong Kong SAR China": "Hong Kong"}

# concentration thresholds (%) for the diversification look-through flags
CONCENTRATION_THRESHOLDS = {"sector": 30.0, "country": 35.0, "stock": 5.0}

# A portfolio's sleeve weights must sum to 100% — a portfolio cannot hold more or less than
# itself. This tolerance exists ONLY to absorb floating-point noise (typically ~1e-9 pp), not to
# forgive real input errors; it is an internal implementation detail and should never be surfaced
# to the user ("100%" means 100%, full stop). Shared by the Python API and the dashboard's live
# diversification widget so both reject/accept the same range.
PORTFOLIO_WEIGHT_TOLERANCE_PCT = 0.01

ROLLING_WINDOW_MONTHS = 36
FACTSHEET_ASOF = "2026-06-30"

# macro-link engine settings
MACRO_MIN_OVERLAP_MONTHS = 36        # pairs with fewer overlapping months are flagged insufficient
MACRO_LAGS = [0, 1, 3, 6, 12]        # months by which macro LEADS returns (0 = contemporaneous)
# per-regime macro correlations use a much shorter window (regimes are as short as ~15 months),
# so a separate, lower overlap floor applies -- these are noisier/smaller-sample by nature and
# reported as such, not to be read with the same confidence as the full-sample numbers above.
MACRO_REGIME_MIN_OVERLAP_MONTHS = 6


def factor_type(index_name: str) -> str:
    """Map a full index name to its factor bucket."""
    n = index_name.lower()
    if "momentum" in n:
        return "Momentum"
    if "enhanced value" in n:
        return "Enhanced Value"
    if "quality" in n:
        return "Quality"
    return "Reference"


def load_registry() -> list[dict]:
    """Read the index registry (data/index_registry.csv) — the single source of truth for which
    indexes are tracked and where each one's data comes from. One dict per index with keys:
    index_id, display_name, region, factor_type, source, returns_file, weights_file.

    To add an index: append a row here and drop its file(s) in data/raw/msci_indexes/<region>/.
    'source' selects how ingest loads it (msci_local = xlsx+pdf in the region folder;
    msci_local_webweights = xlsx local, weights supplied by ingest/asia_images.py). A future
    'api' source would add one branch in ingest without changing this contract.
    """
    with open(INDEX_REGISTRY, newline="") as f:
        return list(csv.DictReader(f))
