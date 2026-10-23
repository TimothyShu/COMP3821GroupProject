import math

import networkx as nx
import pytest

from burning.simulate import burning_rounds, exact_burning_number, is_burning_sequence


def test_optimal_path_sequence():
    # P_9 = 0..8 covered by N_2[2] = {0..4}, N_1[6] = {5,6,7}, N_0[8] = {8}
    G = nx.path_graph(9)
    assert is_burning_sequence(G, [2, 6, 8])
    assert burning_rounds(G, [2, 6, 8]) == 3


def test_rounds_can_exceed_sequence_length():
    G = nx.path_graph(10)
    assert burning_rounds(G, [0]) == 10
    assert not is_burning_sequence(G, [0])


def test_source_reached_by_fire_is_not_strict():
    G = nx.path_graph(3)
    assert burning_rounds(G, [1, 0]) == 2  # 0 already burns in round 2
    assert not is_burning_sequence(G, [1, 0])


def test_disconnected_or_empty_raises():
    with pytest.raises(ValueError):
        burning_rounds(nx.Graph([(0, 1), (2, 3)]), [0])
    with pytest.raises(ValueError):
        burning_rounds(nx.path_graph(3), [])


@pytest.mark.parametrize("n", range(1, 17))
def test_exact_path_is_ceil_sqrt_n(n):
    # Bonato, Janssen, Roshanbin (2016): b(P_n) = ceil(sqrt(n))
    assert exact_burning_number(nx.path_graph(n)) == math.isqrt(n - 1) + 1


@pytest.mark.parametrize("n", range(3, 15))
def test_exact_star_is_two(n):
    assert exact_burning_number(nx.star_graph(n - 1)) == 2
