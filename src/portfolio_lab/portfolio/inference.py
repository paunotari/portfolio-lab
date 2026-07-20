"""Sharpe-ratio inference — are the walk-forward's Sharpe differences real?

Implements the paper-track gate (info/TODO.md "Paper track", item 1) per the deep dive
info/literature/classics/sharpe-inference.md:

- ``sharpe_diff_test``: Ledoit & Wolf (2008) robust test for the difference of two Sharpe
  ratios — delta-method HAC (Parzen kernel) z-test + the primary STUDENTIZED CIRCULAR BLOCK
  BOOTSTRAP p-value (heavy-tail/autocorrelation honest).
- ``deflated_sharpe``: Bailey & López de Prado (2014) — P(true Sharpe > 0) after adjusting
  for non-normality AND for having fielded N contestants and looked at the best.
- ``inference_table``: both applied to the walk-forward net OOS returns, every contestant
  vs 1/N (the DeMiguel bar) and vs Min-variance (the incumbent winner).

Point estimates rank; p-values decide what a ranking claim is worth. Failing to reject is
not "equal" — with ~210 OOS months power is modest, so the CI is reported alongside.

Run:  python -m portfolio_lab.portfolio.inference     (needs the cached walk-forward CSV)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from portfolio_lab import config as C

EULER = 0.5772156649015329


# ------------------------------------------------------------------ Ledoit-Wolf (2008)

def _grad_and_delta(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    """Delta-method gradient of SR1-SR2 in the moment vector (mu1, mu2, gamma1, gamma2)."""
    mu1, mu2 = x.mean(), y.mean()
    g1, g2 = (x ** 2).mean(), (y ** 2).mean()
    s1c, s2c = (g1 - mu1 ** 2) ** 1.5, (g2 - mu2 ** 2) ** 1.5   # sigma cubed
    grad = np.array([g1 / s1c, -g2 / s2c, -mu1 / (2 * s1c), mu2 / (2 * s2c)])
    delta = mu1 / np.sqrt(g1 - mu1 ** 2) - mu2 / np.sqrt(g2 - mu2 ** 2)
    return grad, float(delta)


def _influence(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """T x 4 centered influence series V_t for (mu1, mu2, gamma1, gamma2)."""
    return np.column_stack([x - x.mean(), y - y.mean(),
                            x ** 2 - (x ** 2).mean(), y ** 2 - (y ** 2).mean()])


def _parzen(z: np.ndarray) -> np.ndarray:
    w = np.where(z <= 0.5, 1 - 6 * z ** 2 + 6 * z ** 3, 2 * (1 - z) ** 3)
    return np.where(z <= 1.0, w, 0.0)


def _hac_se(x: np.ndarray, y: np.ndarray) -> float:
    """HAC (Parzen kernel, Newey-West bandwidth) standard error of the Sharpe difference."""
    T = len(x)
    V = _influence(x, y)
    grad, _ = _grad_and_delta(x, y)
    m = max(1, int(4 * (T / 100.0) ** (2.0 / 9.0)))
    psi = V.T @ V / T
    for j in range(1, m + 1):
        gj = V[j:].T @ V[:-j] / T
        psi += _parzen(np.array([j / m]))[0] * (gj + gj.T)
    var = float(grad @ psi @ grad) / T
    return np.sqrt(var) if var > 0 else np.nan


def sharpe_diff_test(x, y, block: int = None, B: int = None, seed: int = None) -> dict:
    """Ledoit-Wolf (2008) test of H0: Sharpe(x) = Sharpe(y) on paired series.

    Returns per-MONTH sharpes and delta (annualize with sqrt(12) for display only — d and the
    p-values are scale-invariant), the HAC z-test p, and the primary studentized circular
    block bootstrap p. NaNs out (with a reason) on degenerate inputs."""
    both = pd.concat([pd.Series(x), pd.Series(y)], axis=1, join="inner").dropna()
    xa, ya = both.iloc[:, 0].to_numpy(float), both.iloc[:, 1].to_numpy(float)
    T = len(xa)
    B = B or C.OPTIMIZER_INFER_B
    b = block or C.OPTIMIZER_INFER_BLOCK or max(3, round(T ** (1 / 3)))
    seed = C.OPTIMIZER_SEED if seed is None else seed
    out = dict(T=T, block=b, B=B,
               sharpe_x=float(xa.mean() / xa.std()), sharpe_y=float(ya.mean() / ya.std()))
    if T < 24 or xa.std() == 0 or ya.std() == 0:
        return {**out, "delta": np.nan, "se": np.nan, "p_hac": np.nan, "p_boot": np.nan,
                "note": "degenerate (short window or zero vol)"}
    grad, delta = _grad_and_delta(xa, ya)
    se = _hac_se(xa, ya)
    if not np.isfinite(se) or se == 0:
        return {**out, "delta": delta, "se": np.nan, "p_hac": np.nan, "p_boot": np.nan,
                "note": "degenerate s.e. (near-identical series)"}
    d = delta / se
    out.update(delta=delta, se=se, d=float(d), p_hac=float(2 * norm.cdf(-abs(d))))

    rng = np.random.default_rng(seed)
    L = int(np.ceil(T / b))
    starts = rng.integers(0, T, size=(B, L))                      # circular block starts
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]) % T  # B x L x b
    idx = idx.reshape(B, L * b)[:, :T]
    n_extreme = 0
    used = 0
    for s in range(B):
        xs, ys = xa[idx[s]], ya[idx[s]]
        if xs.std() == 0 or ys.std() == 0:
            continue
        grad_s, delta_s = _grad_and_delta(xs, ys)
        # bootstrap-world s.e.: block sums of the sample's own centered influence series
        Vs = _influence(xs, ys)
        nb = len(xs) // b
        z = Vs[:nb * b].reshape(nb, b, 4).sum(axis=1) / np.sqrt(b)
        psi_s = z.T @ z / nb
        var_s = float(grad_s @ psi_s @ grad_s) / len(xs)
        if var_s <= 0:
            continue
        d_s = (delta_s - delta) / np.sqrt(var_s)
        used += 1
        if abs(d_s) >= abs(d):
            n_extreme += 1
    out["p_boot"] = float((n_extreme + 1) / (used + 1)) if used else np.nan
    return out


# ------------------------------------------------- deflated Sharpe (Bailey-LdP 2014)

def psr(x: np.ndarray, sr0: float) -> float:
    """Probabilistic Sharpe Ratio: P(true SR > sr0), skew/kurtosis-adjusted (monthly units)."""
    x = np.asarray(x, float)
    T = len(x)
    sr = x.mean() / x.std()
    z = (x - x.mean()) / x.std()
    g3, g4 = float((z ** 3).mean()), float((z ** 4).mean())
    denom = 1 - g3 * sr + (g4 - 1) / 4 * sr ** 2
    if denom <= 0 or T < 3:
        return np.nan
    return float(norm.cdf((sr - sr0) * np.sqrt(T - 1) / np.sqrt(denom)))


def deflated_sharpe(x, sharpes_across_trials) -> dict:
    """DSR = PSR against the expected max Sharpe of N zero-skill trials (monthly units).

    sharpes_across_trials: the N contestants' monthly Sharpe estimates (we fielded them all
    and looked at the best — the honest multiplicity count)."""
    srs = np.asarray(list(sharpes_across_trials), float)
    N = len(srs)
    x = pd.Series(x).dropna().to_numpy(float)
    if N < 2 or x.std() == 0:
        return dict(sr0_star=np.nan, dsr=np.nan)
    sr0 = np.sqrt(srs.var(ddof=1)) * ((1 - EULER) * norm.ppf(1 - 1 / N)
                                      + EULER * norm.ppf(1 - 1 / (N * np.e)))
    return dict(sr0_star=float(sr0), dsr=psr(x, sr0))


# --------------------------------------------- PBO (Bailey-Borwein-LdP-Zhu 2017, CSCV)

def pbo_cscv(monthly: pd.DataFrame, S: int = None) -> dict:
    """Probability of Backtest Overfitting via combinatorially symmetric cross-validation.

    Rows with any NaN are dropped (all trials aligned). The T×N return matrix is split into
    S contiguous blocks; for each of C(S, S/2) block-combinations used as 'in-sample', the
    IS-best trial's OUT-of-sample relative rank ω is computed. PBO = P(ω ≤ median), i.e. the
    probability that the trial you would have selected is no better than the median trial
    out of sample. Selection-skill exists when PBO is low; PBO ≈ 0.5 means picking the
    IS winner is a coin flip."""
    from itertools import combinations
    S = S or C.OPTIMIZER_PBO_S
    M = monthly.dropna().to_numpy(float)
    T, N = M.shape
    if T < 2 * S or N < 2:
        return dict(pbo=np.nan, S=S, n_trials=N, n_combos=0)
    blocks = np.array_split(np.arange(T), S)
    s1 = np.array([M[b].sum(axis=0) for b in blocks])            # S x N block sums
    s2 = np.array([(M[b] ** 2).sum(axis=0) for b in blocks])
    nb = np.array([len(b) for b in blocks], float)

    def sharpes(mask: np.ndarray) -> np.ndarray:
        n = nb[mask].sum()
        mu = s1[mask].sum(axis=0) / n
        var = (s2[mask].sum(axis=0) - n * mu ** 2) / (n - 1)
        return mu / np.sqrt(var)

    below = 0
    combos = list(combinations(range(S), S // 2))
    for c in combos:
        mask = np.zeros(S, bool)
        mask[list(c)] = True
        star = int(np.argmax(sharpes(mask)))
        oos = sharpes(~mask)
        omega = (oos < oos[star]).sum() / (N - 1) if N > 1 else np.nan   # OOS rank in [0,1]
        if omega <= 0.5:
            below += 1
    return dict(pbo=float(below / len(combos)), S=S, n_trials=N, n_combos=len(combos))


# ----------------------------------------------------------------- the standing table

BENCHMARKS = ("1/N", "Min-variance")


def inference_table(monthly: pd.DataFrame) -> pd.DataFrame:
    """LW pairwise tests vs each benchmark + DSR, on the walk-forward net OOS returns."""
    srs = {c: float(monthly[c].dropna().mean() / monthly[c].dropna().std())
           for c in monthly.columns}
    rows = []
    for name in monthly.columns:
        x = monthly[name].dropna()
        row = dict(portfolio=name, sharpe_ann=srs[name] * np.sqrt(12),
                   dsr=deflated_sharpe(x, srs.values())["dsr"])
        for bench in BENCHMARKS:
            if bench not in monthly.columns or name == bench:
                row[f"delta_ann_vs_{bench}"] = np.nan
                row[f"p_boot_vs_{bench}"] = np.nan
                row[f"p_hac_vs_{bench}"] = np.nan
                continue
            t = sharpe_diff_test(x, monthly[bench])
            row[f"delta_ann_vs_{bench}"] = t["delta"] * np.sqrt(12) if np.isfinite(
                t.get("delta", np.nan)) else np.nan
            row[f"p_boot_vs_{bench}"] = t.get("p_boot", np.nan)
            row[f"p_hac_vs_{bench}"] = t.get("p_hac", np.nan)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("sharpe_ann", ascending=False)


def run() -> pd.DataFrame:
    C.ensure_dirs()
    monthly = pd.read_csv(C.OPTIMIZER_WALKFORWARD_RETURNS, index_col=0, parse_dates=True)
    table = inference_table(monthly)
    table.to_csv(C.OPTIMIZER_INFERENCE, index=False)
    print(f"[inference] {len(table)} contestants, B={C.OPTIMIZER_INFER_B} bootstrap "
          f"-> {C.OPTIMIZER_INFERENCE.name}")
    print(table.to_string(index=False))
    return table


if __name__ == "__main__":
    run()
