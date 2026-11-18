"""The three heuristic-order 3-approximations must keep every guarantee of the original."""

from itertools import combinations

import networkx as nx
import pytest

from burning.algorithms.eigen_centrality import sorted_vertex_eigenvector
from burning.algorithms.hybrid_approx import (
    burn_guess_farthest,
    degree_with_bound,
    eigen_with_bound,
    farthest_with_bound,
)
from burning.algorithms.max_degree import sorted_vertex_degree
from burning.generators import GENERATORS
from burning.simulate import burn_times, burning_rounds, exact_burning_number

# Every registered family at sizes the exact solver can handle, plus a few classic graphs.
SMALL = {f"{family}_{n}": GENERATORS[family](n, seed=0) for family in GENERATORS for n in (6, 9, 12, 16)}
SMALL |= {
    "single_vertex": nx.empty_graph(1),
    "edge": nx.path_graph(2),
    "cycle_13": nx.cycle_graph(13),
    "complete_8": nx.complete_graph(8),
    "grid_4x4": nx.convert_node_labels_to_integers(nx.grid_2d_graph(4, 4)),
    "petersen": nx.petersen_graph(),
}

VARIANTS = {"degree": degree_with_bound, "eigen": eigen_with_bound, "farthest": farthest_with_bound}
FAMILY_SIZES = [(family, n) for family in GENERATORS for n in (10, 100, 1000)]


def scan_witnesses(G, g, order):
    """Independent Burn-Guess(g) over a fixed order, keeping the centres it finds."""
    radius, centres, covered = 2 * g - 2, [], set()
    for v in order:
        if v in covered:
            continue
        centres.append(v)
        if len(centres) == g:
            break
        covered |= set(nx.single_source_shortest_path_length(G, v, cutoff=radius))
    return centres


def farthest_witnesses(G, g):
    """Independent Gonzalez k-center from the first vertex, keeping up to g centres."""
    nodes, centres = list(G), [next(iter(G))]
    while len(centres) < g:
        dist = nx.multi_source_dijkstra_path_length(G, centres)
        v = max(nodes, key=dist.__getitem__)
        if dist[v] <= 2 * g - 2:
            break
        centres.append(v)
    return centres


WITNESSES = {
    "degree": lambda G, g: scan_witnesses(G, g, sorted_vertex_degree(G)),
    "eigen": lambda G, g: scan_witnesses(G, g, sorted_vertex_eigenvector(G)),
    "farthest": farthest_witnesses,
}


@pytest.mark.parametrize("name", SMALL)
@pytest.mark.parametrize("variant", VARIANTS)
def test_within_three_times_optimal(variant, name):
    G = SMALL[name]
    b = exact_burning_number(G)
    seq, lower = VARIANTS[variant](G)
    assert lower <= b <= burning_rounds(G, seq) <= 3 * b


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
@pytest.mark.parametrize("variant", VARIANTS)
def test_round_guarantee_and_fresh_sources(variant, family, n):
    G = GENERATORS[family](n, seed=0)
    seq, lower = VARIANTS[variant](G)
    assert len(seq) <= lower  # good guess g = lower + 1 yields at most g - 1 centres
    time = burn_times(G, seq)
    assert max(time.values()) <= 3 * lower  # 3g - 3 with g = lower + 1
    for i, x in enumerate(seq, start=1):
        assert time[x] == i and all(time[u] >= i for u in G[x])


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
@pytest.mark.parametrize("variant", VARIANTS)
def test_lower_bound_is_certified(variant, family, n):
    # Bad guess `lower` has `lower` centres pairwise >= 2*lower - 1 apart, forcing b(G) >= lower.
    G = GENERATORS[family](n, seed=0)
    _, lower = VARIANTS[variant](G)
    witnesses = WITNESSES[variant](G, lower)
    assert len(witnesses) == lower
    dist = {v: nx.single_source_shortest_path_length(G, v) for v in witnesses}
    assert all(dist[a][b] >= 2 * lower - 1 for a, b in combinations(witnesses, 2))


def test_farthest_picks_far_ends_of_a_path():
    # P_9 from vertex 0: the farthest vertex is 8, then the middle (4), so guess 3 (radius 4)
    # needs only 0 and 8.
    assert burn_guess_farthest(nx.path_graph(9), 3) == [0, 8]
    assert burn_guess_farthest(nx.path_graph(9), 1) is None
    assert burn_guess_farthest(nx.empty_graph(1), 2) == [0]


def test_degree_order_starts_at_the_hub():
    G = GENERATORS["star"](20)
    hub = max(G, key=G.degree)
    seq, _ = degree_with_bound(G)
    assert seq[0] == hub and burning_rounds(G, seq) == 2
