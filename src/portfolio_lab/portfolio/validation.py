"""Walk-forward out-of-sample validation — the optimizer's honesty protocol.

Directive 7 of the literature synthesis (info/literature.md §4): validate like we forecast.
Every contestant re-estimates EVERYTHING (shrunk covariance, anchors, BL posterior, per-quadrant
means, transition matrix, outlook) on an expanding training window, holds the resulting weights
constant-mix for the next refit interval, and is judged only on months it never saw. Same
warmup/refit discipline as the quadrant-forecasting backtests (info/TODO.md, 2026-07).

Contestants: 1/N (the DeMiguel benchmark — with 330 months it may well win, and saying so is a
feature, not a failure), min-variance, ERC (the anchor), HRP, the balanced-slider default,
momentum, the maximin family (unconstrained, diversified) and — when the proxy sleeves exist —
the **all-weather diversified maximin on its own extended universe** (equities + bonds/gold/
cash), so the project's flagship robust portfolio gets the same OOS verdict as everything else.
Vol-target overlays are applied on selected bases. This table is also the evidence that will
eventually confirm or flip ERC vs HRP as the default anchor.

Honesty caveats, stated not hidden:
- The macro-state labels carry the classifier's mild full-sample z-normalization look-ahead
  (CLAUDE.md caveat #17) — it affects component weighting, never the primary trend's direction.
  Per-quadrant means, transitions and the outlook are recomputed on the training window only.
- Returns are net of transaction costs (config.OPTIMIZER_TC_BPS one-way on turnover); gross
  Sharpe is reported alongside.
- The all-weather contestant's data tail can be 1-2 months shorter than the equity menu's
  (proxy sources lag) — its stats cover its own months.

Exposure robustness (MILESTONES M12 — "a method only gets credit if its edge survives
removing its favorite region"): `exposure_diagnostics()` decomposes each contestant's OOS
record (half-sample Sharpe split, rolling beats-1/N share, correlation with each region's
Reference) and runs on every pipeline build; `leave_one_region_out()` re-runs the whole
walk-forward dropping one region's sleeves at a time (expensive — CLI only, like A2's
`--dispersion`).

Run:  python -m portfolio_lab.portfolio.validation            # the walk-forward table
      python -m portfolio_lab.portfolio.validation --loro     # leave-one-region-out sweep
      python -m portfolio_lab.portfolio.validation --loro EM USA   # only these regions
"""
from __future__ import annotations
import argparse

import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.engine import _perf_stats
from portfolio_lab.portfolio import optimizer as opt
from portfolio_lab.portfolio import rules

# base portfolios the volatility-targeting overlay is tested on (one naive, one that already wins)
VOLTARGET_BASES = ["1/N", "Min-variance"]


def _contestants(inp: dict, n_starts: int, seed: int) -> dict:
    """name -> weight vector, all estimated from the training-window inputs only."""
    out = dict(inp["anchors"])                              # 1/N, ERC (anchor), HRP, Min-variance
    out["Balanced sliders (5/5/5)"] = opt.optimize(
        prefs={"return": 5, "risk": 5, "diversification": 5},
        inputs=inp, n_starts=n_starts, seed=seed)["w"]
    out[f"Momentum {C.OPTIMIZER_MOMENTUM_LOOKBACK}-{C.OPTIMIZER_MOMENTUM_SKIP} "
        f"(top {C.OPTIMIZER_MOMENTUM_K})"] = rules.momentum_weights(inp["rets"])
    if inp["mu_q"] is not None and len(inp["mu_q"]) >= 2:
        out["Maximin (worst quadrant)"] = opt.optimize(
            maximin=True, inputs=inp, n_starts=n_starts, seed=seed)["w"]
        out["Maximin (diversified)"] = opt.optimize(
            maximin=True, cap=C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT / 100.0,
            geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0,
            factor_cap=C.OPTIMIZER_FACTOR_CAP_PCT / 100.0,
            inputs=inp, n_starts=n_starts, seed=seed)["w"]
    return out


