import networkx as nx
import pytest

from burning.generators.cluster import cluster


@pytest.mark.parametrize(
    "n, clusters",
    [(8, 4), (10, 3), (20, 4), (100, 5), (1000, 4)],
)
def test_size_and_structure(n, clusters):
    G = cluster(n, clusters=clusters)
    sizes = G.graph["params"]["sizes"]

    assert G.number_of_nodes() == n
    assert len(sizes) == clusters
    assert sum(sizes) == n
    assert max(sizes) - min(sizes) <= 1
    assert nx.is_connected(G)


@pytest.mark.parametrize("n, clusters", [(10, 3), (20, 4), (100, 5)])
def test_edge_count(n, clusters):
    G = cluster(n, clusters=clusters)
    sizes = G.graph["params"]["sizes"]

    clique_edges = sum(size * (size - 1) // 2 for size in sizes)
    bridge_edges = clusters - 1

    assert G.number_of_edges() == clique_edges + bridge_edges


@pytest.mark.parametrize("n, clusters", [(10, 3), (20, 4), (100, 5)])
def test_clique_structure(n, clusters):
    G = cluster(n, clusters=clusters)
    sizes = G.graph["params"]["sizes"]

    offset = 0
    for size in sizes:
        nodes = range(offset, offset + size)
        subgraph = G.subgraph(nodes)

        assert nx.is_isomorphic(subgraph, nx.complete_graph(size))
        offset += size


@pytest.mark.parametrize("n, clusters", [(10, 3), (20, 4), (100, 5)])
def test_bridge_edges(n, clusters):
    G = cluster(n, clusters=clusters)
    sizes = G.graph["params"]["sizes"]

    starts = []
    offset = 0
    for size in sizes:
        starts.append(offset)
        offset += size

    expected = {
        frozenset((starts[i], starts[i + 1]))
        for i in range(clusters - 1)
    }
    actual = {frozenset(edge) for edge in nx.bridges(G)}

    assert actual == expected


def test_integer_labels():
    G = cluster(100)

    assert sorted(G.nodes()) == list(range(G.number_of_nodes()))


def test_metadata():
    G = cluster(10, clusters=3)

    assert G.graph == {
        "family": "cluster",
        "params": {"clusters": 3, "sizes": [4, 3, 3]},
    }


def test_deterministic():
    a = cluster(100, seed=0)
    b = cluster(100, seed=42)

    assert nx.utils.graphs_equal(a, b)

def test_small_graph_adjusts_clusters():
    G = cluster(6)

    assert G.number_of_nodes() == 6
    assert G.graph["params"]["clusters"] == 3
    assert G.graph["params"]["sizes"] == [2, 2, 2]
    assert nx.is_connected(G)

@pytest.mark.parametrize(
    "n, clusters",
    [(0, 4), (3, 3), (10, 0), (10, 1), (-1, 4)],
)
def test_invalid_arguments(n, clusters):
    with pytest.raises(ValueError):
        cluster(n, clusters=clusters)
