import networkx as nx
import pytest

from burning.generators import GENERATORS

star = GENERATORS["star"]

@pytest.mark.parametrize("n", [2, 3, 10, 11, 100])
def test_features(n):
    G = star(n)
    assert G.number_of_nodes() == n
    assert G.number_of_edges() == n - 1
    assert sorted(degree for _, degree in G.degree()) == [1] * (n - 1) + [n - 1]
    assert nx.is_connected(G)


@pytest.mark.parametrize("n", [-1, 0, 1])
def test_rejects_bad_input(n):
    with pytest.raises(ValueError):
        star(n)
