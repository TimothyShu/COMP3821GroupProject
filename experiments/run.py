"""Run every algorithm in a config on every family, size and seed, and write one CSV.

Usage: PYTHONPATH=src .venv/bin/python experiments/run.py experiments/configs/default.yaml
Output: results/raw/<config name>.csv, one row per (family, n, seed, algorithm).
"""

import csv
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

from burning.algorithms import ALGORITHMS
from burning.generators import GENERATORS
from burning.simulate import burning_rounds

RAW = Path(__file__).resolve().parents[1] / "results" / "raw"
FIELDS = ["family", "n", "seed", "algorithm", "vertices", "edges", "rounds", "seconds"]


def run(config: dict) -> list[dict]:
    algorithms = config.get("algorithms") or list(ALGORITHMS)
    rows = []
    for family, sizes in config["families"].items():
        for n in sizes:
            for seed in config["seeds"]:
                G = GENERATORS[family](n, seed=seed)
                for name in algorithms:
                    start = time.perf_counter()
                    seq = ALGORITHMS[name](G)
                    seconds = time.perf_counter() - start
                    rows.append({
                        "family": family, "n": n, "seed": seed, "algorithm": name,
                        "vertices": G.number_of_nodes(), "edges": G.number_of_edges(),
                        # The shared simulator scores every algorithm the same way.
                        "rounds": burning_rounds(G, seq), "seconds": seconds,
                    })
    return rows


def main(config_path: str) -> None:
    path = Path(config_path)
    rows = run(yaml.safe_load(path.read_text()))
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{path.stem}.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    # Mean rounds per family and size, one column per algorithm.
    df = pd.DataFrame(rows)
    print(df.pivot_table(index=["family", "n"], columns="algorithm", values="rounds").round(2))
    print(f"\n{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
