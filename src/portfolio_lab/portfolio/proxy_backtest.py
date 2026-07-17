"""The 60-year construction-rule race on the proxy universe (research roadmap A1).

The question this answers — the project's main goal stated plainly: WHICH PORTFOLIO
CONSTRUCTION RULES ARE ACTUALLY OPTIMAL, judged with enough history to mean it? Our MSCI
walk-forward covers one kind 17-year OOS window (2009-2026, no prolonged bear market). This
module races the same rules over the PROXY universe instead:

  equity race       6 long-only Fama-French size x value portfolios, 1926+ -> OOS ~1937-2026
                    (~90 years: the Depression tail, WWII, the 1970s, everything).
                    mu-free structural rules only (1/N, min-variance, ERC, HRP).
  multi-asset race  the 6 equity portfolios + US Treasury 10y + Gold + T-bills, 1962+ ->
                    OOS ~1972-2026 (~54 years). Adds the maximin variants, which need the
                    macro-quadrant classification (available from 1960) — so maximin is
                    judged THROUGH the real 1970s stagflation out of sample, not the 2021-22
                    echo.

Same honesty protocol as portfolio/validation.py: expanding window, 120m warmup, annual
refits, everything re-estimated on the training window only, returns net of transaction costs
(10 bps one-way on turnover), 1/N always in the table. Same engines byte-for-byte
(portfolio/shrinkage.py, portfolio/anchors.py, optimizer._solve_maximin) — this is the same
race on a longer track, not a new method.

Proxy caveats, stated: FF portfolios are research constructs (no fees/frictions beyond our
cost model); gold pre-1971 is the managed Bretton Woods price (the multi-asset race starts
1962, so its first decade of gold is calm by construction); the macro-state labels carry the
classifier's full-sample z-normalization (CLAUDE.md caveat #17).

Outputs: outputs/analytics/proxy_backtest/{proxy_backtest_summary.csv, REPORT_proxy_backtest.md}

Run:  python -m portfolio_lab.portfolio.proxy_backtest
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.engine import _perf_stats
from portfolio_lab.portfolio import anchors
from portfolio_lab.portfolio.shrinkage import shrink_constant_correlation
from portfolio_lab.portfolio import optimizer as opt

COST = 0.0010                       # 10 bps one-way, same convention as validation.py
WARMUP, REFIT = 120, 12


# --------------------------------------------------------------------------- universes

def _monthly_period_join(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Join on month PERIOD (sources mix business and calendar month-end stamps)."""
    out = None
    for f in frames:
        f = f.copy()
        f.index = pd.PeriodIndex(f.index, freq="M")
        out = f if out is None else out.join(f, how="inner")
    out = out.dropna()
    out.index = out.index.to_timestamp("M")
    return out


def load_universes() -> dict[str, pd.DataFrame]:
    """{'equity': 1926+ 6 portfolios, 'multi_asset': 1962+ 9 sleeves} — whichever inputs exist."""
    out = {}
    if not C.FF_PORTFOLIOS_MONTHLY.exists():
        return out
    eq = pd.read_csv(C.FF_PORTFOLIOS_MONTHLY, index_col=0, parse_dates=True).sort_index().dropna()
    out["equity"] = eq
    if C.ASSET_CLASS_MONTHLY.exists():
        ac = pd.read_csv(C.ASSET_CLASS_MONTHLY, index_col=0, parse_dates=True).sort_index()
        out["multi_asset"] = _monthly_period_join([eq, ac])
    return out


# --------------------------------------------------------------------------- contestants

def _states_for(rets: pd.DataFrame) -> pd.Series | None:
    """Quadrant label per month of `rets` (period-aligned), or None without macro data."""
    if not C.MACRO_STATE_MONTHLY.exists():
        return None
    from portfolio_lab.analytics.macro_state import classify_states
    st = classify_states(start="1926-01-01")["state"]
    st.index = pd.PeriodIndex(st.index, freq="M")
    aligned = st.reindex(pd.PeriodIndex(rets.index, freq="M"))
    aligned.index = rets.index
    return aligned


def _mu_q(train: pd.DataFrame, states: pd.Series) -> pd.DataFrame | None:
    """Per-quadrant mean returns on the training window (>= 24 months per state to count)."""
    if states is None:
        return None
    st = states.reindex(train.index).dropna()
    rows = {}
    for state in st.unique():
        months = st.index[st == state]
        if len(months) >= 24:
            rows[state] = train.loc[months].mean()
    return pd.DataFrame(rows).T if len(rows) >= 2 else None


