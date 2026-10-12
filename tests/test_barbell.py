import networkx as nx
import pytest

from burning.generators.barbell import MIN_CLIQUE, barbell


def split(G):
    return G.graph["params"]["clique"], G.graph["params"]["bridge"]


@pytest.mark.parametrize("frac", [0.0, 0.25, 0.5, 0.9])
@pytest.mark.parametrize("n", [6, 7, 10, 101, 1000])
def test_exact_size(n, frac):
    G = barbell(n, bridge_frac=frac)
    c, b = split(G)
    assert G.number_of_nodes() == n == 2 * c + b
    assert c >= MIN_CLIQUE and b >= 0


@pytest.mark.parametrize("frac", [0.0, 0.25, 0.5, 0.9])
@pytest.mark.parametrize("n", [6, 10, 101, 1000])
def test_structure(n, frac):
    G = barbell(n, bridge_frac=frac)
    c, b = split(G)
    # two K_c, b path vertices, b + 1 edges joining the cliques through the path
    assert G.number_of_edges() == 2 * (c * (c - 1) // 2) + b + 1
    assert nx.diameter(G) == b + 3
    assert sum(1 for _, deg in G.degree if deg == 2) >= b  # path vertices


@pytest.mark.parametrize("frac", [0.25, 0.5, 0.9])
def test_bridge_fraction_respected_for_large_n(frac):
    n = 1000
    _, b = split(barbell(n, bridge_frac=frac))
    assert abs(b - frac * n) <= 2


def test_small_n_shrinks_bridge_to_keep_cliques():
    G = barbell(10, bridge_frac=0.9)
    assert split(G) == (MIN_CLIQUE, 4)


def test_zero_bridge_joins_cliques_directly():
    G = barbell(8, bridge_frac=0.0)
    assert split(G) == (4, 0)
    assert nx.diameter(G) == 3


def test_metadata():
    G = barbell(100)
    assert G.graph["family"] == "barbell"
    assert G.graph["params"] == {"bridge_frac": 0.5, "clique": 25, "bridge": 50}


@pytest.mark.parametrize("n, frac", [(5, 0.5), (0, 0.0), (10, 1.0), (10, -0.1)])
def test_invalid_arguments(n, frac):
    with pytest.raises(ValueError):
        barbell(n, bridge_frac=frac)
