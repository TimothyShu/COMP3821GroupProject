"""Complete d-ary trees (owner: Tim)."""

import networkx as nx

from burning.generators.registry import register


@register("dary_tree")
def dary_tree(n: int, *, seed: int | None = None, d: int = 2) -> nx.Graph:
    """Complete d-ary tree on exactly n vertices, filled level by level from root 0.

    Deterministic, so `seed` is ignored.
    """
    if n < 1:
        raise ValueError(f"dary_tree needs n >= 1 (got {n})")
    if d < 2:
        raise ValueError(f"dary_tree needs d >= 2 (got {d}); d = 1 is a path")
    G = nx.full_rary_tree(d, n)
    G.graph["family"] = "dary_tree"
    G.graph["params"] = {"d": d}
    return G
