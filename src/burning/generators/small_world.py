"""Watts-Strogatz small-world networks (owner: Tim). Extension family."""

import networkx as nx

from burning.generators.registry import register


@register("small_world")
def small_world(n: int, *, seed: int | None = None, k: int = 4, p: float = 0.1) -> nx.Graph:
    """Ring of n vertices, each joined to its k nearest neighbours, edges rewired with prob. p.

    Resampled until connected (nx.connected_watts_strogatz_graph). p = 0 is the ring lattice,
    p = 1 is close to a random graph.
    """
    if k % 2 or not 2 <= k < n:
        raise ValueError(f"small_world needs even k with 2 <= k < n (got k={k}, n={n})")
    if not 0 <= p <= 1:
        raise ValueError(f"p must be in [0, 1] (got {p})")
    G = nx.connected_watts_strogatz_graph(n, k, p, seed=seed)
    G.graph["family"] = "small_world"
    G.graph["params"] = {"k": k, "p": p}
    return G
