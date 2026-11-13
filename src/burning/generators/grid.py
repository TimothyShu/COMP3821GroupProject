
"""2D rectangular grid graphs (owner: Nathaniel)."""

from math import isqrt

import networkx as nx

from burning.generators.registry import register


@register("grid")
def grid(n: int, *, seed: int | None = None) -> nx.Graph:
    """2D grid with at most n vertices, using near-square dimensions.

    Vertices are connected to their horizontal and vertical neighbours.
    The graph is deterministic, so seed is ignored.
    """
    if n < 4:
        raise ValueError(f"grid needs n >= 4 (got {n})")

    rows = isqrt(n)
    cols = n // rows

    G = nx.grid_2d_graph(rows, cols)
    G = nx.convert_node_labels_to_integers(G)

    G.graph["family"] = "grid"
    G.graph["params"] = {"rows": rows, "cols": cols}

    return G
