import networkx as nx
import pytest

from burning.generators import GENERATORS

spider = GENERATORS["spider"]


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("n, legs", [(4, 3), (10, 3), (11, 4), (100, 7)])
def test_shape(n, legs, seed):
    G = spider(n, legs=legs, seed=seed)
    degrees = sorted(d for _, d in G.degree())
    assert G.number_of_nodes() == n
    assert nx.is_tree(G)
    assert degrees.count(1) == legs
    assert degrees[-1] == legs and degrees[-2] <= 2, "exactly one vertex of degree legs"


def leg_lengths(G):
    centre = max(G.degree, key=lambda x: x[1])[0]
    return sorted(len(c) for c in nx.connected_components(nx.restricted_view(G, [centre], [])))


def test_seed_varies_leg_lengths():
    # The 3-leg spiders on 7 vertices have leg lengths (1,1,4), (1,2,3) and (2,2,2).
    assert {tuple(leg_lengths(spider(7, seed=s))) for s in range(200)} == {(1, 1, 4), (1, 2, 3), (2, 2, 2)}


@pytest.mark.parametrize("n, legs", [(10, 2), (3, 3), (5, 5)])
def test_rejects_bad_input(n, legs):
    with pytest.raises(ValueError):
        spider(n, legs=legs)
