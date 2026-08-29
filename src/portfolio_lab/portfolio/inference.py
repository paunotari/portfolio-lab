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
- ``friedman_nemenyi``: Demšar (2006) protocol for comparing MANY methods at once — Friedman
  test on average ranks across time blocks, then the Nemenyi post-hoc critical difference.
  The pairwise LW table answers "is A better than B?" one pair at a time; run over a dozen
  contestants that is a multiplicity problem the DSR only partly covers. This answers the
  joint question directly: is the whole ranking distinguishable from noise, and which gaps
  survive a simultaneous comparison?

Point estimates rank; p-values decide what a ranking claim is worth. Failing to reject is
not "equal" — with ~210 OOS months power is modest, so the CI is reported alongside.

Run:  python -m portfolio_lab.portfolio.inference     (needs the cached walk-forward CSV)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2, f as f_dist, norm, studentized_range

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


# ------------------------------------------- Friedman + Nemenyi (Demšar 2006 protocol)

def block_ranks(monthly: pd.DataFrame, block: int = 12, metric: str = "sharpe") -> pd.DataFrame:
    """Rank every contestant within each non-overlapping block of `block` OOS months.

    Rank 1 = best in that block. Rows with any NaN are dropped first so all contestants face
    the SAME months — a rank comparison is only meaningful on a common panel (this costs the
    all-weather sleeve's slightly shorter tail, and is stated rather than silently patched).
    A trailing partial block shorter than half `block` is discarded.

    metric: "sharpe" (per-block mean/std — risk-adjusted, the quantity the whole table is
    about) or "return" (per-block compounded return).
    """
    M = monthly.dropna()
    g = np.arange(len(M)) // block
    keep = pd.Series(g).value_counts()
    g = pd.Series(g, index=M.index)
    M = M[g.map(keep) >= max(2, block // 2)]
    g = g[M.index]
    if metric == "sharpe":
        scores = M.groupby(g).agg(lambda s: s.mean() / s.std() if s.std() > 0 else np.nan)
    elif metric == "return":
        scores = M.groupby(g).agg(lambda s: float((1 + s).prod() - 1))
    else:
        raise ValueError(f"unknown metric {metric!r} (sharpe | return)")
    return scores.dropna().rank(axis=1, ascending=False)


def friedman_nemenyi(monthly: pd.DataFrame, block: int = 12, metric: str = "sharpe",
                     alpha: float = 0.05) -> dict:
    """Demšar (2006): Friedman test across blocks + the Nemenyi post-hoc critical difference.

    Two stages, and the second only means anything if the first rejects:

    1. **Friedman** on the average ranks R_j: chi2_F = 12N/(k(k+1)) * [sum R_j^2 - k(k+1)^2/4],
       reported with the Iman-Davenport F correction (chi2_F is known to be conservative).
       H0: every contestant has the same average rank, i.e. the whole ranking is noise.
    2. **Nemenyi**: two contestants differ at level alpha iff their average ranks differ by
       more than CD = q_alpha * sqrt(k(k+1)/(6N)), q_alpha = the Studentized range critical
       value at infinite df divided by sqrt(2). One threshold covering ALL pairs simultaneously
       — which is exactly what a table of a dozen pairwise LW tests does not give you.

    Returns the average ranks, CD, the Friedman/Iman-Davenport statistics and, per contestant,
    whether its rank gap to 1/N and to the best-ranked contestant clears CD.
    """
    ranks = block_ranks(monthly, block=block, metric=metric)
    N, k = ranks.shape
    if N < 3 or k < 3:
        return dict(n_blocks=N, k=k, note="too few blocks/contestants for Friedman")
    avg = ranks.mean().sort_values()
    chi_f = (12.0 * N / (k * (k + 1))) * (float((avg ** 2).sum()) - k * (k + 1) ** 2 / 4.0)
    p_chi = float(chi2.sf(chi_f, k - 1))
    denom = N * (k - 1) - chi_f
    f_f = ((N - 1) * chi_f / denom) if denom > 0 else np.inf
    p_f = float(f_dist.sf(f_f, k - 1, (k - 1) * (N - 1))) if np.isfinite(f_f) else 0.0
    q = float(studentized_range.ppf(1 - alpha, k, np.inf)) / np.sqrt(2.0)
    cd = q * np.sqrt(k * (k + 1) / (6.0 * N))

    best = avg.index[0]
    rows = []
    for name in avg.index:
        row = dict(portfolio=name, avg_rank=float(avg[name]),
                   gap_to_best=float(avg[name] - avg[best]),
                   differs_from_best=bool(abs(avg[name] - avg[best]) > cd))
        if "1/N" in avg.index:
            row["gap_to_1/N"] = float(avg[name] - avg["1/N"])
            row["differs_from_1/N"] = bool(abs(avg[name] - avg["1/N"]) > cd)
        rows.append(row)
    return dict(n_blocks=N, k=k, block=block, metric=metric, alpha=alpha,
                chi2_friedman=float(chi_f), p_friedman=p_chi,
                F_iman_davenport=float(f_f), p_iman_davenport=p_f,
                critical_difference=float(cd), best=best,
                table=pd.DataFrame(rows))


# ----------------------------------------------------------------- the standing table

BENCHMARKS = ("1/N", "Min-variance")


# ------------------------------------------- power of the headline test (paper review C2)

def sharpe_power(x, y, alpha: float = 0.05, target_power: float = 0.80,
                 block: int = None, B: int = None, seed: int = None) -> dict:
    """Power and minimum detectable effect for a Ledoit-Wolf Sharpe-difference test.

    A non-rejection means "no effect" ONLY if the design could have detected one. The module
    docstring has always said power here is modest; this puts a number on it, so a null can be
    reported as "no effect resolvable at this sample size" rather than "no effect".

    Uses the SAME HAC standard error the test itself uses, so power and p come from one object.
    Under the local-alternative normal approximation d = delta/se ~ N(delta_true/se, 1):

        power(delta) = Phi(delta/se - z_a) + Phi(-delta/se - z_a),   z_a = z_{1-alpha/2}
        MDES         = (z_a + z_{target_power}) * se

    Returns monthly units plus annualized (x sqrt(12)) copies for display. `mdes_ann` is the
    smallest annualized Sharpe gap this design could call significant at `target_power`; an
    observed gap below it is uninformative about the true one either way."""
    t = sharpe_diff_test(x, y, block=block, B=B, seed=seed)
    se, delta = t.get("se", np.nan), t.get("delta", np.nan)
    out = dict(T=t["T"], block=t["block"], alpha=alpha, target_power=target_power,
               delta=delta, se=se, p_boot=t.get("p_boot", np.nan))
    if not np.isfinite(se) or se <= 0:
        return {**out, "power_at_observed": np.nan, "mdes": np.nan, "mdes_ann": np.nan,
                "note": t.get("note", "degenerate s.e.")}
    z_a = norm.ppf(1 - alpha / 2)
    lam = abs(delta) / se
    out["power_at_observed"] = float(norm.cdf(lam - z_a) + norm.cdf(-lam - z_a))
    out["mdes"] = float((z_a + norm.ppf(target_power)) * se)
    out["delta_ann"] = float(delta * np.sqrt(12))
    out["mdes_ann"] = float(out["mdes"] * np.sqrt(12))
    out["observed_over_mdes"] = float(abs(delta) / out["mdes"])
    return out


# ------------------------------- inference for the diversification ratio (paper review C1)

def _dr2_equal_weight(R: np.ndarray) -> float:
    """DR^2 of 1/N on the shrunk covariance of `R` — the engine's own estimator, so the point
    estimate here reproduces the optimizer's `dr2_equal_weight` exactly."""
    from portfolio_lab.portfolio.optimizer import diversification_ratio
    from portfolio_lab.portfolio.shrinkage import estimate_covariance
    sigma, _ = estimate_covariance(R)
    n = R.shape[1]
    return float(diversification_ratio(np.ones(n) / n, sigma) ** 2)


def dr2_bootstrap(rets_a: pd.DataFrame, rets_b: pd.DataFrame = None, alpha: float = 0.05,
                  block: int = None, B: int = None, seed: int = None) -> dict:
    """Circular block bootstrap for DR^2 (Choueifaty-Coignard independent bets) under 1/N.

    Every Sharpe claim in this study carries a p-value while DR^2 — the paper's actual
    contribution — was a bare point estimate. This supplies the missing leg: a percentile
    confidence interval for one menu, and, when `rets_b` is given, a PAIRED test of
    H0: DR2_a = DR2_b. Paired means the same resampled month indices drive both menus (they
    share a window and 28 of their columns), so the comparison is not inflated by drawing two
    independent histories.

    Resampling is months, in circular blocks of the same length the Sharpe test uses, and the
    covariance is re-shrunk inside every replicate — the sampling variability being measured is
    the one that matters, i.e. of the whole estimate-then-summarize chain, not of a fixed Sigma.

    The p-value is the usual bootstrap inversion: twice the smaller tail mass of the centered
    difference distribution, floored at 1/(B+1)."""
    B = B or C.OPTIMIZER_INFER_B
    seed = C.OPTIMIZER_SEED if seed is None else seed
    paired = rets_b is not None
    if paired:                       # align on the shared window before anything else
        idx = rets_a.index.intersection(rets_b.index)
        rets_a, rets_b = rets_a.loc[idx], rets_b.loc[idx]
    Ra = rets_a.dropna().values
    T = len(Ra)
    b = block or C.OPTIMIZER_INFER_BLOCK or max(3, round(T ** (1 / 3)))
    Rb = rets_b.loc[rets_a.dropna().index].values if paired else None

    point_a = _dr2_equal_weight(Ra)
    point_b = _dr2_equal_weight(Rb) if paired else np.nan
    out = dict(T=T, block=b, B=B, n_a=Ra.shape[1], dr2_a=point_a,
               n_b=(Rb.shape[1] if paired else np.nan), dr2_b=point_b)

    rng = np.random.default_rng(seed)
    L = int(np.ceil(T / b))
    starts = rng.integers(0, T, size=(B, L))
    idx_bs = (starts[:, :, None] + np.arange(b)[None, None, :]) % T
    idx_bs = idx_bs.reshape(B, L * b)[:, :T]

    draws_a, draws_d = [], []
    for s in range(B):
        i = idx_bs[s]
        try:
            da = _dr2_equal_weight(Ra[i])
        except Exception:
            continue
        if paired:
            try:
                db = _dr2_equal_weight(Rb[i])
            except Exception:
                continue                      # keep the two draw lists aligned
            draws_d.append(db - da)
        draws_a.append(da)
    a = np.array(draws_a, float)
    lo, hi = np.percentile(a, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    out.update(ci_lo_a=float(lo), ci_hi_a=float(hi), boot_used=len(a))

    if paired and draws_d:
        d = np.array(draws_d, float)
        obs = point_b - point_a
        centered = d - d.mean()
        tail = min((centered >= abs(obs)).mean(), (centered <= -abs(obs)).mean())
        out.update(delta_ba=float(obs),
                   delta_ci_lo=float(np.percentile(d, 100 * alpha / 2)),
                   delta_ci_hi=float(np.percentile(d, 100 * (1 - alpha / 2))),
                   p_boot_delta=float(max(2 * tail, 1.0 / (len(d) + 1))))
    return out


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
