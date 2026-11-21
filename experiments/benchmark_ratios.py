"""Approximation ratios and runtimes for every algorithm on every family. One tidy CSV.

Usage: OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src uv run python experiments/benchmark_ratios.py [options]
Output: results/raw/benchmark_ratios.csv by default, one row per (algorithm, family, n, seed),
plus <out>.meta.json (commit, machine, library versions, thread settings, wall time).

Labelling-artefact run (generator labels, n = 1000, three families):
  OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src uv run python experiments/benchmark_ratios.py --no-relabel \
      --families path grid small_world --small-sizes --sizes 1000 \
      --out results/raw/benchmark_ratios_no_relabel.csv

Each graph's reference value does not depend on the algorithm being scored:
  b_exact  path/star formulas, or an exact branch-and-bound solve when n <= 30;
  lb_best  otherwise max(lb_diam, lb_3approx), so `ratio` is an upper bound on the true ratio.
lb_diam = ceil(sqrt(diam + 1)): k rounds cover at most 1 + 3 + ... + (2k - 1) = k^2 vertices of a
shortest path. lb_3approx is the best bound certified by any of the four 3-approx scan orders.

Structure columns per graph: diam_over_sqrt_n = diam(G) / sqrt(n) (about 1 or more for long, thin
graphs; small for well-connected ones) and maxdeg_over_avgdeg = max degree / average degree (large
for hub-dominated graphs).

Every graph is relabelled by a random permutation per seed (vertex labels, node order and
adjacency order all change), so tie-breaking varies even for deterministic families. Random
families also draw a new graph per seed. --no-relabel keeps the generators' labels.
"""

import argparse
import csv
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from functools import cache, lru_cache
from importlib.metadata import version
from pathlib import Path

import networkx as nx

from burning.algorithms import ALGORITHMS
from burning.algorithms.hybrid_approx import (
    degree_with_bound,
    eigen_with_bound,
    farthest_with_bound,
)
from burning.algorithms.three_approx import three_approx_with_bound
from burning.generators import GENERATORS
from burning.simulate import burn_times

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "raw" / "benchmark_ratios.csv"
SMALL_SIZES = [10, 15, 20, 25, 30]
SIZES = [50, 100, 200, 500, 1000]  # every algorithm runs on every size
SEEDS = range(10)
REPEATS = 1  # the 10 relabelled seeds already give 10 timing samples
BOUNDS = (three_approx_with_bound, degree_with_bound, eigen_with_bound, farthest_with_bound)


def relabel(G: nx.Graph, seed: int) -> nx.Graph:
    """Isomorphic copy with labels 0..N-1 shuffled; nodes and edges are added in label order."""
    perm = list(range(G.number_of_nodes()))
    random.Random(seed).shuffle(perm)
    H = nx.Graph(**G.graph)
    H.add_nodes_from(range(len(perm)))
    H.add_edges_from(sorted(tuple(sorted((perm[u], perm[v]))) for u, v in G.edges()))
    return H


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

        @cache
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


def structure(G: nx.Graph, diam: int) -> dict:
    n = G.number_of_nodes()
    degrees = [d for _, d in G.degree()]
    return {
        "diam": diam,
        "max_deg": max(degrees),
        "avg_deg": round(2 * G.number_of_edges() / n, 4),
        "diam_over_sqrt_n": round(diam / math.sqrt(n), 4),
        "maxdeg_over_avgdeg": round(max(degrees) * n / (2 * G.number_of_edges()), 4),
    }


def reference(family: str, G: nx.Graph, exact: bool) -> tuple[int | None, int, int, dict]:
    n = G.number_of_nodes()
    lb3 = max(f(G)[1] for f in BOUNDS)
    diam = nx.diameter(G, usebounds=True)
    lbd = ceil_sqrt(diam + 1)
    if family == "path":
        b = ceil_sqrt(n)  # Bonato, Janssen, Roshanbin 2016
    elif family == "star":
        b = min(n, 2)
    elif exact:
        b = exact_b(G, max(lbd, lb3), 3 * lb3)
    else:
        b = None
    return b, lbd, lb3, structure(G, diam)


def score(
    alg: str, family: str, n: int, G: nx.Graph, seed: int, b, lbd: int, lb3: int, shape: dict
) -> dict:
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
        "m": G.number_of_edges(), "seed": seed,
        "seq_len": len(seq), "rounds": rounds, "b_exact": "" if b is None else b,
        "lb_diam": lbd, "lb_3approx": lb3, "lb_best": lb,
        "ratio": round(rounds / (b or lb), 4), "ratio_is_exact": b is not None,
        "runtime_s": statistics.median(times), "valid": fresh, **shape,
    }


def metadata(args: argparse.Namespace, started: datetime, seconds: float, rows: int) -> dict:
    """Commit, machine and settings, so runtimes can be judged against another run."""

    def output(*cmd: str) -> str:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, check=False).stdout.strip()
        except OSError:
            return ""

    cpu = output("sysctl", "-n", "machdep.cpu.brand_string") if sys.platform == "darwin" else ""
    if not cpu and Path("/proc/cpuinfo").exists():
        names = [x for x in Path("/proc/cpuinfo").read_text().splitlines() if x.startswith("model name")]
        cpu = names[0].split(":", 1)[1].strip() if names else ""
    threads = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
    return {
        "started_utc": started.isoformat(timespec="seconds"),
        "wall_seconds": round(seconds, 1),
        "rows": rows,
        "commit": output("git", "rev-parse", "HEAD"),
        "uncommitted_changes": bool(output("git", "status", "--porcelain", "--untracked-files=no")),
        "command": " ".join(["benchmark_ratios.py", *sys.argv[1:]]),
        "relabel": not args.no_relabel,
        "families": args.families, "small_sizes": args.small_sizes, "sizes": args.sizes,
        "seeds": list(SEEDS), "repeats": REPEATS,
        "python": platform.python_version(),
        "libraries": {lib: version(lib) for lib in ("networkx", "numpy", "scipy", "pandas")},
        "os": platform.platform(),
        "cpu": cpu or platform.processor(),
        "cpu_count": os.cpu_count(),
        "thread_env": {var: os.environ.get(var) for var in threads},
    }


def main(args: argparse.Namespace) -> None:
    started, start = datetime.now(UTC), time.perf_counter()
    rows = []
    for exact, sizes in ((True, args.small_sizes), (False, args.sizes)):
        for family in args.families:
            for n in sizes:
                for seed in SEEDS:
                    G = GENERATORS[family](n, seed=seed)
                    if not args.no_relabel:
                        G = relabel(G, seed)
                    ref = reference(family, G, exact)
                    rows += [score(a, family, n, G, seed, *ref) for a in ALGORITHMS]
                print(f"{family:12} n={n}", file=sys.stderr, flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    meta = metadata(args, started, time.perf_counter() - start, len(rows))
    args.out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"{len(rows)} rows -> {args.out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Approximation ratios and runtimes.")
    parser.add_argument("--out", type=Path, default=OUT, help="output CSV")
    parser.add_argument("--no-relabel", action="store_true", help="keep the generators' labels")
    parser.add_argument("--families", nargs="+", default=list(GENERATORS), choices=list(GENERATORS))
    parser.add_argument("--small-sizes", nargs="*", type=int, default=SMALL_SIZES,
                        help="sizes scored against exact b (n <= 30)")
    parser.add_argument("--sizes", nargs="*", type=int, default=SIZES,
                        help="sizes scored against the lower bound")
    return parser.parse_args()


if __name__ == "__main__":
    main(parse_args())
