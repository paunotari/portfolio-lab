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


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"PASS {fn.__name__}")
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
