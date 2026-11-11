import math

import networkx as nx
import pytest

from burning.algorithms.eigen_centrality import mech, sorted_vertex_eigenvector
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
def test_valid_and_not_better_than_optimal(name):
    # MECH is a heuristic: no upper bound, but it must burn everything and can't beat b(G).
    G = SMALL[name]
    seq = mech(G)
    assert set(burn_times(G, seq)) == set(G)
    assert exact_burning_number(G) <= burning_rounds(G, seq)


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
def test_sequence_is_well_formed(family, n):
    G = GENERATORS[family](n, seed=0)
    seq = mech(G)
    assert len(set(seq)) == len(seq) and set(seq) <= set(G)
    assert set(burn_times(G, seq)) == set(G)


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
def test_sources_are_fresh(family, n):
    # A source is picked from the unburned vertices after the spread step, so the fire
    # never reaches it before its own round and no neighbour burned earlier.
    G = GENERATORS[family](n, seed=0)
    seq = mech(G)
    time = burn_times(G, seq)
    for i, x in enumerate(seq, start=1):
        assert time[x] == i and all(time[u] >= i for u in G[x])


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
def test_each_pick_is_most_central_unburned(family, n):
    # Replays the sequence with distances alone (no spread()), then checks every pick has
    # maximal eigenvector centrality in the unburned subgraph at that moment.
    G = GENERATORS[family](n, seed=0)
    seq = mech(G)
    dist = [nx.single_source_shortest_path_length(G, x) for x in seq]
    for i, x in enumerate(seq):
        # seq[j] is lit in round j + 1, so by the spread of round i + 1 it has reached radius i - j
        rest = G.subgraph(v for v in G if not any(dist[j].get(v, math.inf) <= i - j for j in range(i)))
        assert x in rest
        if rest.number_of_edges() == 0 or not nx.is_connected(rest):
            continue  # ties between components make the reference ranking ambiguous
        c = nx.eigenvector_centrality_numpy(rest)
        assert c[x] >= max(c.values()) - 1e-6


@pytest.mark.parametrize("family, n", FAMILY_SIZES)
def test_deterministic_and_does_not_modify_input(family, n):
    G = GENERATORS[family](n, seed=0)
    before = (list(G.nodes()), list(G.edges()))
    first = mech(G)
    assert (list(G.nodes()), list(G.edges())) == before
    assert mech(G) == first


@pytest.mark.parametrize("n", [1, 2, 5, 16, 17, 100, 1000])
def test_path_against_known_burning_number(n):
    G = nx.path_graph(n)
    b = math.isqrt(n - 1) + 1  # b(P_n) = ceil(sqrt(n))
    assert b <= burning_rounds(G, mech(G))


@pytest.mark.parametrize("n", [3, 10, 100])
def test_star_is_burned_optimally(n):
    # The centre is the unique top-ranked vertex, so MECH lights it first: b(star) = 2.
    G = nx.star_graph(n)
    assert mech(G)[0] == 0
    assert burning_rounds(G, mech(G)) == exact_burning_number(G) == 2


def test_ranking_and_tie_breaking():
    assert sorted_vertex_eigenvector(nx.star_graph(5))[0] == 0
    # Every vertex of a cycle has the same centrality, so ties fall back to node order.
    cycle = nx.cycle_graph(6)
    assert sorted_vertex_eigenvector(cycle) == list(cycle.nodes())
    assert mech(cycle)[0] == 0


def test_edge_cases():
    assert mech(nx.empty_graph(0)) == []
    assert mech(nx.empty_graph(1)) == [0]
    assert mech(nx.empty_graph(3)) == [0, 1, 2]  # edgeless: every vertex must be lit, in node order
    # Disconnected input: the unburned subgraph is disconnected from round 1.
    G = nx.disjoint_union(nx.path_graph(4), nx.star_graph(3))
    seq = mech(G)
    assert set(burn_times(G, seq)) == set(G)
    assert exact_burning_number(G) <= burning_rounds(G, seq)