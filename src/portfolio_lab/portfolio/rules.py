"""Rule-based strategies tested as walk-forward contestants (portfolio/validation.py).

These are NOT optimizer portfolios — they are simple, transparent rules from the canon, added so
we can answer the live question honestly: does anything beat 1/N and min-variance out of sample?
Each rule is validated the only sound way (info/literature.md, DeMiguel lesson): over MANY
decision dates in the walk-forward, never on a single return snapshot.

- ``momentum_weights`` — cross-sectional momentum (Jegadeesh & Titman 1993, the "12-1" formation):
  hold the top-K sleeves by trailing return, skipping the most recent month to avoid short-term
  reversal. The ONLY legitimate use of past returns — at the horizon where momentum is real, as a
  re-tested rule, not as "this index did well lately." High turnover, so it only earns its keep
  net of the transaction costs the walk-forward now charges.

- ``vol_managed`` — volatility targeting (Moreira & Muir 2017, "Volatility-Managed Portfolios",
  *JF*): scale a base portfolio's exposure by the inverse of its trailing volatility. Here in the
  UNLEVERED form for a long-only investor — it can only cut exposure toward the target and hold
  cash when vol runs hot, never lever up. A defensive overlay whose whole thesis is "sidestep the
  turbulent months," which the walk-forward can confirm or reject. Causal by construction (uses
  only past returns), so it is a fair out-of-sample test.

- ``gmv_combo_weights`` — the Yuan & Zhou (2023, *JFQA*) GMV combination rule, our central
  humility claim's strongest published challenger (deep dive:
  `info/literature/frontier/beating-1N-yuan-zhou.md`). Shrinks the plug-in global-minimum-variance
  portfolio toward 1/N with a data-driven intensity λ*. **Pre-registered prediction, from their
  own theory, declared before the first run: no significant win on our menu** — our warmup
  T=120 is a third of the T=360 they call the minimum, and our menu is one-factor-dominated
  (first PC 77%, M18), i.e. Proposition-3 territory where 1/N is asymptotically optimal.
  The only UNCONSTRAINED (short-allowing) contestant in the table, deliberately — constraining
  it would test our rule, not theirs.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from portfolio_lab import config as C


def momentum_weights(rets_train: pd.DataFrame, k: int = None, lookback: int = None,
                     skip: int = None) -> np.ndarray:
    """Equal weight on the top-K sleeves by (lookback)-month return skipping the last (skip)
    months. Estimated only from the training window -> a valid out-of-sample rule."""
    k = k or C.OPTIMIZER_MOMENTUM_K
    lookback = lookback or C.OPTIMIZER_MOMENTUM_LOOKBACK
    skip = C.OPTIMIZER_MOMENTUM_SKIP if skip is None else skip
    window = rets_train.iloc[-(lookback + skip): -skip] if skip else rets_train.iloc[-lookback:]
    score = (1.0 + window).prod() - 1.0                    # cumulative formation-period return
    top = score.nlargest(k).index
    w = np.zeros(len(rets_train.columns))
    for col in top:
        w[rets_train.columns.get_loc(col)] = 1.0 / len(top)
    return w


def vol_managed(gross: pd.Series, target_ann: float = None, window: int = None,
                max_lev: float = None) -> tuple[pd.Series, pd.Series]:
    """Apply the unlevered volatility-targeting overlay to a base portfolio's monthly return
    series. Returns (managed_gross_returns, extra_turnover) where extra_turnover is the trading
    the overlay itself generates (leverage changes), so the caller can charge it.

    leverage_t = min(max_lev, target_monthly_vol / trailing_vol_{t-1}); managed_t = lev_t * gross_t
    (the (1 - lev) cash sleeve earns 0). Trailing vol uses only past months -> causal.
    """
    target_ann = target_ann or C.OPTIMIZER_VOLTARGET_ANN
    window = window or C.OPTIMIZER_VOLTARGET_WINDOW
    max_lev = C.OPTIMIZER_VOLTARGET_MAXLEV if max_lev is None else max_lev
    target_m = target_ann / np.sqrt(12.0)
    trailing = gross.shift(1).rolling(window, min_periods=max(3, window // 2)).std()
    lev = (target_m / trailing).clip(upper=max_lev).fillna(max_lev)
    managed = lev * gross
    extra_turnover = lev.diff().abs().fillna(0.0)          # |Δ exposure| = trading to re-lever
    return managed, extra_turnover


def gmv_combo_weights(rets_train: pd.DataFrame, sigma: np.ndarray = None
                      ) -> tuple[np.ndarray, float]:
    """Yuan & Zhou (2023) GMV combination rule. Returns (weights, λ*).

        ŵ_λ = λ · ŵ_g + (1−λ) · 1_N/N,      ŵ_g = S⁻¹1 / (1'S⁻¹1)

    with S the SAMPLE covariance of the training window (their estimator — deliberately not our
    Ledoit-Wolf Σ: the point is to field THEIR rule, and their λ* is derived for the plug-in
    case; LW shrinkage would be a second, different shrinkage on top).

    λ* maximizes the combination's ASYMPTOTIC (out-of-sample) Sharpe ratio under η = N/T
    concentration. We do not have their eq. (29) transcribed, so λ* is re-derived here from the
    same five estimable scalars their paper lists (η, σ_g, σ_{1/N}, SR_g, SR_{1/N}) and the
    standard large-dimensional results for the plug-in GMV (Kan-Zhou 2007; Frahm-Memmel 2010;
    Bodnar-Parolya-Schmid 2018):

      · in-sample GMV variance      σ̃² = 1/(1'S⁻¹1),  E[σ̃²] ≈ σ_g²(1−η)  ⇒  σ̂_g² = σ̃²/(1−η)
      · OOS variance of ŵ_g         A = σ_g²/(1−η)
      · Cov(r_ŵg, r_1/N)            B = σ_g²   (in population the GMV covaries σ_g² with EVERY
                                                fully-invested portfolio; estimation noise in ŵ_g
                                                is uncorrelated with the fixed 1/N)
      · Var(r_1/N)                  C = σ_n²,  means a = μ̂_g, b = μ̂_n (training-window means)

    Maximizing (λa+(1−λ)b)/√(λ²A+2λ(1−λ)B+(1−λ)²C) gives the stationary point

        λ* = [ b·E − (a−b)·C ] / [ a·E − b·σ_g²·η/(1−η) ],      E = σ_g² − σ_n²

    which has exactly their stated dependence on (η, σ_g, σ_n, SR_g=a/σ_g, SR_n=b/σ_n) — and the
    right qualitative behaviour: η→0 recovers the classic two-fund Sharpe combination, η→1 drives
    λ*→0 (all estimation error ⇒ pure 1/N). λ is then clipped to [0,1] and the estimated OOS
    Sharpe is evaluated at {0, λ*, 1}, taking the best — i.e. the boundary cases of the same
    constrained problem, all from training data only, so the rule stays causal.

    Degenerate windows (T ≤ N, singular S, non-positive 1'S⁻¹1) fall back to λ=0 (pure 1/N).

    `sigma`: substitute a different covariance estimate for S — used only for the reported
    SENSITIVITY variant (our Ledoit-Wolf Σ, i.e. the version a practitioner would actually run),
    never for the fielded contestant, which stays their plug-in specification.
    """
    R = rets_train.values
    T, N = R.shape
    ones = np.ones(N)
    w_n = ones / N
    eta = N / T
    if T <= N + 2 or eta >= 1.0:
        return w_n, 0.0
    try:
        S = np.cov(R, rowvar=False) if sigma is None else sigma
        Sinv1 = np.linalg.solve(S, ones)
    except np.linalg.LinAlgError:
        return w_n, 0.0
    denom = float(ones @ Sinv1)
    if not np.isfinite(denom) or denom <= 0:
        return w_n, 0.0

    w_g = Sinv1 / denom
    sig_g2 = (1.0 / denom) / (1.0 - eta)                    # bias-corrected true GMV variance
    A, B = sig_g2 / (1.0 - eta), sig_g2
    C = float(np.var(R @ w_n, ddof=1))
    a, b = float((R @ w_g).mean()), float((R @ w_n).mean())

    E = B - C
    num = b * E - (a - b) * C
    den = a * E - b * sig_g2 * eta / (1.0 - eta)
    lam_star = num / den if abs(den) > 1e-18 else 0.0
    lam_star = float(np.clip(lam_star, 0.0, 1.0))

    def est_sharpe(lam: float) -> float:                    # the objective being maximized
        m = lam * a + (1 - lam) * b
        v = lam ** 2 * A + 2 * lam * (1 - lam) * B + (1 - lam) ** 2 * C
        return m / np.sqrt(v) if v > 0 else -np.inf

    lam = max([0.0, lam_star, 1.0], key=est_sharpe)
    return lam * w_g + (1 - lam) * w_n, lam
