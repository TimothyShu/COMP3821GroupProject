import math

import networkx as nx
import pytest

from burning.algorithms import ALGORITHMS
from burning.algorithms.farthest_first import farthest_first
from burning.generators import GENERATORS
from burning.simulate import burn_times, burning_rounds, exact_burning_number


@pytest.mark.parametrize("family", GENERATORS)
@pytest.mark.parametrize("n", [10, 100])
def test_sequence_burns_graph(family, n):
    G = GENERATORS[family](n, seed=0)
    seq = farthest_first(G)

    assert seq
    assert len(seq) == len(set(seq))
    assert all(v in G for v in seq)
    assert set(burn_times(G, seq)) == set(G)


@pytest.mark.parametrize("family", GENERATORS)
def test_deterministic(family):
    G = GENERATORS[family](100, seed=0)

    assert farthest_first(G) == farthest_first(G)


def test_does_not_modify_graph():
    G = nx.path_graph(100)
    before = G.copy()

    farthest_first(G)

    assert nx.utils.graphs_equal(G, before)


def test_sources_are_fresh():
    for family in GENERATORS:
        G = GENERATORS[family](100, seed=0)
        seq = farthest_first(G)
        times = burn_times(G, seq)

        for i, source in enumerate(seq, start=1):
            assert times[source] == i
            assert all(times[u] >= i for u in G[source])


def test_farthest_selection_on_path():
    G = nx.path_graph(9)

    # First source is 0, second is 8, third is 4.
    assert farthest_first(G) == [0, 8, 4]
    assert burning_rounds(G, farthest_first(G)) == 4


def test_complete_graph():
    G = nx.complete_graph(10)

    assert farthest_first(G) == [0]
    assert burning_rounds(G, farthest_first(G)) == 2


def test_star_graph():
    G = nx.star_graph(9)

    assert farthest_first(G)[0] == 0
    assert burning_rounds(G, farthest_first(G)) == 2


@pytest.mark.parametrize("n", range(1, 13))
def test_not_better_than_optimal(n):
    G = nx.path_graph(n)
    optimum = exact_burning_number(G)

    assert burning_rounds(G, farthest_first(G)) >= optimum


@pytest.mark.parametrize("n", [1, 2, 5, 16, 17, 100, 1000])
def test_path_against_known_burning_number(n):
    G = nx.path_graph(n)
    optimum = math.isqrt(n - 1) + 1

    assert burning_rounds(G, farthest_first(G)) >= optimum


def test_tie_breaking():
    G = nx.path_graph(4)

    assert farthest_first(G) == [0, 3]


def test_registry():
    assert ALGORITHMS["farthest_first"] is farthest_first


def test_single_vertex():
    assert farthest_first(nx.empty_graph(1)) == [0]


def test_empty_graph():
    with pytest.raises(ValueError):
        farthest_first(nx.empty_graph(0))


def test_disconnected_graph():
    G = nx.disjoint_union(nx.path_graph(3), nx.path_graph(3))

    with pytest.raises(ValueError):
        farthest_first(G)
