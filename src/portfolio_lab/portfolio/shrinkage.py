"""Ledoit-Wolf covariance shrinkage — the one estimator the literature pass adopts outright.

"Nobody should be using the sample covariance matrix for portfolio optimization" (Ledoit & Wolf
2004). The sample covariance S is unbiased but high-variance entry-by-entry; a structured target
F is biased but stable. The optimal (squared-Frobenius-loss) blend is closed-form:

    Sigma_shrunk = delta* . F  +  (1 - delta*) . S,        delta* in [0, 1]

Extreme entries of S — exactly the ones a mean-variance optimizer piles onto — get pulled toward
the structure in proportion to how noisy they are. Closed-form, no tuning, no fitting loop
(cleanly on the allowed side of the FRED-ToS line, and it consumes MSCI returns anyway).

Two variants (see info/literature/classics/ledoit-wolf-shrinkage.md):

- ``shrink_constant_correlation`` (variant B, *JPM* 2004 "Honey, I Shrunk the Sample Covariance
  Matrix") — the DEFAULT. Target keeps each asset's own variance and sets every correlation to
  the average correlation: the right structure for equity indices, where everything is positively
  correlated at similar strength. Indexing follows the faithful reference implementation
  (github.com/WLM1ke/LedoitWolf) — the pi/rho/gamma sums are the classic off-by-a-term trap.
- ``shrink_identity`` (variant A, *JMVA* 2004) — scaled-identity target, what
  ``sklearn.covariance.LedoitWolf`` implements. Kept as the cross-check / test oracle.

Both take a (T x n) matrix of returns (rows = months), demean internally, and return
``(Sigma_shrunk, delta_star)``. Report delta* in any downstream output — it is one free number of
transparency about input quality (near 0: the sample matrix was fine; near 1: it was noise).
"""
from __future__ import annotations
import numpy as np


def shrink_constant_correlation(returns: np.ndarray) -> tuple[np.ndarray, float]:
    """Variant B: shrink toward the constant-correlation target. Returns (Sigma, delta*)."""
    X = np.asarray(returns, dtype=float)
    t, n = X.shape
    if t < 2 or n < 2:
        raise ValueError(f"need at least 2 observations and 2 assets, got shape {X.shape}")
    X = X - X.mean(axis=0)
    S = X.T @ X / t

    # constant-correlation target F: own variances on the diagonal, average correlation off it
    var = np.diag(S).reshape(-1, 1)
    sqrt_var = np.sqrt(var)
    unit_cov = sqrt_var @ sqrt_var.T                       # sqrt(s_ii * s_jj)
    r_bar = ((S / unit_cov).sum() - n) / (n * (n - 1))
    F = r_bar * unit_cov
    np.fill_diagonal(F, var.ravel())

    # pi-hat: estimation noise in the entries of S
    y = X ** 2
    pi_mat = y.T @ y / t - S ** 2
    pi_hat = pi_mat.sum()

    # rho-hat: covariance between the estimation errors of S and of F
    theta_mat = (X ** 3).T @ X / t - var * S
    np.fill_diagonal(theta_mat, 0.0)
    rho_hat = np.diag(pi_mat).sum() + r_bar * ((1.0 / sqrt_var) @ sqrt_var.T * theta_mat).sum()

    # gamma-hat: misspecification of the target
    gamma_hat = np.linalg.norm(S - F, "fro") ** 2

    kappa = (pi_hat - rho_hat) / gamma_hat if gamma_hat > 0 else 0.0
    delta = float(max(0.0, min(1.0, kappa / t)))
    return delta * F + (1.0 - delta) * S, delta


def shrink_identity(returns: np.ndarray) -> tuple[np.ndarray, float]:
    """Variant A: shrink toward the scaled identity m.I (= sklearn's LedoitWolf).
    Returns (Sigma, delta*)."""
    X = np.asarray(returns, dtype=float)
    t, n = X.shape
    if t < 2 or n < 2:
        raise ValueError(f"need at least 2 observations and 2 assets, got shape {X.shape}")
    X = X - X.mean(axis=0)
    S = X.T @ X / t

    m = np.trace(S) / n
    d2 = np.linalg.norm(S - m * np.eye(n), "fro") ** 2 / n
    b2_bar = sum(np.linalg.norm(np.outer(x, x) - S, "fro") ** 2 for x in X) / (t ** 2) / n
    b2 = min(b2_bar, d2)
    delta = float(b2 / d2) if d2 > 0 else 0.0
    return delta * m * np.eye(n) + (1.0 - delta) * S, delta


