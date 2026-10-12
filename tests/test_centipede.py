import networkx as nx
import pytest

from burning.generators import GENERATORS

centipede = GENERATORS["centipede"]


@pytest.mark.parametrize("n", [2, 3, 10, 11, 100])
def test_shape(n):
    G = centipede(n)
    k = n // 2
    assert G.number_of_nodes() == 2 * k
    assert nx.is_tree(G)
    leaves = [v for v, d in G.degree() if d == 1]
    assert len(leaves) == k if k > 1 else len(leaves) == 2
    spine = G.subgraph(set(G) - set(leaves)) if k > 2 else None
    if spine is not None:
        assert nx.is_isomorphic(spine, nx.path_graph(k)), "non-leaves form the spine path"
        assert all(sum(1 for u in G[v] if u in leaves) == 1 for v in spine), "one leaf per spine vertex"


@pytest.mark.parametrize("n", [0, 1])
def test_rejects_bad_input(n):
    with pytest.raises(ValueError):
        centipede(n)
