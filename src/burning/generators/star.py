

import networkx as nx

from burning.generators.registry import register


@register("star")
def star(n: int, *, seed: int | None = None) -> nx.Graph:
    """Centre vertex 0 joined to n - 1 leaves, so exactly n vertices. Deterministic; seed is ignored."""
    if n < 2:
        raise ValueError(f"star needs n >= 2 (got {n})")
    G = nx.star_graph(n - 1)  # star_graph(k) has k leaves plus the centre
    G.graph["family"] = "star"
    G.graph["params"] = {}
    return G
