"""Scale-free networks using Barabasi-Albert preferential attachment (owner: Nathaniel)."""

import networkx as nx

from burning.generators.registry import register


@register("scale_free")
def scale_free(n: int, *, seed: int | None = None, m: int = 2) -> nx.Graph:
    """Barabasi-Albert graph with n vertices and m edges per new vertex.

    New vertices preferentially attach to existing high-degree vertices.
    The seed controls randomness for reproducible experiments.
    """
    if n < 3:
        raise ValueError(f"scale_free needs n >= 3 (got {n})")
    if not 1 <= m < n:
        raise ValueError(f"scale_free needs 1 <= m < n (got m={m}, n={n})")

    G = nx.barabasi_albert_graph(n, m, seed=seed)

    G.graph["family"] = "scale_free"
    G.graph["params"] = {"m": m}

    return G
