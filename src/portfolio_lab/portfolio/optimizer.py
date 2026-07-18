"""Multi-objective portfolio optimizer — the unified method (info/portfolio_optimization.md).

The whole modern literature is one long argument about a single fact: optimizers amplify input
error (Michaud 1989; DeMiguel 2009: with 330 months x 21 assets we are an order of magnitude
below the ~3,000-month break-even where sample-based mean-variance reliably beats 1/N). This
module is built around that fact, in five stages:

1. ESTIMATE DEFENSIVELY — Ledoit-Wolf shrunk covariance (portfolio/shrinkage.py, delta*
   reported); the only expected-return vector any objective sees is the Black-Litterman
   posterior mu_BL (portfolio/views.py), never raw historical means.
2. ANCHOR ON STRUCTURE — the neutral portfolio is ERC on the shrunk covariance; 1/N, HRP and
   min-variance are computed on every run as honesty benchmarks (portfolio/anchors.py).
3. OPINIONS TILT, PROPORTIONAL TO CONFIDENCE — regime views weighted by the Markov outlook's
   calibrated probabilities update Pi into mu_BL. No views => the optimizer returns the anchor.
4. PREFERENCES SELECT ALONG THE FRONTIER — the user states importances for Return / Risk /
   Diversification (+ an optional per-quadrant regime row, or the maximin mode). Each objective
   is normalized to a 0-100 score on its own attainable range over the capped simplex (its
   "utopia" and "nadir"), so a 5/5 mix is genuinely balanced and every recommendation ships
   with a scorecard. Solved by multi-start SLSQP. Constraints are statistics, not apologies
   (Jagannathan-Ma): default 40% sleeve cap; min-sleeves enforced THROUGH the cap (a cap of c
   forces >= ceil(1/c) sleeves).
5. JUDGE LIKE A SKEPTIC — risk contributions, per-quadrant breakdown, corner warnings, the
   benchmark table, scenario validation and the walk-forward backtest (portfolio/validation.py)
   ship with every output. The label is "historically optimal under your priorities," never a
   forecast.

Objectives (all maximized, all on the 21-series common monthly window):
- return:          w' mu_BL                                  (monthly arithmetic; display ann.)
- risk:            -annualized vol from the shrunk covariance (default), or the empirical
                   max drawdown of the blended constant-mix path (risk_metric="maxdd")
- diversification: mean effective number of look-through bets = average over sector / country /
                   stock of 1/HHI_dim(w), where HHI_dim(w) = w' (A_dim A_dim') w is the exact
                   look-through Herfindahl (A_dim = per-index exposure fractions; stock dim is
                   a lower bound, top-10 holdings only — CLAUDE.md caveat #4)
- regime row:      sum_q importance_q * score_q(w' mu_q), each quadrant normalized on its own
                   attainable range so importances compare like-for-like across quadrants
- maximin MODE:    max_w min_q w' mu_q via the epigraph reformulation (max z s.t. w' mu_q >= z)
                   — All Weather's philosophy on our four quadrants; targets exactly where
                   Ang-Bekaert located the value of regime awareness (not being destroyed in
                   the bad state)

Degenerate honesty: all importances zero => you get the ERC anchor back, by construction.
Macro-dependent pieces (views, regime row, maximin) degrade gracefully when the macro-state
outputs are absent (e.g. after --no-macro): mu_BL falls back to Pi and regime modes error
clearly instead of silently optimizing on nothing.

Run:  python -m portfolio_lab.portfolio.optimizer --return 5 --risk 5 --div 5
      python -m portfolio_lab.portfolio.optimizer --maximin
"""
from __future__ import annotations
import argparse

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from portfolio_lab import config as C
from portfolio_lab.analytics.engine import _perf_stats
from portfolio_lab.portfolio import anchors, views as bl
from portfolio_lab.portfolio.shrinkage import shrink_constant_correlation
from portfolio_lab.portfolio.diversification import _load_tables

ANN = 12                       # months per year
DIV_DIMS = ("sector", "country", "stock")
CORNER_TOL = 1e-4              # a weight this close to its cap counts as "at the corner"
DISPLAY_MIN_W = 0.001          # weights below 0.1% are noise, dropped from displayed output


# --------------------------------------------------------------------------- inputs

def load_returns(include_asset_classes: bool = False) -> pd.DataFrame:
    """Monthly returns of all 21 series on the common window (same window the analytics use).

    include_asset_classes=True appends the non-equity PROXY sleeves (bond/gold/cash from
    ingest/asset_classes.py) on the same window — the all-weather OPT-IN. Equity-only stays the
    product default (house thesis: equity indices are the productive asset; other profiles can
    opt in)."""
    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    rets = lv.dropna(how="any").pct_change().dropna()
    if include_asset_classes and C.ASSET_CLASS_MONTHLY.exists():
        ac = pd.read_csv(C.ASSET_CLASS_MONTHLY, index_col=0, parse_dates=True).sort_index()
        # align by month PERIOD: equity levels stamp business month-ends (1999-01-29), the
        # proxies calendar month-ends (1999-01-31) — an exact-date join silently drops ~30%
        ac.index = ac.index.to_period("M")
        aligned = ac.reindex(rets.index.to_period("M"))
        aligned.index = rets.index
        rets = pd.concat([rets, aligned], axis=1).dropna()
    return rets


def _div_matrices(series: list[str]) -> dict[str, np.ndarray]:
    """One PSD matrix per look-through dimension with HHI_dim(w) = w' M w.

    M = A A' where A[i, j] is sleeve i's fractional exposure to category j — so the quadratic
    form is exactly the Herfindahl of the portfolio's rolled-up exposures, cheap enough to sit
    inside the optimizer loop (the roll-up itself is linear in w).
    """
    sec_by, ctry_by, stk_by, usa_idx, series_key = _load_tables()
    col_to_index = {v: k for k, v in series_key.items()}
    tables = {"sector": sec_by, "country": ctry_by, "stock": stk_by}
    mats = {}
    for dim, table in tables.items():
        expo = {}
        for col in series:
            idx_name = col_to_index.get(col)
            if idx_name is None:                 # non-equity proxy sleeve (no factsheet): it IS
                expo[col] = {col: 100.0}         # its own category in every dimension — one
                continue                         # whole independent bet, which is the truth
            w = dict(table.get(idx_name, {}))
            if dim == "country":
                if not w and idx_name in usa_idx:
                    w = {"United States": 100.0}
                w = {C.COUNTRY_FIX.get(k, k): v for k, v in w.items()}
            expo[col] = w
        cats = sorted({c for w in expo.values() for c in w})
        A = np.zeros((len(series), len(cats)))
        for i, col in enumerate(series):
            for cat, pct in expo[col].items():
                A[i, cats.index(cat)] = pct / 100.0
        mats[dim] = A @ A.T
    return mats


