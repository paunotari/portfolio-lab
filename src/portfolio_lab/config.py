"""Central configuration: filesystem paths and shared domain constants.

Every module imports paths from here — nothing hard-codes a relative path or assumes a
current working directory. Paths are derived from this file's location, so the pipeline runs
the same regardless of where it is invoked from.
"""
from __future__ import annotations
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


def ensure_dirs() -> None:
    """Create all writable output directories if missing (idempotent)."""
    for d in (PROCESSED_DIR, ANALYTICS_DIR, CORR_REGIME_DIR, DIVERSIFICATION_DIR,
              MACRO_ANALYTICS_DIR):
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

ROLLING_WINDOW_MONTHS = 36
FACTSHEET_ASOF = "2026-06-30"

# macro-link engine settings
MACRO_MIN_OVERLAP_MONTHS = 36        # pairs with fewer overlapping months are flagged insufficient
MACRO_LAGS = [0, 1, 3, 6, 12]        # months by which macro LEADS returns (0 = contemporaneous)


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
