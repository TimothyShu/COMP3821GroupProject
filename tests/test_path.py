import networkx as nx
import pytest

from burning.generators import GENERATORS

path = GENERATORS["path"]

@pytest.mark.parametrize("n", [2, 3, 10, 11, 100])
def test_features(n):
    G = path(n)
    assert G.number_of_nodes() == n
    assert nx.is_tree(G)




@pytest.mark.parametrize("n", [0, -1])
def test_rejects_bad_input(n):
    with pytest.raises(ValueError):
        path(n)