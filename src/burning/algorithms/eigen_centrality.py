"""Maximum eigenvector centrality heuristic for eigengraph centrality algorithm for graph burning (owner: Antyabha).

Rank every vertex by its eigenvector centrality score. Burn the vertex with the highest score and 
then burn the vertex with the next highest score in the subgraph of unburned vertices. Repeat until all vertices are burned.
"""

from collections.abc import Hashable

import networkx as nx
import numpy as np
import scipy.linalg

from burning.algorithms.registry import register


def spread(G: nx.Graph, burned: set[Hashable]) -> set[Hashable]:
    """Burns neighbours and updates the graph."""
    spreaded: set[Hashable] = set()
    for burnt_node in burned:
        spreaded.update(G.neighbors(burnt_node))
    return spreaded - burned

def _perron_vector(G: nx.Graph) -> dict[Hashable, float]:
    """Eigenvector centrality of a connected graph, unit norm.

    nx.eigenvector_centrality_numpy runs ARPACK from a random start vector, so tied
    vertices can swap order between runs. A dense
    symmetric solve has no random start: the same graph always gives the same vector.
    """
    
    A = nx.to_numpy_array(G)
    _, vec = scipy.linalg.eigh(A, subset_by_index=[len(A) - 1, len(A) - 1])
    v = np.abs(vec[:, 0])  # the top eigenvector of a connected graph has one sign
    return dict(zip(G, v / np.linalg.norm(v)))


def sorted_vertex_eigenvector(G: nx.Graph) -> list[Hashable]:
    """Sort by component-wise eigenvector centrality, preserving node order on ties.

    Each connected component is solved on its own, which keeps the ranking
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
            centrality.update(_perron_vector(component))

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