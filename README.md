# Graph Burning: Empirical Comparison of Approximation Algorithms

COMP3821 group project. We compare four polynomial-time algorithms for estimating the burning
number b(G), measuring accuracy and runtime across simple and adversarial graph families, plus two random
network models (small-world and scale-free).

## Layout

```
src/burning/
  algorithms/      one file per algorithm
  generators/      one file per graph family (or group of families)
experiments/
  configs/         experiment configs (graph families, sizes, seeds, algorithms)
  benchmark_ratios.py  the report's benchmark (ratios, runtimes, structure)
  plot.py          report figures and tables from the benchmark CSVs
tests/             unit tests for algorithms and generators
notebooks/         exploration only
results/
  raw/             experiment output CSVs (git-ignored, except the benchmark data)
  figures/         report figures (PDF)
  tables/          report tables (CSV and LaTeX)
```

### Code

- `src/burning/` is the main Python package, holding all shared, importable code.
  - `algorithms/` has one file per algorithm (e.g. `three_approx.py`, `max_degree.py`).
  Each takes a graph and returns a burning sequence.
  - `generators/` has the code that builds the test graphs (paths, grids, spiders,
  barbells, etc.). Each member adds their assigned generators here.
  - `simulate.py` simulates burning and counts rounds, so every algorithm is scored the
  same way. It also has a brute-force exact solver for small graphs (n <= 16) used in tests.
- `tests/` has unit tests, e.g. "the path generator returns a connected graph with n
vertices" or "this algorithm's sequence burns the whole graph". Run them with `pytest`.

### Running experiments

- `experiments/` has the scripts that run the algorithms over many graphs and collect
results, and the scripts that turn those results into plots.
  - `configs/` has small files describing *what* to run: which graph families, sizes,
  random seeds and algorithms. Rerunning a config reproduces an experiment exactly.
- `notebooks/` is for Jupyter notebooks used to explore and try ideas. Anything used in
the final results moves into `experiments/` so it can be rerun.

### Data and output

- `results/raw/` holds the CSVs produced by experiment runs: one row per algorithm,
graph and size, with rounds taken and runtime. It is git-ignored because the CSVs can be
regenerated from the configs. The exception is the benchmark data behind the report
(`benchmark_ratios*.csv` and their `.meta.json` files), which is committed.
- `results/figures/` and `results/tables/` hold the figures and tables made from those CSVs,
used in the report and poster.

### Pipeline

```
generators  ->  algorithms  ->  experiments (driven by a config)  ->  results/raw/*.csv  ->  results/figures/
build graphs    burning seqs    run + time + score                    raw data              plots
```

## Run an experiment

### Set up

