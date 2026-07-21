"""Structural (mu-free) portfolio engines: 1/N, ERC, HRP, min-variance + risk contributions.

These are the "anchor" portfolios of the optimizer's unified method (see
info/portfolio_optimization.md): allocations built only from the covariance structure — the
trustworthy input (Chopra-Ziemba) — never from estimated mean returns. ERC on the shrunk
covariance is the neutral prior the Black-Litterman tilt bends away from; 1/N, HRP and
min-variance are computed on every run as the mandatory honesty benchmarks (DeMiguel 2009).

All engines take a covariance matrix (feed them the Ledoit-Wolf shrunk one from
``portfolio.shrinkage``) and return long-only weights summing to 1. Deep dives:
info/literature/classics/risk-parity-erc.md and info/literature/classics/hierarchical-risk-parity.md.
"""
from __future__ import annotations
import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage, leaves_list
from scipy.optimize import minimize
from scipy.spatial.distance import squareform


def equal_weight(n: int) -> np.ndarray:
    """1/N — the DeMiguel benchmark. Deliberately trivial; must be on screen next to any
    optimizer output."""
    return np.full(n, 1.0 / n)


def erc_weights(sigma: np.ndarray, budgets: np.ndarray = None) -> np.ndarray:
    """Risk-budgeted contributions: asset i contributes budgets_i of the portfolio risk
    (default: equal budgets = classic ERC — each contributes sigma_p/n).

    Solved via Spinu (2013)'s convex reformulation — minimize 1/2 y'Sigma y - sum(b_i ln y_i)
    (the log barrier keeps y > 0; the first-order condition y_i (Sigma y)_i = b_i * const is
    exactly the risk-budget condition), then normalize w = y / sum(y). Existence/uniqueness
    of the long-only solution: Maillard, Roncalli & Teiletche (2010). `budgets`: positive,
    normalized internally ("EM gets 10% of my RISK, not 10% of my money" — the TODO item).
    """
    sigma = np.asarray(sigma, dtype=float)
    n = len(sigma)
    if budgets is None:
        b = np.full(n, 1.0 / n)
    else:
        b = np.asarray(budgets, dtype=float)
        if len(b) != n or (b <= 0).any():
            raise ValueError("budgets must be positive, one per asset")
        b = b / b.sum()
    bb = b * n                                  # barrier scaled so equal budgets reproduce
    y0 = np.sqrt(bb) / np.sqrt(np.diag(sigma))  # the classic objective (solver precision)

    def f(y):
        return 0.5 * y @ sigma @ y - bb @ np.log(y)

    def grad(y):
        return sigma @ y - bb / y

    res = minimize(f, y0, jac=grad, method="L-BFGS-B",
                   bounds=[(1e-9, None)] * n, options={"maxiter": 10_000, "ftol": 1e-14})
    y = res.x
    w = y / y.sum()
    # sanity: realized contribution SHARES should match the budgets; a failed solve shows up
    # here. Tolerance is RELATIVE to total risk — with very low-vol assets in the menu (e.g.
    # the cash proxy) sigma_p is tiny and an absolute-ish threshold rejects good solves
    rc = risk_contributions(w, sigma)
    if np.abs(rc / rc.sum() - b).max() > 1e-3:
        raise RuntimeError(f"risk-budget solve did not converge (max share error "
                           f"{np.abs(rc / rc.sum() - b).max():.2e})")
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


def _corr_distance(sigma: np.ndarray) -> np.ndarray:
    """d_ij = sqrt((1 - rho_ij)/2) — the correlation distance HRP and HERC both cluster on."""
    std = np.sqrt(np.diag(sigma))
    corr = sigma / np.outer(std, std)
    dist = np.sqrt(np.clip((1.0 - corr) / 2.0, 0.0, None))
    np.fill_diagonal(dist, 0.0)
    return dist


def _within_dispersion(dist: np.ndarray, labels: np.ndarray) -> float:
    """Tibshirani's W_k = sum_clusters (1/2n_r) * sum_{i,j in r} d_ij^2."""
    total = 0.0
    for c in np.unique(labels):
        idx = np.where(labels == c)[0]
        if len(idx) < 2:
            continue
        sub = dist[np.ix_(idx, idx)]
        total += float((sub ** 2).sum()) / (2.0 * len(idx))
    return total


