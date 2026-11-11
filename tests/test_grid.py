
import math

import networkx as nx
import pytest

from burning.generators.grid import grid


@pytest.mark.parametrize("n", [4, 6, 7, 10, 15, 100, 1000])
def test_size_and_structure(n):
    G = grid(n)
    rows = math.isqrt(n)
    cols = n // rows

    assert G.number_of_nodes() == rows * cols
    assert G.number_of_nodes() <= n
    assert nx.is_connected(G)

    expected = nx.grid_2d_graph(rows, cols)
    assert nx.is_isomorphic(G, expected)


@pytest.mark.parametrize("n", [4, 10, 100, 1000])
def test_edge_count(n):
    G = grid(n)
    rows = math.isqrt(n)
    cols = n // rows

    expected_edges = rows * (cols - 1) + cols * (rows - 1)

    assert G.number_of_edges() == expected_edges


@pytest.mark.parametrize("n", [4, 10, 100, 1000])
def test_vertex_degrees(n):
    G = grid(n)

    assert all(2 <= degree <= 4 for _, degree in G.degree())


def test_integer_labels():
    G = grid(100)

    assert sorted(G.nodes()) == list(range(G.number_of_nodes()))


def test_metadata():
    G = grid(100)

    assert G.graph == {
        "family": "grid",
        "params": {"rows": 10, "cols": 10},
    }


def test_deterministic():
    a = grid(100, seed=0)
    b = grid(100, seed=42)

    assert nx.utils.graphs_equal(a, b)


@pytest.mark.parametrize("n", [0, 1, 2, 3, -1])
def test_invalid_arguments(n):
    with pytest.raises(ValueError):
        grid(n)
