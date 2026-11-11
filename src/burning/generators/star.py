

import networkx as nx

from burning.generators.registry import register


@register("star")
def star(n: int, *, seed: int | None = None) -> nx.Graph:
    """N vericies are connected in a single line or chain without branches or loops
    """
    if n < 0:
            raise ValueError(f"star needs n >= 0 (got {n})")
    G = nx.star_graph(n)
    G.graph["family"] = "star"
    G.graph["params"] = {}
    return G