def gap_index(rets: np.ndarray, method: str = "ward", k_max: int = None, b: int = 20,
              seed: int = 0) -> int:
    """Number of clusters by the Tibshirani et al. (2001) gap statistic — HERC's "early
    stopping" rule (Raffinot 2018), which is what keeps it from growing HRP's full dendrogram.

    Gap(k) = E*[log W_k] - log W_k, with the reference expectation taken over `b` null datasets
    built by permuting each sleeve's return series INDEPENDENTLY. That null preserves every
    sleeve's own marginal distribution exactly and destroys only the cross-correlation — i.e.
    "the same assets, no cluster structure", which is the hypothesis the index is supposed to
    test. (The textbook uniform-box reference is meaningless in correlation-distance space.)

    Returns the smallest k satisfying Tibshirani's 1-standard-error rule
    Gap(k) >= Gap(k+1) - s_{k+1}, falling back to the argmax if none does. k=1 is a legitimate
    answer: it says the menu has no cluster structure worth cutting.

    **MEASURED on our menu (2026-07-21): the rule never fires.** Gap(k) rises monotonically all
    the way to the k_max ceiling (1.41 at k=1 → 3.69 at k=21, with s ≈ 0.01 — the increments
    dwarf the standard error at every step). The reason is transparent and worth stating rather
    than hiding: the permutation null has near-zero correlation everywhere, so its dispersion
    falls only through the arithmetic 0.25·(n−k) term, while the real menu's falls faster at
    EVERY k. There is no scale at which our sleeves stop looking more clustered than nothing at
    all — which is M18/M27 from a third angle: a one-factor-dominated menu is a continuum, not
    crisp groups. So HERC's early stopping is INOPERATIVE here and the fielded rule descends the
    full hierarchy; the K-sensitivity is reported instead of being papered over.

    k_max defaults to n-1 (no ceiling short of "every asset its own cluster"), precisely so the
    ceiling is not what determines the answer.
    """
    rng = np.random.default_rng(seed)
    T, n = rets.shape
    k_max = int(min(k_max if k_max is not None else n - 1, n - 1))
    if k_max < 2:
        return 1

    def _labels(x: np.ndarray) -> tuple:
        d = _corr_distance(np.cov(x, rowvar=False))
        lk = linkage(squareform(d, checks=False), method=method)
        return d, lk

    dist, link = _labels(rets)
    obs = np.array([np.log(max(_within_dispersion(
        dist, fcluster(link, k, criterion="maxclust")), 1e-12)) for k in range(1, k_max + 2)])

    ref = np.zeros((b, k_max + 1))
    for j in range(b):
        null = np.column_stack([rng.permutation(rets[:, i]) for i in range(n)])
        d0, l0 = _labels(null)
        for i, k in enumerate(range(1, k_max + 2)):
            ref[j, i] = np.log(max(_within_dispersion(
                d0, fcluster(l0, k, criterion="maxclust")), 1e-12))

    gap = ref.mean(axis=0) - obs
    s = ref.std(axis=0, ddof=1) * np.sqrt(1.0 + 1.0 / b)
    for i in range(k_max):                                  # 1-standard-error rule
        if gap[i] >= gap[i + 1] - s[i + 1]:
            return i + 1
    return int(np.argmax(gap[:k_max]) + 1)


def herc_weights(sigma: np.ndarray, rets: np.ndarray = None, method: str = "ward",
                 n_clusters: int = None, seed: int = 0) -> tuple[np.ndarray, int]:
    """Hierarchical Equal Risk Contribution (Raffinot 2018). Returns (weights, n_clusters).

    Literally "ERC on HRP's topology" — both sides of the M25 anchor decision in one rule
    (deep dive: info/literature/frontier/hrp-extensions.md §2). Four differences from
    ``hrp_weights``, each one of Raffinot's:

    1. **Ward linkage** instead of single linkage (single linkage chains; Ward minimizes
       within-cluster variance). `method="single"` reruns the same allocation on HRP's own
       topology — the linkage sensitivity the CBS thesis rightly insists on reporting.
    2. **Early stopping at K clusters** chosen by the gap index (``gap_index``), instead of
       bisecting all the way down to individual assets.
    3. **Top-down splits that respect the dendrogram** — capital is divided at each real
       merge node — instead of HRP's count-based "cut the ordered list in half".
    4. **True equal risk contribution across and within clusters** instead of HRP's
       inverse-cluster-variance factor: at each split we build the exact 2x2 covariance of the
       two child sub-portfolios (including their correlation) and run the ERC solver on it;
       inside a terminal cluster we run the ERC solver on that cluster's own sub-covariance.
       So the recursion never leaves the equal-risk-contribution family.

    Declared prior (recorded in TODO before the first run): statistically indistinguishable
    from HRP/ERC on our menu, since M27 measures the menu at ~1.3 independent risk bets and a
    smarter partition of one bet is still one bet.
    """
    sigma = np.asarray(sigma, dtype=float)
    n = len(sigma)
    dist = _corr_distance(sigma)
    link = linkage(squareform(dist, checks=False), method=method)
    if n_clusters is None:
        n_clusters = gap_index(rets, method=method, seed=seed) if rets is not None else 1
    n_clusters = int(np.clip(n_clusters, 1, n))
    labels = fcluster(link, n_clusters, criterion="maxclust")

    def leaves_of(node: int) -> list[int]:
        if node < n:
            return [node]
        a, b_ = int(link[node - n, 0]), int(link[node - n, 1])
        return leaves_of(a) + leaves_of(b_)

    def erc_or_equal(sub: np.ndarray) -> np.ndarray:
        if len(sub) == 1:
            return np.ones(1)
        try:
            return erc_weights(sub)
        except Exception:                                   # non-convergent 2x2 corner
            ivp = 1.0 / np.sqrt(np.diag(sub))
            return ivp / ivp.sum()

    def alloc(node: int) -> np.ndarray:
        lv = leaves_of(node)
        w = np.zeros(n)
        if len(set(labels[lv])) <= 1:                       # terminal cluster: ERC inside it
            w[lv] = erc_or_equal(sigma[np.ix_(lv, lv)])
            return w
        left, right = int(link[node - n, 0]), int(link[node - n, 1])
        wl, wr = alloc(left), alloc(right)
        c2 = np.array([[wl @ sigma @ wl, wl @ sigma @ wr],
                       [wr @ sigma @ wl, wr @ sigma @ wr]])
        a = erc_or_equal(c2)                                # ERC BETWEEN the two clusters
        return a[0] * wl + a[1] * wr

    w = alloc(2 * n - 2)
    return w / w.sum(), n_clusters


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
