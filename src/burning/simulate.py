"""Shared burning model. Every algorithm is scored with these functions, never its own count.

Round 1: source x_1 is ignited. Each later round t: fire first spreads to every neighbour of a
burned vertex, then source x_t (if any remain) is ignited.
"""

from collections.abc import Hashable, Sequence
from itertools import product

import networkx as nx


def burn_times(G: nx.Graph, seq: Sequence[Hashable]) -> dict[Hashable, int]:
    """Round in which each vertex burns. Raises ValueError if G never fully burns."""
    if not seq:
        raise ValueError("empty burning sequence")
    time: dict[Hashable, int] = {}
    frontier: list[Hashable] = []
    t = 0
    while len(time) < G.number_of_nodes():
        t += 1
        new = []
        for u in frontier:
            for v in G[u]:
                if v not in time:
                    time[v] = t
                    new.append(v)
        if t <= len(seq) and seq[t - 1] not in time:
            time[seq[t - 1]] = t
            new.append(seq[t - 1])
        if not new and t >= len(seq):
            raise ValueError("fire cannot reach every vertex (graph disconnected?)")
        frontier = new
    return time


def burning_rounds(G: nx.Graph, seq: Sequence[Hashable]) -> int:
    """Rounds until every vertex is burned. Can exceed len(seq) if sources run out early."""
    return max(burn_times(G, seq).values())


def is_burning_sequence(G: nx.Graph, seq: Sequence[Hashable]) -> bool:
    """Strict definition: each source is unburned when chosen and G is burned by round len(seq)."""
    time = burn_times(G, seq)
    # x_i is fresh iff no neighbour burned before round i (else the fire reached it first)
    fresh = all(
        time[x] == i and all(time[u] >= i for u in G[x]) for i, x in enumerate(seq, start=1)
    )
    return fresh and max(time.values()) == len(seq)


def exact_burning_number(G: nx.Graph, max_n: int = 16) -> int:
    """Brute-force b(G), for testing on small graphs only.

    b(G) <= k  iff  some x_1..x_k satisfy N_{k-1}[x_1] U N_{k-2}[x_2] U ... U N_0[x_k] = V(G).
    """
    n = G.number_of_nodes()
    if n > max_n:
        raise ValueError(f"exact solver limited to n <= {max_n} (got {n})")
    nodes = list(G)
    bit = {v: 1 << i for i, v in enumerate(nodes)}
    dist = dict(nx.all_pairs_shortest_path_length(G))
    full = (1 << n) - 1
    k = 1
    while True:
        # balls[i][j] = vertices within radius k-1-i of nodes[j], as a bitmask
        balls = [
            [sum(bit[u] for u, d in dist[v].items() if d <= k - 1 - i) for v in nodes]
            for i in range(k)
        ]
        for combo in product(range(n), repeat=k):
            mask = 0
            for i, j in enumerate(combo):
                mask |= balls[i][j]
            if mask == full:
                return k
        k += 1
