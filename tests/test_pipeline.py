"""Lightweight validation tests for the processed dataset and analytics.

Run after the pipeline:  python -m pytest tests/ -q   (or plain: python tests/test_pipeline.py)
These are data-integrity checks, not unit tests of internals.
"""
import sys
import csv
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from portfolio_lab import config as C


def _rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def _sums(path, key):
    s = defaultdict(float)
    for r in _rows(path):
        s[r["index_name"]] += float(r["weight_pct"])
    return s


def test_registry_files_exist_and_are_consistent():
    reg = C.load_registry()
    assert reg, "index_registry.csv is empty"
    for idx in reg:
        assert idx["region"] in C.REGIONS, f"{idx['index_id']}: unknown region {idx['region']}"
        assert idx["factor_type"] in C.FACTOR_TYPES, f"{idx['index_id']}: bad factor {idx['factor_type']}"
        if idx["source"] == "msci_api":
            cache = C.MSCI_API_CACHE_DIR / f"{idx['returns_file']}.json"
            assert cache.exists(), f"{idx['index_id']}: msci_api cache missing at {cache}"
        else:
            rf = C.RAW_DIR / idx["region"] / idx["returns_file"]
            assert rf.exists(), f"{idx['index_id']}: missing returns file {rf}"
        if idx["weights_file"]:
            wf = C.RAW_DIR / idx["region"] / idx["weights_file"]
            assert wf.exists(), f"{idx['index_id']}: missing weights file {wf}"
    # each (region, factor) is unique — that pair is the series key downstream
    keys = [(idx["region"], idx["factor_type"]) for idx in reg]
    assert len(keys) == len(set(keys)), "duplicate (region, factor_type) in registry"


def test_registry_matches_return_series():
    reg_keys = {(idx["region"], idx["factor_type"]) for idx in C.load_registry()}
    ret_keys = {(r["region"], r["factor_type"]) for r in _rows(C.RETURNS_LONG)}
    assert reg_keys == ret_keys, f"registry vs returns mismatch: {reg_keys ^ ret_keys}"


def test_sector_weights_sum_to_100():
    for idx, tot in _sums(C.SECTOR_WEIGHTS, "sector").items():
        assert 98.0 <= tot <= 102.0, f"{idx} sector weights sum to {tot:.1f}%"


def test_country_weights_sum_to_100():
    for idx, tot in _sums(C.COUNTRY_WEIGHTS, "country").items():
        assert 98.0 <= tot <= 102.0, f"{idx} country weights sum to {tot:.1f}%"


def test_ten_constituents_each():
    c = defaultdict(int)
    for r in _rows(C.TOP_CONSTITUENTS):
        c[r["index_name"]] += 1
    for idx, n in c.items():
        assert n == 10, f"{idx} has {n} constituents (expected 10)"


def test_all_registry_return_series_present():
    expected = len(C.load_registry())
    series = {(r["region"], r["factor_type"]) for r in _rows(C.RETURNS_LONG)}
    assert len(series) == expected, f"expected {expected} return series, got {len(series)}"


def test_usa_indices_have_no_country_chart():
    # USA indices are single-country; they legitimately carry no country rows
    usa = {r["index_name"] for r in _rows(C.INDEX_META) if r["region"] == "USA"}
    have = {r["index_name"] for r in _rows(C.COUNTRY_WEIGHTS)}
    assert usa.isdisjoint(have), "USA indices unexpectedly have country weights"


def test_macro_present_if_fetched():
    # macro is network-dependent (skippable); only validate when the file exists
    if not C.MACRO_MONTHLY.exists():
        return
    rows = _rows(C.MACRO_MONTHLY)
    assert rows, "macro_monthly.csv is empty"
    assert "cpi_yoy" in rows[0], "expected macro indicator columns missing"


