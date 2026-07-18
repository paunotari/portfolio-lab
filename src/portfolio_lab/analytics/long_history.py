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


FF_BY_FACTOR_TYPE = {"Momentum": "mom", "Enhanced Value": "hml"}   # Quality: no FF counterpart


def msci_factor_prior(rets: pd.DataFrame) -> dict | None:
    """Long-history prior for the optimizer's regime views (the recorded TODO follow-up).

    For each MSCI factor type with an FF counterpart, per quadrant:
      - beta: OLS slope of the modern MSCI factor-vs-Reference excess (region-mean) on the FF
        factor — translates the academic long-short factor into 'long-only sleeve excess' space
        (expect ~0.2-0.5). Same univariate-OLS precedent as analytics/macro_link.py.
      - long_diff = beta * mean FF factor return in that quadrant over the LONG sample
      - agree: do the long and modern samples agree on the factor's SIGN in that quadrant?
        (views.py blends toward long_diff only where they do — never replaces blindly)

    Walk-forward honesty: everything is clipped to `rets.index.max()`, so a training window
    ending in 2015 uses 1960-2015 long history, not the future. Returns None when the FF file
    is absent (the views then run modern-only, as before).
    """
    if not C.FF_FACTORS_MONTHLY.exists():
        return None
    end = rets.index.max()
    ff = pd.read_csv(C.FF_FACTORS_MONTHLY, index_col=0, parse_dates=True).sort_index().loc[:end]
    states_long = classify_states(start="1926-01-01")
    ff = ff.join(states_long[["state"]], how="inner").dropna(subset=["state"])
    modern_start = rets.index.min()

    out = {}
    for ftype, fcol in FF_BY_FACTOR_TYPE.items():
        cols = [c for c in rets.columns if c.split(" | ")[1] == ftype]
        pairs = [(c, f"{c.split(' | ')[0]} | Reference") for c in cols]
        pairs = [(c, r) for c, r in pairs if r in rets.columns]
        if not pairs:
            continue
        exc = pd.concat([rets[c] - rets[r] for c, r in pairs], axis=1).mean(axis=1)
        both = pd.concat([exc, ff[fcol]], axis=1, join="inner").dropna()
        if len(both) < C.MACRO_MIN_OVERLAP_MONTHS:
            continue
        x, y = both.iloc[:, 1], both.iloc[:, 0]
        beta = float(((x - x.mean()) * (y - y.mean())).sum() / ((x - x.mean()) ** 2).sum())

        per_state = {}
        for state, g in ff.groupby("state"):
            f_long = g[fcol].dropna()
            f_mod = g.loc[modern_start:, fcol].dropna()
            if len(f_long) < 24 or len(f_mod) < 6:
                continue
            per_state[state] = dict(
                agree=bool(np.sign(f_long.mean()) == np.sign(f_mod.mean())),
                long_diff=float(beta * f_long.mean()), n_long=int(len(f_long)))
        if per_state:
            out[ftype] = dict(beta=beta, states=per_state)
    return out or None


def asset_class_prior(rets: pd.DataFrame) -> dict | None:
    """Long-history prior for the NON-EQUITY proxy sleeves' per-quadrant means.

    Unlike the factor prior (which needs a beta to translate long-short factors into sleeve
    space), the proxies ARE the same series over the long sample — bond/gold/cash have
    per-quadrant means from 1962+ (~64y vs ~27y modern). Per sleeve x state:
    {agree (era sign-agreement), long_mean, n_long}. Clipped to rets.index.max() for
    walk-forward honesty. Returns None when the proxy file is absent."""
    if not C.ASSET_CLASS_MONTHLY.exists():
        return None
    end = rets.index.max()
    ac = pd.read_csv(C.ASSET_CLASS_MONTHLY, index_col=0, parse_dates=True).sort_index()
    # cash is EXCLUDED on principle: its per-quadrant "mean" is the era's policy-rate LEVEL
    # (5-15% in the 1962-1990 sample), not a cross-era asset behavior — anchoring it would
    # smuggle high-rate-era yields into today's expectations. Gold/bond quadrant dynamics
    # (flight-to-quality, real-asset behavior) are the transferable signal; rate levels are not.
    cols = [c for c in ac.columns if c in rets.columns and "Cash" not in c]
    if not cols:
        return None
    states_long = classify_states(start="1926-01-01")[["state"]]
    ac.index = pd.PeriodIndex(ac.index, freq="M")
    states_long.index = pd.PeriodIndex(states_long.index, freq="M")
    joined = ac[cols].join(states_long, how="inner").dropna(subset=["state"])
    joined = joined.loc[:pd.Period(end, freq="M")]
    modern_start = pd.Period(rets.index.min(), freq="M")

    out = {}
    for col in cols:
        per_state = {}
        for state, g in joined.groupby("state"):
            f_long = g[col].dropna()
            f_mod = g.loc[modern_start:, col].dropna()
            if len(f_long) < 24 or len(f_mod) < 6:
                continue
            per_state[state] = dict(
                agree=bool(np.sign(f_long.mean()) == np.sign(f_mod.mean())),
                long_mean=float(f_long.mean()), n_long=int(len(f_long)))
        if per_state:
            out[col] = per_state
    return out or None


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
