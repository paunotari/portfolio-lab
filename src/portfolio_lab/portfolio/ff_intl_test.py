"""THE CONFIRMATORY TEST — the frozen estimator on a universe it never touched (M16).

PROTOCOL, DECLARED BEFORE THE FIRST RUN (pre-registration spirit; this docstring is committed
before any result is computed, and the verdict below is reported whatever it says):

Universe
    9 sleeves from Ken French's international library (ingest/ff_international.py):
    {FF Europe, FF Japan, FF Asia-Pacific} x {Reference, Enhanced Value, Momentum},
    USD monthly 1990-07+. Chosen because (a) it was NEVER downloaded or inspected during
    estimator development, (b) its OOS window (~2000+ after the 120m warmup) contains the
    dot-com bust AND the GFC — two prolonged bears our MSCI OOS window (2009+) lacks, and
    (c) Japan's deflation decades are the regime environment most alien to the US-trained
    classifier, making it the natural place for the estimator to break.

Procedure
    The EXACT frozen machinery, no re-tuning: same walk-forward (120m warmup, annual refits,
    net of 10 bps), same contestants, same estimator rules (msci_factor_prior: beta on modern
    overlap, era sign-agreement gate, month-weighted blend; OPTIMIZER_ANCHOR_REGIONAL stays
    False per M15). One A/B: OPTIMIZER_ANCHOR_LONG False ("estimator off", modern-only
    inputs) vs True ("estimator on"). Macro states: the same classifier over its long window
    (labels identical on the overlap).

Primary declared verdict (mirrors M10's claim, thresholds fixed here, in advance)
    Delta = net OOS Sharpe (anchored - modern) per maximin variant (worst-quadrant,
    diversified):
      CONFIRMS   if every variant's Delta >= 0 and at least one Delta > +0.005
      REFUTES    if any variant's Delta < -0.02
      WEAK/INCONCLUSIVE otherwise — reported as such, no re-running with tweaks.

Secondary readouts (reported, not gated): the full contestant table on the anchored run;
    the M1/M2 hierarchy replication (does anything beat 1/N? do ERC/HRP? does min-var hold
    up through two bears?); Ledoit-Wolf p-values vs 1/N; per-region betas/gates actually used.

Outputs: outputs/analytics/ff_intl/ (REPORT_ff_intl.md, ff_intl_ab.csv, ff_intl_inference.csv)

Run:  python -m portfolio_lab.portfolio.ff_intl_test          (fetches the data if absent)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.portfolio.inference import inference_table
from portfolio_lab.portfolio.validation import walk_forward

MAXIMIN_VARIANTS = ["Maximin (worst quadrant)", "Maximin (diversified)"]


def load_universe() -> pd.DataFrame:
    if not C.FF_INTL_MONTHLY.exists():
        from portfolio_lab.ingest import ff_international
        ff_international.run()
    rets = pd.read_csv(C.FF_INTL_MONTHLY, index_col=0, parse_dates=True).sort_index()
    if rets.shape[1] < 6:
        raise RuntimeError(f"virgin universe incomplete: {list(rets.columns)}")
    return rets


def run() -> dict:
    C.ensure_dirs()
    rets = load_universe()
    print(f"[ff_intl_test] universe: {rets.shape[1]} sleeves, {len(rets)} months "
          f"{rets.index[0].date()} -> {rets.index[-1].date()}")

    runs = {}
    prev = C.OPTIMIZER_ANCHOR_LONG
    try:
        for flag, label in ((False, "modern"), (True, "anchored")):
            C.OPTIMIZER_ANCHOR_LONG = flag
            summary, meta, monthly = walk_forward(rets=rets)
            runs[label] = dict(summary=summary.set_index("portfolio"), meta=meta,
                               monthly=monthly)
            print(f"[ff_intl_test] {label}: OOS {meta['oos_start']} -> {meta['oos_end']}")
    finally:
        C.OPTIMIZER_ANCHOR_LONG = prev

    ab = pd.concat({lab: r["summary"][["oos_sharpe_rf0", "oos_ann_vol", "oos_max_drawdown"]]
                    for lab, r in runs.items()}, axis=1)
    ab.to_csv(C.FF_INTL_AB)

    deltas = {v: float(runs["anchored"]["summary"].loc[v, "oos_sharpe_rf0"]
                       - runs["modern"]["summary"].loc[v, "oos_sharpe_rf0"])
              for v in MAXIMIN_VARIANTS if v in runs["anchored"]["summary"].index}
    if not deltas:
        verdict = "NO VERDICT — maximin variants missing (no usable macro states?)"
    elif all(d >= 0 for d in deltas.values()) and any(d > 0.005 for d in deltas.values()):
        verdict = "CONFIRMS"
    elif any(d < -0.02 for d in deltas.values()):
        verdict = "REFUTES"
    else:
        verdict = "WEAK/INCONCLUSIVE"

    infer = inference_table(runs["anchored"]["monthly"])
    infer.to_csv(C.FF_INTL_INFERENCE, index=False)

    _write_report(rets, runs, ab, deltas, verdict, infer)
    print(f"[ff_intl_test] PRIMARY VERDICT: {verdict}  "
          + "  ".join(f"{k.split('(')[1].rstrip(')')} Δ={v:+.3f}" for k, v in deltas.items()))
    print(f"[ff_intl_test] wrote {C.FF_INTL_REPORT}")
    return dict(verdict=verdict, deltas=deltas, ab=ab, inference=infer)


def _fmt(x, f="{:.2f}"):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f.format(x)


def _write_report(rets, runs, ab, deltas, verdict, infer):
    meta = runs["anchored"]["meta"]
    s_on = runs["anchored"]["summary"].sort_values("oos_sharpe_rf0", ascending=False)
    s_off = runs["modern"]["summary"]
    L = ["# The confirmatory test — frozen estimator on the virgin FF international universe",
         "",
         "Protocol declared in `portfolio/ff_intl_test.py` (committed before the first run): "
         "9 sleeves (Europe/Japan/Asia-Pacific x Reference/Value/Momentum, Ken French, "
         f"{rets.index[0].date()} → {rets.index[-1].date()}), the exact frozen machinery, one "
         "A/B (long-history estimator off/on), fixed thresholds. OOS "
         f"{meta['oos_start']} → {meta['oos_end']} ({meta['oos_months']} months, "
         f"{meta['n_refits']} refits, net of {meta['tc_bps']:.0f} bps) — a window containing "
         "the dot-com bust and the GFC, which the MSCI OOS window lacks.", "",
         f"## PRIMARY VERDICT: **{verdict}**", ""]
    for v, d in deltas.items():
        L += [f"- {v}: net OOS Sharpe {s_off.loc[v, 'oos_sharpe_rf0']:.3f} (modern) → "
              f"{runs['anchored']['summary'].loc[v, 'oos_sharpe_rf0']:.3f} (anchored), "
              f"**Δ = {d:+.3f}**"]
    L += ["", "Declared rule: CONFIRMS if every Δ ≥ 0 and any Δ > +0.005; REFUTES if any "
          "Δ < −0.02; else weak/inconclusive.", ""]
    L += ["## Full table (estimator ON) — with the A/B columns", ""]
    L += ["| portfolio | Sharpe (on) | Sharpe (off) | vol (on) | maxDD (on) |",
          "|---|---|---|---|---|"]
    for p in s_on.index:
        off = s_off.loc[p, "oos_sharpe_rf0"] if p in s_off.index else np.nan
        L += [f"| {p} | {s_on.loc[p, 'oos_sharpe_rf0']:.2f} | {_fmt(off)} | "
              f"{s_on.loc[p, 'oos_ann_vol']:.1%} | {s_on.loc[p, 'oos_max_drawdown']:.1%} |"]
    L += ["", "## Hierarchy replication (secondary, ungated)", ""]
    one_n = float(s_on.loc["1/N", "oos_sharpe_rf0"]) if "1/N" in s_on.index else np.nan
    for p in ["Min-variance", "HRP", "ERC (anchor)"]:
        if p in s_on.index:
            rel = float(s_on.loc[p, "oos_sharpe_rf0"]) - one_n
            L += [f"- {p} vs 1/N: {rel:+.3f}"]
    L += ["", "## Are the differences real? (Ledoit-Wolf vs 1/N, anchored run)", ""]
    L += ["| portfolio | Sharpe (ann) | Δ vs 1/N | p_boot |", "|---|---|---|---|"]
    for _, r in infer.iterrows():
        L += [f"| {r['portfolio']} | {r['sharpe_ann']:.2f} | "
              f"{_fmt(r['delta_ann_vs_1/N'], '{:+.2f}')} | "
              f"{_fmt(r['p_boot_vs_1/N'], '{:.3f}')} |"]
    L += ["", "_One run, whatever it says. No re-tuning followed this measurement — any "
          "refinement it motivates belongs to a NEW test on data this one didn't use._", ""]
    C.FF_INTL_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    run()
