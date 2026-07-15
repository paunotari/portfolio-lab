"""Long-history regime proxy: do our per-quadrant factor patterns hold over ~66 years?

The problem this answers (info/TODO.md data roadmap P2): our per-quadrant factor evidence rests
on 1997-2026 — a sample whose Stagflation months are mostly the 2021-22 echo, not the real
1970s. The macro-state classifier can actually label months from 1960 (core PCE YoY, its
inflation primary, starts then; the composite scores are computed on full macro history, so
labels are identical to the pipeline's — see classify_states docstring). Joining that long
classification with the Fama-French research factors (ingest/ff_factors.py, 1926+) triples the
regime sample and lets us check every claimed pattern against decades it has never seen:

- Momentum leads in Goldilocks/Reflation but breaks in Stagflation (the 2022 pattern — was it
  also the 1970s pattern?)
- Value (HML) shines in Deflationary bust / high-rate squeezes
- The market factor's per-quadrant ordering (the maximin objective's raw material)

Output: long_history_factor_states.csv (per sample x state x factor stats) and
REPORT_long_history.md with the modern-vs-long comparison and a sign-agreement verdict per
factor/state cell. Research layer only — nothing here feeds the optimizer directly; if the
long-history differentials prove stable, wiring them into the regime views' Q is the recorded
follow-up (TODO.md).

Still on the allowed side of the FRED ToS line (caveat #11): counting + averaging pooled months;
the FF returns are not FRED data at all.

Run:  python -m portfolio_lab.analytics.long_history
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.macro_state import classify_states, STATE_ORDER

FACTORS = ["mkt_rf", "smb", "hml", "mom"]
FACTOR_LABEL = {"mkt_rf": "Market minus T-bill", "smb": "Size (SMB)",
                "hml": "Value (HML)", "mom": "Momentum (Mom)"}


def _stats(r: pd.Series) -> dict:
    return dict(n_months=len(r), mean_monthly=float(r.mean()),
                ann_return=float((1 + r.mean()) ** 12 - 1),
                ann_vol=float(r.std() * np.sqrt(12)),
                hit_rate=float((r > 0).mean()))


def build() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """(per-sample stats table, state-frequency table, meta)."""
    ff = pd.read_csv(C.FF_FACTORS_MONTHLY, index_col=0, parse_dates=True).sort_index()
    states_long = classify_states(start="1926-01-01")      # data dictates the real start (~1960)
    modern_start = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).index.min()

    joined = ff.join(states_long[["state"]], how="inner").dropna(subset=["state"])
    samples = {"long (full classifiable history)": joined,
               "modern (index common window)": joined.loc[modern_start:]}

    rows = []
    for sample, df in samples.items():
        for state in STATE_ORDER:
            months = df[df.state == state]
            for f in FACTORS:
                r = months[f].dropna()
                if len(r) < 6:
                    continue
                rows.append(dict(sample=sample, state=state, factor=f,
                                 factor_label=FACTOR_LABEL[f], **_stats(r)))
    stats = pd.DataFrame(rows)

    freq = pd.DataFrame({name: df.state.value_counts() for name, df in samples.items()}) \
        .reindex(STATE_ORDER).fillna(0).astype(int)

    meta = dict(long_start=str(joined.index[0].date()), long_end=str(joined.index[-1].date()),
                long_months=len(joined), modern_months=int(len(samples["modern (index common window)"])))
    return stats, freq, meta


def _agreement(stats: pd.DataFrame) -> pd.DataFrame:
    """Does the modern sample's per-quadrant SIGN of each factor's mean hold in the long one?"""
    piv = stats.pivot_table(index=["state", "factor"], columns="sample",
                            values="mean_monthly", aggfunc="first")
    long_col = [c for c in piv.columns if c.startswith("long")][0]
    mod_col = [c for c in piv.columns if c.startswith("modern")][0]
    piv["signs_agree"] = np.sign(piv[long_col]) == np.sign(piv[mod_col])
    return piv.reset_index()


def run():
    C.ensure_dirs()
    if not C.FF_FACTORS_MONTHLY.exists():
        print("[long_history] ff_factors_monthly.csv missing (run ingest.ff_factors) — skipping")
        return
    stats, freq, meta = build()
    stats.to_csv(C.LONG_HISTORY_CSV, index=False)
    agree = _agreement(stats)
    _write_report(stats, freq, meta, agree)
    print(f"[long_history] wrote {C.LONG_HISTORY_CSV} and {C.LONG_HISTORY_REPORT} "
          f"({meta['long_months']} long months vs {meta['modern_months']} modern)")
    return stats, freq, meta


def _short(state: str) -> str:
    return state.split(" (")[0]


def _write_report(stats, freq, meta, agree):
    L = ["# Long-history regime proxy — Fama-French factors × macro quadrants", ""]
    L += [f"Classifiable history **{meta['long_start']} → {meta['long_end']}** "
          f"({meta['long_months']} months) vs the modern index window "
          f"({meta['modern_months']} months) — same classifier, same labels, just a longer "
          "clip (see `classify_states` docstring). Factors are Ken French's research series — "
          "proxies for the regime layer, **not investable sleeves**.", ""]

    L += ["## The sample the modern window never had", "",
          "| quadrant | long months | modern months | ×gain |", "|---|---|---|---|"]
    for state in freq.index:
        lo, mo = freq.iloc[:, 0][state], freq.iloc[:, 1][state]
        L += [f"| {_short(state)} | {lo} | {mo} | ×{lo / max(mo, 1):.1f} |"]
    L += ["", "The whole point in one row: the long sample's Stagflation months include the "
          "actual 1970s, not just the 2021-22 echo.", ""]

    L += ["## Per-quadrant factor behaviour — long vs modern", ""]
    for state in STATE_ORDER:
        sub = stats[stats.state == state]
        if sub.empty:
            continue
        L += [f"### {_short(state)}", "",
              "| factor | sample | n | ann. return | ann. vol | hit rate |", "|---|---|---|---|---|---|"]
        for f in FACTORS:
            for _, r in sub[sub.factor == f].iterrows():
                L += [f"| {r.factor_label} | {r['sample'].split(' (')[0]} | {r.n_months} | "
                      f"{r.ann_return:+.1%} | {r.ann_vol:.1%} | {r.hit_rate:.0%} |"]
        L += [""]

    n_ok = int(agree.signs_agree.sum())
    L += ["## Verdict — does the modern pattern hold out-of-era?", "",
          f"Sign agreement (long vs modern mean, per state × factor): **{n_ok}/{len(agree)} "
          "cells agree.** Cells that flip:", ""]
    flips = agree[~agree.signs_agree]
    if flips.empty:
        L += ["- none — every modern per-quadrant sign survives the long sample."]
    else:
        for _, r in flips.iterrows():
            L += [f"- {_short(r.state)} × {FACTOR_LABEL[r.factor]}: modern and long samples "
                  "disagree on direction — treat the modern reading as era-specific, not "
                  "structural."]
    L += ["", "Interpretation rule: patterns that agree across both samples are candidates for "
          "feeding the optimizer's regime views with long-history Q (recorded follow-up in "
          "TODO.md); patterns that flip are exactly the ones the 28-year window would have "
          "overfit.", ""]
    C.LONG_HISTORY_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    run()
