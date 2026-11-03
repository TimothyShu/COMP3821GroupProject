import networkx as nx

from burning.generators.registry import register


@register("path")
def path(n: int, *, seed: int | None = None) -> nx.Graph:
    """N vericies are connected in a single line or chain without branches or loops
    """
    if n < 1:
            raise ValueError(f"path needs n >= 1 (got {n})")
    G = nx.path_graph(n)
    G.graph["family"] = "path"
    G.graph["params"] = {}
    return G