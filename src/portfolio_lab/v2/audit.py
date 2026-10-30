"""Computation audit (v2.0, 2026-10-30): the checks a referee would run next.

Each job writes to outputs/v2.0/audit/ and can run in its own process:

  python -m portfolio_lab.v2.audit <job>        jobs below; `all-cheap` runs the fast ones

- facts      recomputes the menu facts the prose quotes, from the processed data, by hand
- dr2        DR^2 under 1/N AND at its maximum, on several menus: is "three assets add more
             than twenty-eight equity indices" true, and is DR^2 under 1/N a property of the
             menu or of the weights?
- menus      THE RECONCILIATION TEST: the same rules on menus with very different dispersion.
             The paper claims the menu decides whether optimization beats 1/N; that needs more
             than one menu.
- momentum   cross-sectional momentum refit monthly and quarterly, not only annually
- proxy      the 90-year race in excess returns, with p-values (v1 reported neither)
- worked     the shrinkage estimator worked out on real numbers, for the explanation in the paper
- race jobs  full walk-forwards under one changed assumption, in excess returns:
             loro:<REGION>, lag2, refit6, refit24, cov:<estimator>, caps:<s>_<g>, disjoint, ff_intl
"""
from __future__ import annotations
import argparse
import itertools
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from portfolio_lab import config as C
from portfolio_lab.portfolio import anchors, inference as I, optimizer as opt, rules, validation
from portfolio_lab.dates import align_months
from portfolio_lab.portfolio.shrinkage import shrink_constant_correlation
from portfolio_lab.v2 import factors as F
from portfolio_lab.v2 import risk_adjusted as R

OUT = C.V2_DIR / "audit"
DISJOINT = ["USA", "Europe", "Japan", "EM", "AC_Asia_ex_Japan"]
COST = C.OPTIMIZER_TC_BPS / 1e4
KF = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{}_CSV.zip"
KF_MENUS = {"FF 10 industries": "10_Industry_Portfolios", "FF 30 industries": "30_Industry_Portfolios",
            "FF 48 industries": "48_Industry_Portfolios", "FF 6 size/value": "6_Portfolios_2x3",
            "FF 25 size/value": "25_Portfolios_5x5", "FF 100 size/value": "100_Portfolios_10x10"}


def _rf(index: pd.DatetimeIndex) -> pd.Series:
    us = pd.read_csv(C.FF_FACTORS_MONTHLY, index_col=0, parse_dates=True)["rf"]
    return align_months(us, index)


def _excess(monthly: pd.DataFrame) -> pd.DataFrame:
    return monthly.sub(_rf(monthly.index), axis=0)


def race_summary(monthly: pd.DataFrame, bench: str = "1/N") -> pd.DataFrame:
    ex = _excess(monthly)
    rows = []
    for c in monthly.columns:
        e = ex[c].dropna()
        row = dict(portfolio=c, months=len(e), sharpe=float(e.mean() / e.std() * np.sqrt(12)))
        if c != bench:
            t = I.sharpe_diff_test(e, ex[bench])
            row.update(d_sharpe=t["delta"] * np.sqrt(12), p_boot=t["p_boot"])
        rows.append(row)
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False).reset_index(drop=True)


def _save(tag: str, monthly: pd.DataFrame) -> pd.DataFrame:
    OUT.mkdir(parents=True, exist_ok=True)
    s = race_summary(monthly)
    monthly.to_csv(OUT / f"returns_{tag}.csv")
    s.to_csv(OUT / f"race_{tag}.csv", index=False)
    print(f"[audit] {tag}\n" + s.round(3).to_string())
    return s


# ------------------------------------------------------------------ DR^2