Install [uv](https://docs.astral.sh/uv/), then install the dependencies from the project root:

```bash
uv sync
```

`uv run` runs a command inside the project's virtual environment, so you don't need to set
`PYTHONPATH`.

### Write a config

A config is a YAML file in `experiments/configs/` with these keys:

| Key          | Required | Meaning                                                                  |
| ------------ | -------- | ------------------------------------------------------------------------ |
| `seeds`      | yes      | List of seeds. The runner builds each graph once per seed.               |
| `families`   | yes      | Map from a family name to a list of target sizes `n`.                    |
| `algorithms` | no       | List of algorithm names. Leave it out to run every registered algorithm. |

```yaml
seeds: [0, 1, 2]
algorithms: [max_degree, three_approx]
families:
  path: [10, 100]
  spider: [100]
```

Names are the ones passed to `@register`. To list them:

```bash
uv run python -c "from burning.algorithms import ALGORITHMS; from burning.generators import GENERATORS; print(sorted(ALGORITHMS)); print(sorted(GENERATORS))"
```

Every family runs with its default shape parameters, for example `legs=3` for `spider`. A
config can't change them. Deterministic families such as `path` give the same graph for every
seed, so extra seeds only repeat the timing.

`experiments/configs/default.yaml` runs all ten families at sizes 10, 100 and 1000, with seeds
0, 1 and 2 and every algorithm.

### Run it

```bash
uv run python experiments/run.py experiments/configs/default.yaml
```

The runner builds each graph, times each algorithm
on it, and scores the sequence with `burning_rounds`. It writes `results/raw/<config name>.csv`,
named after the config file, and overwrites any earlier file with that name. It then prints the
mean rounds for each family and size, one column per algorithm:

```
algorithm  max_degree  three_approx
family n
path   10         5.0           6.0
       50        25.0          10.0
star   10         2.0           2.0
```

### Read the CSV

The CSV has one row per family, size, seed and algorithm:

| Column      | Meaning                                                                       |
| ----------- | ----------------------------------------------------------------------------- |
| `family`    | Family name.                                                                  |
| `n`         | Target size from the config.                                                  |
| `seed`      | Seed passed to the generator.                                                 |
| `algorithm` | Algorithm name.                                                               |
| `vertices`  | Number of vertices in the graph built. It can be less than `n`.               |
| `edges`     | Number of edges in the graph built.                                           |
| `rounds`    | Rounds the algorithm's sequence takes to burn the graph.                      |
| `seconds`   | Wall-clock time of the algorithm call alone, not graph building or scoring.   |

The first call to an algorithm can include one-off library start-up time. Compare `seconds`
across seeds, not from a single row.

To load it for plotting:

```python
import pandas as pd

df = pd.read_csv("results/raw/default.csv")
df.groupby(["family", "n", "algorithm"])["rounds"].mean()
```

## Reproduce the report's results

The report's numbers come from `experiments/benchmark_ratios.py`, not from a config. Each run
writes a CSV and a `.meta.json` next to it with the commit, machine, library versions and thread
settings. Pin BLAS to one thread so runtimes are comparable across algorithms:

```bash
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src

# Main benchmark: every family and algorithm, n = 10-30 (exact b) and 50-1000, 10 relabelled
# seeds. Writes results/raw/benchmark_ratios.csv. Takes about 2 hours, mostly eigenvector
# centrality at n = 500 and 1000.
uv run python experiments/benchmark_ratios.py

# Labelling artefact: generator labels (no relabelling), n = 1000.
uv run python experiments/benchmark_ratios.py --no-relabel \
    --families path grid small_world --small-sizes --sizes 1000 \
    --out results/raw/benchmark_ratios_no_relabel.csv

# Figures F1-F6 (results/figures/*.pdf) and tables (results/tables/).
uv run python experiments/plot.py
```

| Output                                | Content                                                       |
| ------------------------------------- | ------------------------------------------------------------- |
| `figures/f1_ratio_vs_n.pdf`           | Ratio against n, one panel per family, sd over seeds          |
| `figures/f2_gap_vs_structure.pdf`     | 3-approx gap to the best algorithm against diam/√n and Δ/d̄   |
| `figures/f3_runtime.pdf`              | Median runtime against n, log-log, with fitted slopes         |
| `figures/f4_hybrids.pdf`              | Hybrid scan orders relative to plain 3-approx                 |
| `figures/f5_spread.pdf`               | sd of rounds over relabellings                                |
| `figures/f6_labelling.pdf`            | Generator labels against relabelled                           |
| `tables/t1_small_exact.{csv,tex}`     | Mean rounds / b for n ≤ 30                                    |
| `tables/summary.csv`                  | Per-algorithm headline numbers                                |

Each benchmark row has `rounds`, `b_exact` (n ≤ 30, or the path and star formulas),
`lb_best` = L(G), `ratio` (rounds / b, or rounds / L(G), an upper bound on the true ratio),
`valid` (every source unburned when lit), `runtime_s`, and the structure columns `diam`,
`max_deg`, `avg_deg`, `diam_over_sqrt_n` and `maxdeg_over_avgdeg`.

## Algorithms

| Algorithm                         | Owner     |
| --------------------------------- | --------- |
| 3-approximation (Bonato & Kamali) | Timothy   |
| Eigenvector centrality            | Adam      |
| Farthest-first                    | Nathaniel |
| Maximum degree                    | Antyabha  |
| 3-approximation, heuristic scan orders (extension) | Timothy |

The extension variants (`three_approx_degree`, `three_approx_eigen`, `three_approx_farthest` in
`hybrid_approx.py`) run Burn-Guess in degree, eigenvector-centrality or farthest-first order.
The 3-approximation proof never depends on the scan order, so each keeps the 3 b(G) guarantee.
See "Reproduce the report's results" for the benchmark that compares them.

## Generators

Refer to python library [NetworkX](https://networkx.org/en/) for generating graphs.

| Family                       | Owner |
| ---------------------------- | ----- |
| Path                         |  Adam  |
| 2D grid                      |  Nathan  |
| d-ary tree                   |  Tim  |
| Barbell                      |  Tim  |
| Spider                       |  Ant |
| Centipede                    |  Ant |
| Star                         |  Adam  |
| Cluster                      |  Nathan  |
| Scale-free (extension)       |  Nathan  |
| Small-world (extension)      |  Tim  |

## Interfaces to agree on before coding

- **Algorithm:** see "Algorithm interface" below.
- **Generator:** see "Generator interface" below.

## Algorithm interface

One file per algorithm in `src/burning/algorithms/`, registered with `@register`, then added
to the import list in `src/burning/algorithms/__init__.py`:

```python
import networkx as nx

from burning.algorithms.registry import register


@register("max_degree")
def max_degree(G: nx.Graph) -> list:
    ...  # return the sources in ignition order
```

Rules:

1. **Return a burning sequence:** a non-empty list of vertices of `G`, in ignition order.
2. **Don't count rounds yourself.** Score sequences with `burning.simulate.burning_rounds(G, seq)`

   so every algorithm is measured identically. `is_burning_sequence` checks the strict
    definition (each source unburned when chosen, and `G` burned by round `len(seq)`).
3. **Deterministic:** the same graph gives the same sequence. Break ties by a fixed rule (e.g.

   smallest label) and document it.
4. **Don't modify** `G`**.**

`tests/test_algorithms.py` checks rules 1, 3 and 4 automatically for every registered
algorithm on every registered graph family. Add algorithm-specific checks in
`tests/test_<algorithm>.py`.

## Generator interface

One file per family in `src/burning/generators/` (e.g. `spider.py`), registered with
`@register`:

```python
import networkx as nx

from burning.generators.registry import register


@register("spider")
def spider(n: int, *, seed: int | None = None, legs: int = 3) -> nx.Graph:
    G = ...  # build with NetworkX
    G = nx.convert_node_labels_to_integers(G)
    G.graph["family"] = "spider"
    G.graph["params"] = {"legs": legs}
    return G
```

Then add `from burning.generators import spider  # noqa: F401` to
`src/burning/generators/__init__.py` so it registers itself.

Rules:

1. `n` **is the first positional argument: the target number of vertices.** Return at most

   `n` vertices, as close to `n` as the family allows (exactly `n` where possible). Code that
    uses the graph reads the real size from `G.number_of_nodes()`. Raise `ValueError` if `n` is
    too small for the structure.
2. `seed` **is always accepted, keyword-only.** Deterministic families ignore it. Random

   families pass it to NetworkX (`seed=seed`) and never use global `random`/`numpy` state.
    The same `(n, seed, params)` must give the same graph.
3. **Shape parameters are keyword-only with sensible defaults**, so `gen(n)` alone works.
4. **Output:** an undirected simple `nx.Graph` that is connected, with integer node labels

   `0..N-1` (use `nx.convert_node_labels_to_integers`).
5. **Metadata:** set `G.graph["family"]` to the registered name and `G.graph["params"]` to the

   shape parameters used.
6. **No side effects:** no printing, file I/O or plotting.

`tests/test_generators.py` checks rules 1–5 automatically for every registered generator. Add
family-specific checks (e.g. a spider has exactly one vertex of degree `legs`) in
`tests/test_<family>.py`.
