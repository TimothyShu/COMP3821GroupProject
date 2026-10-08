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
