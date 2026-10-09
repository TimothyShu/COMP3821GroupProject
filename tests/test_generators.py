"""Contract tests run against every registered generator (see README "Generator interface").

Family-specific tests go in tests/test_<family>.py.
"""

import networkx as nx
import pytest

from burning.generators import GENERATORS

SIZES = [10, 100, 1000]


@pytest.mark.parametrize("n", SIZES)
@pytest.mark.parametrize("name", GENERATORS)
def test_output_guarantees(name, n):
    G = GENERATORS[name](n, seed=0)
    assert type(G) is nx.Graph, "must be an undirected simple nx.Graph"
    assert nx.number_of_selfloops(G) == 0
    assert nx.is_connected(G)
    assert n / 2 <= G.number_of_nodes() <= n
    assert sorted(G.nodes) == list(range(G.number_of_nodes())), "labels must be 0..N-1"


@pytest.mark.parametrize("name", GENERATORS)
def test_metadata(name):
    G = GENERATORS[name](100, seed=0)
    assert G.graph.get("family") == name
    assert isinstance(G.graph.get("params"), dict)


@pytest.mark.parametrize("name", GENERATORS)
def test_same_seed_same_graph(name):
    a, b = GENERATORS[name](100, seed=7), GENERATORS[name](100, seed=7)
    assert nx.utils.graphs_equal(a, b)


@pytest.mark.parametrize("name", GENERATORS)
def test_defaults_work(name):
    GENERATORS[name](100)
