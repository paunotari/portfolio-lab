"""Structural (mu-free) portfolio engines: 1/N, ERC, HRP, min-variance + risk contributions.

These are the "anchor" portfolios of the optimizer's unified method (see
info/portfolio_optimization.md): allocations built only from the covariance structure — the
trustworthy input (Chopra-Ziemba) — never from estimated mean returns. ERC on the shrunk
covariance is the neutral prior the Black-Litterman tilt bends away from; 1/N, HRP and
min-variance are computed on every run as the mandatory honesty benchmarks (DeMiguel 2009).

All engines take a covariance matrix (feed them the Ledoit-Wolf shrunk one from
``portfolio.shrinkage``) and return long-only weights summing to 1. Deep dives:
info/literature/risk-parity-erc.md and info/literature/hierarchical-risk-parity.md.
"""
from __future__ import annotations
import numpy as np
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.optimize import minimize
from scipy.spatial.distance import squareform


def equal_weight(n: int) -> np.ndarray:
    """1/N — the DeMiguel benchmark. Deliberately trivial; must be on screen next to any
    optimizer output."""
    return np.full(n, 1.0 / n)


def erc_weights(sigma: np.ndarray) -> np.ndarray:
    """Equal Risk Contribution: each asset contributes sigma_p/n of the portfolio risk.

    Solved via Spinu (2013)'s convex reformulation — minimize 1/2 y'Sigma y - sum(ln y_i)
    (the log barrier keeps y > 0; the first-order condition y_i (Sigma y)_i = const is exactly
    ERC), then normalize w = y / sum(y). Existence/uniqueness of the long-only solution:
    Maillard, Roncalli & Teiletche (2010).
    """
    sigma = np.asarray(sigma, dtype=float)
    n = len(sigma)
    y0 = 1.0 / np.sqrt(np.diag(sigma))          # inverse-vol start (exact answer if corr equal)

    def f(y):
        return 0.5 * y @ sigma @ y - np.log(y).sum()

    def grad(y):
        return sigma @ y - 1.0 / y

    res = minimize(f, y0, jac=grad, method="L-BFGS-B",
                   bounds=[(1e-9, None)] * n, options={"maxiter": 10_000, "ftol": 1e-14})
    y = res.x
    w = y / y.sum()
    # sanity: risk contributions should be (near-)equal; a failed solve would show up here
    rc = risk_contributions(w, sigma)
    if rc.max() - rc.min() > 1e-4 * rc.sum():
        raise RuntimeError(f"ERC solve did not converge (RC spread {rc.max() - rc.min():.2e})")
    return w


def hrp_weights(sigma: np.ndarray) -> np.ndarray:
    """Hierarchical Risk Parity (Lopez de Prado 2016), exact 3-stage algorithm.

    1. Cluster assets on correlation distance d_ij = sqrt((1 - rho_ij)/2), single linkage
       (the paper's choice; revisit via walk-forward if chaining ever bites — see deep dive).
    2. Quasi-diagonalize: reorder assets in dendrogram-leaf order.
    3. Recursive bisection of the ordered list, splitting capital between halves in inverse
       proportion to each half's inverse-variance-weighted cluster variance.

    Never inverts the covariance matrix, so estimation error stays local to its cluster.
    """
    sigma = np.asarray(sigma, dtype=float)
    n = len(sigma)
    std = np.sqrt(np.diag(sigma))
    corr = sigma / np.outer(std, std)
    dist = np.sqrt(np.clip((1.0 - corr) / 2.0, 0.0, None))
    np.fill_diagonal(dist, 0.0)
    link = linkage(squareform(dist, checks=False), method="single")
    order = list(leaves_list(link))

    def cluster_var(idx: list[int]) -> float:
        sub = sigma[np.ix_(idx, idx)]
        ivp = 1.0 / np.diag(sub)
        ivp /= ivp.sum()
        return float(ivp @ sub @ ivp)

    w = np.ones(n)
    stack = [order]
    while stack:
        items = stack.pop()
        if len(items) < 2:
            continue
        half = len(items) // 2
        left, right = items[:half], items[half:]
        v_l, v_r = cluster_var(left), cluster_var(right)
        alpha = 1.0 - v_l / (v_l + v_r)
        w[left] *= alpha
        w[right] *= 1.0 - alpha
        stack += [left, right]
    return w / w.sum()


def min_var_weights(sigma: np.ndarray) -> np.ndarray:
    """Long-only minimum-variance portfolio (SLSQP on the simplex). A benchmark, not the
    recommendation — it is what the optimizer's risk slider alone should approximately recover."""
    sigma = np.asarray(sigma, dtype=float)
    n = len(sigma)
    res = minimize(lambda w: w @ sigma @ w, equal_weight(n),
                   jac=lambda w: 2.0 * sigma @ w, method="SLSQP",
                   bounds=[(0.0, 1.0)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
                   options={"maxiter": 1000, "ftol": 1e-12})
    w = np.clip(res.x, 0.0, None)
    return w / w.sum()


def risk_contributions(w: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Euler decomposition RC_i = w_i (Sigma w)_i / sigma_p — sums exactly to sigma_p.
    'Where your risk actually sits': reported with every recommended portfolio."""
    w = np.asarray(w, dtype=float)
    sigma_p = float(np.sqrt(w @ sigma @ w))
    if sigma_p == 0.0:
        return np.zeros_like(w)
    return w * (sigma @ w) / sigma_p
