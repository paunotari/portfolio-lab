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


def test_all_21_return_series_present():
    series = {(r["region"], r["factor_type"]) for r in _rows(C.RETURNS_LONG)}
    assert len(series) == 21, f"expected 21 return series, got {len(series)}"


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
    for path in (C.MACRO_CORR_CONTEMP_LEVEL, C.MACRO_CORR_CONTEMP_CHG):
        rows = _rows(path)
        assert len(rows) == 21, f"{path.name}: expected 21 series rows, got {len(rows)}"
        n_ind = len(rows[0]) - 1  # minus the series index column
        assert n_ind == 12, f"{path.name}: expected 12 indicator cols, got {n_ind}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"PASS {fn.__name__}")
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
