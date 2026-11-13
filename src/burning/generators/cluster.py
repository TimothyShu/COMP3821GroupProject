
"""Cluster graphs: dense cliques connected by sparse bridges (owner: Nathaniel)."""

import networkx as nx

from burning.generators.registry import register


@register("cluster")
def cluster(n: int, *, seed: int | None = None, clusters: int = 4) -> nx.Graph:
    """Chain of complete graphs connected by single bridge edges.

    Distribute n vertices as evenly as possible across the clusters.
    Each cluster is a clique, and consecutive clusters are joined
    by one edge. The graph is deterministic, so seed is ignored.
    """
    if clusters < 2:
        raise ValueError(f"cluster needs at least 2 clusters (got {clusters})")
    if n < 4:
        raise ValueError(f"cluster needs n >= 4 (got {n})")

    clusters = min(clusters, n // 2)

    base, extra = divmod(n, clusters)
    sizes = [base + (1 if i < extra else 0) for i in range(clusters)]

    G = nx.disjoint_union_all([nx.complete_graph(size) for size in sizes])

    # Connect consecutive clusters using one bridge edge each.
    starts = []
    offset = 0
    for size in sizes:
        starts.append(offset)
        offset += size

    for i in range(clusters - 1):
        G.add_edge(starts[i], starts[i + 1])

    G.graph["family"] = "cluster"
    G.graph["params"] = {"clusters": clusters, "sizes": sizes}

    return G
