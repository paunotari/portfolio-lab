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
# computed live in the browser, not a fitted model -- see dashboard/template.py)
MACRO_STATE_FORECAST_MOMENTUM_MONTHS = 6
MACRO_STATE_FORECAST_HORIZON_MONTHS = 6

# scenario simulation (analytics/scenario.py) output file handles
SCENARIO_DIR = ANALYTICS_DIR / "scenario"
SCENARIO_SUMMARY = SCENARIO_DIR / "scenario_summary.csv"
SCENARIO_REPORT = SCENARIO_DIR / "REPORT_scenario.md"
SCENARIO_YEARS = 10
SCENARIO_TRIALS = 2000
SCENARIO_SEED = 42


def ensure_dirs() -> None:
    """Create all writable output directories if missing (idempotent)."""
    for d in (PROCESSED_DIR, ANALYTICS_DIR, CORR_REGIME_DIR, DIVERSIFICATION_DIR,
              MACRO_ANALYTICS_DIR, MACRO_CORR_BY_REGIME_DIR, MACRO_STATE_DIR, SCENARIO_DIR):
        d.mkdir(parents=True, exist_ok=True)


# --- domain constants ----------------------------------------------------
REGIONS = ["ACWI", "World", "World_ex_USA", "USA", "EM", "Europe", "AC_Asia_ex_Japan"]

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
