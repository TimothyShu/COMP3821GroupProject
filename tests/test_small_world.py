import networkx as nx
import pytest

from burning.generators.small_world import small_world


@pytest.mark.parametrize("p", [0.0, 0.1, 1.0])
@pytest.mark.parametrize("n, k", [(10, 4), (100, 2), (100, 6), (1000, 4)])
def test_exact_size_and_edge_count(n, k, p):
    G = small_world(n, k=k, p=p, seed=0)
    assert G.number_of_nodes() == n
    assert G.number_of_edges() == n * k // 2  # rewiring moves edges, never adds or removes


@pytest.mark.parametrize("n, k", [(10, 2), (100, 4), (101, 6)])
def test_p_zero_is_ring_lattice(n, k):
    lattice = nx.circulant_graph(n, range(1, k // 2 + 1))
    assert nx.utils.edges_equal(small_world(n, k=k, p=0.0).edges, lattice.edges)


def test_rewiring_shrinks_diameter():
    diameters = [nx.diameter(small_world(1000, p=p, seed=0)) for p in (0.0, 0.01, 0.1, 1.0)]
    assert diameters == sorted(diameters, reverse=True)
    assert diameters[0] == 250  # ring lattice: n / k


def test_different_seeds_differ():
    assert not nx.utils.graphs_equal(small_world(100, seed=1), small_world(100, seed=2))


def test_metadata():
    G = small_world(100, k=6, p=0.2)
    assert G.graph == {"family": "small_world", "params": {"k": 6, "p": 0.2}}


@pytest.mark.parametrize(
    "n, k, p", [(10, 3, 0.1), (10, 0, 0.1), (10, 10, 0.1), (4, 4, 0.1), (10, 4, -0.1), (10, 4, 1.5)]
)
def test_invalid_arguments(n, k, p):
    with pytest.raises(ValueError):
        small_world(n, k=k, p=p)