def max_dr_weights(sigma: np.ndarray) -> np.ndarray:
    """Long-only maximum-diversification portfolio (Choueifaty-Coignard): the QP
    min y'Sy s.t. vol'y = 1, y >= 0; w = y / sum(y)."""
    from scipy.optimize import minimize
    vol = np.sqrt(np.diag(sigma))
    n = len(vol)
    res = minimize(lambda y: y @ sigma @ y, np.ones(n) / vol.sum(), jac=lambda y: 2 * sigma @ y,
                   bounds=[(0, None)] * n, method="SLSQP",
                   constraints=[{"type": "eq", "fun": lambda y: vol @ y - 1, "jac": lambda y: vol}],
                   options=dict(maxiter=2000, ftol=1e-14))
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def menu_stats(rets: pd.DataFrame) -> dict:
    sigma, _ = shrink_constant_correlation(rets.values)
    n = rets.shape[1]
    corr = rets.corr().values[np.triu_indices(n, 1)] if n > 1 else np.array([np.nan])
    ev = np.linalg.eigvalsh(rets.corr().values)[::-1]
    w = np.ones(n) / n
    dr = opt.diversification_ratio(w, sigma)
    wm = max_dr_weights(sigma)
    return dict(n=n, mean_corr=float(np.nanmean(corr)), min_corr=float(np.nanmin(corr)),
                pc1=float(ev[0] / ev.sum()), dr2_1n=float(dr ** 2),
                inv_mean_corr=float(1 / np.nanmean(corr)),
                dr2_max=float(opt.diversification_ratio(wm, sigma) ** 2),
                max_w_top=float(wm.max()))


def job_dr2():
    eq = opt.load_returns()
    ext = opt.load_returns(include_asset_classes=True)
    px = [c for c in ext.columns if c.startswith("Asset")]
    nocash = [c for c in px if "Cash" not in c]
    refs5 = [f"{r} | Reference" for r in DISJOINT]
    dis = [c for c in eq.columns if c.split(" | ")[0] in DISJOINT]
    menus = {"28 equity sleeves": eq, "19 disjoint-region sleeves": eq[dis],
             "5 regional markets": eq[refs5],
             "4 USA sleeves": eq[[c for c in eq.columns if c.startswith("USA")]],
             "28 + Treasury, gold, cash": ext, "28 + Treasury, gold": ext[list(eq.columns) + nocash],
             "ACWI + Treasury, gold, cash": ext[["ACWI | Reference"] + px],
             "ACWI + Treasury, gold": ext[["ACWI | Reference"] + nocash],
             "ACWI + Treasury": ext[["ACWI | Reference", "Asset | US Treasury 10y"]],
             "5 regional + Treasury, gold, cash": ext[refs5 + px],
             "Treasury, gold, cash only": ext[px]}
    t = pd.DataFrame([dict(menu=k, **menu_stats(v)) for k, v in menus.items()])
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "dr2_menus.csv", index=False)
    print(t.round(3).to_string())


# ------------------------------------------------------------------ the reconciliation test

def simple_race(rets: pd.DataFrame, warmup: int = 120, refit: int = 12) -> pd.DataFrame:
    """1/N, min-variance, ERC, HRP on the v1 protocol: expanding Ledoit-Wolf covariance, annual
    refit, long-only, 10 bps on one-way turnover, constant mix between refits."""
    chunks, prev = {}, {}
    for t in range(warmup, len(rets), refit):
        sigma, _ = shrink_constant_correlation(rets.iloc[:t].values)
        n = rets.shape[1]
        ws = {"1/N": anchors.equal_weight(n), "Min-variance": anchors.min_var_weights(sigma),
              "ERC": anchors.erc_weights(sigma), "HRP": anchors.hrp_weights(sigma)}
        oos = rets.iloc[t:t + refit]
        for k, w in ws.items():
            r = pd.Series(oos.values @ w, index=oos.index)
            if k in prev:
                r.iloc[0] -= COST * float(np.abs(w - prev[k]).sum() / 2)
            prev[k] = w
            chunks.setdefault(k, []).append(r)
    return pd.DataFrame({k: pd.concat(v) for k, v in chunks.items()})


def _kf_menu(stem: str) -> pd.DataFrame:
    """First block of a Ken French portfolio file: value-weighted monthly returns."""
    from portfolio_lab.ingest.ff_factors import _fetch_csv_lines
    return F._parse_monthly(_fetch_csv_lines(KF.format(stem)))


