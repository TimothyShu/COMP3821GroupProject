import networkx as nx
import pytest

from burning.generators import GENERATORS

star = GENERATORS["star"]

@pytest.mark.parametrize("n", [0, 2, 3, 10, 11, 100])
def test_features(n):
    G = star(n)
    assert G.number_of_nodes() == n + 1
    assert G.number_of_edges() == n
    assert sorted(degree for _, degree in G.degree()) == [1] * n + [n]


@pytest.mark.parametrize("n", [-1, -2, -10])
def test_rejects_bad_input(n):
    with pytest.raises(ValueError):
        star(n)