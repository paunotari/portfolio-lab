"""Black-Litterman layer: the only place expected returns are ever produced.

The literature's hardest rule (Michaud 1989, Chopra-Ziemba 1993, DeMiguel 2009): never hand an
optimizer raw historical mean returns — it amplifies exactly their errors. This module builds the
one return vector the optimizer is allowed to see, the BL posterior mu_BL, in two moves
(info/literature/black-litterman.md):

1. Reverse-optimize the neutral anchor:  Pi = delta_ra . Sigma . w0. If you say nothing else, the
   optimizer hands back exactly w0 — garbage-in is structurally impossible at this stage.
   delta_ra is calibrated so the anchor's implied return matches its own historical mean (one
   scalar, reported).
2. Blend views in Bayesianly, each weighted by a stated confidence c in (0, C_MAX]. Low
   confidence barely moves mu_BL; no views leave mu_BL = Pi exactly (the safety property AND the
   unit test).

Regime views — the signature pipe from the macro module into allocation: per-quadrant factor-vs-
reference differentials (the pattern factor_attribution() measured and the factor canon predicts)
become relative views, with Q = the outlook-weighted expected excess and confidence = the Markov
outlook's own probability mass. A 34%-confidence quadrant call tilts 34%-hard, not 100%-hard.

Conventions (fixed, never user-exposed; only per-view confidence is): tau = 1/T; Omega diagonal,
He-Litterman-style Omega_kk = (tau . P Sigma P')_kk / c_k; c capped at C_MAX = 0.95 so a single
view can never degenerate the posterior into constrained MVO on itself.

All returns here are MONTHLY ARITHMETIC means (the covariance's own space); annualize only for
display.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C

C_MAX = 0.95            # per-view confidence cap (deep dive pitfall: c=1 degenerates BL)
C_MIN = 0.05


def implied_returns(sigma: np.ndarray, w0: np.ndarray, anchor_mean: float) -> tuple[np.ndarray, float]:
    """Pi = delta_ra . Sigma . w0, with delta_ra calibrated so w0' Pi equals the anchor
    portfolio's own historical mean monthly return. Returns (Pi, delta_ra)."""
    w0 = np.asarray(w0, dtype=float)
    var0 = float(w0 @ sigma @ w0)
    if var0 <= 0:
        raise ValueError("anchor portfolio has zero variance — cannot reverse-optimize")
    delta_ra = anchor_mean / var0
    return delta_ra * sigma @ w0, delta_ra


def posterior(pi: np.ndarray, sigma: np.ndarray, T: int,
              P: np.ndarray = None, Q: np.ndarray = None,
              conf: np.ndarray = None) -> np.ndarray:
    """The BL master formula. With no views (P is None or empty), returns Pi unchanged.

    mu_BL = [ (tau Sigma)^-1 + P' Omega^-1 P ]^-1 [ (tau Sigma)^-1 Pi + P' Omega^-1 Q ]
    """
    pi = np.asarray(pi, dtype=float)
    if P is None or len(P) == 0:
        return pi.copy()
    P = np.atleast_2d(np.asarray(P, dtype=float))
    Q = np.atleast_1d(np.asarray(Q, dtype=float))
    conf = np.clip(np.atleast_1d(np.asarray(conf, dtype=float)), C_MIN, C_MAX)
    if not (len(P) == len(Q) == len(conf)):
        raise ValueError(f"inconsistent view shapes: P {P.shape}, Q {Q.shape}, conf {conf.shape}")

    tau = 1.0 / T
    view_var = np.diag(P @ (tau * sigma) @ P.T)
    if np.any(view_var <= 0):
        raise ValueError("a view portfolio has zero risk (P Sigma P' not positive) — drop it")
    omega_diag = view_var / conf
    tau_sigma_inv = np.linalg.inv(tau * sigma)
    A = tau_sigma_inv + P.T @ np.diag(1.0 / omega_diag) @ P
    b = tau_sigma_inv @ pi + P.T @ (Q / omega_diag)
    return np.linalg.solve(A, b)


def regime_views(series: list[str], perf: pd.DataFrame, outlook: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    """Build the regime views from per-quadrant performance + the Markov outlook.

    One RELATIVE view per factor type ("<factor> sleeves minus their own regions' Reference"):
      P row: +1/k on each factor-F series, -1/k on the matching region References
      Q_F:   sum_q outlook[q] . (avg monthly excess of F over Reference in quadrant q)
      c_F:   the outlook's max quadrant probability (how sure the macro module is about the mix),
             clipped to [C_MIN, C_MAX] — the "tilt proportional to confidence" property.

    Relative views only — no absolute "asset X will return Y%" claims, which would smuggle raw
    historical means back in. Returns (P, Q, conf, view_descriptions).
    """
    regions = {s.split(" | ")[0] for s in series}
    ref_cols = {r: f"{r} | Reference" for r in regions if f"{r} | Reference" in series}
    conf_val = float(np.clip(max(outlook.values()), C_MIN, C_MAX))
    mean_by = perf.set_index(["state", "series"]).mean_monthly_return

    P_rows, Q_vals, confs, descs = [], [], [], []
    for factor in ("Momentum", "Enhanced Value", "Quality"):
        f_cols = [s for s in series
                  if s.split(" | ")[1] == factor and s.split(" | ")[0] in ref_cols]
        if not f_cols:
            continue
        row = np.zeros(len(series))
        for s in f_cols:
            row[series.index(s)] += 1.0 / len(f_cols)
            row[series.index(ref_cols[s.split(" | ")[0]])] -= 1.0 / len(f_cols)
        q_val, wsum = 0.0, 0.0
        for state, p_state in outlook.items():
            diffs = [mean_by.get((state, s), np.nan) - mean_by.get((state, ref_cols[s.split(" | ")[0]]), np.nan)
                     for s in f_cols]
            diffs = [d for d in diffs if not np.isnan(d)]
            if diffs:
                q_val += p_state * float(np.mean(diffs))
                wsum += p_state
        if wsum == 0:
            continue
        P_rows.append(row)
        Q_vals.append(float(q_val / wsum))
        confs.append(conf_val)
        descs.append(dict(view=f"{factor} vs Reference (outlook-weighted)",
                          q_monthly=float(q_val / wsum), confidence=conf_val))
    if not P_rows:
        return np.empty((0, len(series))), np.empty(0), np.empty(0), []
    return np.array(P_rows), np.array(Q_vals), np.array(confs), descs
