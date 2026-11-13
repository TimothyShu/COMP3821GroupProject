"""Smoke test for experiments/run.py: one row per (family, n, seed, algorithm)."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "run", Path(__file__).resolve().parents[1] / "experiments" / "run.py"
)
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def test_one_row_per_combination():
    config = {"seeds": [0, 1], "algorithms": ["max_degree"], "families": {"path": [5, 9]}}
    rows = run.run(config)
    assert len(rows) == 2 * 2 * 1
    assert {r["n"] for r in rows} == {5, 9}
    assert all(r["rounds"] >= 3 for r in rows if r["n"] == 9)  # nothing beats b(P_9) = 3
    assert set(rows[0]) == set(run.FIELDS)
