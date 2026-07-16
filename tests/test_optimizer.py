"""Unit + integration tests for the portfolio optimizer stack (shrinkage, anchors, views,
optimizer, scenario cone). The synthetic-data unit tests are the deep dives' own test lists
(info/literature/*.md); the integration tests run on the processed dataset and self-skip when it
(or the macro outputs) are absent — same convention as tests/test_pipeline.py.

Run after the pipeline:  python -m pytest tests/ -q   (or plain: python tests/test_optimizer.py)
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from portfolio_lab import config as C
from portfolio_lab.portfolio.shrinkage import shrink_constant_correlation, shrink_identity
from portfolio_lab.portfolio import anchors
from portfolio_lab.portfolio import views as bl


def _toy_returns(seed=0, n=6, T=300):
    rng = np.random.default_rng(seed)
    corr = np.kron(np.eye(2), np.full((3, 3), 0.7))
    np.fill_diagonal(corr, 1.0)
    vols = np.linspace(0.02, 0.07, n)
    return rng.multivariate_normal(np.zeros(n), corr * np.outer(vols, vols), size=T)


# --------------------------------------------------------------------------- shrinkage

def test_shrinkage_delta_in_unit_interval_and_pd():
    X = _toy_returns()
    for fn in (shrink_constant_correlation, shrink_identity):
        sigma, delta = fn(X)
        assert 0.0 <= delta <= 1.0, f"{fn.__name__}: delta* {delta} outside [0,1]"
        assert np.all(np.linalg.eigvalsh(sigma) > 0), f"{fn.__name__}: not positive-definite"
        assert np.allclose(sigma, sigma.T), f"{fn.__name__}: not symmetric"


def test_shrinkage_variants_agree_on_broad_structure():
    X = _toy_returns()
    sb, _ = shrink_constant_correlation(X)
    sa, _ = shrink_identity(X)
    # same data, mild shrinkage: entries should be close in relative terms
    assert np.abs(sb - sa).max() / np.abs(sb).max() < 0.15, "variants disagree structurally"


def test_shrinkage_identity_matches_sklearn_oracle():
    try:
        from sklearn.covariance import LedoitWolf
    except ImportError:
        return  # sklearn not installed — oracle check skipped (it is not a dependency)
    X = _toy_returns()
    ours, delta = shrink_identity(X)
    lw = LedoitWolf().fit(X)
    assert np.allclose(ours, lw.covariance_, atol=1e-10), "variant A != sklearn LedoitWolf"
    assert abs(delta - lw.shrinkage_) < 1e-10


# --------------------------------------------------------------------------- anchors

def test_erc_equals_inverse_vol_on_diagonal_sigma():
    vols = np.array([0.02, 0.03, 0.05, 0.08])
    w = anchors.erc_weights(np.diag(vols ** 2))
    iv = (1 / vols) / (1 / vols).sum()
    assert np.allclose(w, iv, atol=1e-5), "ERC on diagonal sigma must equal inverse-vol"


def test_volatility_ordering_minvar_erc_equalweight():
    sigma, _ = shrink_constant_correlation(_toy_returns())
    vol = lambda w: float(np.sqrt(w @ sigma @ w))
    v_mv = vol(anchors.min_var_weights(sigma))
    v_erc = vol(anchors.erc_weights(sigma))
    v_eq = vol(anchors.equal_weight(len(sigma)))
    assert v_mv <= v_erc + 1e-10 and v_erc <= v_eq + 1e-10, \
        f"sigma ordering violated: {v_mv} / {v_erc} / {v_eq}"


def test_hrp_two_assets_is_inverse_variance_split():
    w = anchors.hrp_weights(np.diag([0.04, 0.01]))
    assert np.allclose(w, [0.2, 0.8], atol=1e-9), f"2-asset HRP {w} != inverse-variance"


def test_hrp_permutation_invariance():
    sigma, _ = shrink_constant_correlation(_toy_returns())
    w = anchors.hrp_weights(sigma)
    rng = np.random.default_rng(3)
    for _ in range(3):
        perm = rng.permutation(len(sigma))
        w_p = anchors.hrp_weights(sigma[np.ix_(perm, perm)])
        assert np.allclose(w[perm], w_p, atol=1e-12), "HRP weights depend on input order"


def test_hrp_separates_block_diagonal_clusters():
    # two independent blocks; low-variance block should get more weight, all weights positive
    s1, s2 = np.full((2, 2), 0.8) * 0.01, np.full((3, 3), 0.8) * 0.09
    np.fill_diagonal(s1, 0.01), np.fill_diagonal(s2, 0.09)
    sigma = np.block([[s1, np.zeros((2, 3))], [np.zeros((3, 2)), s2]])
    w = anchors.hrp_weights(sigma)
    assert np.all(w > 0) and abs(w.sum() - 1) < 1e-12
    assert w[:2].sum() > w[2:].sum(), "low-variance cluster should carry more weight"


def test_all_engines_long_only_sum_to_one():
    sigma, _ = shrink_constant_correlation(_toy_returns())
    for fn in (anchors.erc_weights, anchors.hrp_weights, anchors.min_var_weights):
        w = fn(sigma)
        assert np.all(w >= -1e-12) and abs(w.sum() - 1) < 1e-9, f"{fn.__name__} broke the simplex"


def test_risk_contributions_euler_identity():
    sigma, _ = shrink_constant_correlation(_toy_returns())
    w = anchors.erc_weights(sigma)
    rc = anchors.risk_contributions(w, sigma)
    assert abs(rc.sum() - np.sqrt(w @ sigma @ w)) < 1e-12, "Euler identity violated"
    assert rc.max() - rc.min() < 1e-6, "ERC risk contributions not equal"


# --------------------------------------------------------------------------- views (BL)

def test_no_views_returns_prior_exactly():
    sigma, _ = shrink_constant_correlation(_toy_returns())
    w0 = anchors.erc_weights(sigma)
    pi, _ = bl.implied_returns(sigma, w0, anchor_mean=0.006)
    assert abs(w0 @ pi - 0.006) < 1e-15, "delta_ra calibration broken"
    assert np.allclose(bl.posterior(pi, sigma, T=300), pi), "k=0 views must leave mu_BL = Pi"


def test_posterior_monotone_in_confidence():
    sigma, _ = shrink_constant_correlation(_toy_returns())
    pi, _ = bl.implied_returns(sigma, anchors.equal_weight(len(sigma)), 0.006)
    P = np.zeros((1, len(sigma)))
    P[0, 0], P[0, 1] = 1, -1
    Q = np.array([0.02])
    gaps = [abs((P @ bl.posterior(pi, sigma, 300, P, Q, np.array([c]))).item() - Q[0])
            for c in (0.1, 0.3, 0.6, 0.9)]
    assert all(a > b for a, b in zip(gaps, gaps[1:])), "higher confidence must pull mu_BL to Q"


def test_regime_views_long_prior_blend():
    """Where eras agree the Q blends toward beta*f_long by month weights; where they disagree
    (or no prior) the modern value stands."""
    import pandas as pd
    series = ["USA | Reference", "USA | Momentum"]
    perf = pd.DataFrame([
        dict(state="S1", series="USA | Reference", mean_monthly_return=0.004, n_months=100),
        dict(state="S1", series="USA | Momentum", mean_monthly_return=0.006, n_months=100),
    ])
    outlook = {"S1": 1.0}
    # modern diff = 0.002; long prior: agree, long_diff = 0.005, n_long = 300
    prior = {"Momentum": dict(beta=0.5, states={"S1": dict(agree=True, long_diff=0.005,
                                                           n_long=300)})}
    _, Q, _, descs = bl.regime_views(series, perf, outlook, long_prior=prior)
    expected = (100 * 0.002 + 300 * 0.005) / 400
    assert abs(Q[0] - expected) < 1e-12, f"blend wrong: {Q[0]} != {expected}"
    assert descs[0]["long_anchored_states"] == 1
    # eras disagree -> modern value untouched
    prior["Momentum"]["states"]["S1"]["agree"] = False
    _, Q2, _, d2 = bl.regime_views(series, perf, outlook, long_prior=prior)
    assert abs(Q2[0] - 0.002) < 1e-12 and d2[0]["long_anchored_states"] == 0
    # no prior -> identical to modern-only
    _, Q3, _, _ = bl.regime_views(series, perf, outlook)
    assert abs(Q3[0] - 0.002) < 1e-12


def test_zero_risk_view_rejected():
    sigma, _ = shrink_constant_correlation(_toy_returns())
    pi, _ = bl.implied_returns(sigma, anchors.equal_weight(len(sigma)), 0.006)
    try:
        bl.posterior(pi, sigma, 300, np.zeros((1, len(sigma))), np.array([0.01]), np.array([0.5]))
        assert False, "zero-risk view must raise"
    except ValueError:
        pass


# --------------------------------------------------------------------------- optimizer (data)

def _inputs():
    from portfolio_lab.portfolio import optimizer as O
    return O, O.build_inputs()


def test_optimizer_zero_prefs_returns_anchor():
    if not C.LEVELS_WIDE.exists():
        return
    O, inp = _inputs()
    res = O.optimize(prefs={}, inputs=inp)
    assert np.allclose(res["w"], inp["w_anchor"]), "all-zero sliders must return the ERC anchor"
    assert res["mode"] == "anchor"


def test_optimizer_weights_sum_to_100pct():
    if not C.LEVELS_WIDE.exists():
        return
    O, inp = _inputs()
    for res in (O.optimize(prefs={"risk": 10}, inputs=inp, n_starts=8),
                O.optimize(prefs={"return": 3, "diversification": 7}, inputs=inp, n_starts=8)):
        assert abs(res["w"].sum() - 1.0) * 100 <= C.PORTFOLIO_WEIGHT_TOLERANCE_PCT
        assert np.all(res["w"] >= -1e-12), "weights must be long-only"


def test_optimizer_risk_only_approximates_min_variance():
    if not C.LEVELS_WIDE.exists():
        return
    O, inp = _inputs()
    res = O.optimize(prefs={"risk": 10}, inputs=inp, n_starts=8)
    v_res = float(np.sqrt(res["w"] @ inp["sigma"] @ res["w"]))
    v_mv = float(np.sqrt(inp["anchors"]["Min-variance"] @ inp["sigma"]
                         @ inp["anchors"]["Min-variance"]))
    assert v_res <= v_mv * 1.05, f"risk-only vol {v_res} far above min-var {v_mv}"


def test_optimizer_return_only_respects_caps_and_warns():
    if not C.LEVELS_WIDE.exists():
        return
    O, inp = _inputs()
    res = O.optimize(prefs={"return": 10}, inputs=inp, n_starts=8)
    cap = C.OPTIMIZER_MAX_SLEEVE_PCT / 100.0
    assert res["w"].max() <= cap + 1e-6, "return-only run must still respect the sleeve cap"
    assert any("CORNER" in w for w in res["warnings"]), "corner solution must be flagged"


def test_optimizer_infeasible_target_is_reported():
    if not C.LEVELS_WIDE.exists():
        return
    O, inp = _inputs()
    res = O.optimize(prefs={"risk": 10}, target=("cagr", 0.50), inputs=inp, n_starts=6)
    assert any("NOT ACHIEVABLE" in w for w in res["warnings"]), \
        "an impossible hard target must be reported, not silently dropped"


def test_maximin_beats_blend_on_worst_quadrant():
    if not (C.LEVELS_WIDE.exists() and C.MACRO_STATE_MONTHLY.exists()):
        return
    O, inp = _inputs()
    if inp["mu_q"] is None:
        return
    worst = lambda r: min(r["per_quadrant_monthly"].values())
    res_m = O.optimize(maximin=True, inputs=inp, n_starts=8)
    res_b = O.optimize(prefs={"return": 5, "risk": 5, "diversification": 5},
                       inputs=inp, n_starts=8)
    assert worst(res_m) >= worst(res_b) - 1e-9, \
        "maximin must not have a worse worst-quadrant than the blend"


def test_geo_cap_respected_and_costs_objective():
    if not (C.LEVELS_WIDE.exists() and C.MACRO_STATE_MONTHLY.exists()):
        return
    O, inp = _inputs()
    if inp["mu_q"] is None:
        return
    cap = C.OPTIMIZER_GEO_CAP_PCT / 100.0
    res_u = O.optimize(maximin=True, inputs=inp, n_starts=8)
    res_g = O.optimize(maximin=True, geo_cap=cap, inputs=inp, n_starts=8)
    for zone, v in res_g["geo_exposure"].items():
        assert v <= cap + 1e-4, f"geo cap violated: {zone} = {v:.1%}"
    worst = lambda r: min(r["per_quadrant_monthly"].values())
    assert worst(res_g) <= worst(res_u) + 1e-9, \
        "a constrained maximin cannot beat the unconstrained one in-sample"
    # infeasible cap (sum of caps < 100%) must raise, not silently relax
    try:
        O.optimize(maximin=True, geo_cap=0.20, inputs=inp, n_starts=4)
        assert False, "infeasible geo_cap must raise"
    except ValueError:
        pass


def test_all_weather_optin_lifts_the_floor():
    """The asset-class opt-in must (a) align on the same monthly window (the business-vs-
    calendar month-end trap), (b) leave equity-only untouched as the default, and (c) give
    maximin a worst-quadrant floor at least as good as equity-only (superset feasible set)."""
    if not (C.LEVELS_WIDE.exists() and C.MACRO_STATE_MONTHLY.exists()
            and C.ASSET_CLASS_MONTHLY.exists()):
        return
    O, inp_eq = _inputs()
    inp_aw = O.build_inputs(include_asset_classes=True)
    assert len(inp_aw["series"]) == len(inp_eq["series"]) + 3, "expected 3 proxy sleeves"
    assert inp_aw["T"] >= inp_eq["T"] - 3, \
        f"asset join lost months ({inp_aw['T']} vs {inp_eq['T']}) — date alignment regressed"
    if inp_aw["mu_q"] is None:
        return
    worst = lambda r: min(r["per_quadrant_monthly"].values())
    res_eq = O.optimize(maximin=True, inputs=inp_eq, n_starts=8)
    res_aw = O.optimize(maximin=True, inputs=inp_aw, n_starts=8)
    assert worst(res_aw) >= worst(res_eq) - 1e-6, \
        "all-weather maximin cannot have a worse floor than equity-only (superset of assets)"
    # proxy sleeves are exempt from geo caps (zero geographic exposure rows)
    names = inp_aw["series"]
    Z = inp_aw["geo_Z"]
    for i, s in enumerate(names):
        if s.startswith("Asset | "):
            assert abs(Z[i].sum()) < 1e-12, f"{s} should have zero geographic exposure"


def test_scenario_portfolio_cone_matches_per_series_when_one_hot():
    if not (C.LEVELS_WIDE.exists() and C.MACRO_STATE_MONTHLY.exists()):
        return
    from portfolio_lab.analytics import scenario as S
    uni = S.build_universe()
    col = uni["series"][0]
    cone = S.portfolio_cone({col: 1.0}, uni=uni, n_trials=200, seed=11)
    row = S.simulate_from_current(uni=uni, n_trials=200, seed=11)
    row = row[row.series == col].iloc[0]
    for k in ("cagr_p5", "cagr_p50", "cagr_p95", "prob_cumulative_loss"):
        assert abs(cone[k] - row[k]) < 1e-12, f"one-hot cone diverges from per-series on {k}"


def test_momentum_weights_top_k_equal_and_valid():
    import pandas as pd
    from portfolio_lab.portfolio import rules
    # 4 sleeves with clearly ordered trend; top-2 by 12-1 momentum must be the two risers
    idx = pd.date_range("2000-01-31", periods=20, freq="ME")
    df = pd.DataFrame({
        "A": 0.03, "B": 0.02, "C": -0.01, "D": -0.02}, index=idx)
    w = rules.momentum_weights(df, k=2, lookback=12, skip=1)
    assert abs(w.sum() - 1.0) < 1e-12 and np.all(w >= 0), "momentum weights must be a valid simplex"
    assert (w > 0).sum() == 2, "must hold exactly top-2"
    assert w[0] > 0 and w[1] > 0 and w[2] == 0 and w[3] == 0, "must pick the two best performers"


def test_vol_managed_is_causal_and_derisks():
    import pandas as pd
    from portfolio_lab.portfolio import rules
    rng = np.random.default_rng(0)
    # calm then turbulent: leverage should fall in the turbulent stretch, never exceed max_lev
    calm = rng.normal(0.005, 0.01, 60)
    wild = rng.normal(0.0, 0.08, 60)
    r = pd.Series(np.concatenate([calm, wild]), index=pd.date_range("2000-01-31", periods=120, freq="ME"))
    managed, extra = rules.vol_managed(r, target_ann=0.10, window=12, max_lev=1.0)
    lev = managed / r.replace(0, np.nan)
    assert lev.dropna().max() <= 1.0 + 1e-9, "unlevered overlay must never exceed leverage 1"
    # average leverage in the turbulent half must be below the calm half (it de-risks)
    assert lev.iloc[-40:].mean() < lev.iloc[15:55].mean(), "must cut exposure when vol runs hot"
    assert (extra >= 0).all(), "turnover is non-negative"


def test_walkforward_reports_gross_and_net_and_rules():
    if not (C.LEVELS_WIDE.exists() and C.MACRO_STATE_MONTHLY.exists()):
        return
    from portfolio_lab.portfolio.validation import walk_forward
    summary, meta, monthly = walk_forward(n_starts=4)
    names = set(summary.portfolio)
    assert any(n.startswith("Momentum") for n in names), "momentum contestant missing"
    assert any("vol-target" in n for n in names), "vol-target contestant missing"
    assert "oos_sharpe_gross" in summary.columns and meta["tc_bps"] > 0
    # costs can only lower (or equal) the net Sharpe vs gross
    for _, row in summary.iterrows():
        assert row.oos_sharpe_rf0 <= row.oos_sharpe_gross + 1e-9, \
            f"{row.portfolio}: net Sharpe above gross — costs applied with wrong sign"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"PASS {fn.__name__}")
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