def test_macro_link_correlations_valid():
    # structural validity of the macro-link outputs (skipped if not generated)
    if not C.MACRO_CORRELATIONS.exists():
        return
    rows = _rows(C.MACRO_CORRELATIONS)
    assert rows, "macro_correlations.csv is empty"
    for r in rows:
        if r["insufficient"] == "True":
            continue
        c = float(r["corr"])
        assert -1.0 <= c <= 1.0, f"corr out of bounds: {r['series']} vs {r['indicator']} = {c}"
        assert int(r["n"]) >= 36, f"reported pair with n<36: {r['series']} vs {r['indicator']}"


def test_macro_link_wide_matrices_shape():
    if not C.MACRO_CORR_CONTEMP_CHG.exists():
        return
    n_indicators = len(_rows(C.MACRO_META))
    for path in (C.MACRO_CORR_CONTEMP_LEVEL, C.MACRO_CORR_CONTEMP_CHG):
        rows = _rows(path)
        expected = len(C.load_registry())
        assert len(rows) == expected, f"{path.name}: expected {expected} series rows, got {len(rows)}"
        n_ind = len(rows[0]) - 1  # minus the series index column
        assert n_ind == n_indicators, f"{path.name}: expected {n_indicators} indicator cols, got {n_ind}"


def test_macro_link_per_regime_matrices_valid():
    if not C.MACRO_CORR_BY_REGIME_DIR.exists():
        return
    files = list(C.MACRO_CORR_BY_REGIME_DIR.glob("*.csv"))
    assert files, "no per-regime macro correlation matrices found"
    for f in files:
        rows = _rows(f)
        expected = len(C.load_registry())
        assert len(rows) == expected, f"{f.name}: expected {expected} series rows, got {len(rows)}"
        for r in rows:
            for k, v in r.items():
                if k == "" or v == "":
                    continue
                c = float(v)
                assert -1.0 <= c <= 1.0, f"{f.name}: corr out of bounds {k}={v}"


def test_macro_state_classification_valid():
    if not C.MACRO_STATE_MONTHLY.exists():
        return
    rows = _rows(C.MACRO_STATE_MONTHLY)
    assert rows, "macro_state_monthly.csv is empty"
    valid_states = {
        "Goldilocks (disinflationary growth)", "Reflation (overheating)",
        "Deflationary bust (recession/slowdown)", "Stagflation (growth-inflation squeeze)",
    }
    prob_cols = ("p_goldilocks", "p_reflation", "p_stagflation", "p_deflationary_bust")
    for r in rows:
        assert r["state"] in valid_states, f"unknown state label: {r['state']}"
        assert r["growth_up"] in ("True", "False"), f"non-boolean growth_up: {r['growth_up']}"
        assert r["inflation_up"] in ("True", "False"), f"non-boolean inflation_up: {r['inflation_up']}"
        # composite scores are finite and the hard label is their sign
        g, i = float(r["growth_score"]), float(r["inflation_score"])
        assert (g > 0) == (r["growth_up"] == "True"), f"growth_up inconsistent with score at {r['']}"
        assert (i > 0) == (r["inflation_up"] == "True"), f"inflation_up inconsistent with score at {r['']}"
        # the 4 soft quadrant probabilities are a distribution
        total = sum(float(r[c]) for c in prob_cols)
        assert 0.99 <= total <= 1.01, f"quadrant probs sum to {total} at {r['']}"
        for c in prob_cols:
            assert 0.0 <= float(r[c]) <= 1.0, f"{c} out of [0,1] at {r['']}"


def test_macro_state_transition_matrix_valid():
    if not C.MACRO_STATE_TRANSITIONS.exists():
        return
    rows = _rows(C.MACRO_STATE_TRANSITIONS)
    assert len(rows) == 4, f"expected 4 transition rows, got {len(rows)}"
    for r in rows:
        probs = [float(v) for k, v in r.items() if k not in ("", "from")]
        assert all(0.0 <= p <= 1.0 for p in probs), f"transition prob out of bounds: {r}"
        assert 0.99 <= sum(probs) <= 1.01, f"transition row sums to {sum(probs)}: {r}"


