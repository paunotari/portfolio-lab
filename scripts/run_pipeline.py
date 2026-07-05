#!/usr/bin/env python3
"""End-to-end pipeline: raw MSCI files -> processed CSVs -> analytics -> dashboard.

    python scripts/run_pipeline.py            # full run
    python scripts/run_pipeline.py --no-dashboard

Steps:
  1. ingest.returns      xlsx  -> returns_monthly_long.csv, levels_wide.csv
  2. ingest.factsheets   pdf   -> sector/country/top_constituents/index_meta CSVs
  3. ingest.asia_images  append the 2 image-sourced AC Asia ex Japan factor indices
  4. ingest.macro        FRED  -> macro_monthly.csv, macro_meta.csv       (skippable: --no-macro)
  5. analytics.engine    performance / factor-vs-ref / regimes / correlations -> outputs/analytics
  6. analytics.macro_link  index<->macro correlations/betas -> outputs/analytics/macro
  7. portfolio.diversification  example look-through -> outputs/diversification
  8. dashboard.build     self-contained outputs/dashboard.html
"""
import sys
import argparse
from pathlib import Path

# make src/ importable without an install
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_lab.ingest import returns, factsheets, asia_images, macro
from portfolio_lab.analytics import engine, macro_link
from portfolio_lab.portfolio import diversification
from portfolio_lab.dashboard import build as dashboard_build


def main():
    ap = argparse.ArgumentParser(description="Run the portfolio_lab data pipeline")
    ap.add_argument("--no-dashboard", action="store_true", help="skip the HTML dashboard build")
    ap.add_argument("--no-macro", action="store_true", help="skip FRED macro fetch (needs network)")
    args = ap.parse_args()

    print("=== 1/8 ingest returns ===");     returns.run()
    print("=== 2/8 ingest factsheets ===");  factsheets.run()
    print("=== 3/8 ingest asia images ==="); asia_images.run()
    if not args.no_macro:
        print("=== 4/8 ingest macro (FRED) ==="); macro.run()
    print("=== 5/8 analytics ===");          engine.run()
    if not args.no_macro:
        print("=== 6/8 macro-link ===");     macro_link.run()
    print("=== 7/8 diversification ===");    diversification.run()
    if not args.no_dashboard:
        print("=== 8/8 dashboard ===");      dashboard_build.run()
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
