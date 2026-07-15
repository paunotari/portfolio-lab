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