def shrink_nonlinear(returns: np.ndarray) -> tuple[np.ndarray, float]:
    """Ledoit & Wolf (2020) ANALYTICAL nonlinear shrinkage. Returns (Sigma, mean_adjustment).

    The linear estimators above pull the whole sample matrix a single distance delta* toward one
    target. Nonlinear shrinkage instead corrects **each eigenvalue by its own amount**, using the
    Marchenko-Pastur theory of how the sample spectrum spreads out relative to the true one: the
    largest sample eigenvalues are shrunk down, the smallest pushed up, and the middle barely
    touched. It is the estimator that supersedes LW-2004 in the large-dimensional literature, so
    a referee will ask whether our verdicts are an artifact of the simpler one.

    Implements the closed-form kernel estimator of *Analytical Nonlinear Shrinkage of
    Large-Dimensional Covariance Matrices* (Ann. Statist. 48(5)): eigendecompose the sample
    covariance, estimate the limiting spectral density and its Hilbert transform with an
    Epanechnikov kernel of bandwidth h = n^(-1/3), and map

        d_i = lambda_i / ( (pi*(p/n)*lambda_i*f(lambda_i))^2
                           + (1 - p/n - pi*(p/n)*lambda_i*Hf(lambda_i))^2 )

    No tuning parameter and no fitting loop, so it stays on the allowed side of the FRED-ToS
    line (caveat #11) exactly like the linear variants.

    The second return value is NOT a delta* — a nonlinear estimator has no single shrinkage
    intensity. It is the mean relative eigenvalue adjustment mean(|d_i - lambda_i|/lambda_i),
    reported so the diagnostic slot stays populated and comparable in spirit.

    Only the p <= n case is implemented: this project always has more months than sleeves, and a
    silent wrong branch is worse than an explicit error.
    """
    X = np.asarray(returns, dtype=float)
    t, p = X.shape
    if t < 2 or p < 2:
        raise ValueError(f"need at least 2 observations and 2 assets, got shape {X.shape}")
    X = X - X.mean(axis=0)
    n = t - 1                                              # effective sample size
    if p > n:
        raise ValueError(f"analytical nonlinear shrinkage needs p <= n, got p={p}, n={n}")
    S = X.T @ X / n
    lam, u = np.linalg.eigh(S)                             # ascending, orthonormal
    lam = np.maximum(lam, 0.0)

    h = n ** (-1.0 / 3.0)
    L = np.tile(lam.reshape(-1, 1), (1, p))                # L[i, j] = lambda_i
    H = h * L.T                                            # H[i, j] = h * lambda_j
    x = (L - L.T) / H                                      # (lambda_i - lambda_j)/(h lambda_j)

    # Epanechnikov density estimate of the limiting spectral distribution
    f_tilde = (3.0 / 4.0 / np.sqrt(5.0)) * np.mean(np.maximum(1.0 - x ** 2 / 5.0, 0.0) / H, axis=1)
    # its Hilbert transform (closed form for the Epanechnikov kernel)
    with np.errstate(divide="ignore", invalid="ignore"):
        hf = ((-3.0 / 10.0 / np.pi) * x
              + (3.0 / 4.0 / np.sqrt(5.0) / np.pi) * (1.0 - x ** 2 / 5.0)
              * np.log(np.abs((np.sqrt(5.0) - x) / (np.sqrt(5.0) + x))))
    edge = np.abs(np.abs(x) - np.sqrt(5.0)) < 1e-12        # the log's removable singularity
    hf[edge] = (-3.0 / 10.0 / np.pi) * x[edge]
    hf = np.nan_to_num(hf, nan=0.0, posinf=0.0, neginf=0.0)
    hf_tilde = np.mean(hf / H, axis=1)

    c = p / n
    denom = (np.pi * c * lam * f_tilde) ** 2 + (1.0 - c - np.pi * c * lam * hf_tilde) ** 2
    d = np.where(denom > 0, lam / np.maximum(denom, 1e-300), lam)
    sigma = u @ np.diag(d) @ u.T
    sigma = (sigma + sigma.T) / 2.0                        # kill numerical asymmetry
    nz = lam > 1e-300
    return sigma, float(np.mean(np.abs(d[nz] - lam[nz]) / lam[nz]))


ESTIMATORS = {"constant_correlation": shrink_constant_correlation,
              "identity": shrink_identity,
              "nonlinear": shrink_nonlinear}


def estimate_covariance(returns: np.ndarray, method: str = None) -> tuple[np.ndarray, float]:
    """Dispatcher used by ``optimizer.build_inputs`` so the covariance estimator is a
    ONE-LINE swap (config.OPTIMIZER_SIGMA_ESTIMATOR) and can therefore be a sensitivity grid
    dimension rather than a hard-coded assumption. Default: the shipped constant-correlation
    Ledoit-Wolf."""
    from portfolio_lab import config as C
    method = method or C.OPTIMIZER_SIGMA_ESTIMATOR
    if method not in ESTIMATORS:
        raise ValueError(f"unknown covariance estimator {method!r} "
                         f"(one of {sorted(ESTIMATORS)})")
    return ESTIMATORS[method](returns)
