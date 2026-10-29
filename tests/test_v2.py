"""Unit tests for the v2.0 stack (global factors, Sortino / Treynor / alphas).

Synthetic data only, so they run offline and without the licensed MSCI files; the one
integration test self-skips when the processed data or the v2 walk-forward cache is absent —
same convention as tests/test_pipeline.py and tests/test_optimizer.py.

Run:  python tests/test_v2.py   (or: python -m pytest tests/ -q)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from portfolio_lab import config as C
from portfolio_lab.v2 import factors as F
from portfolio_lab.v2 import risk_adjusted as R


def _toy(T=240, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2005-01-31", periods=T, freq="ME")
    fac = pd.DataFrame({c: rng.normal(0.004, 0.03, T) for c in
                        ("dev_mkt_rf", "dev_smb", "dev_hml", "dev_rmw", "dev_cma", "dev_wml",
                         "em_mkt_rf", "acwi_mkt_rf")}, index=idx)
    fac["rf"] = 0.001
    return fac, rng


# ------------------------------------------------------------------ regression

def test_hac_ols_coefficients_match_plain_ols():
    fac, rng = _toy()
    X = fac[["dev_mkt_rf", "dev_smb"]].to_numpy()
    y = 0.002 + X @ np.array([0.9, -0.3]) + rng.normal(0, 0.01, len(X))
    r = R.hac_ols(y, X)
    ref = np.linalg.lstsq(np.column_stack([np.ones(len(X)), X]), y, rcond=None)[0]
    assert np.allclose(r["coef"], ref), "HAC OLS point estimates differ from plain OLS"
    assert np.all(r["se"] > 0) and 0 < r["r2"] < 1


def test_alpha_recovers_a_known_intercept_and_beta():
    fac, rng = _toy()
    y = pd.Series(0.002 + 0.8 * fac["dev_mkt_rf"] + rng.normal(0, 1e-4, len(fac)), index=fac.index)
    a = R.alpha(y, fac, "CAPM")
    assert abs(a["alpha_ann"] - 0.024) < 1e-3, f"alpha {a['alpha_ann']:.4f} != 0.024"
    assert abs(a["b_dev_mkt_rf"] - 0.8) < 1e-3
    assert a["p_alpha"] < 1e-6, "a noiseless intercept must be overwhelmingly significant"


def test_alpha_vs_1n_is_the_difference_of_alphas():
    """OLS is linear in y, so alpha(x - y) = alpha(x) - alpha(y) under the same model —
    the property that lets the table call the difference regression 'alpha vs 1/N'."""
    fac, rng = _toy()
    x = pd.Series(rng.normal(0.008, 0.04, len(fac)), index=fac.index)
    y = pd.Series(rng.normal(0.006, 0.04, len(fac)), index=fac.index)
    for model in R.available_models(fac):
        d = R.alpha(x - y, fac, model)["alpha_ann"]
        assert abs(d - (R.alpha(x, fac, model)["alpha_ann"] - R.alpha(y, fac, model)["alpha_ann"])) < 1e-12


def test_newey_west_lag_rule():
    assert R.nw_lags(210) == 4 and R.nw_lags(100) == 4 and R.nw_lags(10) >= 1


# ------------------------------------------------------------------ ratios

def test_sortino_and_downside_deviation_by_hand():
    e = np.array([0.02, -0.01, 0.03, -0.02])
    dd = np.sqrt((0.01 ** 2 + 0.02 ** 2) / 4)
    assert abs(R.downside_deviation(e) - dd) < 1e-15
    assert abs(R.sortino(e) - e.mean() * 12 / (dd * np.sqrt(12))) < 1e-12
    assert np.isnan(R.sortino(np.array([0.01, 0.02]))), "no downside months -> undefined"


def test_treynor_is_excess_return_over_beta():
    fac, rng = _toy()
    m = fac["dev_mkt_rf"].to_numpy()
    e = 0.5 * m + rng.normal(0, 0.005, len(m))
    b = R.capm_beta(e, m)
    assert abs(b - 0.5) < 0.05
    assert abs(R.treynor(e, m) - e.mean() * 12 / b) < 1e-12
    assert np.isnan(R.treynor(-m, m)), "Treynor is undefined for a negative beta"


def test_ratio_diff_test_identical_series_is_null():
    fac, rng = _toy()
    m = fac["dev_mkt_rf"].to_numpy()
    x = 0.9 * m + rng.normal(0.001, 0.01, len(m))
    for stat in ("sortino", "treynor"):
        t = R.ratio_diff_test(x, x.copy(), m, stat, B=199)
        assert t["delta"] == 0 and t["p_boot"] > 0.9, f"{stat}: identical series not null"


def test_alpha_block_bootstrap_detects_a_real_intercept():
    fac, rng = _toy()
    y = pd.Series(0.004 + 0.7 * fac["dev_mkt_rf"] + rng.normal(0, 0.005, len(fac)),
                  index=fac.index)
    b = R.alpha_block_bootstrap(y, fac, "CAPM", B=499)
    assert b["p_boot"] < 0.01 and abs(b["alpha_ann"] - 0.048) < 0.01


# ------------------------------------------------------------------ alignment

def test_align_matches_business_to_calendar_month_ends():
    """The M40 trap: MSCI stamps business month-ends, Ken French calendar month-ends."""
    cal = pd.DataFrame({"rf": [0.001, 0.002, 0.003]},
                       index=pd.to_datetime(["2009-01-31", "2009-02-28", "2009-05-31"]))
    biz = pd.DataFrame(index=pd.to_datetime(["2009-01-30", "2009-02-27", "2009-05-29"]))
    out = F.align(biz, factors=cal)
    assert out["rf"].notna().all(), "period alignment dropped months an exact join would drop"
    assert list(out.index) == list(biz.index), "aligned frame must keep the caller's stamps"
    assert biz.index.isin(cal.index).sum() == 0, "test premise: exact-date join matches nothing"


# ------------------------------------------------------------------ integration

OVERLAYS = ["1/N + vol-target", "Min-variance + vol-target", "1/N + trend (Faber 10m SMA)",
            "Dual momentum (Antonacci)"]


def test_v2_baseline_reproduces_v1_walkforward():
    """The v2 120-month baseline is the v1 race, recomputed: every contestant the M48 overlay
    fix does not touch must match v1's frozen returns exactly (outputs/v1.0), or v1-vs-v2
    comparisons compare two different races. The four overlays are expected to differ."""
    v1 = C.OUTPUT_DIR / "v1.0" / "optimizer" / "optimizer_walkforward_returns.csv"
    v2 = C.V2_DIR / f"wf_returns_warmup{C.V2_BASELINE_WARMUP}.csv"
    if not (v1.exists() and v2.exists()):
        return
    a = pd.read_csv(v1, index_col=0, parse_dates=True)
    cols = [c for c in a.columns if c not in OVERLAYS]
    b = pd.read_csv(v2, index_col=0, parse_dates=True)[cols]
    assert np.allclose(a[cols].to_numpy(), b.to_numpy(), equal_nan=True), "v2 baseline != v1 race"


def test_vectorized_intercept_t_matches_hac_ols():
    """romano_wolf's vectorized intercept s.e. must equal hac_ols's, column by column."""
    fac, rng = _toy()
    X = fac[["dev_mkt_rf", "dev_smb", "dev_hml"]].to_numpy()
    Y = np.column_stack([0.001 * k + X @ rng.normal(0, 1, 3) + rng.normal(0, 0.01, len(X))
                         for k in range(4)])
    Z = np.column_stack([np.ones(len(X)), X])
    a, se = R._intercept_t_matrix(Y, Z, 4)
    for j in range(4):
        r = R.hac_ols(Y[:, j], X, lags=4)
        assert abs(a[j] - r["coef"][0]) < 1e-12 and abs(se[j] - r["se"][0]) < 1e-12


def test_cer_by_hand():
    e = np.array([0.02, -0.01, 0.03, 0.00])
    assert abs(R.cer(e, 5) - (e.mean() - 2.5 * e.var(ddof=1)) * 12) < 1e-15


def test_rolling_ahead_share_compares_cumulative_returns():
    idx = pd.date_range("2010-01-31", periods=24, freq="ME")
    x = pd.Series(0.02, index=idx)
    b = pd.Series(0.01, index=idx)
    assert R.rolling_ahead_share(x, b, 12) == 1.0 and R.rolling_ahead_share(b, x, 12) == 0.0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"PASS {fn.__name__}")
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
