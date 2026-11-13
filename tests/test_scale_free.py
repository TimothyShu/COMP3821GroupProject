import networkx as nx
import pytest

from burning.generators.scale_free import scale_free


@pytest.mark.parametrize("n, m", [(3, 2), (10, 1), (10, 2), (100, 3), (1000, 2)])
def test_size_and_structure(n, m):
    G = scale_free(n, m=m, seed=0)

    assert G.number_of_nodes() == n
    assert type(G) is nx.Graph
    assert nx.is_connected(G)
    assert nx.number_of_selfloops(G) == 0


@pytest.mark.parametrize("n, m", [(3, 2), (10, 1), (10, 2), (100, 3), (1000, 2)])
def test_edge_count(n, m):
    G = scale_free(n, m=m, seed=0)

    assert G.number_of_edges() == m * (n - m)


@pytest.mark.parametrize("n, m", [(10, 1), (100, 2), (1000, 3)])
def test_vertex_degrees(n, m):
    G = scale_free(n, m=m, seed=0)

    assert all(degree >= 1 for _, degree in G.degree())
    assert max(dict(G.degree()).values()) > m


def test_integer_labels():
    G = scale_free(100, seed=0)

    assert sorted(G.nodes()) == list(range(G.number_of_nodes()))


def test_metadata():
    G = scale_free(100, m=3, seed=0)

    assert G.graph == {
        "family": "scale_free",
        "params": {"m": 3},
    }


def test_same_seed_same_graph():
    a = scale_free(100, seed=7)
    b = scale_free(100, seed=7)

    assert nx.utils.graphs_equal(a, b)


def test_different_seeds():
    a = scale_free(100, seed=1)
    b = scale_free(100, seed=2)

    assert not nx.utils.graphs_equal(a, b)


@pytest.mark.parametrize(
    "n, m",
    [(0, 2), (1, 2), (2, 2), (10, 0), (10, 10), (10, 11), (-1, 2)],
)
def test_invalid_arguments(n, m):
    with pytest.raises(ValueError):
        scale_free(n, m=m)