def _geo_matrix(series: list[str]) -> tuple[np.ndarray, list[str]]:
    """(Z, zone_names): Z[i, z] = sleeve i's LOOK-THROUGH exposure fraction to geographic zone z
    (config.OPTIMIZER_GEO_ZONES; unmapped countries -> 'Rest of world'). Zone exposure of a
    portfolio is the linear form w'Z — cheap as an optimizer constraint. Look-through matters:
    an 'EM' sleeve is mostly Asia and gets constrained as such, which a label-based cap
    would miss."""
    _, ctry_by, _, usa_idx, series_key = _load_tables()
    col_to_index = {v: k for k, v in series_key.items()}
    country_zone = {c: z for z, cs in C.OPTIMIZER_GEO_ZONES.items() for c in cs}
    zones = list(C.OPTIMIZER_GEO_ZONES) + ["Rest of world"]
    Z = np.zeros((len(series), len(zones)))
    for i, col in enumerate(series):
        idx_name = col_to_index.get(col)
        if idx_name is None:                     # non-equity proxy sleeve: zero geographic
            continue                             # exposure — geo caps constrain equity bets only
        w = dict(ctry_by.get(idx_name, {})) or ({"United States": 100.0}
                                                if idx_name in usa_idx else {})
        for c, pct in w.items():
            zone = country_zone.get(C.COUNTRY_FIX.get(c, c), "Rest of world")
            Z[i, zones.index(zone)] += pct / 100.0
    return Z, zones


def _factor_matrix(series: list[str]) -> tuple[np.ndarray, list[str]]:
    """(F, bucket_names): F[i, b] = 1 if sleeve i belongs to factor bucket b (its label after
    ' | ' — Reference/Momentum/Enhanced Value/Quality, and each non-equity proxy is its own
    bucket). Portfolio factor exposure is the linear form w'F — cheap as a constraint, closing
    the third concentration axis (sleeve, geography, FACTOR)."""
    buckets = sorted({s.split(" | ")[1] for s in series})
    F = np.zeros((len(series), len(buckets)))
    for i, s in enumerate(series):
        F[i, buckets.index(s.split(" | ")[1])] = 1.0
    return F, buckets


def _load_states(index: pd.DatetimeIndex = None) -> pd.DataFrame | None:
    """Monthly macro-state labels + soft probabilities, or None when macro outputs are absent."""
    if not C.MACRO_STATE_MONTHLY.exists():
        return None
    states = pd.read_csv(C.MACRO_STATE_MONTHLY, index_col=0, parse_dates=True).sort_index()
    return states.reindex(index).dropna(subset=["state"]) if index is not None else states


def _state_mean_returns(rets: pd.DataFrame, states: pd.DataFrame,
                        min_months: int = 3) -> pd.DataFrame:
    """Long (state, series, mean_monthly_return, n_months) — per-quadrant pooled means,
    computable on any window (walk-forward reuses this on train slices)."""
    rows = []
    for state, months in rets.index.groupby(states.state.reindex(rets.index)).items():
        sub = rets.loc[months]
        if len(sub) < min_months:
            continue
        for col in rets.columns:
            rows.append(dict(state=state, series=col,
                             mean_monthly_return=float(sub[col].mean()), n_months=len(sub)))
    return pd.DataFrame(rows)


def _anchor_mu_q(mu_q: pd.DataFrame, long_prior: dict, asset_prior: dict,
                 n_by_state: dict) -> pd.DataFrame:
    """Sleeve-level long-anchored per-quadrant means for the OBJECTIVES (mu_q_obj).

    Same rule the BL views use (agree-only, month-weighted), now applied to the maximin /
    regime-row input itself: factor sleeves blend their modern EXCESS over their region's
    Reference toward beta*f_long; proxy sleeves blend their own mean toward their 1962+
    per-quadrant mean. Reference/Quality sleeves and disagreeing cells stay modern — shrink
    toward a century of evidence, never replace it blindly."""
    mu = mu_q.copy()
    for state in mu.index:
        n_mod = int(n_by_state.get(state, 0))
        for col in mu.columns:
            region, label = col.split(" | ", 1)
            if region == "Asset" and asset_prior:
                st = (asset_prior.get(col) or {}).get(state)
                if st and st["agree"]:
                    mu.loc[state, col] = ((n_mod * mu_q.loc[state, col]
                                           + st["n_long"] * st["long_mean"])
                                          / (n_mod + st["n_long"]))
            elif long_prior and label in long_prior:
                ref = f"{region} | Reference"
                if ref not in mu.columns:
                    continue
                st = long_prior[label]["states"].get(state)
                if st and st["agree"]:
                    e_mod = float(mu_q.loc[state, col] - mu_q.loc[state, ref])
                    e = ((n_mod * e_mod + st["n_long"] * st["long_diff"])
                         / (n_mod + st["n_long"]))
                    mu.loc[state, col] = float(mu_q.loc[state, ref]) + e
    return mu