def test_macro_state_performance_valid():
    if not C.MACRO_STATE_PERFORMANCE.exists():
        return
    rows = _rows(C.MACRO_STATE_PERFORMANCE)
    assert rows, "macro_state_performance.csv is empty"
    series_per_state = defaultdict(int)
    for r in rows:
        series_per_state[r["state"]] += 1
        assert int(r["n_months"]) >= 3, f"{r['state']}/{r['series']}: n_months < 3"
    expected = len(C.load_registry())
    for state, n in series_per_state.items():
        assert n == expected, f"{state}: expected {expected} series, got {n}"


def test_macro_state_factor_attribution_valid():
    if not C.MACRO_STATE_FACTOR_ATTRIBUTION.exists():
        return
    rows = _rows(C.MACRO_STATE_FACTOR_ATTRIBUTION)
    assert rows, "macro_state_factor_attribution.csv is empty"
    for r in rows:
        hr = float(r["hit_rate"])
        assert 0.0 <= hr <= 1.0, f"hit_rate out of bounds: {r['state']}/{r['factor']} = {hr}"
        assert r["factor"] in ("Momentum", "Enhanced Value", "Quality"), f"bad factor: {r['factor']}"


def test_scenario_summary_valid():
    if not C.SCENARIO_SUMMARY.exists():
        return
    rows = _rows(C.SCENARIO_SUMMARY)
    assert rows, "scenario_summary.csv is empty"
    scenarios = defaultdict(int)
    for r in rows:
        scenarios[r["scenario"]] += 1
        p5, p25, p50, p75, p95 = (float(r[k]) for k in
                                  ("cagr_p5", "cagr_p25", "cagr_p50", "cagr_p75", "cagr_p95"))
        assert p5 <= p25 <= p50 <= p75 <= p95, f"{r['scenario']}/{r['series']}: percentiles out of order"
        pl = float(r["prob_cumulative_loss"])
        assert 0.0 <= pl <= 1.0, f"{r['scenario']}/{r['series']}: prob_cumulative_loss out of bounds"
    expected = len(C.load_registry())
    for name, n in scenarios.items():
        assert n == expected, f"scenario {name}: expected {expected} series, got {n}"


def test_ff_factors_valid():
    # Fama-French proxy series (network-dependent; skipped if not fetched)
    if not C.FF_FACTORS_MONTHLY.exists():
        return
    rows = _rows(C.FF_FACTORS_MONTHLY)
    assert rows, "ff_factors_monthly.csv is empty"
    for col in ("mkt_rf", "smb", "hml", "rf", "mom"):
        assert col in rows[0], f"missing factor column {col}"
    assert rows[0]["date"] <= "1927-01-31", f"history should start by 1927, got {rows[0]['date']}"
    for r in rows:
        for col in ("mkt_rf", "smb", "hml", "mom"):
            if r[col] == "":
                continue                                   # mom starts 1927; early months blank
            v = float(r[col])
            assert -0.6 <= v <= 0.6, f"implausible monthly factor return {col}={v} at {r['date']}"


def test_asset_class_proxies_valid():
    # bond/gold/cash proxy returns (network for gold; skipped if not generated)
    if not C.ASSET_CLASS_MONTHLY.exists():
        return
    rows = _rows(C.ASSET_CLASS_MONTHLY)
    assert rows, "asset_class_monthly.csv is empty"
    cols = [c for c in rows[0] if c.startswith("Asset | ")]
    assert len(cols) >= 2, f"expected at least 2 proxy sleeves, got {cols}"
    for r in rows:
        for c in cols:
            if r[c] == "":
                continue
            v = float(r[c])
            assert -0.5 <= v <= 0.6, f"implausible monthly return {c}={v} at {r['date']}"
    # construction sanity: 2022's rate shock must show up as a clearly negative bond year
    if "Asset | US Treasury 10y" in rows[0]:
        b22 = [float(r["Asset | US Treasury 10y"]) for r in rows
               if r["date"].startswith("2022") and r["Asset | US Treasury 10y"] != ""]
        year = 1.0
        for v in b22:
            year *= 1 + v
        assert year - 1 < -0.05, f"2022 bond return {year - 1:.1%} — construction suspect"


