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
