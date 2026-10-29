"""Descriptive statistics of the menu and of the factor regressors (v2.0).

The v1 paper reported correlations and the diversification ratio but never a plain table of
what each sleeve did. A referee reads that table first, so it is generated here from the same
processed data the race uses: the 28 MSCI sleeves over the common window (1999-01 -> 2026-06,
330 months) and the global factors over the same months.

Conventions: monthly USD net total returns; mean and Sharpe on returns in EXCESS of the
one-month T-bill; mean x 12, volatility x sqrt(12); skewness and EXCESS kurtosis of monthly
returns; worst month and maximum drawdown on total returns; beta against the global
(Ken French "Developed") market excess return.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

from portfolio_lab.portfolio import optimizer as opt
from portfolio_lab.v2 import factors as F
from portfolio_lab.v2.risk_adjusted import capm_beta, sortino

FACTOR_LABELS = {"dev_mkt_rf": "Market (developed)", "dev_smb": "SMB (size)",
                 "dev_hml": "HML (value)", "dev_wml": "WML (momentum)",
                 "dev_rmw": "RMW (profitability)", "dev_cma": "CMA (investment)",
                 "em_mkt_rf": "Market (emerging)"}


def max_drawdown(r: pd.Series) -> float:
    lvl = (1 + r).cumprod()
    return float((lvl / lvl.cummax() - 1).min())


def sleeve_table(rets: pd.DataFrame = None) -> pd.DataFrame:
    rets = opt.load_returns() if rets is None else rets
    fac = F.align(rets)
    rows = []
    for col in rets.columns:
        r = rets[col]
        e = (r - fac["rf"]).to_numpy(float)
        region, factor = col.split(" | ")
        rows.append(dict(series=col, region=region.replace("_", " "), factor=factor,
                         months=len(r), mean_excess_ann=float(e.mean() * 12),
                         vol_ann=float(r.std(ddof=1) * np.sqrt(12)),
                         sharpe=float(e.mean() / e.std(ddof=1) * np.sqrt(12)),
                         sortino=sortino(e), skew=float(skew(r)),
                         exkurt=float(kurtosis(r)), worst_month=float(r.min()),
                         max_drawdown=max_drawdown(r),
                         beta=capm_beta(e, fac["dev_mkt_rf"].to_numpy(float))))
    return pd.DataFrame(rows)


def factor_table(index: pd.DatetimeIndex) -> pd.DataFrame:
    fac = F.align(pd.DataFrame(index=index))
    rows = []
    for col, label in FACTOR_LABELS.items():
        x = fac[col].dropna()
        rows.append(dict(factor=label, column=col, months=len(x),
                         mean_ann=float(x.mean() * 12), vol_ann=float(x.std() * np.sqrt(12)),
                         t_mean=float(x.mean() / x.std() * np.sqrt(len(x))),
                         skew=float(skew(x)), exkurt=float(kurtosis(x)),
                         worst_month=float(x.min())))
    return pd.DataFrame(rows)
