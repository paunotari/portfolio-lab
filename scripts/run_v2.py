#!/usr/bin/env python3
"""v2.0 experiments (the collaborator's review): global factors, shorter training windows,
Sortino / Treynor / alphas, descriptive statistics -> outputs/v2.0/ + paper/v2.0/tables/.

    python scripts/run_v2.py            # uses cached walk-forwards in outputs/v2.0/ when present
    python scripts/run_v2.py --rerun    # recompute the three walk-forwards (~1 min each)

Needs the v1 processed data (python scripts/run_pipeline.py) and network for the Ken French
global factors on first run. Does not touch any v1 output.
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_lab.v2 import report

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run the v2.0 experiments")
    ap.add_argument("--rerun", action="store_true", help="recompute the walk-forwards")
    report.run(ap.parse_args().rerun)