def job_menus():
    OUT.mkdir(parents=True, exist_ok=True)
    menus_recent, menus_long = {}, {}
    eq = opt.load_returns()
    ext = opt.load_returns(include_asset_classes=True)
    menus_recent["MSCI 28 factor sleeves"] = eq
    menus_recent["MSCI 19 disjoint sleeves"] = eq[[c for c in eq.columns if c.split(" | ")[0] in DISJOINT]]
    menus_recent["MSCI 5 regional markets"] = eq[[f"{r} | Reference" for r in DISJOINT]]
    menus_recent["MSCI 28 + 3 asset classes"] = ext
    menus_recent["ACWI + 3 asset classes"] = ext[["ACWI | Reference"] + [c for c in ext.columns if c.startswith("Asset")]]
    if C.FF_INTL_MONTHLY.exists():
        fi = pd.read_csv(C.FF_INTL_MONTHLY, index_col=0, parse_dates=True).sort_index()
        menus_recent["FF international 9"] = fi.loc["1999-01-01":]
    for name, stem in KF_MENUS.items():
        d = _kf_menu(stem)
        d.index = d.index.to_period("M").to_timestamp("M")
        menus_recent[name] = d.loc["1999-01-01":"2026-06-30"].dropna(axis=1, how="any")
        menus_long[name] = d.loc["1963-07-01":"2026-06-30"].dropna(axis=1, how="any")
    rows = []
    for era, menus in (("1999-2026", menus_recent), ("1963-2026", menus_long)):
        for name, rets in menus.items():
            m = simple_race(rets)
            ex = _excess(m)
            st = menu_stats(rets)
            row = dict(era=era, menu=name, oos_months=len(m), **st,
                       sharpe_1n=float(ex["1/N"].mean() / ex["1/N"].std() * np.sqrt(12)))
            for rule in ("Min-variance", "ERC", "HRP"):
                t = I.sharpe_diff_test(ex[rule], ex["1/N"])
                row[f"d_{rule}"] = t["delta"] * np.sqrt(12)
                row[f"p_{rule}"] = t["p_boot"]
            rows.append(row)
            print(f"[audit] {era} {name}: DR2 {st['dr2_1n']:.2f} max {st['dr2_max']:.2f} "
                  f"minvar d {row['d_Min-variance']:+.3f} p {row['p_Min-variance']:.3f}", flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "menus_reconciliation.csv", index=False)
    summ = {}
    for era, g in t.groupby("era"):
        for rule in ("Min-variance", "ERC", "HRP"):
            for x in ("dr2_1n", "mean_corr"):
                rho, p = spearmanr(g[x], g[f"d_{rule}"])
                summ[f"{era} | {rule} | {x}"] = dict(spearman=float(rho), p=float(p), n=len(g))
    (OUT / "menus_spearman.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


# ------------------------------------------------------------------ other single checks

def job_momentum():
    rets = opt.load_returns()
    start = C.OPTIMIZER_WF_WARMUP_MONTHS
    out = {"1/N": rets.iloc[start:].mean(axis=1)}
    for refit in (1, 3, 12):
        prev, parts = None, []
        for t in range(start, len(rets), refit):
            w = rules.momentum_weights(rets.iloc[:t])
            oos = rets.iloc[t:t + refit]
            r = pd.Series(oos.values @ w, index=oos.index)
            if prev is not None:
                r.iloc[0] -= COST * float(np.abs(w - prev).sum() / 2)
            prev = w
            parts.append(r)
        out[f"Momentum 12-1, refit {refit}m"] = pd.concat(parts)
    _save("momentum", pd.DataFrame(out))


def job_proxy():
    from portfolio_lab.portfolio import proxy_backtest as PB
    uni = PB.load_universes()["equity"]
    m = simple_race(uni)
    s = _save("proxy_equity_1936", m)
    ex = _excess(m)
    p0 = {r: I.sharpe_diff_test(m[r], m["1/N"])["p_boot"] for r in ("Min-variance", "ERC", "HRP")}
    print("rf=0 p", p0)
    print(pd.Series({r: I.sharpe_diff_test(ex[r], ex["Min-variance"])["p_boot"]
                     for r in ("ERC", "HRP", "1/N")}, name="p vs Min-variance").round(3).to_string())
    return s


def job_facts():
    r = opt.load_returns()
    ext = opt.load_returns(include_asset_classes=True)
    reg = lambda c: c.split(" | ")[0]                      # noqa: E731
    fac = lambda c: c.split(" | ")[1]                      # noqa: E731
    cm = r.corr()
    pairs = list(itertools.combinations(r.columns, 2))
    cut = {"same region, different factor": [], "same factor, different region": [],
           "reference across regions": []}
    for a, b in pairs:
        v = cm.loc[a, b]
        if reg(a) == reg(b):
            cut["same region, different factor"].append(v)
        elif fac(a) == fac(b):
            if fac(a) == "Reference":
                cut["reference across regions"].append(v)
            else:
                cut["same factor, different region"].append(v)
    facts = {k: float(np.mean(v)) for k, v in cut.items()}
    facts["mean pairwise corr"] = float(cm.values[np.triu_indices(28, 1)].mean())
    ev = np.linalg.eigvalsh(cm.values)[::-1]
    facts["PC1 share"] = float(ev[0] / ev.sum())
    cx = ext.corr()
    for a in ("Asset | US Treasury 10y", "Asset | Gold", "Asset | Cash (T-bill)"):
        facts[f"corr {a} with sleeves"] = float(cx.loc[a, r.columns].mean())
    cagr = (1 + r).prod() ** (12 / len(r)) - 1
    facts["best-worst CAGR spread"] = float(cagr.max() - cagr.min())
    for label, sub in (("full", r), ("2015+", r.loc["2015-01-01":])):
        cg = (1 + sub).prod() ** (12 / len(sub)) - 1
        for f in ("Enhanced Value", "Momentum", "Quality"):
            gaps = [cg[c] - cg[f"{reg(c)} | Reference"] for c in r.columns if fac(c) == f]
            facts[f"{f} minus Reference, {label}"] = float(np.mean(gaps))
            facts[f"{f} wins, {label}"] = f"{sum(g > 0 for g in gaps)}/{len(gaps)}"
    ev_x = {reg(c): r[c] - r[f"{reg(c)} | Reference"] for c in r.columns if fac(c) == "Enhanced Value"}
    mo_x = {reg(c): r[c] - r[f"{reg(c)} | Reference"] for c in r.columns if fac(c) == "Momentum"}
    both = sorted(set(ev_x) & set(mo_x))
    facts["value/momentum corr, excess"] = float(np.mean([ev_x[g].corr(mo_x[g]) for g in both]))
    facts["value/momentum corr, raw"] = float(np.mean(
        [r[f"{g} | Enhanced Value"].corr(r[f"{g} | Momentum"]) for g in both]))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "facts.json").write_text(json.dumps(facts, indent=1))
    print(json.dumps(facts, indent=1))


