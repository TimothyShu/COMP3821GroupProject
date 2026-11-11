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
    """Sort by component-wise eigenvector centrality, preserving node order on ties.

    A power iteration can converge very slowly on long paths and barbell graphs.
    Solve each connected component directly instead; this also makes the ranking
    well-defined for disconnected residual graphs.
    """
    if G.number_of_edges() == 0:
        return list(G.nodes())

    centrality: dict[Hashable, float] = {}
    for nodes in nx.connected_components(G):
        component = G.subgraph(nodes)
        if len(nodes) == 1:
            centrality[next(iter(nodes))] = 1.0
        elif len(nodes) == 2:
            centrality.update({node: 1 / 2**0.5 for node in nodes})
        else:
            centrality.update(
                nx.eigenvector_centrality_numpy(
                    component,
                    max_iter=max(1_000, 100 * len(nodes)),
                    tol=1e-10,
                )
            )

    node_order = {node: i for i, node in enumerate(G)}
    # Ignore tiny solver noise so mathematically tied vertices use node order.
    return sorted(G, key=lambda v: (-round(centrality[v], 10), node_order[v]))

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
    return mech(G)