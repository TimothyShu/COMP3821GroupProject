"""Burning algorithms. Add your module to the import list so it registers itself."""

from burning.algorithms import (  # noqa: F401
    eigen_centrality,
    farthest_first,
    hybrid_approx,
    max_degree,
    three_approx,
)
from burning.algorithms.registry import ALGORITHMS, register

__all__ = ["ALGORITHMS", "register"]