def job_worked():
    """The estimator on real numbers, full sample, for every (factor, state) cell."""
    from portfolio_lab.analytics.long_history import msci_factor_prior
    r = opt.load_returns()
    st = opt._load_states(r.index)
    prior = msci_factor_prior(r)
    rows = []
    for ftype, p in prior.items():
        pairs = [c for c in r.columns if c.split(" | ")[1] == ftype]
        exc = pd.concat([r[c] - r[f"{c.split(' | ')[0]} | Reference"] for c in pairs], axis=1).mean(axis=1)
        for state, d in p["states"].items():
            mask = (st.state == state).reindex(r.index).fillna(False)
            n = int(mask.sum())
            modern = float(exc[mask].mean())
            m = d["n_long"]
            blended = (n * modern + m * d["long_diff"]) / (n + m) if d["agree"] else modern
            rows.append(dict(factor=ftype, state=state.split(" (")[0], beta=p["beta"], n_modern=n,
                             m_long=m, gate_open=d["agree"], modern_pct=modern * 100,
                             long_mapped_pct=d["long_diff"] * 100, blended_pct=blended * 100,
                             weight_on_long=(m / (n + m)) if d["agree"] else 0.0))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "estimator_worked_example.csv", index=False)
    print(t.round(3).to_string())


def job_widen():
    """Does widening the menu improve PERFORMANCE, not just DR^2? The v1 comparison ("the menu
    effect is significant, the method effect is not") set a DR^2 gap against a Sharpe gap: two
    different quantities. Here both are Sharpe gaps, on the same months, same protocol."""
    OUT.mkdir(parents=True, exist_ok=True)
    eq = opt.load_returns()
    ext = opt.load_returns(include_asset_classes=True)
    px = [c for c in ext.columns if c.startswith("Asset")]
    nc = [c for c in px if "Cash" not in c]
    menus = {"28 sleeves": eq, "28 + T, gold, cash": ext, "28 + T, gold": ext[list(eq.columns) + nc],
             "ACWI + T, gold, cash": ext[["ACWI | Reference"] + px],
             "ACWI + T, gold": ext[["ACWI | Reference"] + nc],
             "ACWI alone": ext[["ACWI | Reference"]]}
    series = {}
    for name, rets in menus.items():
        if rets.shape[1] == 1:
            series[f"{name} | 1/N"] = rets.iloc[120:, 0]
            continue
        m = simple_race(rets)
        for rule in ("1/N", "ERC", "Min-variance"):
            series[f"{name} | {rule}"] = m[rule]
    d = pd.DataFrame(series)
    ex = _excess(d)
    base = "28 sleeves | 1/N"
    rows = []
    for c in d.columns:
        e, r = ex[c].dropna(), d[c].dropna()
        lvl = (1 + r).cumprod()
        row = dict(portfolio=c, months=len(e), sharpe=float(e.mean() / e.std() * np.sqrt(12)),
                   cagr=float(lvl.iloc[-1] ** (12 / len(r)) - 1), vol=float(r.std() * np.sqrt(12)),
                   max_dd=float((lvl / lvl.cummax() - 1).min()))
        if c != base:
            t = I.sharpe_diff_test(e, ex[base])
            row.update(d_sharpe=t["delta"] * np.sqrt(12), p_boot=t["p_boot"])
        rows.append(row)
    t = pd.DataFrame(rows).sort_values("sharpe", ascending=False)
    t.to_csv(OUT / "widen_modern.csv", index=False)
    print(t.round(3).to_string())
    # the same question over 1972-2026 on the long proxy universe (6 FF portfolios + 3 proxies)
    from portfolio_lab.portfolio import proxy_backtest as PB
    uni = PB.load_universes()
    eq6, ma = uni["equity"], uni["multi_asset"]
    ma = ma.dropna()
    px_l = [c for c in ma.columns if c.startswith("Asset")]
    series = {}
    for name, rets in {"6 FF equity": ma[list(eq6.columns)], "6 FF + T, gold, cash": ma,
                       "6 FF + T, gold": ma[list(eq6.columns) + [c for c in px_l if "Cash" not in c]]}.items():
        m = simple_race(rets)
        for rule in ("1/N", "ERC"):
            series[f"{name} | {rule}"] = m[rule]
    d = pd.DataFrame(series)
    ex = _excess(d)
    base = "6 FF equity | 1/N"
    rows = []
    for c in d.columns:
        e, r = ex[c].dropna(), d[c].dropna()
        lvl = (1 + r).cumprod()
        row = dict(portfolio=c, months=len(e), sharpe=float(e.mean() / e.std() * np.sqrt(12)),
                   vol=float(r.std() * np.sqrt(12)), max_dd=float((lvl / lvl.cummax() - 1).min()))
        if c != base:
            t = I.sharpe_diff_test(e, ex[base])
            row.update(d_sharpe=t["delta"] * np.sqrt(12), p_boot=t["p_boot"])
        rows.append(row)
    t2 = pd.DataFrame(rows).sort_values("sharpe", ascending=False)
    t2.to_csv(OUT / "widen_long.csv", index=False)
    print(t2.round(3).to_string())


