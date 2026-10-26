import math
from itertools import combinations

import networkx as nx
import pytest

from burning.algorithms.three_approx import burn_guess, three_approx, three_approx_with_bound
from burning.generators import GENERATORS
from burning.simulate import burn_times, burning_rounds, exact_burning_number

FAMILY_SIZES = [(family, n) for family in GENERATORS for n in (10, 100, 1000)]

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


@pytest.mark.parametrize("name", SMALL)
def test_within_three_times_optimal(name):
    G = SMALL[name]
    b = exact_burning_number(G)
    seq, lower = three_approx_with_bound(G)
    assert lower <= b <= burning_rounds(G, seq) <= 3 * b


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
def test_round_guarantee(family, n):
    # Final good guess is g = lower + 1: fewer than g centres and at most 3g - 3 = 3 * lower rounds.
    G = GENERATORS[family](n, seed=0)
    seq, lower = three_approx_with_bound(G)
    assert len(seq) <= lower
    assert burning_rounds(G, seq) <= 3 * lower


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
def test_sources_are_fresh(family, n):
    # Centres are > 2g - 2 apart, so the fire never reaches a source before its own round.
    G = GENERATORS[family](n, seed=0)
    seq = three_approx(G)
    time = burn_times(G, seq)
    for i, x in enumerate(seq, start=1):
        assert time[x] == i and all(time[u] >= i for u in G[x])


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
def test_lower_bound_is_certified(family, n):
    # Bad guess `lower` found `lower` centres pairwise >= 2*lower - 1 apart, forcing b(G) >= lower.
    G = GENERATORS[family](n, seed=0)
    _, lower = three_approx_with_bound(G)
    witnesses = bad_guess_centres(G, lower)
    assert len(witnesses) == lower
    dist = {v: nx.single_source_shortest_path_length(G, v) for v in witnesses}
    assert all(dist[a][b] >= 2 * lower - 1 for a, b in combinations(witnesses, 2))


@pytest.mark.parametrize("n", [1, 2, 5, 16, 17, 100, 1000])
def test_path_against_known_burning_number(n):
    G = nx.path_graph(n)
    b = math.isqrt(n - 1) + 1  # b(P_n) = ceil(sqrt(n))
    seq, lower = three_approx_with_bound(G)
    assert lower <= b <= burning_rounds(G, seq) <= 3 * b


def test_edge_cases():
    G = nx.path_graph(5)
    assert burn_guess(G, 1) is None  # the first centre already reaches g = 1
    assert burn_guess(G, 6) == [0]  # radius 10 covers P_5 from vertex 0
    assert three_approx(nx.empty_graph(1)) == [0]
    with pytest.raises(ValueError):
        three_approx(nx.empty_graph(0))


def bad_guess_centres(G, g):
    """Independent re-implementation of Burn-Guess(g) that keeps the g centres it finds."""
    radius, centres, covered = 2 * g - 2, [], set()
    for v in G:
        if v in covered:
            continue
        centres.append(v)
        if len(centres) == g:
            break
        covered |= set(nx.single_source_shortest_path_length(G, v, cutoff=radius))
    return centres
