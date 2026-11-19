"""Approximation ratios and runtimes for every algorithm on every family. One tidy CSV.

Usage: PYTHONPATH=src uv run python experiments/benchmark_ratios.py [out.csv]
Output: results/raw/benchmark_ratios.csv by default, one row per (algorithm, family, n, seed).

Each graph's reference value does not depend on the algorithm being scored:
  b_exact  path/star formulas, or an exact branch-and-bound solve when n <= 30;
  lb_best  otherwise max(lb_diam, lb_3approx), so `ratio` is an upper bound on the true ratio.
lb_diam = ceil(sqrt(diam + 1)): k rounds cover at most 1 + 3 + ... + (2k - 1) = k^2 vertices of a
shortest path. lb_3approx is the best bound certified by any of the four 3-approx scan orders.
"""

import csv
import math
import statistics
import sys
import time
from functools import lru_cache
from pathlib import Path

import networkx as nx

from burning.algorithms import ALGORITHMS
from burning.algorithms.hybrid_approx import degree_with_bound, eigen_with_bound, farthest_with_bound
from burning.algorithms.three_approx import three_approx_with_bound
from burning.generators import GENERATORS
from burning.simulate import burn_times

OUT = Path(__file__).resolve().parents[1] / "results" / "raw" / "benchmark_ratios.csv"
RANDOM = {"spider", "small_world", "scale_free"}  # families whose graph depends on the seed
SMALL_SIZES = [10, 15, 20, 25, 30]
SIZES = [50, 100, 200, 500, 1000]  # every algorithm runs on every size
SEEDS = range(10)
REPEATS = 3
BOUNDS = (three_approx_with_bound, degree_with_bound, eigen_with_bound, farthest_with_bound)


def ceil_sqrt(x: int) -> int:
    r = math.isqrt(x)
    return r if r * r == x else r + 1


def exact_b(G: nx.Graph, lo: int, hi: int) -> int:
    """Exact b(G) in [lo, hi] by branch and bound on the covering characterisation (n <= ~30).

    b <= k iff balls of radii k-1, ..., 0 (one each) cover V. Branch on the lowest uncovered
    vertex u: some unused radius r and centre x with d(x, u) <= r must cover it.
    """
    nodes = list(G)
    idx = {v: i for i, v in enumerate(nodes)}
    full = (1 << len(nodes)) - 1
    dist = dict(nx.all_pairs_shortest_path_length(G))
    for k in range(lo, hi + 1):
        ball = [[sum(1 << idx[u] for u, d in dist[v].items() if d <= r) for v in nodes] for r in range(k)]
        biggest = [max(b.bit_count() for b in ball[r]) for r in range(k)]

        @lru_cache(maxsize=None)
        def covers(covered: int, radii: int) -> bool:
            if covered == full:
                return True
            free = full & ~covered
            if free.bit_count() > sum(biggest[r] for r in range(k) if radii >> r & 1):
                return False
            u = nodes[(free & -free).bit_length() - 1]
            return any(
                covers(covered | ball[r][idx[x]], radii & ~(1 << r))
                for r in range(k) if radii >> r & 1
                for x, d in dist[u].items() if d <= r
            )

        if covers(0, (1 << k) - 1):
            return k
    raise AssertionError("b(G) above the upper bound")


def reference(family: str, G: nx.Graph, exact: bool) -> tuple[int | None, int, int]:
    n = G.number_of_nodes()
    lb3 = max(f(G)[1] for f in BOUNDS)
    lbd = ceil_sqrt(nx.diameter(G, usebounds=True) + 1)
    if family == "path":
        b = ceil_sqrt(n)  # Bonato, Janssen, Roshanbin 2016
    elif family == "star":
        b = min(n, 2)
    elif exact:
        b = exact_b(G, max(lbd, lb3), 3 * lb3)
    else:
        b = None
    return b, lbd, lb3


def score(alg: str, family: str, n: int, G: nx.Graph, seed: int, b, lbd: int, lb3: int) -> dict:
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        seq = ALGORITHMS[alg](G)
        times.append(time.perf_counter() - start)
    burn = burn_times(G, seq)  # raises if G never fully burns
    rounds = max(burn.values())
    fresh = all(burn[x] == i and all(burn[u] >= i for u in G[x]) for i, x in enumerate(seq, 1))
    lb = max(lbd, lb3)
    assert lb <= rounds and (b is None or lb <= b <= rounds), (alg, family, n, seed)
    if alg.startswith("three_approx"):
        assert rounds <= 3 * (b or lb), (alg, family, n, seed)
    return {
        "alg": alg, "family": family, "n_target": n, "n": G.number_of_nodes(),
        "m": G.number_of_edges(), "seed": seed if family in RANDOM else "",
        "seq_len": len(seq), "rounds": rounds, "b_exact": "" if b is None else b,
        "lb_diam": lbd, "lb_3approx": lb3, "lb_best": lb,
        "ratio": round(rounds / (b or lb), 4), "ratio_is_exact": b is not None,
        "runtime_s": statistics.median(times), "valid": fresh,
    }


def main(out: Path) -> None:
    rows = []
    for exact, sizes in ((True, SMALL_SIZES), (False, SIZES)):
        for family in GENERATORS:
            for n in sizes:
                for seed in SEEDS if family in RANDOM else [0]:
                    G = GENERATORS[family](n, seed=seed)
                    ref = reference(family, G, exact)
                    rows += [score(a, family, n, G, seed, *ref) for a in ALGORITHMS]
                print(f"{family:12} n={n}", file=sys.stderr, flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