def collect() -> dict:
    """Everything the audit measured, as plain numbers for numbers.json."""
    out = {}
    for name in ("dr2_menus", "menus_reconciliation", "widen_modern", "widen_long",
                 "estimator_worked_example", "estimator_ab_summary"):
        f = OUT / f"{name}.csv"
        if f.exists():
            out[name] = json.loads(pd.read_csv(f).to_json(orient="records"))
    for name in ("facts", "menus_spearman"):
        f = OUT / f"{name}.json"
        if f.exists():
            out[name] = json.loads(f.read_text())
    races = {}
    for f in sorted(OUT.glob("race_*.csv")):
        t = pd.read_csv(f)
        idx = t.set_index("portfolio")
        row = dict(top=t.portfolio.iloc[0], top_sharpe=float(t.sharpe.iloc[0]),
                   rank_minvar=(int(t.index[t.portfolio == "Min-variance"][0]) + 1
                                if "Min-variance" in idx.index else None),
                   significant=[dict(portfolio=r.portfolio, d=float(r.d_sharpe), p=float(r.p_boot))
                                for r in t.itertuples() if r.p_boot == r.p_boot and r.p_boot < 0.05])
        for c in ("1/N", "Min-variance", "Maximin (all-weather div)", "Maximin (diversified)",
                  "Maximin (worst quadrant)"):
            if c in idx.index:
                row[c] = dict(sharpe=float(idx.loc[c, "sharpe"]),
                              p=(None if pd.isna(idx.loc[c, "p_boot"]) else float(idx.loc[c, "p_boot"])))
        races[f.stem[5:]] = row
    out["races"] = races
    pl = [pd.read_csv(f) for pat in ("placebo_circular_*.csv", "placebo_iid_*.csv")
          for f in sorted(OUT.glob(pat))]
    if pl:
        d = pd.concat(pl, ignore_index=True)
        d.to_csv(OUT / "placebo_all.csv", index=False)
        metrics = [c for c in d.columns if " | " in c and not c.startswith("1/N")]
        real = d[d.arm == "real"].iloc[0]
        rows = []
        for mode, g in d[d.arm == "placebo"].groupby("mode"):
            for mt in metrics:
                x = g[mt].dropna()
                rows.append(dict(mode=mode, metric=mt, real=float(real[mt]), placebo_mean=float(x.mean()),
                                 placebo_sd=float(x.std()), B=len(x),
                                 p_perm=float((1 + (x >= real[mt]).sum()) / (len(x) + 1))))
        t = pd.DataFrame(rows)
        t.to_csv(OUT / "placebo_summary.csv", index=False)
        out["placebo"] = json.loads(t.to_json(orient="records"))
    return out