def build_inputs(rets: pd.DataFrame = None, include_asset_classes: bool = False) -> dict:
    """Everything one optimization needs, computed once (pass a sliced `rets` to rebuild on a
    training window — the walk-forward does). include_asset_classes: see load_returns."""
    rets = load_returns(include_asset_classes) if rets is None else rets
    series = list(rets.columns)
    R = rets.values
    T = len(rets)

    sigma, delta_star = shrink_constant_correlation(R)
    w_erc = anchors.erc_weights(sigma)
    anchor_set = {"1/N": anchors.equal_weight(len(series)), "ERC (anchor)": w_erc,
                  "HRP": anchors.hrp_weights(sigma), "Min-variance": anchors.min_var_weights(sigma)}

    pi, delta_ra = bl.implied_returns(sigma, w_erc, float((R @ w_erc).mean()))

    mu_q, mu_q_obj, view_descs, outlook = None, None, [], None
    mu_bl = pi.copy()
    states = _load_states(rets.index)
    if states is not None and len(states) >= C.MACRO_MIN_OVERLAP_MONTHS:
        from portfolio_lab.analytics.macro_state import transition_matrix, quadrant_outlook
        perf_long = _state_mean_returns(rets, states)
        trans = transition_matrix(states)
        outlook = quadrant_outlook(states, trans)
        try:                                    # 66y FF prior for the views (optional, clipped
            from portfolio_lab.analytics.long_history import msci_factor_prior   # to rets end)
            long_prior = msci_factor_prior(rets)
        except Exception as e:
            print(f"[optimizer] WARN long-history prior unavailable ({e}) — modern-only views")
            long_prior = None
        P, Q, conf, view_descs = bl.regime_views(series, perf_long, outlook,
                                                 long_prior=long_prior)
        mu_bl = bl.posterior(pi, sigma, T, P, Q, conf)
        mu_q = (perf_long.pivot(index="state", columns="series", values="mean_monthly_return")
                .reindex(columns=series))
        # objectives consume the long-anchored version; mu_q itself stays the empirical
        # modern record (descriptive reporting must not be blended)
        mu_q_obj = mu_q
        try:
            asset_prior = None
            if any(c.startswith("Asset | ") for c in series):
                from portfolio_lab.analytics.long_history import asset_class_prior
                asset_prior = asset_class_prior(rets)
            if long_prior or asset_prior:
                n_by_state = perf_long.groupby("state").n_months.first().to_dict()
                mu_q_obj = _anchor_mu_q(mu_q, long_prior or {}, asset_prior, n_by_state)
        except Exception as e:
            print(f"[optimizer] WARN mu_q anchoring unavailable ({e}) — modern-only objective")
    Z, zones = _geo_matrix(series)
    F, buckets = _factor_matrix(series)
    return dict(rets=rets, series=series, T=T, sigma=sigma, delta_star=delta_star,
                anchors=anchor_set, w_anchor=w_erc, pi=pi, delta_ra=delta_ra, mu_bl=mu_bl,
                mu_q=mu_q, mu_q_obj=mu_q_obj, outlook=outlook, view_descs=view_descs,
                div_mats=_div_matrices(series), geo_Z=Z, geo_zones=zones,
                factor_F=F, factor_buckets=buckets)


# --------------------------------------------------------------------------- blended-path stats

def blended_level(rets: pd.DataFrame, w: np.ndarray) -> pd.Series:
    """Constant-mix (monthly-rebalanced) level series rebased to 100 — same construction as
    portfolio/diversification.py's portfolio_performance, on the common window."""
    growth = 1.0 + rets.values @ w
    level = 100.0 * np.concatenate([[1.0], np.cumprod(growth)])
    idx = [rets.index[0] - pd.offsets.MonthEnd(1)] + list(rets.index)
    return pd.Series(level, index=pd.DatetimeIndex(idx))


def empirical_cagr(R: np.ndarray, w: np.ndarray) -> float:
    growth = 1.0 + R @ w
    return float(np.prod(growth) ** (ANN / len(R)) - 1.0)


def empirical_maxdd(R: np.ndarray, w: np.ndarray) -> float:
    cum = np.cumprod(1.0 + R @ w)
    return float((cum / np.maximum.accumulate(cum) - 1.0).min())


# --------------------------------------------------------------------------- objectives

def _objective_fns(inp: dict, risk_metric: str) -> dict:
    """Raw objective callables, all 'bigger is better'."""
    R, sigma, mu_bl, mats = inp["rets"].values, inp["sigma"], inp["mu_bl"], inp["div_mats"]
    fns = {"return": lambda w: float(w @ mu_bl)}
    if risk_metric == "vol":
        fns["risk"] = lambda w: -float(np.sqrt(max(w @ sigma @ w, 0.0)) * np.sqrt(ANN))
    elif risk_metric == "maxdd":
        fns["risk"] = lambda w: empirical_maxdd(R, w)      # negative; shallower = bigger
    else:
        raise ValueError(f"unknown risk_metric {risk_metric!r} (vol | maxdd)")
    # geometric mean of the per-dimension effective bets (1/HHI): scale-free, so no dimension
    # dominates — stock-level bets run ~100x sector-level (top-10-only exposures make stock HHI
    # tiny; caveat #4) and an arithmetic mean would optimize stock spread almost exclusively
    fns["diversification"] = lambda w: float(np.exp(np.mean(
        [-np.log(max(float(w @ M @ w), 1e-12)) for M in mats.values()])))
    return fns


def effective_bets_by_dim(w: np.ndarray, mats: dict) -> dict:
    """Per-dimension effective number of look-through bets, 1/HHI_dim(w) — the display version
    of the diversification objective."""
    return {dim: 1.0 / max(float(w @ M @ w), 1e-12) for dim, M in mats.items()}


def _linear_extreme(mu: np.ndarray, cap: float, maximize: bool) -> float:
    """Exact utopia/nadir of a linear objective on the capped simplex: fill the cap greedily
    from the best (or worst) entries down."""
    order = np.argsort(mu)[::-1] if maximize else np.argsort(mu)
    left, val = 1.0, 0.0
    for i in order:
        take = min(cap, left)
        val += take * mu[i]
        left -= take
        if left <= 1e-12:
            break
    return float(val)


def _solve_extreme(fn, n: int, cap: float, maximize: bool, n_starts: int, rng) -> float:
    """Utopia/nadir of a nonlinear objective on the capped simplex (multi-start SLSQP)."""
    sign = -1.0 if maximize else 1.0
    best = None
    for w0 in _starts(n, cap, n_starts, rng):
        res = minimize(lambda w: sign * fn(w), w0, method="SLSQP",
                       bounds=[(0.0, cap)] * n,
                       constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
                       options={"maxiter": 300, "ftol": 1e-10})
        if res.success or res.status == 8:                  # 8 = positive directional derivative
            v = fn(res.x)
            if best is None or (v > best if maximize else v < best):
                best = v
    if best is None:
        raise RuntimeError("utopia/nadir solve failed on all starts")
    return float(best)


