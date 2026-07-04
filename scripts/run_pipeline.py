#!/usr/bin/env python3
"""End-to-end pipeline: raw MSCI files -> processed CSVs -> analytics -> dashboard.

    python scripts/run_pipeline.py            # full run
    python scripts/run_pipeline.py --no-dashboard

Steps:
  1. ingest.returns      xlsx  -> returns_monthly_long.csv, levels_wide.csv
  2. ingest.factsheets   pdf   -> sector/country/top_constituents/index_meta CSVs
  3. ingest.asia_images  append the 2 image-sourced AC Asia ex Japan factor indices
  4. analytics.engine    performance / factor-vs-ref / regimes / correlations -> outputs/analytics
  5. portfolio.diversification  example look-through -> outputs/diversification
  6. dashboard.build     self-contained outputs/dashboard.html
"""
import sys
import argparse
from pathlib import Path

# make src/ importable without an install
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_lab.ingest import returns, factsheets, asia_images
from portfolio_lab.analytics import engine
from portfolio_lab.portfolio import diversification
from portfolio_lab.dashboard import build as dashboard_build


def main():
    ap = argparse.ArgumentParser(description="Run the portfolio_lab data pipeline")
    ap.add_argument("--no-dashboard", action="store_true", help="skip the HTML dashboard build")
    args = ap.parse_args()

    print("=== 1/6 ingest returns ===");     returns.build()
    print("=== 2/6 ingest factsheets ===");  factsheets.build()
    print("=== 3/6 ingest asia images ==="); asia_images.build()
    print("=== 4/6 analytics ===");          engine.run()
    print("=== 5/6 diversification ===");    diversification.main()
    if not args.no_dashboard:
        print("=== 6/6 dashboard ===");      dashboard_build.build()
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
