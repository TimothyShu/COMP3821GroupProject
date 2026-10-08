# Graph Burning: Empirical Comparison of Approximation Algorithms

COMP3821 group project. We compare four polynomial-time algorithms for estimating the burning
number b(G), measuring accuracy and runtime across simple, adversarial and real-world graphs.

## Layout

```
src/burning/
  algorithms/      one file per algorithm
  generators/      one file per graph family (or group of families)
experiments/
  configs/         experiment configs (graph families, sizes, seeds, algorithms)
tests/             unit tests for algorithms and generators
notebooks/         exploration only
data/snap/         downloaded SNAP datasets (git-ignored)
results/
  raw/             experiment output CSVs (git-ignored, regenerate from configs)
  figures/         plots
```

### Code

- **`src/burning/`** is the main Python package, holding all shared, importable code.
  - **`algorithms/`** has one file per algorithm (e.g. `three_approx.py`, `max_degree.py`).
    Each takes a graph and returns a burning sequence.
  - **`generators/`** has the code that builds the test graphs (paths, grids, spiders,
    barbells, etc.). Each member adds their assigned generators here.
  - A shared module that simulates burning and counts rounds will sit next to these two
    folders, so every algorithm is scored the same way.
- **`tests/`** has unit tests, e.g. "the path generator returns a connected graph with n
  vertices" or "this algorithm's sequence burns the whole graph". Run them with `pytest`.

### Running experiments

- **`experiments/`** has the scripts that run the algorithms over many graphs and collect
  results, and the scripts that turn those results into plots.
  - **`configs/`** has small files describing *what* to run: which graph families, sizes,
    random seeds and algorithms. Rerunning a config reproduces an experiment exactly.
- **`notebooks/`** is for Jupyter notebooks used to explore and try ideas. Anything used in
  the final results moves into `experiments/` so it can be rerun.

### Data and output

- **`data/snap/`** holds real-world graphs downloaded from the Stanford SNAP collection
  (extension). It is git-ignored because the files can be large and can be re-downloaded.
- **`results/raw/`** holds the CSVs produced by experiment runs: one row per algorithm,
  graph and size, with rounds taken and runtime. It is git-ignored because the CSVs can be
  regenerated from the configs.
- **`results/figures/`** holds the plots made from those CSVs, used in the report and poster.

### Pipeline

```
generators  ->  algorithms  ->  experiments (driven by a config)  ->  results/raw/*.csv  ->  results/figures/
build graphs    burning seqs    run + time + score                    raw data              plots
```

## Algorithms

| Algorithm                         | Owner     |
| --------------------------------- | --------- |
| 3-approximation (Bonato & Kamali) | Timothy   |
| Eigenvector centrality            | Adam      |
| Farthest-first                    | Nathaniel |
| Maximum degree                    | Antyabha  |

## Generators

| Family                       | Owner |
| ---------------------------- | ----- |
| Path                         |       |
| 2D grid                      |       |
| d-ary tree                   |       |
| Barbell                      |       |
| Spider                       |       |
| Centipede                    |       |
| Star                         |       |
| Cluster                      |       |
| Scale-free (extension)       |       |
| Small-world (extension)      |       |
| SNAP loader (extension)      |       |

## Interfaces to agree on before coding

- **Algorithm:** takes a graph and returns a burning sequence (sources in ignition order).
  Rounds are counted by one shared function, not by each algorithm, so results are comparable.
- **Generator:** takes `n`, a `seed` and family-specific parameters, and returns a connected
  graph with about n vertices. The same seed must always give the same graph.

## Workflow

- Branch per task (e.g. `timothy/three-approx`), never push straight to `main`.
- Open a PR. Another member reviews and merges it, which doubles as our peer cross-review.
- Commit configs, not results. Anyone should be able to regenerate a figure from a config.
