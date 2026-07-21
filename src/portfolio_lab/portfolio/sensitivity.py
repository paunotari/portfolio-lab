"""Sensitivity grids — is anything we claim a knife-edge? (paper track item 3, M17)

Four declared dimensions, each varying ONE thing around the shipped configuration and
re-reading the conclusions the ledger actually relies on:

  costs   : transaction cost 0 / 10 / 25 bps, re-netted from the SAME gross returns and
            turnover (weights never depend on costs — no re-optimization involved)
  refit   : walk-forward refit every 6 / 12 / 24 months (full re-runs)
  caps    : the diversified preset at (20/35/35), (25/40/40, shipped), (30/45/45)
            [sleeve/geo/factor %] (full re-runs)
  block   : the Ledoit-Wolf bootstrap block length 3 / 6 / 10 on the headline pairs
  sigma   : the covariance ESTIMATOR itself — constant-correlation Ledoit-Wolf (shipped),
            scaled-identity Ledoit-Wolf, and Ledoit-Wolf 2020 analytical NONLINEAR shrinkage
            (full re-runs). Declared expectation, recorded before the run: no material change,
            because N << T here (p/n = 0.085 on the full window) is precisely the regime where
            nonlinear shrinkage has little left to correct — every risk number in the engine
            rides on this one matrix, so "little left to correct" deserves to be measured
            rather than asserted.

Conclusions tracked across every cell (the grid's verdict line):
  C1 "min-variance is the OOS winner"            — min-var rank 1 among the always-on set
  C2 "nothing beats 1/N significantly at 5%"     — LW p_boot(min-var vs 1/N) >= 0.05
  C3 "capping does not cost OOS performance"      — diversified maximin >= unconstrained (M3)
  C4 "the all-weather flagship stays on the podium" — rank <= 3

MSCI menu only (the universe the headline claims are made on). Expensive (4 extra full
walk-forwards) — CLI, not a pipeline stage, same pattern as --loro and A2's --dispersion.
The agreement-rule variant grid (sign vs magnitude bands) tests the ESTIMATOR's
specification, not a reported number's robustness — deliberately out of scope here
(recorded in TODO; post-M16 it would need a fresh confirmatory universe).

Run:  python -m portfolio_lab.portfolio.sensitivity
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.engine import _perf_stats
from portfolio_lab.portfolio.inference import sharpe_diff_test
from portfolio_lab.portfolio.validation import walk_forward

COSTS_BPS = (0.0, 10.0, 25.0)
REFITS = (6, 12, 24)
CAPS = ((20, 35, 35), (25, 40, 40), (30, 45, 45))       # sleeve / geo / factor, %
BLOCKS = (3, 6, 10)
SIGMA_ESTIMATORS = ("constant_correlation", "identity", "nonlinear")
AW = "Maximin (all-weather div)"


def _sharpe_from(gross: pd.DataFrame, turn: pd.DataFrame, bps: float) -> pd.Series:
    out = {}
    for c in gross.columns:
        net = (gross[c] - bps / 10_000.0 * turn[c]).dropna()
        lvl = pd.concat([pd.Series([100.0], index=[net.index[0] - pd.offsets.MonthEnd(1)]),
                         100.0 * (1 + net).cumprod()])
        out[c] = _perf_stats(lvl)["sharpe_rf0"]
    return pd.Series(out)


def _conclusions(sharpes: pd.Series) -> dict:
    rank = sharpes.sort_values(ascending=False).index
    return dict(
        c1_minvar_rank=int(list(rank).index("Min-variance") + 1),
        c3_capped_minus_unconstrained=float(
            sharpes.get("Maximin (diversified)", np.nan)
            - sharpes.get("Maximin (worst quadrant)", np.nan)),
        c4_allweather_rank=int(list(rank).index(AW) + 1) if AW in sharpes else None)


def run() -> pd.DataFrame:
    C.ensure_dirs()
    rows = []

    print("[sensitivity] baseline walk-forward (also feeds the cost grid) ...")
    base_summary, base_meta, base_monthly = walk_forward()
    gross, turn = base_meta["_gross"], base_meta["_turnover"]

    for bps in COSTS_BPS:
        sh = _sharpe_from(gross, turn, bps)
        rows.append(dict(dimension="cost_bps", cell=str(int(bps)),
                         sharpes=sh, **_conclusions(sh)))
        print(f"[sensitivity] cost {bps:.0f} bps done")

    for refit in REFITS:
        if refit == C.OPTIMIZER_WF_REFIT_MONTHS:
            sh = _sharpe_from(gross, turn, C.OPTIMIZER_TC_BPS)
        else:
            s, m, _ = walk_forward(refit=refit)
            sh = s.set_index("portfolio")["oos_sharpe_rf0"]
        rows.append(dict(dimension="refit_months", cell=str(refit),
                         sharpes=sh, **_conclusions(sh)))
        print(f"[sensitivity] refit {refit}m done")

    shipped = (C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT, C.OPTIMIZER_GEO_CAP_PCT,
               C.OPTIMIZER_FACTOR_CAP_PCT)
    for caps in CAPS:
        if caps == shipped:
            sh = _sharpe_from(gross, turn, C.OPTIMIZER_TC_BPS)
        else:
            try:
                (C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT, C.OPTIMIZER_GEO_CAP_PCT,
                 C.OPTIMIZER_FACTOR_CAP_PCT) = caps
                s, m, _ = walk_forward()
                sh = s.set_index("portfolio")["oos_sharpe_rf0"]
            finally:
                (C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT, C.OPTIMIZER_GEO_CAP_PCT,
                 C.OPTIMIZER_FACTOR_CAP_PCT) = shipped
        rows.append(dict(dimension="caps_slv_geo_fac", cell="/".join(map(str, caps)),
                         sharpes=sh, **_conclusions(sh)))
        print(f"[sensitivity] caps {caps} done")

    shipped_sigma = C.OPTIMIZER_SIGMA_ESTIMATOR
    for est in SIGMA_ESTIMATORS:
        if est == shipped_sigma:
            sh = _sharpe_from(gross, turn, C.OPTIMIZER_TC_BPS)
        else:
            try:
                C.OPTIMIZER_SIGMA_ESTIMATOR = est
                s_, m_, _ = walk_forward()
                sh = s_.set_index("portfolio")["oos_sharpe_rf0"]
            finally:
                C.OPTIMIZER_SIGMA_ESTIMATOR = shipped_sigma
        rows.append(dict(dimension="sigma_estimator", cell=est,
                         sharpes=sh, **_conclusions(sh)))
        print(f"[sensitivity] sigma estimator {est} done")

    # block-size grid on the headline inference pair (+ HRP, the other near-line pair)
    blocks = {}
    for b in BLOCKS:
        cell = {}
        for name in ("Min-variance", "HRP"):
            t = sharpe_diff_test(base_monthly[name], base_monthly["1/N"], block=b)
            cell[name] = t["p_boot"]
        blocks[b] = cell
        rows.append(dict(dimension="lw_block", cell=str(b), sharpes=None,
                         c2_p_minvar_vs_1N=float(cell["Min-variance"]),
                         c2_p_hrp_vs_1N=float(cell["HRP"])))
        print(f"[sensitivity] LW block {b}: p(min-var vs 1/N) = {cell['Min-variance']:.4f}")

    flat = []
    for r in rows:
        base = {k: v for k, v in r.items() if k != "sharpes"}
        if r["sharpes"] is not None:
            for p, s in r["sharpes"].items():
                flat.append({**base, "portfolio": p, "oos_sharpe": float(s)})
        else:
            flat.append(base)
    df = pd.DataFrame(flat)
    df.to_csv(C.OPTIMIZER_SENSITIVITY, index=False)
    _write_report(rows, blocks)
    print(f"[sensitivity] wrote {C.OPTIMIZER_SENSITIVITY} and {C.OPTIMIZER_SENSITIVITY_REPORT}")
    return df


def _write_report(rows, blocks):
    L = ["# Sensitivity grids — is anything we claim a knife-edge?", "",
         "One dimension varied at a time around the shipped configuration (MSCI menu, "
         "walk-forward protocol unchanged). The question per cell is not 'do the numbers "
         "move' (they always move) but 'does any LEDGER CONCLUSION flip'.", ""]
    grid_rows = [r for r in rows if r["sharpes"] is not None]
    L += ["| dimension | cell | min-var rank (C1) | capped − uncapped maximin (C3) | "
          "all-weather rank (C4) |", "|---|---|---|---|---|"]
    for r in grid_rows:
        L += [f"| {r['dimension']} | {r['cell']} | #{r['c1_minvar_rank']} | "
              f"{r['c3_capped_minus_unconstrained']:+.3f} | "
              f"#{r['c4_allweather_rank']} |"]
    L += ["", "## C2 — 'nothing beats 1/N at 5%' across bootstrap block sizes", ""]
    L += ["| block b | p_boot min-var vs 1/N | p_boot HRP vs 1/N |", "|---|---|---|"]
    for b, cell in blocks.items():
        L += [f"| {b} | {cell['Min-variance']:.4f} | {cell['HRP']:.4f} |"]
    # A conclusion that already fails in the SHIPPED cell is not a sensitivity flip — it is a
    # stale conclusion, and conflating the two would let a grid take the blame for something
    # the baseline did on its own (e.g. a newly fielded contestant changing a rank).
    shipped = next((r for r in grid_rows
                    if r["dimension"] == "cost_bps"
                    and r["cell"] == str(int(C.OPTIMIZER_TC_BPS))), grid_rows[0])
    checks = {
        "C1": ("min-variance is the OOS winner",
               lambda r: r["c1_minvar_rank"] == 1,
               lambda r: f"min-var rank #{r['c1_minvar_rank']}"),
        "C3": ("capping does not cost OOS performance",
               lambda r: r["c3_capped_minus_unconstrained"] >= 0,
               lambda r: f"capped − uncapped {r['c3_capped_minus_unconstrained']:+.3f}"),
        "C4": ("the all-weather flagship stays on the podium",
               lambda r: r["c4_allweather_rank"] is None or r["c4_allweather_rank"] <= 3,
               lambda r: f"all-weather rank #{r['c4_allweather_rank']}"),
    }
    stale, flips = [], []
    for key, (text, ok, describe) in checks.items():
        if not ok(shipped):
            stale.append(f"**{key} — '{text}' — is FALSE IN THE SHIPPED CELL ITSELF** "
                         f"({describe(shipped)}). Not a robustness failure: the conclusion is "
                         f"stale and must be restated or retired in the ledger, never "
                         f"re-thresholded to make it pass.")
            continue
        for r in grid_rows:
            if not ok(r):
                flips.append(f"{key} flips at {r['dimension']}={r['cell']} ({describe(r)})")
    for b, cell in blocks.items():
        if cell["Min-variance"] < 0.05:
            flips.append(f"C2 flips at block={b} (p={cell['Min-variance']:.4f} < 0.05)")
    L += ["", "## Verdict", ""]
    if stale:
        L += ["### Conclusions that no longer hold at the shipped configuration", ""]
        L += [f"- {t}" for t in stale] + [""]
        L += ["### Sensitivity flips (among conclusions the shipped cell still satisfies)", ""]
    L += ([f"- {f}" for f in flips] if flips else
          ["- **No ledger conclusion flips in any grid cell.**"])
    L += ["", "Full per-contestant Sharpes per cell: `optimizer_sensitivity.csv`.", ""]
    C.OPTIMIZER_SENSITIVITY_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    run()
