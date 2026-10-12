import networkx as nx
import pytest

from burning.generators.dary_tree import dary_tree


def expected_height(n: int, d: int) -> int:
    """Smallest h such that a complete d-ary tree of height h has >= n vertices."""
    h, size, level = 0, 1, 1
    while size < n:
        h += 1
        level *= d
        size += level
    return h


@pytest.mark.parametrize("d", [2, 3, 5])
@pytest.mark.parametrize("n", [1, 2, 7, 13, 100, 1000])
def test_exact_size_and_is_tree(n, d):
    G = dary_tree(n, d=d)
    assert G.number_of_nodes() == n
    assert nx.is_tree(G)


@pytest.mark.parametrize("d", [2, 3, 5])
@pytest.mark.parametrize("n", [7, 40, 100, 1000])
def test_branching_factor(n, d):
    G = dary_tree(n, d=d)
    assert G.degree(0) == min(d, n - 1)  # root has no parent
    assert max(deg for _, deg in G.degree) <= d + 1  # d children + 1 parent


@pytest.mark.parametrize("d", [2, 3])
@pytest.mark.parametrize("n", [7, 15, 16, 40, 100, 1000])
def test_height_is_minimal(n, d):
    assert nx.eccentricity(dary_tree(n, d=d), 0) == expected_height(n, d)


@pytest.mark.parametrize("n, d", [(7, 2), (15, 2), (13, 3), (40, 3)])
def test_perfect_tree_leaves_all_at_same_depth(n, d):
    G = dary_tree(n, d=d)
    depth = nx.single_source_shortest_path_length(G, 0)
    leaves = [v for v in G if G.degree(v) == 1]
    assert {depth[v] for v in leaves} == {expected_height(n, d)}
    assert len(leaves) == d ** expected_height(n, d)


def test_metadata():
    G = dary_tree(50, d=3)
    assert G.graph == {"family": "dary_tree", "params": {"d": 3}}


@pytest.mark.parametrize("n, d", [(0, 2), (10, 1), (10, 0)])
def test_invalid_arguments(n, d):
    with pytest.raises(ValueError):
        dary_tree(n, d=d)