# ------------------------------------------------------------------ full walk-forwards

def run_job(job: str):
    if job in ("facts", "dr2", "menus", "momentum", "proxy", "worked", "widen"):
        return globals()[f"job_{job}"]()
    if job.startswith("placebo:"):                     # placebo:<mode>:<b>:<seed> (parallel chunks)
        from portfolio_lab.portfolio import placebo as PL
        mode, b, seed = job.split(":")[1:]
        OUT.mkdir(parents=True, exist_ok=True)
        C.OPTIMIZER_PLACEBO = OUT / f"placebo_{mode}_{seed}.csv"
        C.OPTIMIZER_PLACEBO_REPORT = OUT / f"placebo_{mode}_{seed}.md"
        return PL.run(b=int(b), modes=(mode,), seed=int(seed))
    if job.startswith("estimator:"):                   # estimator:<b>:<seed>
        from portfolio_lab.portfolio import placebo as PL
        b, seed = job.split(":")[1:]
        OUT.mkdir(parents=True, exist_ok=True)
        C.OPTIMIZER_ESTIMATOR_AB = OUT / f"estimator_ab_{seed}.csv"
        C.OPTIMIZER_ESTIMATOR_AB_REPORT = OUT / f"estimator_ab_{seed}.md"
        return PL.estimator_ab(b=int(b), mode="circular", seed=int(seed))
    if job.startswith("loro:"):
        reg = job.split(":")[1]
        _, _, m = validation.walk_forward(drop_region=reg)
        return _save(f"loro_{reg}", m)
    if job == "lag2":
        C.OPTIMIZER_STATE_LAG_MONTHS = 2
        _, _, m = validation.walk_forward()
        return _save("lag2", m)
    if job.startswith("refit"):
        _, _, m = validation.walk_forward(refit=int(job[5:]))
        return _save(job, m)
    if job.startswith("cov:"):
        C.OPTIMIZER_SIGMA_ESTIMATOR = job.split(":")[1]
        _, _, m = validation.walk_forward()
        return _save(f"cov_{job.split(':')[1]}", m)
    if job.startswith("caps:"):
        s_, g_ = job.split(":")[1].split("_")
        C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT = float(s_)
        C.OPTIMIZER_GEO_CAP_PCT = C.OPTIMIZER_FACTOR_CAP_PCT = float(g_)
        _, _, m = validation.walk_forward()
        return _save(f"caps_{s_}_{g_}", m)
    if job == "disjoint":
        r = opt.load_returns()
        _, _, m = validation.walk_forward(
            rets=r[[c for c in r.columns if c.split(" | ")[0] in DISJOINT]])
        return _save("disjoint", m)
    if job == "ff_intl":
        from portfolio_lab.portfolio.ff_intl_test import load_universe
        _, _, m = validation.walk_forward(rets=load_universe())
        return _save("ff_intl", m)
    raise ValueError(job)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    run_job(ap.parse_args().job)
