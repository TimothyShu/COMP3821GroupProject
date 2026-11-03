"""Maximum eigenvector centrality heuristic for eigengraph centrality algorithm for graph burning (owner: Antyabha).

Rank every vertex by its eigenvector centrality score. Burn the vertex with the highest score and 
then burn the vertex with the next highest score in the subgraph of unburned vertices. Repeat until all vertices are burned.
"""

from collections.abc import Hashable

import networkx as nx

from burning.algorithms.registry import register

def spread(G: nx.Graph, burned: set[Hashable]) -> set[Hashable]:
    """Burns neighbours and updates the graph."""
    spreaded: set[Hashable] = set()
    for burnt_node in burned:
        spreaded.update(G.neighbors(burnt_node))
    return spreaded - burned

def sorted_vertex_eigenvector(G: nx.Graph) -> list[Hashable]:
    """Sorted by highest eigenvector centrality first. Ties keep G's node order."""
    if G.number_of_edges() == 0:
        return list(G.nodes())
    try:
        c = nx.eigenvector_centrality(G, max_iter=1000, tol=1e-8)
    except nx.PowerIterationFailureConvergence:
        c = nx.eigenvector_centrality_numpy(G)

    return sorted(G.nodes(), key=lambda v: (-c[v], v))

def mech(G: nx.Graph) -> list[Hashable]:
    """Burning sequence for G, sources in ignition order. Does not modify G."""
    burned: set[Hashable] = set()
    sequence: list[Hashable] = []
    while len(burned) < G.number_of_nodes():
        burned.update(spread(G, burned))  # step 1: fire spreads
        remaining = [v for v in G.nodes() if v not in burned]
        if remaining:  # step 2: light the most central unburned vertex
            source = sorted_vertex_eigenvector(G.subgraph(remaining))[0]
            burned.add(source)
            sequence.append(source)
    return sequence

@register("eigen_centrality")
def eigen_centrality(G: nx.Graph) -> list[Hashable]:
    return mech(G)[0]