def _drop_region(rets: pd.DataFrame, region: str) -> pd.DataFrame:
    """Remove every sleeve of one region (column labels are '<region> | <factor>')."""
    keep = [c for c in rets.columns if c.split(" | ")[0] != region]
    if len(keep) == len(rets.columns):
        raise ValueError(f"no sleeves matched region {region!r} "
                         f"(have: {sorted({c.split(' | ')[0] for c in rets.columns})})")
    return rets[keep]


def walk_forward(warmup: int = None, refit: int = None, n_starts: int = None,
                 seed: int = None, drop_region: str = None, rets: pd.DataFrame = None
                 ) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Expanding-window backtest. Returns (summary DataFrame, dict, monthly OOS returns
    DataFrame — one column per contestant, used by portfolio/visualize.py for the cumulative
    comparison curves). drop_region: run on the menu WITHOUT that region's sleeves (the
    leave-one-region-out probe — M12). rets: run on a CUSTOM returns universe instead of the
    MSCI menu (the FF-international confirmatory test — M16); the all-weather contestant is
    skipped there, its extended universe being MSCI-specific."""
    warmup = warmup or C.OPTIMIZER_WF_WARMUP_MONTHS
    refit = refit or C.OPTIMIZER_WF_REFIT_MONTHS
    n_starts = n_starts or C.OPTIMIZER_WF_N_STARTS
    seed = C.OPTIMIZER_SEED if seed is None else seed

    custom_universe = rets is not None
    if not custom_universe:
        rets = opt.load_returns()
    if drop_region is not None:
        rets = _drop_region(rets, drop_region)
    T = len(rets)
    if T <= warmup + refit:
        raise ValueError(f"not enough history for walk-forward (T={T}, warmup={warmup})")

    AW_NAME = "Maximin (all-weather div)"
    div_kw = dict(cap=C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT / 100.0,
                  geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0,
                  factor_cap=C.OPTIMIZER_FACTOR_CAP_PCT / 100.0)
    rets_aw = None
    if not custom_universe and C.ASSET_CLASS_MONTHLY.exists():
        aw = opt.load_returns(include_asset_classes=True)
        if drop_region is not None:
            aw = _drop_region(aw, drop_region)
        if aw.shape[1] > rets.shape[1]:                     # proxies actually joined
            rets_aw = aw

    # per contestant: gross monthly return + monthly one-way turnover (only rebalance months > 0)
    gross_chunks: dict[str, list] = {}
    turn_chunks: dict[str, list] = {}
    prev_w: dict[str, np.ndarray] = {}
    whist: dict[str, list] = {}                             # (oos_start, weights) per refit
    refit_dates = []
    for t in range(warmup, T, refit):
        inp = opt.build_inputs(rets.iloc[:t])
        refit_dates.append(str(rets.index[t - 1].date()))
        oos = rets.iloc[t:t + refit].values
        entries = [(name, w, oos, rets.columns)
                   for name, w in _contestants(inp, n_starts, seed).items()]
        if rets_aw is not None:                             # flagship on its own universe
            train_aw = rets_aw.loc[:rets.index[t - 1]]
            oos_aw = rets_aw.loc[rets.index[t]:rets.index[min(t + refit, T) - 1]]
            if len(train_aw) >= warmup - 12 and len(oos_aw):
                try:
                    inp_aw = opt.build_inputs(train_aw)
                    if inp_aw["mu_q"] is not None:
                        w_aw = opt.optimize(maximin=True, inputs=inp_aw,
                                            n_starts=n_starts, seed=seed, **div_kw)["w"]
                        entries.append((AW_NAME, w_aw, oos_aw.values, rets_aw.columns))
                except Exception as e:
                    print(f"[validation] WARN all-weather refit at {rets.index[t - 1].date()} "
                          f"skipped ({e})")
        for name, w, oos_m, cols in entries:
            whist.setdefault(name, []).append((rets.index[t], pd.Series(w, index=cols)))
            chunk = oos_m @ w
            tmonth = np.zeros(len(chunk))
            if name in prev_w:                              # trading happens on the first month
                tmonth[0] = float(np.abs(w - prev_w[name]).sum() / 2)
            prev_w[name] = w
            gross_chunks.setdefault(name, []).append(chunk)
            turn_chunks.setdefault(name, []).append(tmonth)

    oos_index = rets.index[warmup:]
    gross = {n: pd.Series(np.concatenate(c), index=oos_index[:sum(map(len, c))])
             for n, c in gross_chunks.items()}
    turn = {n: pd.Series(np.concatenate(c), index=oos_index[:sum(map(len, c))])
            for n, c in turn_chunks.items()}

    # volatility-targeting overlays on selected bases (their own leverage-change turnover is
    # charged on top of the base's rebalancing turnover)
    for base in VOLTARGET_BASES:
        if base not in gross:
            continue
        managed, extra_turn = rules.vol_managed(gross[base])
        vt = f"{base} + vol-target"
        gross[vt] = managed
        turn[vt] = turn[base] + extra_turn

    cost = C.OPTIMIZER_TC_BPS / 10_000.0
    rows, monthly = [], {}
    for name in gross:
        net = gross[name] - cost * turn[name]              # charge transaction costs
        monthly[name] = net
        lvl = pd.concat([pd.Series([100.0], index=[oos_index[0] - pd.offsets.MonthEnd(1)]),
                         100.0 * (1 + net).cumprod()])
        p = _perf_stats(lvl)
        gp = _perf_stats(pd.concat([pd.Series([100.0], index=[lvl.index[0]]),
                                    100.0 * (1 + gross[name]).cumprod()]))
        rows.append(dict(portfolio=name, oos_CAGR=p["CAGR"], oos_ann_vol=p["ann_vol"],
                         oos_sharpe_rf0=p["sharpe_rf0"], oos_max_drawdown=p["max_drawdown"],
                         oos_sharpe_gross=gp["sharpe_rf0"],
                         mean_turnover_per_refit=float(turn[name].sum() / max(1, len(refit_dates)))))
    summary = pd.DataFrame(rows).sort_values("oos_sharpe_rf0", ascending=False)
    meta = dict(warmup_months=warmup, refit_months=refit, n_refits=len(refit_dates),
                oos_start=str(oos_index[0].date()), oos_end=str(oos_index[-1].date()),
                oos_months=len(oos_index), tc_bps=C.OPTIMIZER_TC_BPS,
                n_series=rets.shape[1], dropped_region=drop_region,
                # pre-cost pieces, so the sensitivity grid can re-net at any cost level
                # without re-running the optimization (weights never depend on costs)
                _gross=pd.DataFrame(gross), _turnover=pd.DataFrame(turn),
                # per-refit weights (overlays excluded — they scale a base), for attribution
                _weights={n: pd.DataFrame({d: s for d, s in ws}).T for n, ws in whist.items()})
    return summary, meta, pd.DataFrame(monthly)


def sleeve_attribution(meta: dict) -> pd.DataFrame:
    """Which sleeves actually paid each contestant's OOS return? (M21)

    Arithmetic Brinson-style decomposition: sleeve i's contribution to contestant P is
    sum_t w_i(t) * r_i(t) over every OOS month (weights constant within each refit
    interval); `share` normalizes by the contestant's total. Ignores compounding — shares
    are approximate but the ordering is what the question needs (e.g. does min-variance
    live off the Quality sleeves, as M2/low-vol suggests?)."""
    rets = opt.load_returns()
    rets_aw = (opt.load_returns(include_asset_classes=True)
               if C.ASSET_CLASS_MONTHLY.exists() else None)
    rows = []
    for name, wdf in meta["_weights"].items():
        uni = rets if list(wdf.columns) == list(rets.columns) else rets_aw
        if uni is None:
            continue
        contrib = pd.Series(0.0, index=wdf.columns)
        for i, start in enumerate(wdf.index):
            if i + 1 < len(wdf.index):                      # up to, excluding, the next refit
                chunk = uni.loc[start:wdf.index[i + 1]]
                if len(chunk) and chunk.index[-1] == wdf.index[i + 1]:
                    chunk = chunk.iloc[:-1]
            else:
                chunk = uni.loc[start:]
            contrib += chunk.mul(wdf.iloc[i], axis=1).sum()
        total = contrib.sum()
        for sleeve, v in contrib.items():
            if abs(v) > 1e-12:
                rows.append(dict(portfolio=name, sleeve=sleeve, contribution=float(v),
                                 share=float(v / total) if total else np.nan))
    return pd.DataFrame(rows).sort_values(["portfolio", "share"], ascending=[True, False])


# ------------------------------------------------- exposure robustness (MILESTONES M12)

def _ann_sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(12)) if len(x) > 1 and x.std() > 0 else np.nan


def exposure_diagnostics(monthly: pd.DataFrame, roll: int = 36) -> pd.DataFrame:
    """Where does each contestant's OOS record come from? Three cheap reads per contestant:

    - sharpe_h1 / sharpe_h2: OOS Sharpe in the first vs second half of the OOS period. An
      edge that only exists in one half is a period effect, not a property of the method
      (M12: the equity maximin was 1/N-like pre-2024 and got lifted by the EM rally).
    - beats_1N_roll{roll}: share of rolling windows where the contestant's Sharpe beats
      1/N's on the SAME months — the A2 window-robustness metric, applied to OOS returns.
    - corr_<region>: correlation with each region Reference's returns. A high number says
      the record is that market's beta wearing a method's name; the CSV keeps every region,
      the report shows the largest.
    """
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    refs = {c.split(" | ")[0]: lv[c].pct_change()
            for c in lv.columns if c.split(" | ")[1] == "Reference"}
    rows = []
    for name in monthly.columns:
        x = monthly[name].dropna()
        half = len(x) // 2
        row = dict(portfolio=name,
                   sharpe_h1=_ann_sharpe(x.iloc[:half]), sharpe_h2=_ann_sharpe(x.iloc[half:]))
        if "1/N" in monthly.columns and name != "1/N":
            both = pd.concat([x, monthly["1/N"]], axis=1, join="inner").dropna()
            rs = both.rolling(roll).apply(lambda w: w.mean() / w.std() if w.std() > 0 else np.nan)
            valid = rs.dropna()
            row[f"beats_1N_roll{roll}"] = (float((valid.iloc[:, 0] > valid.iloc[:, 1]).mean())
                                           if len(valid) else np.nan)
        else:
            row[f"beats_1N_roll{roll}"] = np.nan
        for region, ref in refs.items():
            row[f"corr_{region}"] = float(x.corr(ref.reindex(x.index)))
        rows.append(row)
    return pd.DataFrame(rows)


def leave_one_region_out(regions: list[str] = None, n_starts: int = None) -> pd.DataFrame:
    """Re-run the walk-forward once per dropped region (default: every equity region on the
    menu). A contestant only gets credit for its OOS rank if the rank survives losing its
    favorite region — the direct answer to M12. Writes optimizer_loro.csv and
    REPORT_exposure_robustness.md; expensive (one full walk-forward per region), so this is
    a CLI mode, not a pipeline stage."""
    C.ensure_dirs()
    menu_regions = sorted({c.split(" | ")[0] for c in opt.load_returns().columns})
    regions = regions or menu_regions
    runs = {}
    for reg in [None] + list(regions):
        label = reg or "none"
        print(f"[validation] leave-one-region-out: dropping {label} ...")
        summary, meta, _ = walk_forward(n_starts=n_starts, drop_region=reg)
        s = summary.reset_index(drop=True)
        s["rank"] = s.index + 1
        s["dropped_region"] = label
        runs[label] = s
    long = pd.concat(runs.values(), ignore_index=True)
    long.to_csv(C.OPTIMIZER_LORO, index=False)
    _write_loro_report(runs, regions)
    print(f"[validation] wrote {C.OPTIMIZER_LORO} and {C.OPTIMIZER_LORO_REPORT}")
    return long


def _write_loro_report(runs: dict, regions: list[str]):
    base = runs["none"].set_index("portfolio")
    L = ["# Exposure robustness — leave-one-region-out walk-forward", "",
         "Motivation (MILESTONES M12): the equity maximin's full-period OOS Sharpe was largely "
         "its EM exposure meeting the 2024+ EM rally. This table re-runs the ENTIRE walk-forward "
         "with each region's sleeves removed from the menu: a method whose rank collapses "
         "without one region was riding that region, not adding skill. Same protocol as the "
         "main honesty table (expanding window, training-only estimation, net of costs).", ""]
    cols = ["none"] + list(regions)
    L += ["| portfolio | " + " | ".join(f"drop {c}" if c != "none" else "full menu"
                                        for c in cols) + " |",
          "|" + "---|" * (len(cols) + 1)]
    for p in base.index:
        cells = []
        for c in cols:
            s = runs[c].set_index("portfolio")
            cells.append(f"{s.loc[p, 'oos_sharpe_rf0']:.2f} (#{int(s.loc[p, 'rank'])})"
                         if p in s.index else "—")
        L.append(f"| {p} | " + " | ".join(cells) + " |")
    L += ["", "Cells: net OOS Sharpe (rank in that run). '—': contestant not available on "
          "that menu.", ""]
    # verdict: worst rank slip per contestant across drops
    L += ["## Verdict — worst rank slip per contestant", ""]
    for p in base.index:
        ranks = [int(runs[c].set_index("portfolio").loc[p, "rank"])
                 for c in cols if p in runs[c].set_index("portfolio").index]
        L.append(f"- **{p}**: rank #{ranks[0]} on the full menu, worst #{max(ranks)} across "
                 f"drops (best #{min(ranks)}).")
    L += ["", "_A rank that survives every drop is a property of the method; a rank that "
          "collapses on one drop was that region's beta._", ""]
    C.OPTIMIZER_LORO_REPORT.write_text("\n".join(L))


def run():
    C.ensure_dirs()
    summary, meta, monthly = walk_forward()
    summary.to_csv(C.OPTIMIZER_WALKFORWARD, index=False)
    monthly.to_csv(C.OPTIMIZER_WALKFORWARD_RETURNS)
    expo = exposure_diagnostics(monthly)
    expo.to_csv(C.OPTIMIZER_EXPOSURE, index=False)
    from portfolio_lab.portfolio.inference import inference_table, pbo_cscv
    inference_table(monthly).to_csv(C.OPTIMIZER_INFERENCE, index=False)
    sleeve_attribution(meta).to_csv(C.OPTIMIZER_ATTRIBUTION, index=False)
    pbo = pbo_cscv(monthly)
    print(f"[validation] PBO (CSCV S={pbo['S']}): {pbo['pbo']:.0%}" if pbo["n_combos"]
          else "[validation] PBO skipped (short sample)")
    print(f"[validation] walk-forward: {meta['n_refits']} refits, OOS "
          f"{meta['oos_start']} -> {meta['oos_end']} ({meta['oos_months']} months)")
    print(summary.to_string(index=False))
    return summary, meta, monthly


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Walk-forward OOS validation")
    ap.add_argument("--loro", nargs="*", metavar="REGION", default=None,
                    help="leave-one-region-out sweep (no args = every equity region)")
    args = ap.parse_args()
    if args.loro is not None:
        leave_one_region_out(args.loro or None)
    else:
        run()
