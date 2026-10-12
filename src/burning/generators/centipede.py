import networkx as nx

from burning.generators.registry import register


@register("centipede")
def centipede(n: int, *, seed: int | None = None) -> nx.Graph:
    """Path of n // 2 spine vertices, each with one pendant leaf. Odd n gives n - 1 vertices."""
    k = n // 2
    if k < 1:
        raise ValueError("centipede needs n >= 2")

    G = nx.path_graph(k)
    G.add_edges_from((i, k + i) for i in range(k))

    G = nx.convert_node_labels_to_integers(G)
    G.graph["family"] = "centipede"
    G.graph["params"] = {}
    return G