def _starts(n: int, cap: float, n_starts: int, rng) -> list[np.ndarray]:
    """Feasible starting points: equal weight + Dirichlet draws pushed under the cap."""
    starts = [np.full(n, 1.0 / n)]
    for _ in range(n_starts):
        w = rng.dirichlet(np.ones(n))
        for _ in range(50):                                  # clip-renormalize until under cap
            w = np.minimum(w, cap)
            s = w.sum()
            if s >= 1.0 - 1e-12:
                w = w / s
                break
            w = w / s
        starts.append(np.minimum(w, cap))
    return starts


def _normalize_ranges(inp: dict, active: list[str], regime_weights: dict, risk_metric: str,
                      cap: float, n_starts: int, rng) -> dict:
    """(nadir, utopia) per active objective — the attainable range over the capped simplex.
    Linear objectives (return, each quadrant) are exact greedy; the rest multi-start SLSQP."""
    n, fns = len(inp["series"]), _objective_fns(inp, risk_metric)
    ranges = {}
    for name in active:
        if name == "return":
            ranges[name] = (_linear_extreme(inp["mu_bl"], cap, False),
                            _linear_extreme(inp["mu_bl"], cap, True))
        elif name == "regime":
            for state in regime_weights:
                mu_s = _objective_mu_q(inp).loc[state].values
                ranges[f"regime:{state}"] = (_linear_extreme(mu_s, cap, False),
                                             _linear_extreme(mu_s, cap, True))
        else:
            ranges[name] = (_solve_extreme(fns[name], n, cap, False, n_starts, rng),
                            _solve_extreme(fns[name], n, cap, True, n_starts, rng))
    return ranges


def _objective_mu_q(inp: dict) -> pd.DataFrame:
    """The per-quadrant means the OBJECTIVES consume: the long-anchored version when available
    (see _anchor_mu_q), else the modern empirical one. Reporting always uses inp['mu_q']."""
    obj = inp.get("mu_q_obj")
    return obj if obj is not None else inp["mu_q"]


def _score(value: float, rng_pair: tuple) -> float:
    lo, hi = rng_pair
    if hi - lo < 1e-15:
        return 100.0
    return 100.0 * (value - lo) / (hi - lo)


# --------------------------------------------------------------------------- optimize

def optimize(prefs: dict = None, regime_weights: dict = None, maximin: bool = False,
             risk_metric: str = "vol", cap: float = None, min_sleeves: int = None,
             target: tuple = None, geo_cap: float = None, factor_cap: float = None,
             inputs: dict = None, n_starts: int = None, seed: int = None) -> dict:
    """One optimization run.

    prefs           {"return": 0-10, "risk": 0-10, "diversification": 0-10, "regime": 0-10} —
                    relative importances (any nonnegative scale; normalized internally).
                    All zero/None => the ERC anchor is returned as-is.
    regime_weights  {state: importance} for the regime row (used when prefs["regime"] > 0).
    maximin         True => ignore prefs and solve max_w min_q w' mu_q (robust-across-quadrants).
    risk_metric     "vol" (shrunk-covariance, default) or "maxdd" (empirical blended path).
    cap             per-sleeve cap as a fraction (default config.OPTIMIZER_MAX_SLEEVE_PCT).
    min_sleeves     enforced through the cap: effective cap = min(cap, 1/min_sleeves).
    target          optional hard target: ("cagr", 0.12) = blended historical CAGR >= 12%/yr,
                    or ("maxdd", 0.30) = blended historical max drawdown no deeper than -30%.
    geo_cap         optional cap (fraction) on the LOOK-THROUGH exposure to each geographic
                    zone (config.OPTIMIZER_GEO_ZONES). Forces geographic spread while the
                    objective still picks the best sleeves *within* each zone — diversification
                    by constraint, never "investing somewhere just because".
    factor_cap      optional cap (fraction) on the exposure to each factor bucket (the sleeve
                    label: Reference/Momentum/Enhanced Value/Quality, each proxy its own) —
                    closes the third concentration axis (an all-Enhanced-Value maximin is a
                    single-factor bet even when geographically spread).
    """
    inp = inputs or build_inputs()
    n, series, R = len(inp["series"]), inp["series"], inp["rets"].values
    cap = cap if cap is not None else C.OPTIMIZER_MAX_SLEEVE_PCT / 100.0
    min_sleeves = min_sleeves if min_sleeves is not None else C.OPTIMIZER_MIN_SLEEVES
    # a cap c forces at least ceil(1/c) sleeves; to force >= m sleeves the cap must be < 1/(m-1)
    # (the default 40% cap already forces >= 3 on its own: 2 x 40% < 100%)
    cap_eff = min(cap, (1.0 - 1e-9) / (min_sleeves - 1)) if min_sleeves and min_sleeves > 1 else cap
    n_starts = n_starts if n_starts is not None else C.OPTIMIZER_N_STARTS
    rng = np.random.default_rng(C.OPTIMIZER_SEED if seed is None else seed)
    warnings = []

    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    if geo_cap is not None:
        Z, zones = inp["geo_Z"], inp["geo_zones"]
        # feasibility: total exposure ~1 must fit under the caps (sum of caps >= 1)
        if geo_cap * len(zones) < 1.0 - 1e-9:
            raise ValueError(f"geo_cap {geo_cap:.0%} x {len(zones)} zones cannot hold 100%")
        for z in range(len(zones)):
            cons.append({"type": "ineq", "fun": (lambda w, z=z: geo_cap - float(w @ Z[:, z]))})
    if factor_cap is not None:
        F, buckets = inp["factor_F"], inp["factor_buckets"]
        if factor_cap * len(buckets) < 1.0 - 1e-9:
            raise ValueError(f"factor_cap {factor_cap:.0%} x {len(buckets)} buckets cannot hold 100%")
        for b in range(len(buckets)):
            cons.append({"type": "ineq", "fun": (lambda w, b=b: factor_cap - float(w @ F[:, b]))})
    if target is not None:
        kind, x = target
        if kind == "cagr":
            cons.append({"type": "ineq", "fun": lambda w: empirical_cagr(R, w) - x})
        elif kind == "maxdd":
            cons.append({"type": "ineq", "fun": lambda w: empirical_maxdd(R, w) + abs(x)})
        else:
            raise ValueError(f"unknown target kind {kind!r} (cagr | maxdd)")

    if maximin:
        if inp["mu_q"] is None:
            raise ValueError("maximin needs the macro-state outputs (run the pipeline with macro)")
        w, diag = _solve_maximin(inp, cap_eff, cons, n_starts, rng)
        mode = "maximin"
    else:
        prefs = {k: float(v) for k, v in (prefs or {}).items() if v}
        if prefs.get("regime") and (inp["mu_q"] is None or not regime_weights):
            raise ValueError("regime preference needs macro-state outputs and regime_weights")
        if not prefs:
            w, diag, mode = inp["w_anchor"].copy(), {"note": "no preferences — ERC anchor"}, "anchor"
        else:
            if regime_weights:
                tot = sum(regime_weights.values())
                regime_weights = {k: v / tot for k, v in regime_weights.items()
                                  if k in inp["mu_q"].index}
            w, diag = _solve_blend(inp, prefs, regime_weights or {}, risk_metric,
                                   cap_eff, cons, n_starts, rng)
            mode = "blend"

    # --- guardrails / honesty checks -------------------------------------
    if target is not None:
        kind, x = target
        tol = 1e-4                       # 0.01pp — SLSQP satisfies constraints to ftol, not exactly
        ok = (empirical_cagr(R, w) >= x - tol if kind == "cagr"
              else empirical_maxdd(R, w) >= -abs(x) - tol)
        if not ok:
            warnings.append(f"HARD TARGET NOT ACHIEVABLE: {kind} {x:.1%} is outside the feasible "
                            "set under the current caps — showing the closest attempt.")
    at_cap = [series[i] for i in range(n) if w[i] >= cap_eff - CORNER_TOL]
    n_sleeves = int((w > 0.01).sum())
    if at_cap or n_sleeves <= int(np.ceil(1.0 / cap_eff)):
        warnings.append("CORNER SOLUTION: weights sit at the constraint caps "
                        f"({', '.join(at_cap) if at_cap else f'only {n_sleeves} sleeves'}). "
                        "This is a bet on one index's past, not an allocation — the caps are "
                        "doing the diversifying, not the preferences.")

    return _package(inp, w, mode, risk_metric, diag, warnings)


