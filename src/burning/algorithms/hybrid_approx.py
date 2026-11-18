"""3-approximation with heuristic scan orders (owner: Tim).

Bonato & Kamali's guarantee only needs two properties of Burn-Guess(G, g):
  1. a vertex becomes a centre only if it is further than 2g - 2 from every centre so far, and
  2. it stops (bad guess) on reaching g centres, or succeeds once every vertex is covered.
Neither depends on which vertex is examined next, so the scan order is free. These variants
choose it with the team's heuristics; each still burns G within 3 b(G) rounds and certifies a
lower bound on b(G):

  three_approx_degree    scan by degree, highest first (max_degree.sorted_vertex_degree)
  three_approx_eigen     scan by eigenvector centrality (eigen_centrality.sorted_vertex_eigenvector)
  three_approx_farthest  next centre is the vertex farthest from all centres so far, starting
                         from the first vertex in G (Gonzalez's greedy k-center; Garcia-Diaz
                         et al. show this ordering gives 3 - 2/b(G))
"""

from collections.abc import Hashable

import networkx as nx

from burning.algorithms.eigen_centrality import sorted_vertex_eigenvector
from burning.algorithms.max_degree import sorted_vertex_degree
from burning.algorithms.registry import register
from burning.algorithms.three_approx import burn_guess, relax, search


def burn_guess_farthest(G: nx.Graph, g: int) -> list[Hashable] | None:
    """Burn-Guess where the next vertex examined is the farthest from the current centres.

    Ties go to the vertex first in G's node order. Same contract as burn_guess.
    """
    radius = 2 * g - 2
    nodes = list(G)
    dist: dict[Hashable, int] = {}  # exact distance to nearest centre (no radius cap)
    centres: list[Hashable] = []
    v = nodes[0]
    while True:
        centres.append(v)
        if len(centres) >= g:
            return None
        relax(G, v, dist, float("inf"))
        v = max(nodes, key=dist.__getitem__)  # max keeps the first vertex on a tie
        if dist[v] <= radius:
            return centres


def degree_with_bound(G: nx.Graph) -> tuple[list[Hashable], int]:
    order = sorted_vertex_degree(G)
    return search(G, lambda g: burn_guess(G, g, order))


def eigen_with_bound(G: nx.Graph) -> tuple[list[Hashable], int]:
    order = sorted_vertex_eigenvector(G)
    return search(G, lambda g: burn_guess(G, g, order))


def farthest_with_bound(G: nx.Graph) -> tuple[list[Hashable], int]:
    return search(G, lambda g: burn_guess_farthest(G, g))


@register("three_approx_degree")
def three_approx_degree(G: nx.Graph) -> list[Hashable]:
    return degree_with_bound(G)[0]


@register("three_approx_eigen")
def three_approx_eigen(G: nx.Graph) -> list[Hashable]:
    return eigen_with_bound(G)[0]


@register("three_approx_farthest")
def three_approx_farthest(G: nx.Graph) -> list[Hashable]:
    return farthest_with_bound(G)[0]