def test_long_history_factor_states_valid():
    if not C.LONG_HISTORY_CSV.exists():
        return
    rows = _rows(C.LONG_HISTORY_CSV)
    assert rows, "long_history_factor_states.csv is empty"
    samples = {r["sample"] for r in rows}
    assert len(samples) == 2, f"expected long+modern samples, got {samples}"
    long_rows = [r for r in rows if r["sample"].startswith("long")]
    states = {r["state"] for r in long_rows}
    assert len(states) == 4, f"long sample should cover 4 quadrants, got {len(states)}"
    assert sum(int(r["n_months"]) for r in long_rows if r["factor"] == "mkt_rf") > 700, \
        "long sample should classify far more months than the modern window"
    for r in rows:
        assert 0.0 <= float(r["hit_rate"]) <= 1.0, f"hit_rate out of bounds: {r}"


def test_proxy_backtest_valid():
    # 60-year construction-rule race (skipped if not generated)
    if not C.PROXY_BACKTEST_SUMMARY.exists():
        return
    rows = _rows(C.PROXY_BACKTEST_SUMMARY)
    races = {r["race"] for r in rows}
    assert "equity" in races, "equity race missing"
    for r in rows:
        assert r["portfolio"], "empty contestant name"
        assert -1.0 <= float(r["oos_max_drawdown"]) <= 0.0
        assert abs(float(r["oos_sharpe"])) < 10, f"implausible Sharpe: {r}"
    eq_names = {r["portfolio"] for r in rows if r["race"] == "equity"}
    assert "1/N" in eq_names, "1/N benchmark missing from the equity race"


def test_stress_library_valid():
    if not C.STRESS_SUMMARY.exists():
        return
    rows = _rows(C.STRESS_SUMMARY)
    assert rows, "stress_summary.csv is empty"
    for r in rows:
        assert -1.0 <= float(r["max_drawdown"]) <= 0.0, f"bad maxDD: {r}"
        assert float(r["worst_month"]) <= 0.05, f"implausible worst month: {r}"
        assert int(r["n_months"]) >= 2
    tables = {r["table"] for r in rows}
    assert "historic" in tables or "modern" in tables


def test_optimizer_portfolios_valid():
    # structural validity of the optimizer stage's outputs (skipped if not generated);
    # unit tests of the optimizer internals live in tests/test_optimizer.py
    if not C.OPTIMIZER_PORTFOLIOS.exists():
        return
    totals = defaultdict(float)
    for r in _rows(C.OPTIMIZER_PORTFOLIOS):
        w = float(r["weight"])
        assert 0.0 <= w <= 1.0, f"{r['portfolio']}/{r['series']}: weight {w} out of bounds"
        totals[r["portfolio"]] += w
    assert totals, "optimizer_portfolios.csv is empty"
    for name, tot in totals.items():
        # displayed weights drop sub-0.1% dust, so allow a little under 100%
        assert 0.97 <= tot <= 1.0001, f"{name}: weights sum to {tot:.4f}"


def test_optimizer_walkforward_valid():
    if not C.OPTIMIZER_WALKFORWARD.exists():
        return
    rows = _rows(C.OPTIMIZER_WALKFORWARD)
    names = {r["portfolio"] for r in rows}
    assert "1/N" in names, "walk-forward must always include the 1/N benchmark (DeMiguel)"
    for r in rows:
        assert float(r["oos_ann_vol"]) > 0, f"{r['portfolio']}: nonpositive OOS vol"
        assert -1.0 <= float(r["oos_max_drawdown"]) <= 0.0, f"{r['portfolio']}: bad maxDD"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"PASS {fn.__name__}")
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