def _solve_blend(inp, prefs, regime_weights, risk_metric, cap, cons, n_starts, rng):
    """Maximize the importance-weighted sum of normalized objective scores."""
    fns = _objective_fns(inp, risk_metric)
    active = [k for k in ("return", "risk", "diversification", "regime") if prefs.get(k)]
    ranges = _normalize_ranges(inp, active, regime_weights, risk_metric, cap,
                               max(6, n_starts // 6), rng)
    tot = sum(prefs[k] for k in active)
    imp = {k: prefs[k] / tot for k in active}
    mu_q = _objective_mu_q(inp)

    def total_score(w):
        s = 0.0
        for k in active:
            if k == "regime":
                s += imp[k] * sum(rw * _score(float(w @ mu_q.loc[st].values),
                                              ranges[f"regime:{st}"])
                                  for st, rw in regime_weights.items())
            else:
                s += imp[k] * _score(fns[k](w), ranges[k])
        return s

    w = _multistart(lambda w: -total_score(w), len(inp["series"]), cap, cons, n_starts, rng,
                    prefer=inp["w_anchor"])
    scorecard = {}
    for k in active:
        if k == "regime":
            scorecard[k] = sum(rw * _score(float(w @ mu_q.loc[st].values), ranges[f"regime:{st}"])
                               for st, rw in regime_weights.items())
        else:
            scorecard[k] = _score(fns[k](w), ranges[k])
    return w, {"ranges": ranges, "importances": imp, "scorecard": scorecard}


def _solve_maximin(inp, cap, cons, n_starts, rng):
    """Epigraph reformulation: variables (w, z), maximize z s.t. w' mu_q >= z for every state.
    Consumes the long-anchored per-quadrant means when available (_objective_mu_q)."""
    mu_q = _objective_mu_q(inp)
    n = len(inp["series"])
    states = list(mu_q.index)
    M = mu_q.values

    def unpack(x):
        return x[:n], x[n]

    epi_cons = ([{"type": "eq", "fun": lambda x: x[:n].sum() - 1.0}]
                + [{"type": "ineq", "fun": (lambda x, i=i: float(x[:n] @ M[i]) - x[n])}
                   for i in range(len(states))]
                + [{**c, "fun": (lambda x, f=c["fun"]: f(x[:n]))} for c in cons
                   if c["type"] == "ineq"])
    best_x, best_v = None, -np.inf
    for w0 in _starts(n, cap, n_starts, rng):
        x0 = np.concatenate([w0, [float((M @ w0).min())]])
        res = minimize(lambda x: -x[n], x0, method="SLSQP",
                       bounds=[(0.0, cap)] * n + [(-1.0, 1.0)],
                       constraints=epi_cons, options={"maxiter": 500, "ftol": 1e-12})
        w, z = unpack(res.x)
        if (res.success or res.status == 8) and abs(w.sum() - 1.0) < 1e-6:
            v = float((M @ w).min())
            if v > best_v:
                best_v, best_x = v, w.copy()
    if best_x is None:
        raise RuntimeError("maximin solve failed on all starts")
    return best_x, {"worst_quadrant_monthly": best_v,
                    "per_quadrant_monthly": dict(zip(states, (M @ best_x).tolist()))}


def _multistart(neg_obj, n, cap, cons, n_starts, rng, prefer=None):
    starts = _starts(n, cap, n_starts, rng)
    if prefer is not None and np.all(prefer <= cap + 1e-9):
        starts.insert(0, np.minimum(prefer, cap) / np.minimum(prefer, cap).sum())
    best_w, best_v = None, np.inf
    for w0 in starts:
        res = minimize(neg_obj, w0, method="SLSQP", bounds=[(0.0, cap)] * n,
                       constraints=cons, options={"maxiter": 500, "ftol": 1e-10})
        if (res.success or res.status == 8) and abs(res.x.sum() - 1.0) < 1e-6:
            v = neg_obj(res.x)
            if v < best_v:
                best_v, best_w = v, np.clip(res.x, 0.0, cap)
    if best_w is None:
        raise RuntimeError("optimization failed on all starts")
    return best_w / best_w.sum()


# --------------------------------------------------------------------------- packaging

def _package(inp, w, mode, risk_metric, diag, warnings) -> dict:
    """Everything the transparency principle demands, for one portfolio."""
    series, sigma, R = inp["series"], inp["sigma"], inp["rets"].values
    fns = _objective_fns(inp, risk_metric)
    rc = anchors.risk_contributions(w, sigma)
    perf = _perf_stats(blended_level(inp["rets"], w))
    per_quadrant = (None if inp["mu_q"] is None else
                    {st: float(w @ inp["mu_q"].loc[st].values) for st in inp["mu_q"].index})
    weights = {series[i]: float(w[i]) for i in range(len(series)) if w[i] >= DISPLAY_MIN_W}
    geo_exposure = {z: float(w @ inp["geo_Z"][:, j]) for j, z in enumerate(inp["geo_zones"])}
    factor_exposure = {b: float(w @ inp["factor_F"][:, j])
                       for j, b in enumerate(inp["factor_buckets"])
                       if float(w @ inp["factor_F"][:, j]) >= DISPLAY_MIN_W}
    return dict(
        mode=mode, weights=weights, w=w, all_series=list(series), performance=perf,
        geo_exposure=geo_exposure, factor_exposure=factor_exposure,
        objective_values={"return_monthly_mu_bl": fns["return"](w),
                          "risk": fns["risk"](w),
                          "effective_bets": fns["diversification"](w),
                          "effective_bets_by_dim": effective_bets_by_dim(w, inp["div_mats"])},
        risk_contributions={series[i]: float(rc[i]) for i in range(len(series))
                            if w[i] >= DISPLAY_MIN_W},
        per_quadrant_monthly=per_quadrant, warnings=warnings, diagnostics=diag,
        delta_star=inp["delta_star"], delta_ra=inp["delta_ra"],
        view_descriptions=inp["view_descs"], outlook=inp["outlook"],
    )


def benchmark_table(inp: dict) -> pd.DataFrame:
    """CAGR/vol/Sharpe/maxDD of 1/N, ERC, HRP, min-variance on the common window — the
    mandatory comparison row shown next to every recommendation."""
    rows = []
    for name, w in inp["anchors"].items():
        p = _perf_stats(blended_level(inp["rets"], w))
        rows.append(dict(portfolio=name, CAGR=p["CAGR"], ann_vol=p["ann_vol"],
                         sharpe_rf0=p["sharpe_rf0"], max_drawdown=p["max_drawdown"],
                         n_sleeves=int((w > 0.01).sum())))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- profiles (A4)

def run_profiles(inp: dict = None) -> dict:
    """The preference layer made concrete (config.OPTIMIZER_PROFILES): each profile is a
    constraint preset; for each we solve the best portfolio WITHIN it and its unrestricted
    TWIN, so the report can state what the profile's guardrails cost — and buy. Returns
    {profile: {res, twin, twin_label}}."""
    div_kw = dict(cap=C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT / 100.0,
                  geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0,
                  factor_cap=C.OPTIMIZER_FACTOR_CAP_PCT / 100.0)
    inp_eq = inp or build_inputs()
    inputs_cache = {False: inp_eq}
    out = {}
    for name, spec in C.OPTIMIZER_PROFILES.items():
        aw = spec["include_asset_classes"]
        if aw and not C.ASSET_CLASS_MONTHLY.exists():
            continue
        if aw not in inputs_cache:
            inputs_cache[aw] = build_inputs(include_asset_classes=True)
        pinp = inputs_cache[aw]
        if spec["kwargs"].get("maximin") and pinp["mu_q"] is None:
            continue
        try:
            out[name] = dict(
                res=optimize(inputs=pinp, **spec["kwargs"], **div_kw),
                twin=optimize(inputs=pinp, **spec["kwargs"]),
                twin_label=spec["twin"])
        except Exception as e:
            print(f"[optimizer] WARN profile {name!r} skipped ({e})")
    return out


def _profiles_section(profiles: dict) -> list[str]:
    L = ["## User profiles — the price of preferences", "",
         "Preferences are personal; their COST is measurable. Each profile is a constraint "
         "preset (sleeve ≤25%, geo ≤40%, factor ≤40% — the diversified family) around a "
         "stated objective; its 'unrestricted twin' drops the caps. The delta line is what "
         "the guardrails cost in headline CAGR — and what they buy in concentration, "
         "drawdown and floor. In-sample numbers; the same caps IMPROVED out-of-sample "
         "results in every test we ran (see the walk-forward and A2).", ""]
    for name, p in profiles.items():
        r, t = p["res"]["performance"], p["twin"]["performance"]
        rw, tw = p["res"], p["twin"]
        floor = (min(rw["per_quadrant_monthly"].values())
                 if rw["per_quadrant_monthly"] else None)
        tfloor = (min(tw["per_quadrant_monthly"].values())
                  if tw["per_quadrant_monthly"] else None)
        L += [f"### {name}", "",
              "| | CAGR | vol | maxDD | sleeves | worst quadrant (mo) |", "|---|---|---|---|---|---|",
              f"| profile | {r['CAGR']:.2%} | {r['ann_vol']:.2%} | {r['max_drawdown']:.1%} | "
              f"{len(rw['weights'])} | " + (f"{floor:+.2%} |" if floor is not None else "— |"),
              f"| twin ({p['twin_label']}) | {t['CAGR']:.2%} | {t['ann_vol']:.2%} | "
              f"{t['max_drawdown']:.1%} | {len(tw['weights'])} | "
              + (f"{tfloor:+.2%} |" if tfloor is not None else "— |")]
        L += [f"", f"Price of the guardrails: {r['CAGR'] - t['CAGR']:+.2%} CAGR for "
              f"{r['ann_vol'] - t['ann_vol']:+.2%} vol and "
              f"{len(rw['weights']) - len(tw['weights']):+d} sleeves of spread.", ""]
    return L


# --------------------------------------------------------------------------- pipeline stage

def run():
    """Zero-touch pipeline stage: anchor + benchmarks + the two flagship portfolios (balanced
    sliders, maximin), each with its scorecard, risk contributions, per-quadrant breakdown and
    scenario cone, plus the walk-forward table. Degrades gracefully without macro outputs."""
    C.ensure_dirs()
    inp = build_inputs()
    bench = benchmark_table(inp)

    portfolios = {"Balanced sliders (5/5/5)": optimize(
        prefs={"return": 5, "risk": 5, "diversification": 5}, inputs=inp)}
    if inp["mu_q"] is not None and len(inp["mu_q"]) >= 2:
        # unconstrained maximin kept as the pedagogical exhibit of the corner problem; the
        # DIVERSIFIED preset (sleeve/geo/factor caps = implicit shrinkage on all three
        # concentration axes) is the recommended robust mode
        div_kw = dict(cap=C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT / 100.0,
                      geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0,
                      factor_cap=C.OPTIMIZER_FACTOR_CAP_PCT / 100.0)
        portfolios["Maximin (worst quadrant)"] = optimize(maximin=True, inputs=inp)
        portfolios["Maximin (diversified)"] = optimize(maximin=True, inputs=inp, **div_kw)
        if C.ASSET_CLASS_MONTHLY.exists():       # the all-weather OPT-IN (equity-only default)
            try:
                inp_aw = build_inputs(include_asset_classes=True)
                if inp_aw["mu_q"] is not None:
                    portfolios["Maximin (all-weather: +bonds/gold/cash)"] = optimize(
                        maximin=True, inputs=inp_aw, **div_kw)
            except Exception as e:
                print(f"[optimizer] WARN all-weather flagship skipped ({e})")

    cones = {}
    if C.MACRO_STATE_MONTHLY.exists():
        from portfolio_lab.analytics.scenario import build_universe, portfolio_cone
        uni = build_universe()
        uni_ext = None
        for name, res in portfolios.items():
            full_w = dict(zip(res["all_series"], (float(x) for x in res["w"])))
            full_w = {s: v for s, v in full_w.items() if v > 0}
            if set(full_w) <= set(uni["series"]):
                cones[name] = portfolio_cone(full_w, uni=uni)
                continue
            if uni_ext is None:              # extended universe for proxy-holding portfolios
                try:
                    uni_ext = build_universe(include_asset_classes=True)
                except Exception as e:
                    print(f"[optimizer] WARN extended scenario universe unavailable ({e})")
                    uni_ext = {}
            if uni_ext and set(full_w) <= set(uni_ext["series"]):
                cones[name] = portfolio_cone(full_w, uni=uni_ext)

    from portfolio_lab.portfolio.validation import walk_forward
    wf_summary, wf_meta, wf_monthly = walk_forward()
    wf_summary.to_csv(C.OPTIMIZER_WALKFORWARD, index=False)
    wf_monthly.to_csv(C.OPTIMIZER_WALKFORWARD_RETURNS)   # cached for portfolio/visualize.py

    profiles = run_profiles(inp)

    rows = [dict(portfolio=name, series=s, weight=w)
            for name, res in portfolios.items() for s, w in res["weights"].items()]
    pd.DataFrame(rows).to_csv(C.OPTIMIZER_PORTFOLIOS, index=False)
    _write_report(inp, bench, portfolios, cones, wf_summary, wf_meta, profiles)
    print(f"[optimizer] wrote {C.OPTIMIZER_REPORT} and {C.OPTIMIZER_PORTFOLIOS}")


def _md_table(df: pd.DataFrame, fmts: dict) -> list[str]:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(fmts.get(c, "{}").format(r[c]) for c in cols) + " |")
    return lines


def _write_report(inp, bench, portfolios, cones, wf_summary, wf_meta, profiles=None):
    rets = inp["rets"]
    L = ["# Portfolio optimizer — default report", ""]
    L += [f"Common window **{rets.index[0].date()} → {rets.index[-1].date()}** "
          f"({inp['T']} months × {len(inp['series'])} series). "
          f"Covariance: Ledoit-Wolf constant-correlation shrinkage, **δ\\* = "
          f"{inp['delta_star']:.3f}** (0 = sample matrix was fine, 1 = it was noise). "
          f"Anchor: ERC on the shrunk covariance (risk-aversion δ = {inp['delta_ra']:.2f}, "
          "calibrated so the anchor's implied return matches its own history).", ""]
    L += ["**Label: every portfolio below is _historically optimal under its stated "
          "priorities_ — not a forecast.** The method is documented in "
          "info/portfolio_optimization.md; the evidence behind it in info/literature.md.", ""]

    L += ["## Benchmarks (always on screen — DeMiguel 2009)", ""]
    L += _md_table(bench, {"CAGR": "{:.2%}", "ann_vol": "{:.2%}", "sharpe_rf0": "{:.2f}",
                           "max_drawdown": "{:.1%}"})
    L += [""]
    if inp["view_descs"]:
        L += ["## Active regime views (Black-Litterman tilt on the anchor)", ""]
        L += [f"3-month Markov outlook: " + ", ".join(
              f"{k.split(' (')[0]} {v:.0%}" for k, v in inp["outlook"].items()), ""]
        for v in inp["view_descs"]:
            anchored = v.get("long_anchored_states", 0)
            note = (f"; Q anchored on 66y Fama-French history in {anchored}/4 quadrants "
                    f"(β={v['long_beta']})" if anchored else "; modern sample only")
            L += [f"- {v['view']}: expected monthly excess {v['q_monthly']:+.3%} at "
                  f"confidence {v['confidence']:.0%} — tilts exactly that hard, no harder{note}"]
        L += [""]
    else:
        L += ["_No macro-state outputs found — μ_BL = Π (pure anchor-implied returns), regime "
              "modes unavailable. Run the pipeline with macro to enable them._", ""]

    for name, res in portfolios.items():
        L += [f"## {name}", ""]
        p = res["performance"]
        L += [f"Historical (common window): CAGR **{p['CAGR']:.2%}**, vol {p['ann_vol']:.2%}, "
              f"Sharpe {p['sharpe_rf0']:.2f}, maxDD {p['max_drawdown']:.1%}."]
        sc = res["diagnostics"].get("scorecard")
        if sc:
            L += ["Scorecard (0–100 on each objective's attainable range): " +
                  " · ".join(f"{k} **{v:.0f}**" for k, v in sc.items())]
        by_dim = res["objective_values"]["effective_bets_by_dim"]
        L += ["Effective look-through bets: " +
              ", ".join(f"{d} {v:.1f}" for d, v in by_dim.items())]
        L += ["Look-through geographic exposure: " +
              " · ".join(f"{z} {v:.0%}" for z, v in res["geo_exposure"].items())]
        L += ["Factor exposure: " +
              " · ".join(f"{b} {v:.0%}" for b, v in res["factor_exposure"].items()), ""]
        L += ["| weight | sleeve | risk contribution (share) |", "|---|---|---|"]
        total_rc = sum(res["risk_contributions"].values()) or 1.0
        for s, w in sorted(res["weights"].items(), key=lambda kv: -kv[1]):
            L += [f"| {w:.1%} | {s.replace(' | ', ' · ')} "
                  f"| {res['risk_contributions'].get(s, 0) / total_rc:.0%} |"]
        L += [""]
        if res["per_quadrant_monthly"]:
            L += ["Per-quadrant mean monthly return: " + " · ".join(
                  f"{k.split(' (')[0]} {v:+.2%}" for k, v in res["per_quadrant_monthly"].items()),
                  ""]
        if name in cones:
            c = cones[name]
            L += [f"Scenario cone (current_conditions, {c['years']}y, re-sequenced history — "
                  f"not a forecast): CAGR p5 {c['cagr_p5']:.1%} / p50 {c['cagr_p50']:.1%} / "
                  f"p95 {c['cagr_p95']:.1%}; maxDD p50 {c['maxdd_p50']:.1%}; "
                  f"P(cumulative loss) {c['prob_cumulative_loss']:.1%}.", ""]
        for wmsg in res["warnings"]:
            L += [f"> ⚠ {wmsg}", ""]

    if profiles:
        L += _profiles_section(profiles)

    L += ["## Walk-forward out-of-sample (the honesty table)", ""]
    L += [f"Expanding window, warmup {wf_meta['warmup_months']}m, refit every "
          f"{wf_meta['refit_months']}m; OOS {wf_meta['oos_start']} → {wf_meta['oos_end']} "
          f"({wf_meta['oos_months']} months, {wf_meta['n_refits']} refits). Everything is "
          "re-estimated on the training window only (the macro-state labels keep the "
          "classifier's mild full-sample z-normalization — CLAUDE.md caveat #17). Returns are "
          f"**net of {wf_meta.get('tc_bps', 0):.0f} bps** transaction cost on one-way turnover "
          "(`oos_sharpe_gross` is before costs); rule-based contestants (momentum, "
          "vol-target — `portfolio/rules.py`) are tested alongside the portfolios.", ""]
    L += _md_table(wf_summary, {"oos_CAGR": "{:.2%}", "oos_ann_vol": "{:.2%}",
                                "oos_sharpe_rf0": "{:.2f}", "oos_max_drawdown": "{:.1%}",
                                "oos_sharpe_gross": "{:.2f}",
                                "mean_turnover_per_refit": "{:.1%}"})
    best = wf_summary.iloc[0].portfolio
    L += ["", f"Out of sample and net of costs, **{best}** had the best risk-adjusted result. "
          "As of the 2026-07 rule test, no momentum or volatility-targeting overlay beat it — "
          "vol-targeting cut drawdowns but not the Sharpe, and momentum did not clear 1/N. If a "
          "clever portfolio can't clearly beat the dumb benchmarks here, the dumb one wins — and "
          "saying so is a feature. With 330 months of data this is expected "
          "(DeMiguel 2009: break-even ≈ 3,000 months), which is exactly why preferences tilt "
          "a structural anchor instead of trusting estimated returns.", ""]
    C.OPTIMIZER_REPORT.write_text("\n".join(L))


# --------------------------------------------------------------------------- CLI

def _render(res: dict) -> str:
    lines = [f"mode: {res['mode']}   (covariance shrinkage delta* = {res['delta_star']:.3f})", ""]
    p = res["performance"]
    lines.append(f"historical (common window): CAGR {p['CAGR']:.2%}  vol {p['ann_vol']:.2%}  "
                 f"Sharpe {p['sharpe_rf0']:.2f}  maxDD {p['max_drawdown']:.1%}")
    by_dim = res["objective_values"]["effective_bets_by_dim"]
    lines.append("effective look-through bets: " +
                 "  ".join(f"{d} {v:.1f}" for d, v in by_dim.items()) +
                 f"  (geo-mean {res['objective_values']['effective_bets']:.1f})")
    lines.append("\nweights:")
    for s, v in sorted(res["weights"].items(), key=lambda kv: -kv[1]):
        lines.append(f"  {v:6.1%}  {s}   (risk contribution "
                     f"{res['risk_contributions'].get(s, 0.0):.4f})")
    lines.append("\nlook-through geographic exposure: " +
                 "  ".join(f"{z} {v:.0%}" for z, v in res["geo_exposure"].items()))
    lines.append("factor exposure: " +
                 "  ".join(f"{b} {v:.0%}" for b, v in res["factor_exposure"].items()))
    if res["per_quadrant_monthly"]:
        lines.append("\nper-quadrant mean monthly return:")
        for st, v in res["per_quadrant_monthly"].items():
            lines.append(f"  {v:+.3%}  {st}")
    for wmsg in res["warnings"]:
        lines.append(f"\nWARNING: {wmsg}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Multi-objective portfolio optimizer")
    ap.add_argument("--return", dest="ret", type=float, default=0, help="return importance 0-10")
    ap.add_argument("--risk", type=float, default=0, help="risk importance 0-10")
    ap.add_argument("--div", type=float, default=0, help="diversification importance 0-10")
    ap.add_argument("--maximin", action="store_true", help="robust-across-quadrants mode")
    ap.add_argument("--risk-metric", choices=["vol", "maxdd"], default="vol")
    ap.add_argument("--cap", type=float, default=None, help="per-sleeve cap, e.g. 0.4")
    ap.add_argument("--geo-cap", type=float, default=None,
                    help="cap on look-through exposure per geographic zone, e.g. 0.4")
    ap.add_argument("--target-cagr", type=float, default=None, help="hard target, e.g. 0.12")
    ap.add_argument("--target-maxdd", type=float, default=None, help="hard cap, e.g. 0.30")
    args = ap.parse_args()
    target = (("cagr", args.target_cagr) if args.target_cagr is not None else
              ("maxdd", args.target_maxdd) if args.target_maxdd is not None else None)
    res = optimize(prefs={"return": args.ret, "risk": args.risk, "diversification": args.div},
                   maximin=args.maximin, risk_metric=args.risk_metric, cap=args.cap,
                   target=target, geo_cap=args.geo_cap)
    print(_render(res))
    print("\nLabel: historically optimal under your priorities — not a forecast.")


if __name__ == "__main__":
    main()