def _maximin(train: pd.DataFrame, mu_q: pd.DataFrame, cap: float, factor_cap_frac: float = None,
             rng=None) -> np.ndarray:
    """Reuse optimizer._solve_maximin on a minimal inputs dict. Optional per-sleeve-label
    factor cap is not meaningful here (proxy labels are unique), so only the sleeve cap acts."""
    inp = dict(series=list(train.columns), mu_q=mu_q)
    w, _ = opt._solve_maximin(inp, cap, [{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
                              n_starts=C.OPTIMIZER_WF_N_STARTS,
                              rng=rng or np.random.default_rng(C.OPTIMIZER_SEED))
    return w


def _contestants(train: pd.DataFrame, states: pd.Series, multi_asset: bool) -> dict[str, np.ndarray]:
    sigma, _ = shrink_constant_correlation(train.values)
    n = train.shape[1]
    out = {"1/N": anchors.equal_weight(n),
           "Min-variance": anchors.min_var_weights(sigma),
           "ERC": anchors.erc_weights(sigma),
           "HRP": anchors.hrp_weights(sigma)}
    if multi_asset:
        mu_q = _mu_q(train, states)
        if mu_q is not None:
            out["Maximin (unconstrained)"] = _maximin(train, mu_q, cap=0.40)
            out["Maximin (sleeve ≤25%)"] = _maximin(
                train, mu_q, cap=C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT / 100.0)
    return out


# --------------------------------------------------------------------------- the race

def run_race(rets: pd.DataFrame, multi_asset: bool) -> tuple[pd.DataFrame, dict]:
    """When cash is IN the menu (multi-asset race), Sharpe must be computed on EXCESS returns
    over that same cash sleeve — otherwise 'hide everything in T-bills' scores an absurd
    rf=0 Sharpe (near-zero vol, positive mean) while earning nothing over cash by definition."""
    states = _states_for(rets) if multi_asset else None
    cash_col = next((c for c in rets.columns if "Cash" in c), None)
    rf = rets[cash_col] if (multi_asset and cash_col) else None
    T = len(rets)
    oos_r: dict[str, list] = {}
    prev_w: dict[str, np.ndarray] = {}
    turnover: dict[str, list] = {}
    n_refits = 0
    for t in range(WARMUP, T, REFIT):
        n_refits += 1
        train, oos = rets.iloc[:t], rets.iloc[t:t + REFIT].values
        for name, w in _contestants(train, states, multi_asset).items():
            r = oos @ w
            if name in prev_w:
                tw = float(np.abs(w - prev_w[name]).sum() / 2)
                turnover.setdefault(name, []).append(tw)
                r = np.concatenate([[r[0] - COST * tw], r[1:]]) if len(r) else r
            oos_r.setdefault(name, []).append(r)
            prev_w[name] = w

    idx = rets.index[WARMUP:]
    rows = []
    for name, chunks in oos_r.items():
        r = pd.Series(np.concatenate(chunks), index=idx[:sum(map(len, chunks))])
        level = pd.concat([pd.Series([100.0], index=[idx[0] - pd.offsets.MonthEnd(1)]),
                           100.0 * (1 + r).cumprod()])
        p = _perf_stats(level)
        if rf is not None:
            exc = r - rf.reindex(r.index).fillna(0.0)
            sharpe = float(exc.mean() * 12 / (r.std() * np.sqrt(12))) if r.std() else np.nan
        else:
            sharpe = p["sharpe_rf0"]
        rows.append(dict(portfolio=name, oos_CAGR=p["CAGR"], oos_ann_vol=p["ann_vol"],
                         oos_sharpe=sharpe, oos_max_drawdown=p["max_drawdown"],
                         mean_turnover_per_refit=float(np.mean(turnover.get(name, [0.0])))))
    summary = pd.DataFrame(rows).sort_values("oos_sharpe", ascending=False)
    meta = dict(oos_start=str(idx[0].date()), oos_end=str(idx[-1].date()),
                oos_months=len(idx), n_refits=n_refits, n_sleeves=rets.shape[1],
                sharpe_basis=("excess over the cash sleeve" if rf is not None else "rf = 0"))
    return summary, meta


def run():
    C.ensure_dirs()
    universes = load_universes()
    if not universes:
        print("[proxy_backtest] ff_portfolios_monthly.csv missing (run ingest.ff_factors) — skipping")
        return
    all_rows, metas = [], {}
    for name, rets in universes.items():
        summary, meta = run_race(rets, multi_asset=(name == "multi_asset"))
        summary.insert(0, "race", name)
        all_rows.append(summary)
        metas[name] = meta
        print(f"[proxy_backtest] {name}: OOS {meta['oos_start']} -> {meta['oos_end']} "
              f"({meta['oos_months']}m, {meta['n_sleeves']} sleeves)")
        print(summary.to_string(index=False))
    df = pd.concat(all_rows, ignore_index=True)
    df.to_csv(C.PROXY_BACKTEST_SUMMARY, index=False)
    _write_report(df, metas)
    print(f"[proxy_backtest] wrote {C.PROXY_BACKTEST_SUMMARY} and {C.PROXY_BACKTEST_REPORT}")
    return df, metas


def _write_report(df: pd.DataFrame, metas: dict):
    L = ["# The 60-year construction-rule race (proxy universe)", ""]
    L += ["Same rules, same engines, same honesty protocol as the MSCI walk-forward — on a "
          "track long enough to include the Depression tail, the 1970s and every bear market "
          "since. Returns net of 10 bps one-way costs. Proxy caveats in the module docstring.", ""]
    for race, meta in metas.items():
        sub = df[df.race == race]
        L += [f"## {race.replace('_', ' ')} race — OOS {meta['oos_start']} → {meta['oos_end']} "
              f"({meta['oos_months']} months, {meta['n_sleeves']} sleeves; Sharpe basis: "
              f"{meta['sharpe_basis']})", "",
              "| rule | OOS CAGR | vol | Sharpe | maxDD | turnover/refit |", "|---|---|---|---|---|---|"]
        for _, r in sub.iterrows():
            L += [f"| {r.portfolio} | {r.oos_CAGR:.2%} | {r.oos_ann_vol:.2%} | "
                  f"{r.oos_sharpe:.2f} | {r.oos_max_drawdown:.1%} | "
                  f"{r.mean_turnover_per_refit:.1%} |"]
        L += [""]
    eq = df[df.race == "equity"]
    if len(eq):
        L += [f"Equity race winner over ~{metas['equity']['oos_months'] // 12} years: "
              f"**{eq.iloc[0].portfolio}** (Sharpe {eq.iloc[0].oos_sharpe:.2f} vs 1/N "
              f"{eq[eq.portfolio == '1/N'].oos_sharpe.iloc[0]:.2f}). If a rule needs a "
              "particular era to look good, this table is where that shows.", ""]
    C.PROXY_BACKTEST_REPORT.write_text("\n".join(L))


def run_dispersion():
    """Roadmap A2: window-robustness. Each race re-run dropping the first k months of history
    (k in config.PROXY_BACKTEST_OFFSETS) — four different expanding-window paths per race.
    A rule whose rank depends on the window is an era artifact; a rule that holds across
    variants is a finding. CLI-only (several full races)."""
    C.ensure_dirs()
    universes = load_universes()
    if not universes:
        print("[proxy_backtest] inputs missing — skipping dispersion")
        return
    rows = []
    for uname, rets in universes.items():
        for off in C.PROXY_BACKTEST_OFFSETS:
            sub = rets.iloc[off:]
            if len(sub) < WARMUP + 5 * REFIT:
                continue
            summary, meta = run_race(sub, multi_asset=(uname == "multi_asset"))
            for _, r in summary.iterrows():
                rows.append(dict(race=uname, offset_months=off, oos_start=meta["oos_start"],
                                 portfolio=r.portfolio, oos_sharpe=r.oos_sharpe,
                                 oos_CAGR=r.oos_CAGR, oos_max_drawdown=r.oos_max_drawdown))
            print(f"[dispersion] {uname} offset {off}: done (OOS from {meta['oos_start']})")
    df = pd.DataFrame(rows)
    df.to_csv(C.PROXY_BACKTEST_DISPERSION, index=False)

    L = ["# Window-robustness of the construction-rule race (A2)", "",
         "Each race re-run dropping the first k months of history — different expanding-window "
         "paths, same rules and protocol. **A result that only holds in one window is an era "
         "artifact; one that holds across variants is a finding.** Sharpe basis as in the main "
         "report (equity: rf=0; multi-asset: excess over the cash sleeve).", ""]
    for uname in df.race.unique():
        sub = df[df.race == uname]
        L += [f"## {uname.replace('_', ' ')} race — Sharpe across {sub.offset_months.nunique()} "
              "window variants", "",
              "| rule | median | min | max | beats 1/N in | top rule in |", "|---|---|---|---|---|---|"]
        one_n = sub[sub.portfolio == "1/N"].set_index("offset_months").oos_sharpe
        for port in sub.portfolio.unique():
            s = sub[sub.portfolio == port].set_index("offset_months").oos_sharpe
            beats = (s > one_n.reindex(s.index)).mean()
            top = (sub.groupby("offset_months").apply(
                lambda g: g.loc[g.oos_sharpe.idxmax(), "portfolio"], include_groups=False) == port).mean()
            L += [f"| {port} | {s.median():.2f} | {s.min():.2f} | {s.max():.2f} | "
                  f"{beats:.0%} | {top:.0%} |"]
        L += [""]
    C.PROXY_BACKTEST_DISPERSION_REPORT.write_text("\n".join(L))
    print(f"[proxy_backtest] wrote {C.PROXY_BACKTEST_DISPERSION} and "
          f"{C.PROXY_BACKTEST_DISPERSION_REPORT}")
    return df


if __name__ == "__main__":
    import sys
    if "--dispersion" in sys.argv:
        run_dispersion()
    else:
        run()
