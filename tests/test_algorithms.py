"""Contract tests run against every registered algorithm on every registered graph family.

Algorithm-specific tests go in tests/test_<algorithm>.py.
"""

import pytest

from burning.algorithms import ALGORITHMS
from burning.generators import GENERATORS
from burning.simulate import burning_rounds

SIZES = [10, 100, 1000]


@pytest.mark.parametrize("n", SIZES)
@pytest.mark.parametrize("family", GENERATORS)
@pytest.mark.parametrize("alg", ALGORITHMS)
def test_sequence_burns_graph(alg, family, n):
    G = GENERATORS[family](n, seed=0)
    seq = ALGORITHMS[alg](G)
    assert seq, "sequence must be non-empty"
    assert all(v in G for v in seq), "sources must be vertices of G"
    assert burning_rounds(G, seq) >= 1  # raises if G never fully burns


@pytest.mark.parametrize("family", GENERATORS)
@pytest.mark.parametrize("alg", ALGORITHMS)
def test_deterministic(alg, family):
    G = GENERATORS[family](100, seed=0)
    assert ALGORITHMS[alg](G) == ALGORITHMS[alg](G)


@pytest.mark.parametrize("alg", ALGORITHMS)
def test_does_not_modify_graph(alg):
    G = GENERATORS["barbell"](50)
    before = (set(G.nodes), set(G.edges), dict(G.graph))
    ALGORITHMS[alg](G)
    assert (set(G.nodes), set(G.edges), dict(G.graph)) == before
