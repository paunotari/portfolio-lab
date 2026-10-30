"""Risk-adjusted performance beyond the Sharpe ratio (v2.0, the collaborator's review).

The concern: the contestants with the best Sharpe ratios are the ones furthest left on the
risk-return plane, so the Sharpe ranking may be rewarding low volatility rather than skill.
Three other lenses, each asking a different question of the same out-of-sample returns:

- **Sortino** — excess return per unit of DOWNSIDE deviation (months below the T-bill only).
  Asks whether the volatility a strategy avoided was the harmful kind.
- **Treynor** — excess return per unit of global MARKET beta. Asks how much a strategy earns
  for the market risk it carries — the relevant risk if it sits inside a larger portfolio.
- **Information ratio** — mean ACTIVE return over 1/N per unit of tracking error (the
  volatility of that active return). Asks how steadily a strategy beats the benchmark rather
  than whether it beats it on average; 1/N is the benchmark throughout (Grinold-Kahn).
- **Appraisal ratio** (Treynor-Black 1973) — alpha per unit of RESIDUAL risk, the information
  ratio of the part of the return the factors do not explain.
- **Alpha** — the intercept of a time-series regression of excess returns on factor returns:
  CAPM (the minimum), Carhart's four factors (market, size, value, momentum) and robustness
  variants. Asks whether anything is left once the strategy's factor exposures are paid for.

Every comparison against 1/N carries a p-value, as in v1:
- Sharpe: the Ledoit-Wolf (2008) studentized circular block bootstrap of v1, on excess returns.
- Sortino, Treynor: a paired circular block bootstrap of the difference (same block length,
  same B, same seed), p = share of centered replicates at least as extreme as the observed gap.
- Alpha vs 1/N: OLS of the RETURN DIFFERENCE (strategy minus 1/N) on the factors, Newey-West
  HAC t-statistic. By linearity of OLS its intercept is exactly alpha(strategy) - alpha(1/N).

Factors are Ken French's global ("Developed") set plus the emerging-markets set
(``v2/factors.py``), matched to the OOS months by month PERIOD. Excess returns use Ken French's
one-month T-bill. All annualizations: mean x 12, volatility x sqrt(12).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from portfolio_lab import config as C
from portfolio_lab.portfolio import inference as I
from portfolio_lab.v2 import factors as F

BENCH = "1/N"

# model name -> regressors (columns of the aligned factor frame; "acwi_mkt_rf" is added below)
MODELS = {
    "CAPM": ["dev_mkt_rf"],
    "CAPM (ACWI)": ["acwi_mkt_rf"],
    "Carhart 4F": ["dev_mkt_rf", "dev_smb", "dev_hml", "dev_wml"],
    "4F + EM market": ["dev_mkt_rf", "dev_smb", "dev_hml", "dev_wml", "em_mkt_rf"],
    "FF5 + WML": ["dev_mkt_rf", "dev_smb", "dev_hml", "dev_rmw", "dev_cma", "dev_wml"],
    "FF5 + WML + EM": ["dev_mkt_rf", "dev_smb", "dev_hml", "dev_rmw", "dev_cma", "dev_wml",
                       "em_mkt_rf"],
    # ---- round 2 (after the adversarial review; P is pre-registered, MILESTONES PR-2)
    "FF5 + WML + EM + BAB": ["dev_mkt_rf", "dev_smb", "dev_hml", "dev_rmw", "dev_cma",
                             "dev_wml", "em_mkt_rf", "aqr_bab"],
    "Regional 5": [f"reg_{r}" for r in C.V2_PRIMARY_REGIONS],
    "Regional 5 + FF5 styles + WML": [f"reg_{r}" for r in C.V2_PRIMARY_REGIONS]
                                     + ["dev_smb", "dev_hml", "dev_rmw", "dev_cma", "dev_wml"],
    C.V2_PRIMARY_MODEL: [f"reg_{r}" for r in C.V2_PRIMARY_REGIONS] + list(C.V2_PRIMARY_STYLES),
    "P with QMJ for RMW+CMA": [f"reg_{r}" for r in C.V2_PRIMARY_REGIONS]
                              + ["dev_smb", "dev_hml", "dev_wml", "aqr_bab", "aqr_qmj"],
}
PRIMARY_MODELS = ("CAPM", "Carhart 4F")


# ------------------------------------------------------------------ inputs

def factor_frame(monthly: pd.DataFrame) -> pd.DataFrame:
    """Global factors on `monthly`'s months, plus the all-country market built from the MSCI
    ACWI Reference sleeve (developed + emerging, the menu's own widest market) minus rf."""
    fac = F.align(monthly)
    if C.FF_FACTORS_MONTHLY.exists():       # ONE risk-free source: the series overlay cash earns
        us = pd.read_csv(C.FF_FACTORS_MONTHLY, index_col=0, parse_dates=True)
        fac["rf"] = F.align(monthly, factors=us[["rf"]])["rf"].fillna(fac["rf"])
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    acwi = lv["ACWI | Reference"].pct_change()
    acwi.index = acwi.index.to_period("M")
    acwi = acwi.reindex(monthly.index.to_period("M"))
    fac["acwi_mkt_rf"] = acwi.to_numpy() - fac["rf"].to_numpy()
    # the menu's own regional markets (Reference sleeves of the disjoint regions), excess of rf
    for reg in C.V2_PRIMARY_REGIONS:
        r = lv[f"{reg} | Reference"].pct_change()
        r.index = r.index.to_period("M")
        fac[f"reg_{reg}"] = r.reindex(monthly.index.to_period("M")).to_numpy() - fac["rf"].to_numpy()
    return fac


def available_models(fac: pd.DataFrame) -> list[str]:
    """Models whose regressors are all present (AQR columns are optional)."""
    return [m for m, cols in MODELS.items() if all(c in fac.columns for c in cols)]


def excess_returns(monthly: pd.DataFrame, fac: pd.DataFrame = None) -> pd.DataFrame:
    fac = factor_frame(monthly) if fac is None else fac
    return monthly.sub(fac["rf"], axis=0)


# ------------------------------------------------------------------ ratios

def downside_deviation(e: np.ndarray) -> float:
    """Root mean square of the below-target months (target = 0 excess, i.e. the T-bill)."""
    return float(np.sqrt(np.mean(np.minimum(e, 0.0) ** 2)))


def capm_beta(e: np.ndarray, m: np.ndarray) -> float:
    mc = m - m.mean()
    return float(((e - e.mean()) * mc).sum() / (mc ** 2).sum())


def sharpe(e: np.ndarray) -> float:
    return float(e.mean() / e.std(ddof=1) * np.sqrt(12))


def sortino(e: np.ndarray) -> float:
    dd = downside_deviation(e)
    return float(e.mean() * 12 / (dd * np.sqrt(12))) if dd > 0 else np.nan


def cer(e: np.ndarray, gamma: float) -> float:
    """Certainty-equivalent excess return (annualized) of a mean-variance investor with risk
    aversion gamma: mean - gamma/2 * variance (DeMiguel et al. 2009's second metric)."""
    return float((e.mean() - gamma / 2.0 * e.var(ddof=1)) * 12)


def treynor(e: np.ndarray, m: np.ndarray) -> float:
    """Annualized excess return per unit of market beta (in return units: 0.10 = 10%)."""
    b = capm_beta(e, m)
    return float(e.mean() * 12 / b) if b > 0 else np.nan


# ------------------------------------------------------------------ HAC regression

def nw_lags(T: int) -> int:
    """Newey-West (1994) rule of thumb, the same bandwidth rule inference.py uses."""
    return max(1, int(4 * (T / 100.0) ** (2.0 / 9.0)))


def hac_ols(y: np.ndarray, X: np.ndarray, lags: int = None) -> dict:
    """OLS with an intercept and Newey-West (Bartlett) HAC standard errors.
    Returns coefficients (intercept first), HAC s.e., t, two-sided normal p, R^2."""
    T = len(y)
    Z = np.column_stack([np.ones(T), X])
    ZtZ_inv = np.linalg.inv(Z.T @ Z)
    b = ZtZ_inv @ Z.T @ y
    u = y - Z @ b
    L = nw_lags(T) if lags is None else lags
    g = Z * u[:, None]
    S = g.T @ g
    for j in range(1, L + 1):
        w = 1 - j / (L + 1)
        G = g[j:].T @ g[:-j]
        S += w * (G + G.T)
    V = ZtZ_inv @ S @ ZtZ_inv
    se = np.sqrt(np.diag(V))
    t = b / se
    r2 = 1 - (u ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return dict(coef=b, se=se, t=t, p=2 * norm.sf(np.abs(t)), r2=float(r2), lags=L, T=T)


def alpha(y: pd.Series, fac: pd.DataFrame, model: str) -> dict:
    cols = MODELS[model]
    d = pd.concat([y.rename("y"), fac[cols]], axis=1).dropna()
    r = hac_ols(d["y"].to_numpy(float), d[cols].to_numpy(float))
    out = dict(model=model, T=r["T"], alpha_ann=float(r["coef"][0] * 12),
               t_alpha=float(r["t"][0]), p_alpha=float(r["p"][0]), r2=r["r2"])
    for k, c in enumerate(cols, start=1):
        out[f"b_{c}"] = float(r["coef"][k])
        out[f"t_{c}"] = float(r["t"][k])
    return out


# ------------------------------------------------------------------ paired bootstrap

def _block_indices(T: int, B: int, b: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    L = int(np.ceil(T / b))
    starts = rng.integers(0, T, size=(B, L))
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]) % T
    return idx.reshape(B, L * b)[:, :T]


def ratio_diff_test(x: np.ndarray, y: np.ndarray, m: np.ndarray, stat: str,
                    B: int = None, block: int = None, seed: int = None) -> dict:
    """Paired circular block bootstrap for stat(x) - stat(y), stat in {sortino, treynor}.
    x, y: excess returns of the two strategies; m: market excess (Treynor's beta)."""
    B = B or C.OPTIMIZER_INFER_B
    T = len(x)
    b = block or C.OPTIMIZER_INFER_BLOCK or max(3, round(T ** (1 / 3)))
    seed = C.OPTIMIZER_SEED if seed is None else seed
    if stat.startswith("cer"):
        g = float(stat[3:])
        f = lambda e, mm: cer(e, g)                                   # noqa: E731
    else:
        f = {"sortino": lambda e, mm: sortino(e), "treynor": treynor}[stat]
    obs = f(x, m) - f(y, m)
    draws = []
    for i in _block_indices(T, B, b, seed):
        d = f(x[i], m[i]) - f(y[i], m[i])
        if np.isfinite(d):
            draws.append(d)
    d = np.array(draws)
    p = (1 + np.sum(np.abs(d - d.mean()) >= abs(obs))) / (len(d) + 1)
    return dict(delta=float(obs), p_boot=float(p), ci_lo=float(np.percentile(d, 2.5)),
                ci_hi=float(np.percentile(d, 97.5)), block=b, B=len(d))


def alpha_block_bootstrap(y: pd.Series, fac: pd.DataFrame, model: str, B: int = None,
                          block: int = None, seed: int = None) -> dict:
    """Pairs circular block bootstrap of the regression intercept — the robustness check on
    the HAC t: whole months (return + factors) are resampled in blocks, the OLS refitted, and
    p = share of centered replicate alphas at least as far from their mean as the estimate."""
    cols = MODELS[model]
    d = pd.concat([y.rename("y"), fac[cols]], axis=1).dropna()
    Y, X = d["y"].to_numpy(float), d[cols].to_numpy(float)
    T = len(Y)
    B = B or C.OPTIMIZER_INFER_B
    b = block or C.OPTIMIZER_INFER_BLOCK or max(3, round(T ** (1 / 3)))
    Z = np.column_stack([np.ones(T), X])
    a0 = float(np.linalg.lstsq(Z, Y, rcond=None)[0][0])
    draws = np.array([np.linalg.lstsq(Z[i], Y[i], rcond=None)[0][0]
                      for i in _block_indices(T, B, b, C.OPTIMIZER_SEED if seed is None else seed)])
    p = (1 + np.sum(np.abs(draws - draws.mean()) >= abs(a0))) / (len(draws) + 1)
    return dict(model=model, alpha_ann=a0 * 12, p_boot=float(p), block=b, B=len(draws))


def rolling_ahead_share(x: pd.Series, b: pd.Series, months: int) -> float:
    """Share of rolling windows of `months` in which strategy x's cumulative return beats
    benchmark b's. Overlapping windows are not independent observations — descriptive only."""
    d = pd.concat([x, b], axis=1).dropna()
    if len(d) < months:
        return np.nan
    cx = np.log1p(d.iloc[:, 0]).rolling(months).sum()
    cb = np.log1p(d.iloc[:, 1]).rolling(months).sum()
    return float((cx - cb).dropna().gt(0).mean())


def information_table(monthly: pd.DataFrame, bench: str = BENCH,
                      windows=(36, 60, 120)) -> pd.DataFrame:
    """Active-risk view, one row per contestant against `bench`:
    active return and tracking error (annualized), information ratio with a Newey-West t on
    the mean active return, appraisal ratios (own alpha / residual vol, CAPM and Carhart, and
    the alpha over 1/N / residual vol of the difference regression under '4F + EM market'),
    and the share of rolling 3/5/10-year windows the strategy finished ahead of 1/N."""
    fac = factor_frame(monthly)
    ex = excess_returns(monthly, fac)
    rows = []
    for name in monthly.columns:
        row = dict(portfolio=name)
        for model in ("CAPM", "Carhart 4F"):
            d = pd.concat([ex[name].rename("y"), fac[MODELS[model]]], axis=1).dropna()
            r = hac_ols(d["y"].to_numpy(float), d[MODELS[model]].to_numpy(float))
            Z = np.column_stack([np.ones(len(d)), d[MODELS[model]].to_numpy(float)])
            resid = d["y"].to_numpy(float) - Z @ r["coef"]
            row[f"appraisal_{model}"] = float(r["coef"][0] * 12 / (resid.std(ddof=Z.shape[1]) * np.sqrt(12)))
        if name != bench:
            act = (monthly[name] - monthly[bench]).dropna()
            a = act.to_numpy(float)
            t = hac_ols(a, np.empty((len(a), 0)))
            row.update(active_ann=float(a.mean() * 12), te_ann=float(a.std(ddof=1) * np.sqrt(12)),
                       ir=float(a.mean() / a.std(ddof=1) * np.sqrt(12)),
                       t_ir=float(t["t"][0]), p_ir=float(t["p"][0]))
            m = "4F + EM market"
            d = pd.concat([act.rename("y"), fac[MODELS[m]]], axis=1).dropna()
            r = hac_ols(d["y"].to_numpy(float), d[MODELS[m]].to_numpy(float))
            Z = np.column_stack([np.ones(len(d)), d[MODELS[m]].to_numpy(float)])
            resid = d["y"].to_numpy(float) - Z @ r["coef"]
            row["appraisal_vs_1N_4FEM"] = float(r["coef"][0] * 12 / (resid.std(ddof=Z.shape[1]) * np.sqrt(12)))
            for w in windows:
                row[f"ahead_{w}m"] = rolling_ahead_share(monthly[name], monthly[bench], w)
        rows.append(row)
    return pd.DataFrame(rows)


def _intercept_t_matrix(Y: np.ndarray, Z: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized OLS intercepts and Newey-West t-statistics for many dependent variables
    sharing one regressor matrix Z (T x k, first column ones). Identical to hac_ols's
    intercept: with a = (Z'Z)^-1 e0, the intercept's influence is psi_t = (Z_t a) u_t."""
    ZtZ_inv = np.linalg.inv(Z.T @ Z)
    Bc = ZtZ_inv @ Z.T @ Y
    U = Y - Z @ Bc
    h = Z @ ZtZ_inv[:, 0]
    P = h[:, None] * U
    var = (P ** 2).sum(axis=0)
    for j in range(1, lags + 1):
        var += 2 * (1 - j / (lags + 1)) * (P[j:] * P[:-j]).sum(axis=0)
    return Bc[0], np.sqrt(var)


def romano_wolf(monthly: pd.DataFrame, models: list[str], bench: str = BENCH,
                B: int = None, block: int = None, seed: int = None) -> pd.DataFrame:
    """Romano-Wolf step-down family-wise p-values for alpha-over-1/N across every
    (contestant, model) cell in `models` — the studentized max-|t| circular block bootstrap:
    months (returns + factors) are resampled in blocks, every cell's t is recentred on its
    full-sample alpha, and cell k's adjusted p is the share of replicates whose max |t*| over
    the cells not yet rejected reaches |t_k| (monotonized)."""
    B = B or C.V2_RW_B
    b = block or C.V2_RW_BLOCK
    seed = C.OPTIMIZER_SEED if seed is None else seed
    fac = factor_frame(monthly)
    names = [c for c in monthly.columns if c != bench]
    D = monthly[names].sub(monthly[bench], axis=0)
    regs = sorted({c for m in models for c in MODELS[m]})
    d = pd.concat([D, fac[regs]], axis=1).dropna()           # ONE common calendar for all models
    T = len(d)
    Y = d[names].to_numpy(float)
    cells, alphas, ses, Zs = [], [], [], []
    for m in models:
        Z = np.column_stack([np.ones(T), d[MODELS[m]].to_numpy(float)])
        a, se = _intercept_t_matrix(Y, Z, nw_lags(T))
        cells += [(n, m) for n in names]
        alphas.append(a); ses.append(se); Zs.append(Z)
    Ys = [Y] * len(models)
    a_obs = np.concatenate(alphas)
    se_obs = np.concatenate(ses)
    t_obs = a_obs / se_obs
    idx = _block_indices(T, B, b, seed)
    tstar = np.empty((B, len(cells)))
    for i, ix in enumerate(idx):
        parts = []
        for Y, Z, a0 in zip(Ys, Zs, alphas):
            a_b, se_b = _intercept_t_matrix(Y[ix], Z[ix], nw_lags(T))
            parts.append((a_b - a0) / se_b)
        tstar[i] = np.abs(np.concatenate(parts))
    order = np.argsort(-np.abs(t_obs))
    p_adj = np.empty(len(cells))
    prev = 0.0
    for k, c in enumerate(order):
        remaining = order[k:]
        mx = np.nanmax(tstar[:, remaining], axis=1)
        p = (1 + np.sum(mx >= abs(t_obs[c]))) / (B + 1)
        prev = max(prev, p)
        p_adj[c] = prev
    # single-cell studentized bootstrap p (round-2 R4: HAC-normal p is ~2x anti-conservative
    # with 11 regressors and T = 210) and percentile-t 95% intervals for each alpha
    p_single = (1 + (tstar >= np.abs(t_obs)[None, :]).sum(axis=0)) / (B + 1)
    signed = []
    for i, ix in enumerate(idx[:min(B, 1999)]):
        parts = []
        for Y_, Z, a0 in zip(Ys, Zs, alphas):
            a_b, se_b = _intercept_t_matrix(Y_[ix], Z[ix], nw_lags(T))
            parts.append((a_b - a0) / se_b)
        signed.append(np.concatenate(parts))
    signed = np.array(signed)
    q_lo, q_hi = np.nanpercentile(signed, [2.5, 97.5], axis=0)
    # minimum detectable alpha at 80% power from the bootstrap t* (round 3: 2.8 x HAC s.e. was
    # ~10% optimistic, the t* having s.d. ~1.1): critical |t*| at 5% + 0.8416 s.d. of t*
    crit = np.nanpercentile(np.abs(signed), 95, axis=0)
    mde_boot = (crit + 0.8416 * np.nanstd(signed, axis=0)) * se_obs * 12
    return pd.DataFrame({"portfolio": [c[0] for c in cells], "model": [c[1] for c in cells],
                         "T": T, "alpha_vs_1N_ann": a_obs * 12, "t": t_obs,
                         "p_hac": 2 * norm.sf(np.abs(t_obs)), "p_boot": p_single, "p_rw": p_adj,
                         "ci_lo_ann": (a_obs - q_hi * se_obs) * 12,
                         "ci_hi_ann": (a_obs - q_lo * se_obs) * 12,
                         "mde80_ann": 2.80 * se_obs * 12, "mde80_boot_ann": mde_boot})


def sharpe_romano_wolf(monthly: pd.DataFrame, bench: str = BENCH, B: int = None,
                       block: int = None, seed: int = None) -> pd.DataFrame:
    """Sharpe differences against 1/N with family-wise control across all contestants, plus the
    one-sided p (does the rule BEAT 1/N?). A referee can fairly say a test of "beats" should be
    one-sided; the honest reply is that a one-sided test must also pay for having fielded
    sixteen rules. Studentized circular block bootstrap, same machinery as inference.py;
    the same resampled months drive every contestant, so their dependence is preserved."""
    B = B or C.V2_RW_B
    ex = excess_returns(monthly)
    names = [c for c in monthly.columns if c != bench]
    d = ex[names + [bench]].dropna()
    T = len(d)
    b = block or C.OPTIMIZER_INFER_BLOCK or max(3, round(T ** (1 / 3)))
    idx = _block_indices(T, B, b, C.OPTIMIZER_SEED if seed is None else seed)
    y = d[bench].to_numpy(float)
    obs, tstar = [], np.full((B, len(names)), np.nan)
    for j, n in enumerate(names):
        x = d[n].to_numpy(float)
        _, delta = I._grad_and_delta(x, y)
        se = I._hac_se(x, y)
        obs.append((delta, se))
        for s, ix in enumerate(idx):
            xs, ys = x[ix], y[ix]
            grad, delta_s = I._grad_and_delta(xs, ys)
            V = I._influence(xs, ys)
            nb = T // b
            z = V[:nb * b].reshape(nb, b, 4).sum(axis=1) / np.sqrt(b)
            var = float(grad @ (z.T @ z / nb) @ grad) / T
            if var > 0:
                tstar[s, j] = (delta_s - delta) / np.sqrt(var)
    delta = np.array([o[0] for o in obs])
    se = np.array([o[1] for o in obs])
    t = delta / se
    order = np.argsort(-np.abs(t))
    p_rw = np.empty(len(names))
    prev = 0.0
    abst = np.abs(tstar)
    for k, c in enumerate(order):
        mx = np.nanmax(abst[:, order[k:]], axis=1)
        prev = max(prev, (1 + np.sum(mx >= abs(t[c]))) / (B + 1))
        p_rw[c] = prev
    return pd.DataFrame({"portfolio": names, "T": T, "d_sharpe_ann": delta * np.sqrt(12),
                         "se_ann": se * np.sqrt(12), "t": t,
                         "p_two_sided": (1 + (abst >= np.abs(t)).sum(axis=0)) / (B + 1),
                         "p_one_sided": (1 + (tstar >= t).sum(axis=0)) / (B + 1),
                         "p_rw": p_rw}).sort_values("p_rw").reset_index(drop=True)


def alpha_decomposition(monthly: pd.DataFrame, model: str, name: str = "Min-variance",
                        bench: str = BENCH) -> pd.DataFrame:
    """Raw mean gap to 1/N = alpha + sum_k b_k * mean(F_k): where the gap comes from, factor
    by factor (round-2 R2). Annualized; rows sum to the raw gap."""
    fac = factor_frame(monthly)
    cols = MODELS[model]
    d = pd.concat([(monthly[name] - monthly[bench]).rename("y"), fac[cols]], axis=1).dropna()
    r = hac_ols(d["y"].to_numpy(float), d[cols].to_numpy(float))
    rows = [dict(component="alpha", loading=np.nan, factor_mean_ann=np.nan,
                 contribution_ann=float(r["coef"][0] * 12), t=float(r["t"][0]))]
    for k, c in enumerate(cols, start=1):
        rows.append(dict(component=c, loading=float(r["coef"][k]),
                         factor_mean_ann=float(d[c].mean() * 12),
                         contribution_ann=float(r["coef"][k] * d[c].mean() * 12),
                         t=float(r["t"][k])))
    rows.append(dict(component="raw gap", loading=np.nan, factor_mean_ann=np.nan,
                     contribution_ann=float(d["y"].mean() * 12), t=np.nan))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ the tables

def ratio_table(monthly: pd.DataFrame, bench: str = BENCH) -> pd.DataFrame:
    """One row per contestant: excess-return Sharpe, Sortino, Treynor, beta, each against 1/N
    with a p-value. Months where any input is missing are dropped per contestant."""
    fac = factor_frame(monthly)
    ex = excess_returns(monthly, fac)
    rows = []
    for name in monthly.columns:
        d = pd.concat([ex[name], ex[bench], fac["dev_mkt_rf"]], axis=1).dropna()
        x, y, m = (d.iloc[:, k].to_numpy(float) for k in range(3))
        row = dict(portfolio=name, T=len(d), mean_excess_ann=float(x.mean() * 12),
                   vol_ann=float(x.std(ddof=1) * np.sqrt(12)),
                   downside_dev_ann=float(downside_deviation(x) * np.sqrt(12)),
                   beta=capm_beta(x, m), sharpe=sharpe(x), sortino=sortino(x),
                   treynor=treynor(x, m))
        if name != bench:
            s = I.sharpe_diff_test(x, y)
            row.update(d_sharpe=float(s["delta"] * np.sqrt(12)), p_sharpe=s["p_boot"])
            for stat in ("sortino", "treynor"):
                t = ratio_diff_test(x, y, m, stat)
                row.update({f"d_{stat}": t["delta"], f"p_{stat}": t["p_boot"]})
        rows.append(row)
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False).reset_index(drop=True)


def alpha_table(monthly: pd.DataFrame, bench: str = BENCH, models=None) -> pd.DataFrame:
    """Long table: contestant x model -> alpha (own) and alpha relative to 1/N, HAC t and p."""
    fac = factor_frame(monthly)
    ex = excess_returns(monthly, fac)
    rows = []
    for model in models or available_models(fac):
        for name in monthly.columns:
            own = alpha(ex[name], fac, model)
            row = dict(portfolio=name, **own)
            if name != bench:
                rel = alpha(monthly[name] - monthly[bench], fac, model)
                row.update(alpha_vs_1N_ann=rel["alpha_ann"], t_vs_1N=rel["t_alpha"],
                           p_vs_1N=rel["p_alpha"])
            rows.append(row)
    return pd.DataFrame(rows)


def power_vs_bench(monthly: pd.DataFrame, name: str = "Min-variance",
                   bench: str = BENCH) -> dict:
    """v1's power/MDES calculation, redone on excess returns."""
    ex = excess_returns(monthly)
    d = pd.concat([ex[name], ex[bench]], axis=1).dropna()
    return I.sharpe_power(d.iloc[:, 0], d.iloc[:, 1])
