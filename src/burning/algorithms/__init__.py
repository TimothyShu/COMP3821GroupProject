"""Burning algorithms. Add your module to the import list so it registers itself."""

from burning.algorithms import farthest_first, eigen_centrality, max_degree, three_approx  # noqa: F401
from burning.algorithms.registry import ALGORITHMS, register

__all__ = ["ALGORITHMS", "register"]
