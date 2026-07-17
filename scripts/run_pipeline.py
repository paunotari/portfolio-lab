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
  6. analytics.macro_link  index<->macro correlations/betas (+ per-regime) -> outputs/analytics/macro
  7. analytics.macro_state  4-quadrant classification + factor attribution -> outputs/analytics/macro_state
  8. analytics.scenario   bootstrap scenario simulation -> outputs/analytics/scenario
  9. ingest.ff_factors    Ken French factor series (network) -> ff_factors_monthly.csv
  10. ingest.asset_classes  bond/gold/cash proxy returns (network for gold) -> asset_class_monthly.csv
  11. analytics.long_history  FF factors x long macro-state classification -> outputs/analytics/long_history
  12. portfolio.proxy_backtest  60-year construction-rule race on the proxy universe -> outputs/analytics/proxy_backtest
  13. portfolio.stress    named-episode stress library -> outputs/analytics/stress
  14. portfolio.diversification  example look-through -> outputs/diversification
  15. portfolio.optimizer  anchor + benchmarks + flagship portfolios + walk-forward -> outputs/analytics/optimizer
  16. dashboard.build     self-contained outputs/dashboard.html
"""
import sys
import argparse
from pathlib import Path

# make src/ importable without an install
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_lab.ingest import returns, factsheets, asia_images, macro, ff_factors, asset_classes
from portfolio_lab.analytics import engine, macro_link, macro_state, scenario, long_history
from portfolio_lab.portfolio import diversification, optimizer, proxy_backtest, stress
from portfolio_lab.dashboard import build as dashboard_build


def main():
    ap = argparse.ArgumentParser(description="Run the portfolio_lab data pipeline")
    ap.add_argument("--no-dashboard", action="store_true", help="skip the HTML dashboard build")
    ap.add_argument("--no-macro", action="store_true", help="skip FRED macro fetch (needs network)")
    args = ap.parse_args()

    print("=== 1/16 ingest returns ===");     returns.run()
    print("=== 2/16 ingest factsheets ===");  factsheets.run()
    print("=== 3/16 ingest asia images ==="); asia_images.run()
    if not args.no_macro:
        print("=== 4/16 ingest macro (FRED) ==="); macro.run()
    print("=== 5/16 analytics ===");          engine.run()
    if not args.no_macro:
        print("=== 6/16 macro-link ===");      macro_link.run()
        print("=== 7/16 macro-state ===");     macro_state.run()
        print("=== 8/16 scenario ===");        scenario.run()
        print("=== 9/16 ingest FF factors ==="); ff_factors.run()
        print("=== 10/16 asset classes ==="); asset_classes.run()
        print("=== 11/16 long-history ===");   long_history.run()
        print("=== 12/16 proxy backtest ==="); proxy_backtest.run()
        print("=== 13/16 stress ===");        stress.run()
    print("=== 14/16 diversification ===");   diversification.run()
    print("=== 15/16 optimizer ===");         optimizer.run()
    if not args.no_dashboard:
        print("=== 16/16 dashboard ===");     dashboard_build.run()
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
